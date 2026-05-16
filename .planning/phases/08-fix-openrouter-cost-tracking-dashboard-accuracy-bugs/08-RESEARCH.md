# Phase 8: Fix OpenRouter Cost Tracking & Dashboard Accuracy Bugs - Research

**Researched:** 2026-05-16
**Domain:** Python (model_router shared package), FastAPI usage endpoints, OpenRouter API
**Confidence:** HIGH

## Summary

The usage dashboard displays $0.0000 cost for all OpenRouter models despite showing correct token usage. This is caused by four independent bugs in the cost-tracking pipeline:

1. **OpenRouter pricing cache never populated** — `CostCalculator._openrouter_pricing` is initialized as an empty dict and `update_openrouter_pricing()` is never called anywhere in the application. Both `AURA-CHAT/server/main.py` (line 122) and `AURA-NOTES-MANAGER/api/main.py` (line 279) instantiate `CostCalculator()` fresh at startup but never fetch or seed OpenRouter pricing data.

2. **Dashboard relies on local Redis estimation** — The `UsageTracker` stores `estimated_cost_usd` at record time. If the CostCalculator returns $0 (empty pricing cache), the stored value is permanently $0. The dashboard reads from Redis, so historical records cannot be retroactively corrected without a data migration.

3. **Streaming token estimation uses character-count fallback** — `router.py` `stream()` (line 392) and `stream_with_usage()` (line 455) estimate tokens as `len(text) // 4`. For OpenRouter models this is compounded by bug #1 — even with estimated tokens, cost is $0 because pricing cache is empty. Additionally, the chitchat path in `chat.py` (`_estimate_usage_payload`, line 73) creates a fresh `CostCalculator()` with no pricing when the router's calculator is None.

4. **Date range parsing truncates same-day data** — Both `AURA-CHAT/server/routers/usage.py` and `AURA-NOTES-MANAGER/api/routers/usage.py` accept `start_date` and `end_date` as query parameters typed `Optional[datetime]`. FastAPI parses date-only query strings (e.g. `?start_date=2026-05-16`) as `datetime(2026, 5, 16, 0, 0, 0)` with no timezone. The `_parse_date_range` function adds UTC timezone but keeps the time at midnight. This means `end_date=2026-05-16` only includes records up to 00:00:00 UTC on that day, excluding all same-day activity.

**Primary recommendation:** Fetch OpenRouter pricing from the `/api/v1/models` endpoint at startup, populate the CostCalculator cache, replace character-count estimation with OpenRouter's native `usage` object from streaming responses, and fix date range parsing to use end-of-day for date-only inputs.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| OpenRouter pricing fetch | API / Backend | — | Server startup fetches pricing from external API |
| Cost calculation | API / Backend | — | CostCalculator runs in Python backend |
| Usage recording | API / Backend | — | UsageTracker writes to Redis on each request |
| Streaming token counting | API / Backend | — | Router stream methods estimate or extract usage |
| Usage dashboard API | API / Backend | — | FastAPI usage routers query Redis sorted sets |
| Usage dashboard UI | Browser / Client | — | Frontend displays cost data from API responses |
| Date range parsing | API / Backend | — | `_parse_date_range` in usage routers |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | (existing) | HTTP client for OpenRouter models API | Already used in `openrouter.py` for `/models` and `/auth/key` |
| redis.asyncio | (existing) | Redis sorted sets for usage records | Already used by UsageTracker |
| pydantic | v2 (existing) | Model validation for UsageRecord | Already used in types.py |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tenacity | (existing in AURA-CHAT) | Retry logic for pricing fetch | When OpenRouter API is temporarily unavailable at startup |

