# Phase 12: Usage Tracking + Cost Dashboard - Research

**Researched:** 2026-03-11
**Domain:** LLM usage instrumentation, cost estimation, Redis time-series storage, Recharts dashboard
**Confidence:** HIGH

## Summary

Phase 12 adds a usage tracking layer to the model router and exposes it through a cost dashboard. The foundation is strong: `UsageInfo` (input/output/thinking tokens) already exists in `types.py`, and both Vertex AI and OpenRouter providers already populate it in their `generate()` responses. The critical gap is that **no usage data is persisted anywhere** — `GenerateResponse.usage` is returned to callers but discarded after the request. Additionally, streaming endpoints yield `StreamChunk` (type + text only) with **no usage summary at stream completion**, so streaming requests — which are the majority of chat interactions — currently lose all token data.

The phase requires three layers: (1) a shared `UsageTracker` in the model router package that records every LLM call's token/cost data into Redis, (2) FastAPI usage query endpoints in both apps, and (3) a Recharts-based dashboard in the frontend with date-range-filtered charts. Cost estimation is provider-specific: OpenRouter returns pricing per model in its `/api/v1/models` endpoint; Vertex AI pricing must be maintained as a static lookup table; Ollama is free. The per-session cost display in the chat UI (success criterion #3) requires adding usage data to the SSE `"complete"` event so the frontend can accumulate session cost.

The existing Redis infrastructure (`SettingsStore`, `KeyManager`, `ModelCache`) provides a tested pattern for the usage tracker's storage layer — constructor-injected async Redis clients with JSON serialization. The twin-app pattern (build in AURA-CHAT, copy to AURA-NOTES-MANAGER) applies to both backend endpoints and frontend components.

**Primary recommendation:** Build a `UsageTracker` class in `shared/model_router/` that hooks into `ModelRouter.generate()` and `ModelRouter.stream()`, persists `UsageRecord` entries to Redis sorted sets keyed by timestamp, and a `CostCalculator` with cached pricing data. Use Recharts `AreaChart` + `BarChart` for the dashboard. Return usage data in the SSE `"complete"` event for per-session cost display.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| USAGE-01 | System tracks token usage and cost per request, aggregated by session, user, model, and provider | `UsageInfo` model exists. Providers populate it in `generate()`. Need: `UsageRecord` for persistence, `UsageTracker` to hook into router, `CostCalculator` for price estimation, Redis storage with multi-dimension indexing (session, user, model, provider). Streaming gap must be closed — add usage to stream completion. |
| USAGE-02 | Dashboard displays cost charts by provider, model, time period with date range filters | Recharts ^3.8.0 already specified in roadmap (not yet installed). Need: usage query API endpoints, frontend types/hooks/components, date range picker, AreaChart for time series, BarChart for provider/model breakdown. Both apps need the dashboard. |
</phase_requirements>

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `model_router` (shared) | 0.1.0 | `UsageInfo` type, router hooks | Already has token tracking types; natural home for usage tracker |
| Redis | 7+ / redis.asyncio | Usage record storage | Already used for settings, model cache, API keys; proven async pattern |
| Pydantic | >=2.0 | `UsageRecord` model, API schemas | Already used throughout; JSON serialization for Redis round-trips |
| FastAPI | 0.115+ | Usage query API endpoints | Existing API framework in both apps |
| React | 19.2 (CHAT) / 18.3 (NOTES) | Dashboard UI | Already installed |
| TanStack Query | 5.90 (CHAT) / 5.62 (NOTES) | Usage data fetching | Already used for settings hooks |
| Zustand | 5.0.11 (CHAT) / 5.0.2 (NOTES) | Date range filter state | Already used for model store |
| Vitest | 3.2.4 | Frontend component tests | Already configured in both apps |
| pytest | >=8.0 + pytest-asyncio | Backend unit tests | Already configured in model_router |

