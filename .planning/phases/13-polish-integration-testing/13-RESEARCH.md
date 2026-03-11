# Phase 13: Polish + Integration Testing - Research

**Researched:** 2026-03-11
**Domain:** Cross-cutting integration testing, performance verification, and regression validation for multi-provider LLM architecture
**Confidence:** HIGH

## Summary

Phase 13 is a quality validation phase — no new features, only cross-cutting integration tests, performance benchmarks, and regression sweeps that validate the work from Phases 8-12. The existing codebase already has substantial unit-level coverage (model_router package has 15+ test files covering types, routing, streaming, thinking, compat, cost calculation, usage tracking, settings, key management, model caching, errors, and import contexts). What's missing are **cross-cutting integration tests** that exercise multi-concern flows: provider switching mid-session + streaming + thinking mode + session persistence in a single path.

The four success criteria map directly to four distinct testing domains: (1) mid-session provider switching, (2) thinking mode UI parity across providers, (3) full test suite regression, and (4) router overhead benchmarking. The first two require new integration tests; the third requires running existing suites and fixing any failures; the fourth requires new performance benchmarks. A key finding is that the AURA-CHAT chitchat streaming path (lines 210-309 of `server/routers/chat.py`) still uses the legacy `get_model()` path with a TODO to migrate to `router.stream()`, and several requirements (CONFIG-01, CONFIG-03, CONFIG-04, UI-03) are marked "Pending" in REQUIREMENTS.md but appear to be implemented — the traceability table needs updating.

**Primary recommendation:** Structure Phase 13 as three plans: (1) backend integration tests + performance benchmark, (2) frontend integration tests (Vitest + Playwright), (3) regression sweep + gap closure + requirements traceability update.

## Standard Stack

### Core (Testing)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=8.0 | Python unit + integration tests | Already configured in all 3 test roots |
| pytest-asyncio | >=0.23 | Async test support | Required for all router/provider tests |
| pytest-benchmark | >=4.0 | Performance microbenchmarks | Standard for `< 10ms overhead` claims |
| Vitest | 3.2.4 | Frontend unit/component tests | Already configured in AURA-CHAT/client |
| Playwright | (existing) | E2E browser tests | Already configured in both apps |
| React Testing Library | 16.3.1 | Component testing | Already in AURA-CHAT/client |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-timeout | >=2.0 | Test timeout enforcement | Prevent hanging async tests |
| time (stdlib) | - | Simple timing assertions | Router overhead measurement |
| unittest.mock / monkeypatch | - | Provider stubbing | Fake providers for integration flows |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pytest-benchmark | Manual `time.perf_counter()` loops | pytest-benchmark handles warmup, statistics, and comparison baselines automatically |
| Playwright for all E2E | Vitest + msw for integration | Playwright tests real browser flows but requires running backend; Vitest integration tests are faster for component-level validation |

**Installation (if pytest-benchmark not already present):**
```bash
cd shared/model_router && pip install pytest-benchmark
```

## Architecture Patterns

### Test Organization Structure

```
tests/                                  # Root-level cross-cutting tests
├── test_no_direct_imports.py           # EXISTING: AST import audit
├── test_cross_provider_integration.py  # NEW: Multi-provider flow tests
└── test_router_performance.py          # NEW: Router overhead benchmarks

shared/model_router/tests/
├── test_router.py                      # EXISTING: Router unit tests
├── test_streaming.py                   # EXISTING: Cross-provider streaming
├── test_thinking.py                    # EXISTING: Thinking config translation
├── test_compat.py                      # EXISTING: Legacy compat layer
└── test_integration_flows.py           # NEW: Multi-concern flow tests

AURA-CHAT/client/
├── src/**/*.test.{ts,tsx}              # EXISTING: Vitest component tests
└── e2e/
    ├── chat.spec.ts                    # EXISTING: Chat E2E tests
    └── provider-switching.spec.ts      # NEW: Cross-provider E2E tests
```

### Pattern 1: Fake Provider Integration Testing