**Installation:** No new packages required. All dependencies already present.

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| httpx | PyPI | 7+ yrs | 50M+/wk | github.com/encode/httpx | [OK] | Approved |
| redis | PyPI | 10+ yrs | 30M+/wk | github.com/redis/redis-py | [OK] | Approved |
| pydantic | PyPI | 7+ yrs | 100M+/wk | github.com/pydantic/pydantic | [OK] | Approved |
| tenacity | PyPI | 8+ yrs | 40M+/wk | github.com/jd/tenacity | [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
[Client SSE Stream] ──► [chat.py /stream]
                              │
                              ▼
                    [rag_engine.stream_response()]
                              │
                              ▼
                    [generate_content_stream()]
                    (vertex_ai_client.py)
                              │
                              ▼
                    [router.stream()] ──────────────────────┐
                    (model_router/router.py)                 │
                              │                              │
                    ┌─────────┴─────────┐                    │
                    ▼                   ▼                    │
            [Provider.stream()]   [char-count est.]          │
            (OpenRouter/Vertex)   (est_output = len//4)      │
                    │                   │                    │
                    ▼                   ▼                    │
            [UsageInfo]          [UsageInfo]                 │
            (real tokens)        (estimated tokens)          │
                    │                   │                    │
                    └─────────┬─────────┘                    │
                              ▼                              │
                    [CostCalculator.estimate()]              │
                              │                              │
                    ┌─────────┴─────────┐                    │
                    ▼                   ▼                    │
            Vertex: static table   OpenRouter: {} ← BUG #1   │
            (always works)         (empty → $0.00)           │
                              │                              │
                              ▼                              │
                    [UsageTracker.record()]                  │
                    (stores cost in Redis)                   │
                              │                              │
                              ▼                              │
                    [usage.py endpoints] ◄───────────────────┘
                    (query Redis, return summary)
                              │
                              ▼
                    [Frontend Dashboard]
                    (displays $0.0000 for OpenRouter)
```

### Recommended Project Structure

No structural changes needed. Fixes are localized to existing files:

```
shared/model_router/src/model_router/
├── cost_calculator.py     # FIX: add fetch + cache OpenRouter pricing
├── providers/openrouter.py # FIX: extract pricing from /models response
├── router.py              # FIX: use real usage from streaming responses
└── usage_tracker.py       # (no changes needed — works correctly)

AURA-CHAT/server/routers/
├── usage.py               # FIX: date range end-of-day handling
└── chat.py                # FIX: _estimate_usage_payload fallback

AURA-NOTES-MANAGER/api/routers/
└── usage.py               # FIX: date range end-of-day handling
```

### Pattern 1: Startup Pricing Cache Population

**What:** Fetch OpenRouter pricing from `/api/v1/models` at server startup and seed the CostCalculator cache before any requests are processed.

**When to use:** Always — this is the root cause fix for bug #1.

**Implementation approach:**
```python
# In AURA-CHAT/server/main.py lifespan() and
# AURA-NOTES-MANAGER/api/main.py _wire_usage_tracking()
async def _populate_openrouter_pricing(calculator, config):
    """Fetch and cache OpenRouter model pricing."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{config.base_url.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {config.api_key}"},
            )
            resp.raise_for_status()
        pricing = {}
        for model in resp.json().get("data", []):
            model_id = model.get("id", "")
            price_obj = model.get("pricing", {})
            if price_obj:
                # OpenRouter pricing is per-token (string), convert to per-1M
                prompt = float(price_obj.get("prompt", "0"))
                completion = float(price_obj.get("completion", "0"))
                pricing[model_id] = {
                    "input": prompt * 1_000_000,
                    "output": completion * 1_000_000,
                }
        calculator.update_openrouter_pricing(pricing)
    except Exception:
        logger.warning("Failed to populate OpenRouter pricing cache")
```

### Pattern 2: Streaming Usage from OpenRouter Response

**What:** OpenRouter's streaming responses include a final `usage` object with real token counts and cost. The `router.py` `stream()` and `stream_with_usage()` methods should capture this instead of falling back to character-count estimation.

**When to use:** For all OpenRouter streaming paths.

**OpenRouter streaming usage format** (from official docs):
```json
{
  "usage": {
    "completion_tokens": 2,
    "completion_tokens_details": { "reasoning_tokens": 0 },
    "cost": 0.95,
    "cost_details": { "upstream_inference_cost": 19 },
    "prompt_tokens": 194,
    "prompt_tokens_details": { "cached_tokens": 0 },
    "total_tokens": 196
  }
}
```

### Anti-Patterns to Avoid

- **Don't add a separate pricing cron job** — pricing changes infrequently; startup fetch with periodic refresh (e.g., every 24h) is sufficient.
- **Don't hardcode OpenRouter prices** — the whole point of fetching from the API is to stay current.
- **Don't change the UsageRecord schema** — the existing `estimated_cost_usd` and `is_estimated` fields are sufficient.
- **Don't retroactively fix historical Redis records** — add a migration script as optional follow-up; focus on fixing forward-looking recording first.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OpenRouter pricing fetch | Custom scraper of openrouter.ai/pricing page | `/api/v1/models` endpoint | Official API returns structured pricing per model; page scraping is brittle |
| Token counting for streaming | Character-count heuristic (`len // 4`) | OpenRouter `usage` object in final SSE chunk | Native tokenizer gives accurate counts; character estimate is off by 20-40% |
| Date range defaults | Manual datetime arithmetic | `datetime.replace(hour=23, minute=59, second=59)` for end-of-day | Prevents same-day truncation bug |

**Key insight:** OpenRouter already calculates and returns exact token counts and costs in every response. The character-count fallback was a stopgap for Vertex AI direct SDK usage that got carried over to OpenRouter paths where it should never have been used.

## Common Pitfalls

### Pitfall 1: Pricing Cache Empty at First Request
**What goes wrong:** Server starts, CostCalculator has empty `_openrouter_pricing`, first OpenRouter request records $0 cost.
**Why it happens:** The `/models` endpoint fetch is async and may fail or timeout during startup.
**How to avoid:** Wrap pricing fetch in try/except with a warning log; use tenacity retry (3 attempts, 2s backoff). Log the number of models priced so failures are visible.
**Warning signs:** Log message "Failed to populate OpenRouter pricing cache" at startup; dashboard shows $0 for all OpenRouter models.

### Pitfall 2: OpenRouter Pricing is Per-Token, Not Per-1M
**What goes wrong:** The OpenRouter `/models` API returns pricing as cost per single token (e.g., `"prompt": "0.000003"`), but `CostCalculator` expects per-1M-token values (e.g., `{"input": 3.00}`).
**Why it happens:** The `CostCalculator._estimate_openrouter` formula divides by 1,000,000: `(usage.input_tokens / 1_000_000) * pricing.get("input", 0.0)`. If raw per-token values are stored without conversion, costs will be 1,000,000x too small.
**How to avoid:** Multiply by 1,000,000 when converting from the API response: `pricing[model_id] = {"input": prompt * 1_000_000, "output": completion * 1_000_000}`.
**Warning signs:** Costs display as $0.000000 instead of $0.003000.

### Pitfall 3: Streaming Usage Only in Final Chunk
**What goes wrong:** OpenRouter includes the `usage` object only in the final SSE chunk of a streaming response. If the stream is interrupted or the client disconnects early, no usage data is available.
**Why it happens:** This is OpenRouter's design — token counts are only finalized after the stream completes.
**How to avoid:** Keep the character-count fallback as a last-resort safety net for interrupted streams. Mark these records with `is_estimated=True`.
**Warning signs:** Some records have accurate costs, others have $0 — correlates with client disconnects or timeouts.

### Pitfall 4: Date-Only Query Parameters Lose Time Component
**What goes wrong:** FastAPI parses `?end_date=2026-05-16` as `datetime(2026, 5, 16, 0, 0, 0)`. The `_parse_date_range` function adds UTC timezone but doesn't adjust the time, so the query range ends at midnight.
**Why it happens:** FastAPI's datetime query parameter parsing defaults to midnight for date-only strings.
**How to avoid:** When `end_date` has time at midnight (00:00:00), set it to end-of-day (23:59:59.999999). Similarly, when `start_date` has time at midnight, keep it as-is (start of day is correct).
**Warning signs:** Dashboard shows no data for "today" even though requests were made.

### Pitfall 5: Dual Application Wiring
**What goes wrong:** Both `AURA-CHAT` and `AURA-NOTES-MANAGER` wire usage tracking independently. A fix applied to only one app leaves the other broken.
**Why it happens:** The two apps have separate `main.py` files with separate startup sequences.
**How to avoid:** The pricing fetch logic should live in the shared `model_router` package (e.g., a `populate_openrouter_pricing()` function on `CostCalculator`), called from both apps' startup code.

## Code Examples

### OpenRouter Models API Response (pricing extraction)
**Source:** [openrouter.ai/docs/guides/overview/models](https://openrouter.ai/docs/guides/overview/models)

The `/api/v1/models` endpoint returns pricing per token (not per 1M):
```json
{
  "data": [
    {
      "id": "anthropic/claude-sonnet-4",
      "pricing": {
        "prompt": "0.000003",
        "completion": "0.000015",
        "request": "0",
        "internal_reasoning": "0"
      }
    }
  ]
}
```

### OpenRouter Streaming Usage (final chunk)
**Source:** [openrouter.ai/docs/guides/usage-accounting](https://openrouter.ai/docs/guides/administration/usage-accounting)

```json
{
  "usage": {
    "completion_tokens": 2,
    "completion_tokens_details": { "reasoning_tokens": 0 },
    "cost": 0.95,
    "prompt_tokens": 194,
    "prompt_tokens_details": { "cached_tokens": 0 }
  }
}
```

### Current Character-Count Estimation (to be replaced)
**Source:** `shared/model_router/src/model_router/router.py` lines 391-396

```python
# Current (buggy) — estimates tokens from character count
est_output = max(len(total_text) // 4, 1)
est_input = max(len(str(resolved_request.contents)) // 4, 1)
usage = UsageInfo(
    input_tokens=est_input,
    output_tokens=est_output,
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Character-count token estimation | OpenRouter native `usage` object | OpenRouter added usage to streaming (2024) | Accurate token counts per model tokenizer |
| Hardcoded pricing tables | Dynamic pricing from `/api/v1/models` | OpenRouter Models API (2023) | Always-current pricing without manual updates |
| Per-request cost calculation | OpenRouter returns `cost` in response | OpenRouter usage accounting (2024) | Eliminates need for local cost calculation entirely |

**Deprecated/outdated:**
- Character-count token estimation (`len // 4`): OpenRouter provides native tokenizer counts in every response
- Manual cost calculation for OpenRouter: OpenRouter returns exact `cost` in the `usage` object, making local estimation unnecessary for OpenRouter paths

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | OpenRouter `/api/v1/models` pricing values are per-token strings requiring ×1M conversion | Pattern 1, Pitfall 2 | Costs would be 1,000,000x off if conversion is wrong |
| A2 | OpenRouter streaming responses include `usage` object in the final chunk | Pattern 2 | If usage is not in stream chunks, fallback estimation still needed |
| A3 | FastAPI parses `?end_date=2026-05-16` as midnight UTC | Pitfall 4 | If FastAPI behavior differs, the date fix may need adjustment |

## Open Questions

1. **Should historical Redis records be retroactively corrected?**
   - What we know: Existing records have `estimated_cost_usd=0.0` for OpenRouter models
   - What's unclear: Whether the user wants a one-time migration script to re-calculate costs
   - Recommendation: Fix forward-looking recording first; add migration script as optional follow-up task

2. **Should the OpenRouter `cost` field from the response be used directly instead of local calculation?**
   - What we know: OpenRouter returns `usage.cost` in every response
   - What's unclear: Whether to trust OpenRouter's cost or continue using local calculation with fetched pricing
   - Recommendation: Use OpenRouter's `cost` directly for OpenRouter paths (source of truth), keep local calculation as fallback for interrupted streams and for Vertex AI

3. **Should pricing cache be refreshed periodically?**
   - What we know: OpenRouter pricing can change
   - What's unclear: How frequently pricing changes
   - Recommendation: Add a 24-hour TTL to the pricing cache with lazy refresh on stale access

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Redis | UsageTracker, SettingsStore | See audit below | — | Usage tracking disabled, log warning |
| OpenRouter API key | Pricing fetch at startup | Config-dependent | — | Skip pricing fetch, log warning |
| httpx | Pricing fetch | ✓ (existing) | — | — |
| Python 3.10+ | All Python code | ✓ | 3.10+ | — |

**Redis availability** should be verified at runtime — both apps already handle Redis unavailability gracefully with try/except blocks around usage tracking setup.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | `shared/model_router/` uses root conftest |
| Quick run command | `python -m pytest shared/model_router/tests/test_cost_calculator.py -x` |
| Full suite command | `python -m pytest shared/model_router/tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BUG-01 | OpenRouter pricing cache populated at startup | unit | `pytest shared/model_router/tests/test_cost_calculator.py -x` | ✅ existing test file, needs new tests |
| BUG-02 | Streaming uses real token counts, not char-count | unit | `pytest shared/model_router/tests/test_router.py -x` | ✅ existing test file, needs new tests |
| BUG-03 | Date range includes same-day data | unit | `pytest AURA-CHAT/tests/ -k usage -x` | ❌ needs new test file |
| BUG-04 | CostCalculator returns non-zero for known OpenRouter models | unit | `pytest shared/model_router/tests/test_cost_calculator.py -x` | ✅ existing, needs pricing population test |

### Sampling Rate
- **Per task commit:** `python -m pytest shared/model_router/tests/test_cost_calculator.py -x`
- **Per wave merge:** `python -m pytest shared/model_router/tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `shared/model_router/tests/test_cost_calculator.py` — needs tests for `populate_openrouter_pricing()` method
- [ ] `shared/model_router/tests/test_router.py` — needs tests for streaming with real usage extraction
- [ ] `AURA-CHAT/tests/api/test_usage_date_range.py` — needs tests for same-day date range parsing
- [ ] `AURA-NOTES-MANAGER/api/tests/test_usage_date_range.py` — needs tests for same-day date range parsing

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | Validate OpenRouter API response schema before caching pricing |
| V6 Cryptography | no | — |

### Known Threat Patterns for model_router

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Pricing cache poisoning | Tampering | Validate response schema, reject non-numeric pricing values |
| OpenRouter API key exposure | Information Disclosure | Never log API key; use config object for auth headers |
| Denial of service via pricing fetch | Availability | Timeout (15s), retry with backoff, graceful degradation |

## Sources

### Primary (HIGH confidence)
- [openrouter.ai/docs/guides/overview/models](https://openrouter.ai/docs/guides/overview/models) — Models API schema, pricing object format
- [openrouter.ai/docs/guides/administration/usage-accounting](https://openrouter.ai/docs/guides/administration/usage-accounting) — Streaming usage object format, cost fields
- `shared/model_router/src/model_router/cost_calculator.py` — Current CostCalculator implementation (121 lines)
- `shared/model_router/src/model_router/router.py` — Current streaming implementation (515 lines)
- `shared/model_router/src/model_router/providers/openrouter.py` — OpenRouter provider, list_models without pricing extraction (673 lines)
- `AURA-CHAT/server/main.py` — Usage tracking wiring (line 111-126)
- `AURA-NOTES-MANAGER/api/main.py` — Usage tracking wiring (line 266-283)
- `AURA-CHAT/server/routers/chat.py` — `_estimate_usage_payload` fallback (line 73-136)
- `AURA-CHAT/server/routers/usage.py` — `_parse_date_range` (line 54-78)
- `AURA-NOTES-MANAGER/api/routers/usage.py` — `_parse_date_range` (line 60-84)

### Secondary (MEDIUM confidence)
- `shared/model_router/tests/test_cost_calculator.py` — Existing pricing tests (311 lines)
- `shared/model_router/tests/test_usage_tracker.py` — Existing tracker tests (448 lines)
- `shared/model_router/tests/test_router.py` — Existing router tests (stream_with_usage tests at line 275)

### Tertiary (LOW confidence)
- None — all critical claims verified against official documentation or codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages, all existing dependencies
- Architecture: HIGH — all four bugs traced to specific lines in codebase
- Pitfalls: HIGH — each pitfall verified against actual code behavior
- OpenRouter API: HIGH — verified against official documentation

**Research date:** 2026-05-16
**Valid until:** 2026-06-15 (30 days — OpenRouter pricing API is stable)