### New Dependencies
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `recharts` | ^3.8.0 | Cost dashboard charts (AreaChart, BarChart, PieChart) | Install in both AURA-CHAT/client and AURA-NOTES-MANAGER/frontend |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `recharts` | `@nivo/core` | Heavier, more opinionated — recharts already chosen in roadmap |
| `recharts` | `chart.js` + `react-chartjs-2` | Canvas-based (not SVG), harder to style with Tailwind |
| Redis sorted sets | SQLite/Firestore for usage | Redis already in stack, avoids new dependency; sorted sets handle time-range queries natively |
| Static Vertex AI pricing | API-fetched pricing | Google has no public pricing API; static table is the only option |

**Installation:**
```bash
# Frontend charting library
cd AURA-CHAT/client && npm install recharts@^3.8.0
cd AURA-NOTES-MANAGER/frontend && npm install recharts@^3.8.0
# No new Python dependencies needed — Redis + Pydantic already installed
```

## Architecture Patterns

### Recommended Project Structure

**Shared model_router additions:**
```
shared/model_router/src/model_router/
├── types.py              # Extend UsageInfo with cost; add UsageRecord
├── usage_tracker.py      # NEW: UsageTracker class (Redis persistence)
├── cost_calculator.py    # NEW: CostCalculator (pricing lookup + estimation)
├── pricing.py            # NEW: Static pricing tables + OpenRouter pricing cache
├── router.py             # MODIFY: Hook usage tracking into generate() and stream()
└── ...
```

**Backend additions (both apps):**
```
server/routers/              # AURA-CHAT
  usage.py                   # NEW: Usage query API endpoints
api/routers/                 # AURA-NOTES-MANAGER
  usage.py                   # NEW: Same endpoints (adapted)
```

**Frontend additions (both apps):**
```
src/features/usage/          # NEW feature module
  components/
    UsageDashboard.tsx       # Main dashboard page
    CostOverTimeChart.tsx    # AreaChart: daily/weekly cost over time
    CostByProviderChart.tsx  # BarChart: cost breakdown by provider
    CostByModelChart.tsx     # BarChart: cost breakdown by model
    DateRangeFilter.tsx      # Date range selector
    SessionCostBadge.tsx     # Per-session cost display (AURA-CHAT only)
    UsageSummaryCards.tsx     # Summary stat cards (total cost, requests, etc.)
  hooks/
    useUsageApi.ts           # TanStack Query hooks for usage endpoints
  UsagePage.tsx              # Page component with routing
src/types/
  usage.ts                   # Usage-related TypeScript types
```

### Pattern 1: Redis Sorted Set for Time-Series Usage Data
**What:** Store each `UsageRecord` as a JSON-serialized member in a Redis sorted set, with the score being the Unix timestamp. This enables efficient time-range queries with `ZRANGEBYSCORE`.
**When to use:** All usage record storage.
**Why:** Redis sorted sets support O(log(N)+M) time-range queries, Redis is already in the stack, and the volume (~100-1000 records/day for an academic platform) is well within Redis capabilities.

```python
# Usage record storage pattern
USAGE_KEY = "aura:usage:records"
USAGE_SESSION_KEY = "aura:usage:session:{session_id}"

class UsageTracker:
    def __init__(self, redis_client: Any) -> None:
        self._redis = redis_client

    async def record(
        self,
        usage: UsageInfo,
        model: str,
        provider: ProviderType,
        session_id: str | None = None,
        user_id: str | None = None,
        estimated_cost: float = 0.0,
    ) -> None:
        record = UsageRecord(
            timestamp=datetime.utcnow(),
            model=model,
            provider=provider,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            thinking_tokens=usage.thinking_tokens,
            estimated_cost_usd=estimated_cost,
            session_id=session_id,
            user_id=user_id,
        )
        score = record.timestamp.timestamp()
        payload = record.model_dump_json()
        # Global sorted set for dashboard queries
        await self._redis.zadd(USAGE_KEY, {payload: score})
        # Per-session sorted set for session cost display
        if session_id:
            session_key = f"aura:usage:session:{session_id}"
            await self._redis.zadd(session_key, {payload: score})
```