**What:** Use the existing `FakeOpenRouterClient` and `FakeVertexClient` patterns from `test_streaming.py` to create multi-provider integration scenarios without live API calls.

**When to use:** Testing flows that span multiple providers in a single test (e.g., start with Vertex, switch to OpenRouter mid-session).

**Example:**
```python
# Pattern from existing test_streaming.py, extended for integration:
async def test_switch_provider_mid_session():
    """Switching from Vertex to OpenRouter preserves stream contract."""
    router = make_test_router()

    # First request: Vertex AI
    vertex_response = await router.generate(
        model="gemini-2.0-flash", contents="hello",
        metadata={"session_id": "sess-1", "user_id": "user-1"}
    )
    assert vertex_response.provider is ProviderType.VERTEX_AI

    # Second request: OpenRouter (same session)
    openrouter_response = await router.generate(
        model="anthropic/claude-sonnet-4", contents="follow up",
        metadata={"session_id": "sess-1", "user_id": "user-1"}
    )
    assert openrouter_response.provider is ProviderType.OPENROUTER

    # Both responses have identical shape
    assert set(vertex_response.model_dump().keys()) == set(openrouter_response.model_dump().keys())
```

### Pattern 2: Router Overhead Benchmarking

**What:** Measure the time delta between calling `router.generate()` vs calling the provider's `generate()` directly. The overhead must be < 10ms.

**When to use:** Success criterion #4.

**Example:**
```python
import time

async def test_router_overhead_under_10ms():
    """Router abstraction adds < 10ms overhead vs direct provider call."""
    router = ModelRouter(make_config())
    provider = router._providers[ProviderType.VERTEX_AI]
    request = GenerateRequest(model="gemini-2.0-flash", contents="hello")

    # Direct provider call
    start = time.perf_counter_ns()
    for _ in range(100):
        await provider.generate(request)
    direct_ns = (time.perf_counter_ns() - start) / 100

    # Router call (includes routing + potential usage tracking)
    start = time.perf_counter_ns()
    for _ in range(100):
        await router.generate(request)
    router_ns = (time.perf_counter_ns() - start) / 100

    overhead_ms = (router_ns - direct_ns) / 1_000_000
    assert overhead_ms < 10.0, f"Router overhead {overhead_ms:.2f}ms exceeds 10ms"
```

### Pattern 3: Thinking Mode Parity Testing

**What:** Verify that the same thinking mode flow produces identical StreamChunk shapes for both Gemini thinking and Claude extended thinking.

**When to use:** Success criterion #2.

**Example:**
```python
async def test_thinking_mode_parity_across_providers():
    """Thinking chunks from both providers use identical {type, text} shape."""
    vertex_provider = make_vertex_provider([
        make_vertex_chunk(text='thinking...', is_thought=True),
        make_vertex_chunk(text='answer'),
    ])
    openrouter_provider = make_openrouter_provider([
        make_openrouter_chunk(reasoning_content='thinking...'),
        make_openrouter_chunk(content='answer'),
    ])

    vertex_chunks = [c async for c in vertex_provider.stream(vertex_request)]
    openrouter_chunks = [c async for c in openrouter_provider.stream(openrouter_request)]

    # Both have thinking + content chunks
    assert vertex_chunks[0].type == 'thinking'
    assert openrouter_chunks[0].type == 'thinking'
    assert vertex_chunks[1].type == 'content'
    assert openrouter_chunks[1].type == 'content'
    # Same schema
    assert type(vertex_chunks[0]) is type(openrouter_chunks[0])
```

### Anti-Patterns to Avoid

- **Testing against live APIs in integration tests:** Use fake/test-mode providers. Live API tests are flaky and expensive.
- **Asserting exact response text in integration tests:** Test response *shape* and *contract*, not specific text content.
- **Testing provider switching without session context:** The key integration concern is session persistence across switches — always include `metadata={"session_id": ...}` in cross-provider tests.
- **Skipping compat layer in integration tests:** The `VertexCompatModel` is the primary caller path for legacy code. Integration tests must exercise it.
- **Forgetting the chitchat path:** `stream_chitchat_response()` in `chat.py` still uses legacy `get_model()` — this path needs specific attention.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Performance benchmarking | Manual timing loops with statistics | pytest-benchmark | Handles warmup, outlier removal, percentiles, historical comparison |
| Mock SSE streams | Custom SSE parsers for E2E | Playwright's `page.evaluate()` + event listeners | Playwright already handles SSE in the browser context |
| Fake Redis for integration | Custom dict-based mock | `fakeredis[aioredis]` or existing `FakeSortedSetRedis` from test_usage_tracker.py | Existing pattern already works; reuse it |
| Cross-app test orchestration | Shell scripts running tests | pytest with `-x` and explicit test paths per app | Already established pattern from Phase 8 validation |

**Key insight:** This phase should maximize reuse of existing test patterns — `FakeOpenRouterClient`, `FakeVertexClient`, `make_test_router()`, `FakeSortedSetRedis`, and the AST-based import scanner are all established and proven.

## Common Pitfalls

### Pitfall 1: Thinking Mode Config Divergence Between Providers
**What goes wrong:** Gemini uses `thinking_level` (LOW/MEDIUM/HIGH) mapped from budget thresholds. OpenRouter Claude uses `reasoning.effort` (low/medium/high). DeepSeek has always-on reasoning. If any mapping is wrong, the thinking UI shows nothing.
**Why it happens:** Three different thinking config translation paths: Vertex in `chat.py` (lines 250-264), OpenRouter in `_build_thinking_params()`, and compat layer in `_build_thinking_config_from_config()`.
**How to avoid:** Integration test that sends the same `thinking_config: {"thinking_budget": 2048}` to both providers and verifies both produce StreamChunk with `type="thinking"`.
**Warning signs:** Thinking toggle shows as available but no thinking text appears for one provider.

### Pitfall 2: Legacy Chitchat Path Not Routed Through Model Router
**What goes wrong:** `stream_chitchat_response()` in `chat.py` (line 221) calls `get_model()` which returns a `VertexCompatModel`, but the TODO at line 241 notes session metadata isn't propagated. If a student switches to an OpenRouter model and then triggers chitchat, the path still works (compat layer handles OpenRouter routing via slash detection), but usage tracking metadata is incomplete.
**Why it happens:** The chitchat streaming path was wrapped via compat but not fully migrated to direct `router.stream()`.
**How to avoid:** Test that chitchat with both Vertex and OpenRouter models produces valid SSE events. Consider migrating the chitchat path to direct `router.stream()` for consistency.
**Warning signs:** Usage data for chitchat sessions shows null session_id/user_id.

### Pitfall 3: test_compat.py Deferred Failure
**What goes wrong:** The deferred items from Phase 10 note that `test_compat.py` had pre-existing failures related to `_GenerativeModelWrapper` attribute missing.
**Why it happens:** The compat shim test imports real app modules which may have dirty worktree state.
**How to avoid:** Run the full `shared/model_router/tests/` suite first and fix any failures before running cross-app integration tests.
**Warning signs:** `pytest shared/model_router/tests/ -x` fails on `test_compat.py`.

### Pitfall 4: Requirements Marked Pending But Already Implemented
**What goes wrong:** CONFIG-01, CONFIG-03, CONFIG-04, and UI-03 are marked "Pending" in REQUIREMENTS.md but the implementation exists in Phase 10's settings routers, model cache, key manager, and no-direct-imports test.
**Why it happens:** The traceability table wasn't updated after phase completion.
**How to avoid:** Phase 13 should verify these requirements are satisfied and update the traceability table. Don't re-implement what already exists.
**Warning signs:** Planner creates tasks to implement features that already exist.

### Pitfall 5: React Version Gap Between Apps
**What goes wrong:** AURA-CHAT uses React 19, AURA-NOTES-MANAGER uses React 18. Components were copied (not shared). If Phase 13 needs to fix an issue in a shared component, it must be fixed in both places.
**Why it happens:** The two apps are separate git submodules with different React versions.
**How to avoid:** Any component fix must be applied to both `AURA-CHAT/client/src/features/settings/` and `AURA-NOTES-MANAGER/frontend/src/features/settings/`.
**Warning signs:** A fix works in CHAT but breaks in NOTES.