### Pattern 2: Router-Level Usage Hook (Decorator Pattern)
**What:** Hook usage tracking into `ModelRouter.generate()` and `ModelRouter.stream()` so every LLM call is automatically recorded without callers needing to change.
**When to use:** Must be the integration point — not the individual endpoints.
**Why:** There are multiple call paths (RAG engine, chitchat, entity extraction, direct generation). Hooking at the router level ensures 100% coverage.

```python
# In ModelRouter
async def generate(self, request=None, **kwargs):
    resolved_request = self._build_request(request, kwargs)
    provider = self._resolve_provider(resolved_request)
    response = await provider.generate(resolved_request)
    # NEW: Track usage after successful generation
    if self._usage_tracker:
        cost = self._cost_calculator.estimate(
            response.usage, response.model_used, response.provider
        )
        await self._usage_tracker.record(
            usage=response.usage,
            model=response.model_used,
            provider=response.provider,
            estimated_cost=cost,
            session_id=resolved_request.metadata.get("session_id"),
            user_id=resolved_request.metadata.get("user_id"),
        )
    return response
```

### Pattern 3: Metadata Propagation for Attribution
**What:** Extend `GenerateRequest` with optional `metadata` dict for `session_id` and `user_id` so usage records can be attributed.
**When to use:** All LLM call sites that have session/user context.
**Why:** The router needs to know who made the request and in what session. Adding a metadata dict is non-breaking (optional field with default).

```python
class GenerateRequest(BaseModel):
    # ... existing fields ...
    metadata: dict[str, Any] = Field(default_factory=dict)
    # Used by callers: metadata={"session_id": "...", "user_id": "..."}
```

### Pattern 4: Streaming Usage Summary
**What:** After stream completes, make a separate non-streaming call to get usage data, OR track stream chunks and estimate tokens from character count.
**When to use:** For streaming chat responses.
**Why:** Streaming providers typically don't return usage in the stream chunks. Two approaches:
- **OpenRouter**: Returns usage in the final stream event (`usage` field in the last chunk with `finish_reason="stop"`) — this needs extraction in the provider
- **Vertex AI**: The `generate_content_async(stream=True)` response aggregates usage in `usage_metadata` on the response object after iteration completes
- **Estimation fallback**: Count output characters and estimate tokens (1 token ≈ 4 chars) for cases where provider data is unavailable

### Anti-Patterns to Avoid
- **Don't track usage at endpoint level:** Multiple endpoints call the same LLM. Tracking at the router ensures no leaks.
- **Don't use Firestore for real-time usage:** Redis sorted sets are faster for time-range queries and aggregation. Firestore round-trips are too slow for per-request writes.
- **Don't compute aggregates on every dashboard load:** Pre-compute daily/hourly summaries on write or use a periodic background task.
- **Don't hardcode pricing in the tracker:** Keep pricing in a separate `CostCalculator` with a cacheable pricing table so it can be updated independently.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Time-series storage | Custom DB schema | Redis sorted sets (`ZADD`/`ZRANGEBYSCORE`) | O(log N) insert, O(log N + M) range queries, already in stack |
| Cost charts | Custom SVG/Canvas | Recharts `AreaChart`, `BarChart` | Composable React components, SVG-based, Tailwind-friendly |
| Date range filtering | Custom date logic | Simple `start_date`/`end_date` query params + browser `<input type="date">` | Keep it simple; no need for date picker library |
| Token-to-cost conversion | Inline math everywhere | Centralized `CostCalculator` class | Pricing varies by provider, model, and token type (input vs output) |
| Usage aggregation | SQL GROUP BY equivalent | Redis `ZRANGEBYSCORE` + Python aggregation | Volume is small enough (<10K records/month); no need for analytics DB |