### Pitfall 6: Windows Path Issues in Cross-App Test Runner
**What goes wrong:** Tests using `Path` and `subprocess.run` with cross-app contexts can fail on Windows due to backslash/forward-slash differences.
**Why it happens:** The codebase runs on Windows (confirmed by environment context). Tests in `test_no_direct_imports.py` already handle this with `.replace("\\", "/")`.
**How to avoid:** Always use `Path` objects and normalize slashes in any new cross-app tests.
**Warning signs:** Tests pass on the author's machine but fail in CI.

## Code Examples

### Existing Test Patterns to Reuse

#### Cross-Provider Router Test (from test_router.py)
```python
# Source: shared/model_router/tests/test_router.py
def make_config() -> RouterConfig:
    return RouterConfig(
        test_mode=True,
        vertex_ai=VertexAIConfig(project_id="test-project", region="global"),
        openrouter=OpenRouterConfig(api_key="test-key"),
    )

async def test_router_generate_delegates_to_openrouter():
    router = ModelRouter(make_config())
    response = await router.generate(
        model="anthropic/claude-sonnet-4", contents="hello",
    )
    assert response.provider is ProviderType.OPENROUTER
```

#### Fake Provider Stream Pattern (from test_streaming.py)
```python
# Source: shared/model_router/tests/test_streaming.py
def make_openrouter_provider(chunks):
    provider = OpenRouterProvider(OpenRouterConfig(api_key='test-key'))
    provider._test_mode = False
    provider._client = FakeOpenRouterClient(FakeAsyncStream(chunks))
    return provider

def make_vertex_provider(chunks):
    provider = VertexAIProvider(
        VertexAIConfig(project_id='test-project', region='global')
    )
    provider._test_mode = False
    provider._client = FakeVertexClient(chunks)
    return provider
```

#### Usage Tracking with Fake Redis (from test_usage_tracker.py)
```python
# Source: shared/model_router/tests/test_usage_tracker.py
# FakeSortedSetRedis provides zadd, zrangebyscore, zrange, delete
# for testing UsageTracker without real Redis
```

#### AST Import Scanner (from test_no_direct_imports.py)
```python
# Source: tests/test_no_direct_imports.py
# _find_violations_for_dirs() + _matches_forbidden_import()
# AST-based so string mentions don't false-positive
```

### New Integration Test: Provider Switch with Stream Contract Parity
```python
# NEW test for Phase 13
async def test_mid_session_provider_switch_stream_contract():
    """Both providers produce identical StreamChunk schema during streaming."""
    router = ModelRouter(make_config())

    vertex_chunks = [
        c async for c in router.stream(
            model="gemini-2.0-flash", contents="hello",
        )
    ]
    openrouter_chunks = [
        c async for c in router.stream(
            model="anthropic/claude-sonnet-4", contents="hello",
        )
    ]

    # Identical schema
    assert all(isinstance(c, StreamChunk) for c in vertex_chunks)
    assert all(isinstance(c, StreamChunk) for c in openrouter_chunks)
    for vc, oc in zip(vertex_chunks, openrouter_chunks):
        assert set(vc.model_dump().keys()) == set(oc.model_dump().keys())
```