**Key insight:** The usage tracking system is essentially a lightweight analytics pipeline. For the academic scale (10-100 users, 100-1000 requests/day), Redis sorted sets with Python-side aggregation is perfectly adequate. Don't over-engineer with Kafka, ClickHouse, or time-series databases.

## Common Pitfalls

### Pitfall 1: Streaming Requests Lose Usage Data
**What goes wrong:** `ModelRouter.stream()` yields `StreamChunk` objects but never returns a `GenerateResponse` with `UsageInfo`. If usage tracking only hooks `generate()`, all streaming chat responses (the majority) are invisible.
**Why it happens:** The streaming protocol was designed for progressive rendering, not telemetry.
**How to avoid:** Two strategies:
  1. For Vertex AI: After stream iteration completes, access `usage_metadata` on the response object
  2. For OpenRouter: The OpenAI SDK's stream `usage` field in the final chunk — extract it via `stream_options={"include_usage": True}` parameter
  3. Fallback: Estimate tokens from output character count (1 token ≈ 4 English chars)
**Warning signs:** Dashboard shows 0 tokens for chat sessions despite active usage.

### Pitfall 2: Cost Calculation Varies Wildly by Provider
**What goes wrong:** Vertex AI charges per character (not per token), OpenRouter per token, Ollama is free. Applying one formula to all providers produces wrong numbers.
**Why it happens:** No unified pricing model across LLM providers.
**How to avoid:** Provider-specific cost calculation in `CostCalculator`:
  - **OpenRouter**: Use pricing from `/api/v1/models` response (`pricing.prompt`, `pricing.completion` in USD per token)
  - **Vertex AI**: Static pricing table (per 1M characters for input, per 1M characters for output — varies by model)
  - **Ollama**: Always $0.00
**Warning signs:** Cost estimates differ >10x from actual provider bills.

### Pitfall 3: Redis Memory Growth with Unbounded Usage Records
**What goes wrong:** Every LLM request adds a record to Redis. Over months, this grows unbounded.
**Why it happens:** No TTL or cleanup on usage data.
**How to avoid:** Set a 90-day TTL on usage records using `EXPIREAT` on session-keyed sorted sets, and a periodic cleanup task for the global sorted set using `ZREMRANGEBYSCORE` to remove entries older than 90 days.
**Warning signs:** Redis memory usage growing linearly with time.

### Pitfall 4: Request Attribution Without Metadata Propagation
**What goes wrong:** Usage records have no `session_id` or `user_id` because the call path doesn't pass these through to the router.
**Why it happens:** The current `GenerateRequest` has no metadata field. Callers (RAG engine, chat router) know the session/user but have no way to pass it to the router.
**How to avoid:** Add an optional `metadata: dict[str, Any]` field to `GenerateRequest`. Update call sites in `rag_engine.py` and `chat.py` to include `session_id` and `user_id`. For the compatibility layer (`vertex_ai_client.py`), pass metadata through `VertexCompatModel`.
**Warning signs:** All usage records show `session_id=None`.

### Pitfall 5: Recharts Server-Side Rendering Issues
**What goes wrong:** Recharts SVG components can fail in SSR or test environments (jsdom).
**Why it happens:** Recharts uses `ResizeObserver` and SVG APIs that jsdom doesn't fully support.
**How to avoid:** Mock `ResizeObserver` in vitest setup. For component tests, test the data-fetching hooks separately from the chart rendering. Use snapshot tests sparingly for chart components.
**Warning signs:** Vitest test failures with "ResizeObserver is not defined".

### Pitfall 6: OpenRouter Pricing Data Staleness
**What goes wrong:** OpenRouter model prices change frequently. Cached pricing becomes stale, leading to inaccurate cost estimates.
**Why it happens:** Pricing is cached but never refreshed.
**How to avoid:** Cache pricing alongside model listings (already has TTL via `ModelCache`). When model list refreshes, pricing refreshes too. Mark all costs as "estimated" in the UI with a tooltip explaining the approximation.
**Warning signs:** Displayed costs diverge significantly from OpenRouter billing.