### New Performance Benchmark
```python
# NEW test for Phase 13
import time

async def test_router_overhead_under_10ms():
    """Router adds < 10ms overhead over direct provider call."""
    config = RouterConfig(test_mode=True,
        vertex_ai=VertexAIConfig(project_id="test", region="global"),
        openrouter=OpenRouterConfig(api_key="test-key"))
    router = ModelRouter(config)
    provider = router._providers[ProviderType.VERTEX_AI]
    request = GenerateRequest(model="gemini-2.0-flash", contents="hi")

    ITERATIONS = 200
    # Direct
    t0 = time.perf_counter_ns()
    for _ in range(ITERATIONS):
        await provider.generate(request)
    direct_avg_ns = (time.perf_counter_ns() - t0) / ITERATIONS

    # Via router
    t0 = time.perf_counter_ns()
    for _ in range(ITERATIONS):
        await router.generate(request=request)
    router_avg_ns = (time.perf_counter_ns() - t0) / ITERATIONS

    overhead_ms = (router_avg_ns - direct_avg_ns) / 1_000_000
    assert overhead_ms < 10.0, f"Overhead {overhead_ms:.2f}ms > 10ms"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct `vertexai` SDK imports | `model_router` shared package | Phase 8 (2026-03-10) | All LLM calls route through router; legacy imports forbidden |
| Manual stream handling per provider | Normalized `StreamChunk{type, text}` | Phase 9 (2026-03-10) | Identical stream contract for all providers |
| Hardcoded Vertex AI config | Admin settings + encrypted key management | Phase 10 (2026-03-10) | Dynamic provider configuration via Redis-backed settings |
| Single-model chat | Inline model picker with session persistence | Phase 11 (2026-03-11) | Students choose models mid-session |
| No usage tracking | Redis-backed usage tracking + cost dashboard | Phase 12 (2026-03-11) | Per-request cost attribution with aggregated dashboards |

**Deprecated/outdated:**
- Direct `google.genai`, `vertexai`, `openai` SDK imports in app code: forbidden by AST scanner
- Legacy `_GenerativeModelWrapper`: replaced by `VertexCompatModel` from shared package

## Open Questions

1. **test_compat.py Pre-Existing Failure**
   - What we know: Phase 10 deferred items note that `test_compat.py` had failures against `_GenerativeModelWrapper` attribute missing
   - What's unclear: Whether this was fixed in subsequent phases or still broken
   - Recommendation: Run `pytest shared/model_router/tests/test_compat.py -v` as first task and fix any failures before writing new integration tests

2. **Chitchat Path Migration**
   - What we know: `stream_chitchat_response()` uses legacy `get_model()` + compat layer. There's a TODO at line 241 for migrating to `router.stream()` with session metadata
   - What's unclear: Whether this TODO is in-scope for Phase 13 or deferred
   - Recommendation: At minimum, add an integration test proving chitchat works with both providers. Migration to direct router.stream() would be ideal for consistency but may be out of scope.

3. **Pending Requirements in REQUIREMENTS.md**
   - What we know: CONFIG-01, CONFIG-03, CONFIG-04, UI-03 marked "Pending" but implementation exists
   - What's unclear: Whether there are subtle gaps in the implementation vs requirements
   - Recommendation: Verify each requirement against its implementation and update the traceability table

4. **Playwright E2E Test Scope**
   - What we know: Both apps have existing Playwright test suites (7 spec files in CHAT, 6 in NOTES)
   - What's unclear: Whether existing E2E tests already cover provider switching, or if new specs are needed
   - Recommendation: Review existing e2e/ specs first. Write new `provider-switching.spec.ts` only if not already covered.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework (Python) | pytest 8.x + pytest-asyncio 0.23+ |
| Framework (Frontend) | Vitest 3.2.4 + React Testing Library 16.3.1 |
| Framework (E2E) | Playwright (Chromium, Firefox, WebKit + mobile) |
| Config (shared) | `shared/model_router/pyproject.toml` |
| Config (CHAT backend) | `AURA-CHAT/pytest.ini` |
| Config (CHAT frontend) | `AURA-CHAT/client/vitest.config.ts` |
| Config (NOTES backend) | `AURA-NOTES-MANAGER/conftest.py` |
| Config (NOTES frontend) | `AURA-NOTES-MANAGER/frontend/jest.config.cjs` |
| Config (E2E CHAT) | `AURA-CHAT/client/playwright.config.ts` |
| Config (E2E NOTES) | `AURA-NOTES-MANAGER/e2e/playwright.config.ts` + `AURA-NOTES-MANAGER/frontend/playwright.config.ts` |
| Quick run (shared) | `cd shared/model_router && ../../.venv/Scripts/python -m pytest tests/ -x` |
| Quick run (CHAT backend) | `cd AURA-CHAT && ../.venv/Scripts/python -m pytest tests/ server/tests/ -x --tb=short` |
| Quick run (CHAT frontend) | `cd AURA-CHAT/client && npx vitest run --reporter=verbose` |
| Quick run (cross-app) | `.venv/Scripts/python -m pytest tests/ -x` |
| Full suite | Run all four quick commands in sequence |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SC-1 | Mid-session provider switch: no errors, no lost context | integration | `pytest tests/test_cross_provider_integration.py -x` | ❌ Wave 0 |
| SC-2 | Thinking mode UI parity for Gemini and Claude | integration + unit | `pytest shared/model_router/tests/test_integration_flows.py -x` | ❌ Wave 0 |
| SC-3 | Both apps pass full test suites | regression | All quick run commands above | ✅ (existing suites) |
| SC-4 | Router overhead < 10ms | benchmark | `pytest tests/test_router_performance.py -x` | ❌ Wave 0 |
| REQ-VERIFY | CONFIG-01, CONFIG-03, CONFIG-04, UI-03 implementation confirmed | verification | `pytest tests/test_no_direct_imports.py -x` (existing) + manual review | ✅ partially |

### Sampling Rate

- **Per task commit:** Quick run for the affected test scope
- **Per wave merge:** Full suite across all 4 test roots
- **Phase gate:** All suites green + new integration tests green

### Wave 0 Gaps

- [ ] `tests/test_cross_provider_integration.py` — Multi-provider flow tests (SC-1)
- [ ] `tests/test_router_performance.py` — Router overhead benchmark (SC-4)
- [ ] `shared/model_router/tests/test_integration_flows.py` — Thinking mode parity + multi-concern flows (SC-2)
- [ ] Verify and fix any pre-existing failures in `shared/model_router/tests/test_compat.py`
- [ ] Update REQUIREMENTS.md traceability table for CONFIG-01, CONFIG-03, CONFIG-04, UI-03

## Sources

### Primary (HIGH confidence)

- **Codebase inspection:** Direct reading of all key files:
  - `shared/model_router/src/model_router/router.py` — Router routing, delegation, usage tracking
  - `shared/model_router/tests/test_streaming.py` — Cross-provider streaming normalization (fake client patterns)
  - `shared/model_router/tests/test_thinking.py` — Thinking config translation
  - `shared/model_router/tests/test_router.py` — Router unit tests
  - `shared/model_router/tests/test_compat.py` — Compat layer tests
  - `tests/test_no_direct_imports.py` — AST-based import audit
  - `AURA-CHAT/server/routers/chat.py` — Chat streaming, thinking config, SSE events
  - `AURA-CHAT/server/routers/settings.py` — Settings API with model cache, key manager
  - `AURA-CHAT/server/routers/usage.py` — Usage query endpoints
  - `AURA-CHAT/client/src/features/chat/ChatPage.tsx` — Inline model picker, thinking toggle, session model persistence
  - `AURA-CHAT/client/src/features/chat/components/InlineModelPicker.tsx` — Model selection component
  - `AURA-CHAT/client/src/stores/useModelStore.ts` — Zustand session model persistence

- **Phase summaries:** All SUMMARY.md files from phases 8-12 plans
- **Verification reports:** 11-VALIDATION.md, 12-VERIFICATION.md
- **ROADMAP.md and REQUIREMENTS.md** — Phase structure and requirement status

### Secondary (MEDIUM confidence)

- **pytest-benchmark documentation** — Standard benchmarking library for Python (well-established, training data reliable)
- **Playwright API** — E2E testing patterns for SSE and streaming (already configured in project)

### Tertiary (LOW confidence)

- None — all findings are from direct codebase inspection

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all tools already configured in the project
- Architecture: HIGH — patterns directly derived from existing test files
- Pitfalls: HIGH — identified from actual code inspection (TODO comments, deferred items, pending requirements)
- Performance testing: MEDIUM — pytest-benchmark approach is standard but needs validation that test-mode providers have representative overhead

**Research date:** 2026-03-11
**Valid until:** 2026-04-11 (30 days — stable codebase, no external dependency changes expected)