## Code Examples

### UsageRecord Model
```python
# shared/model_router/src/model_router/types.py (extend)
from datetime import datetime

class UsageRecord(BaseModel):
    """Persisted usage record for a single LLM request."""
    timestamp: datetime
    provider: ProviderType
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    estimated_cost_usd: float = 0.0
    is_estimated: bool = True  # Flag: cost is an approximation
    session_id: str | None = None
    user_id: str | None = None
    operation: str = "chat"  # chat, embed, extract
```

### CostCalculator with Provider-Specific Pricing
```python
# shared/model_router/src/model_router/cost_calculator.py
class CostCalculator:
    """Estimate USD cost from token usage and model pricing."""

    # Static Vertex AI pricing (USD per 1M tokens, as of 2026)
    _VERTEX_PRICING: dict[str, dict[str, float]] = {
        "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
        "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
        "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
    }

    def __init__(self, redis_client: Any = None) -> None:
        self._redis = redis_client
        self._openrouter_pricing: dict[str, dict[str, float]] = {}

    def estimate(
        self,
        usage: UsageInfo,
        model: str,
        provider: ProviderType,
    ) -> float:
        if provider == ProviderType.OLLAMA:
            return 0.0
        if provider == ProviderType.VERTEX_AI:
            return self._estimate_vertex(usage, model)
        if provider == ProviderType.OPENROUTER:
            return self._estimate_openrouter(usage, model)
        return 0.0

    def _estimate_vertex(self, usage: UsageInfo, model: str) -> float:
        # Normalize model name
        normalized = model.replace("models/", "")
        pricing = self._VERTEX_PRICING.get(normalized, {})
        input_cost = (usage.input_tokens / 1_000_000) * pricing.get("input", 0.0)
        output_cost = (usage.output_tokens / 1_000_000) * pricing.get("output", 0.0)
        return round(input_cost + output_cost, 6)

    def _estimate_openrouter(self, usage: UsageInfo, model: str) -> float:
        pricing = self._openrouter_pricing.get(model, {})
        input_cost = (usage.input_tokens / 1_000_000) * pricing.get("input", 0.0)
        output_cost = (usage.output_tokens / 1_000_000) * pricing.get("output", 0.0)
        return round(input_cost + output_cost, 6)
```

### Usage API Endpoint
```python
# server/routers/usage.py (AURA-CHAT pattern)
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query

router = APIRouter(prefix="/api/v1/usage", tags=["Usage"])

@router.get("/summary")
async def get_usage_summary(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    provider: str | None = Query(None),
    tracker: UsageTracker = Depends(get_usage_tracker),
) -> dict:
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    return await tracker.get_summary(
        start_date=start_date,
        end_date=end_date,
        provider=provider,
    )

@router.get("/session/{session_id}")
async def get_session_usage(
    session_id: str,
    tracker: UsageTracker = Depends(get_usage_tracker),
) -> dict:
    return await tracker.get_session_summary(session_id)
```

### Frontend Usage Dashboard (Recharts)
```typescript
// src/features/usage/components/CostOverTimeChart.tsx
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface DailyCost {
    date: string;
    cost: number;
    requests: number;
}

export const CostOverTimeChart = ({ data }: { data: DailyCost[] }) => (
    <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="date" stroke="#888" />
            <YAxis stroke="#888" tickFormatter={(v: number) => `$${v.toFixed(2)}`} />
            <Tooltip
                formatter={(value: number) => [`$${value.toFixed(4)}`, 'Cost']}
                contentStyle={{ backgroundColor: '#1A1A1A', border: '1px solid #333' }}
            />
            <Area
                type="monotone"
                dataKey="cost"
                stroke="#FFD400"
                fill="#FFD400"
                fillOpacity={0.2}
            />
        </AreaChart>
    </ResponsiveContainer>
);
```

### SSE Complete Event with Usage Data
```python
# Extension to the "complete" SSE event in chat streaming
complete_payload: Dict[str, Any] = {
    "type": "complete",
    "answer": answer,
    "sources": sources,
    "model_used": self.model_name,
    # NEW: Usage data for per-session cost display
    "usage": {
        "input_tokens": usage_info.input_tokens,
        "output_tokens": usage_info.output_tokens,
        "thinking_tokens": usage_info.thinking_tokens,
        "estimated_cost_usd": estimated_cost,
        "is_estimated": True,
    },
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No usage tracking | `UsageInfo` in `GenerateResponse` | Phase 8 (2026-03-10) | Token counts available but not persisted |
| No pricing data | OpenRouter returns pricing in model list | Already available | Cost estimation possible for OpenRouter models |
| Direct SDK calls | All calls via model router | Phase 10 (2026-03-10) | Single instrumentation point for usage tracking |

**Deprecated/outdated:**
- The original research proposed a `UsageTracker` as an in-memory accumulator — this should be Redis-backed for cross-process persistence (both apps share usage data)
- The original research mentioned Firestore for usage persistence — Redis sorted sets are more appropriate for this volume and query pattern

## Open Questions

1. **How to handle streaming usage for Vertex AI?**
   - What we know: `generate_content_async(stream=True)` returns a response object that aggregates `usage_metadata` after full iteration
   - What's unclear: Whether the compat layer (`vertex_ai_client.py`) can access this after streaming completes
   - Recommendation: In the compat layer, capture usage from the response object after iteration and pass it to the usage tracker. If not possible, use token estimation from character count.

2. **Should the cost dashboard be in AURA-CHAT, AURA-NOTES-MANAGER, or both?**
   - What we know: Success criterion #2 says "a dashboard displays cost charts" (singular). Criterion #3 says "per-session cost is visible in the chat UI" (AURA-CHAT specific). Prior research says "primarily AURA-NOTES-MANAGER for staff cost tracking"
   - What's unclear: Whether students should see the full dashboard or just per-session costs
   - Recommendation: Full dashboard in both apps (admin-only route). Per-session cost badge in AURA-CHAT only (visible to students). The dashboard route should be admin-protected; per-session cost is visible to all users.

3. **Vertex AI pricing accuracy**
   - What we know: Google doesn't expose pricing via API. Prices change periodically.
   - What's unclear: How often Gemini pricing changes
   - Recommendation: Maintain a static pricing table in `cost_calculator.py`. Mark all Vertex costs as "estimated". Include a comment with the date pricing was last verified. Add a `VERTEX_PRICING_OVERRIDE` env var for admin adjustments.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework (Python) | pytest 8+ / pytest-asyncio 0.23+ |
| Config file (Python) | `shared/model_router/pyproject.toml` [tool.pytest.ini_options] |
| Quick run (Python) | `cd shared/model_router && python -m pytest tests/ -x -q` |
| Full suite (Python) | `cd shared/model_router && python -m pytest tests/ -v` |
| Framework (Frontend) | Vitest 3.2.4 / @testing-library/react |
| Config file (Frontend) | `AURA-CHAT/client/vitest.config.ts` |
| Quick run (Frontend) | `cd AURA-CHAT/client && npx vitest run --reporter=verbose` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| USAGE-01 | UsageRecord model serialization | unit | `pytest tests/test_usage_tracker.py::test_usage_record_serialization -x` | ❌ Wave 0 |
| USAGE-01 | CostCalculator Vertex pricing | unit | `pytest tests/test_cost_calculator.py::test_vertex_pricing -x` | ❌ Wave 0 |
| USAGE-01 | CostCalculator OpenRouter pricing | unit | `pytest tests/test_cost_calculator.py::test_openrouter_pricing -x` | ❌ Wave 0 |
| USAGE-01 | UsageTracker.record() persists to Redis | unit | `pytest tests/test_usage_tracker.py::test_record_persists -x` | ❌ Wave 0 |
| USAGE-01 | Router hooks track generate() calls | integration | `pytest tests/test_router.py::test_generate_tracks_usage -x` | ❌ Wave 0 |
| USAGE-01 | Streaming usage captured | unit | `pytest tests/test_usage_tracker.py::test_stream_usage -x` | ❌ Wave 0 |
| USAGE-02 | Usage summary endpoint returns data | unit | Backend test via pytest | ❌ Wave 0 |
| USAGE-02 | Date range filtering works | unit | Backend test via pytest | ❌ Wave 0 |
| USAGE-02 | Dashboard renders with mock data | unit | `npx vitest run src/features/usage -x` | ❌ Wave 0 |
| USAGE-02 | Session cost badge displays | unit | `npx vitest run src/features/usage -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd shared/model_router && python -m pytest tests/ -x -q`
- **Per wave merge:** Full Python + Frontend suites
- **Phase gate:** All test suites green

### Wave 0 Gaps
- [ ] `shared/model_router/tests/test_usage_tracker.py` — covers USAGE-01 (record persistence, retrieval, aggregation)
- [ ] `shared/model_router/tests/test_cost_calculator.py` — covers USAGE-01 (pricing calculation)
- [ ] `AURA-CHAT/server/tests/test_usage_router.py` — covers USAGE-02 (API endpoints)
- [ ] `AURA-CHAT/client/src/features/usage/**/*.test.tsx` — covers USAGE-02 (dashboard components)
- [ ] Recharts install: `npm install recharts@^3.8.0` in both frontends

## Sources

### Primary (HIGH confidence)
- **Codebase inspection** — Direct analysis of `shared/model_router/src/model_router/types.py` (UsageInfo model), `router.py` (generate/stream flow), `providers/vertex_ai.py` (Vertex usage extraction), `providers/openrouter.py` (OpenRouter usage extraction), `settings_store.py` and `key_manager.py` (Redis patterns), `cache.py` (TTL cache pattern)
- **Codebase inspection** — `AURA-CHAT/server/routers/chat.py` (streaming SSE flow, "complete" event structure), `AURA-CHAT/client/src/types/` (frontend type patterns), `AURA-CHAT/client/src/features/settings/` (existing feature module pattern)
- **`.planning/REQUIREMENTS.md`** — USAGE-01, USAGE-02 requirement definitions
- **`.planning/ROADMAP.md`** — Phase 12 scope, success criteria, recharts version specification

### Secondary (MEDIUM confidence)
- **`.planning/research/FEATURES.md`** — D-3 usage tracking feature analysis, pricing source details
- **`.planning/research/STACK.md`** — Recharts v3.8.0 selection rationale, React 18/19 compatibility
- **`.planning/research/ARCHITECTURE.md`** — UsageTracker design pattern, usage API endpoint design

### Tertiary (LOW confidence)
- **Vertex AI pricing** — Static pricing values should be verified against current Google Cloud pricing page before deployment. Training data may be stale.
- **OpenRouter pricing API** — Pricing field structure in `/api/v1/models` response based on research docs. Exact field names (`pricing.prompt`, `pricing.completion`) should be verified against live response.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in project or explicitly specified in roadmap
- Architecture: HIGH — patterns directly extend existing `SettingsStore`/`KeyManager`/`ModelCache` Redis patterns
- Pitfalls: HIGH — identified from direct codebase analysis (streaming gap, provider pricing differences, attribution propagation)
- Cost calculation: MEDIUM — provider-specific pricing needs live verification
- Recharts API: MEDIUM — version confirmed in roadmap, component API based on training data

**Research date:** 2026-03-11
**Valid until:** 2026-04-11 (stable domain — infrastructure + charts)
