---
phase: 13-polish-integration-testing
plan: 01
subsystem: testing
tags: [pytest, integration, performance, model-router, openrouter, vertex-ai]

# Dependency graph
requires:
  - phase: 09-openrouter-streaming
    provides: normalized cross-provider streaming and thinking contracts
  - phase: 10-cross-app-migration-backend-integration
    provides: compat-layer routing and shared package import surface
  - phase: 12-usage-tracking-cost-dashboard
    provides: router usage tracking hooks and Redis usage records
provides:
  - Cross-provider integration tests for mid-session provider switching
  - Thinking parity validation across Vertex AI and OpenRouter streams
  - Router overhead benchmarks for generate, stream, and provider resolution
affects: [13-02 regression sweep, 13-03 requirements verification, model_router tests]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Offline cross-provider integration tests using AURA_TEST_MODE fixtures
    - perf_counter_ns average-overhead benchmarks against direct provider calls

key-files:
  created:
    - shared/model_router/tests/test_integration_flows.py
    - tests/test_cross_provider_integration.py
    - tests/test_router_performance.py
  modified: []

key-decisions:
  - "Force AURA_TEST_MODE in repo-root tests so integration coverage stays offline outside shared/model_router pytest config."
  - "Benchmark router overhead by comparing identical GenerateRequest loops against direct provider calls with perf_counter_ns averages."

patterns-established:
  - "Cross-provider session tests should assert contract parity, provider attribution, and usage recording in one flow."
  - "Repo-root performance tests should measure direct provider and router paths under identical test-mode conditions."

# Metrics
duration: 7 min
completed: 2026-03-11
---

# Phase 13 Plan 01: Cross-provider integration tests + router overhead benchmark Summary

**Cross-provider integration tests for provider switching, thinking parity, usage tracking, and sub-10ms router overhead.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-11T10:24:29Z
- **Completed:** 2026-03-11T10:31:55Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Added multi-concern router tests that validate provider switching, thinking chunk parity, and usage tracking in one session flow.
- Added repo-root integration tests proving both providers and the compat layer work from the shared import context used by both apps.
- Added performance benchmarks proving router generate/stream overhead stays below the 10ms roadmap target and provider resolution stays below 1ms.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Multi-concern integration tests** - `d3af493` (test)
2. **Task 1 GREEN: Multi-concern integration tests** - `ad341a3` (feat)
3. **Task 2 RED: Cross-app integration + performance benchmarks** - `d6b9bb5` (test)
4. **Task 2 GREEN: Cross-app integration + performance benchmarks** - `dcc99e6` (feat)

_Note: Both plan tasks were executed with TDD (RED → GREEN)._ 

## Files Created/Modified
- `shared/model_router/tests/test_integration_flows.py` - Multi-provider integration coverage for provider switching, thinking parity, and usage tracking.
- `tests/test_cross_provider_integration.py` - Repo-root integration coverage for both providers and slash-form compat routing.
- `tests/test_router_performance.py` - Router abstraction overhead benchmarks for generate, stream, and provider resolution.

## Decisions Made
- Forced `AURA_TEST_MODE` in repo-root tests so they reuse deterministic provider behavior even outside `shared/model_router`'s pytest session fixture.
- Used direct-provider vs router timing comparisons on the same `GenerateRequest` objects so the overhead measurement isolates the abstraction layer itself.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added missing `make_config()` helper in integration flow tests**
- **Found during:** Task 1 (Multi-concern integration tests)
- **Issue:** The RED test run failed with `NameError: make_config is not defined`, blocking the test suite before the intended assertions could run.
- **Fix:** Added a local `make_config()` helper matching existing router test patterns.
- **Files modified:** `shared/model_router/tests/test_integration_flows.py`
- **Verification:** `../../.venv/Scripts/python -m pytest tests/test_integration_flows.py -v --tb=short`
- **Committed in:** `ad341a3`

**2. [Rule 3 - Blocking] Forced offline test mode for repo-root integration and benchmark tests**
- **Found during:** Task 2 (Cross-app integration tests + router overhead benchmark)
- **Issue:** Repo-root tests attempted live Vertex/OpenRouter clients because the shared package's session-scoped test fixture did not run outside `shared/model_router`, causing auth/dependency failures.
- **Fix:** Added autouse fixtures that set `AURA_TEST_MODE=true` for repo-root integration and benchmark files.
- **Files modified:** `tests/test_cross_provider_integration.py`, `tests/test_router_performance.py`
- **Verification:** `.venv/Scripts/python -m pytest tests/test_cross_provider_integration.py tests/test_router_performance.py -v --tb=short`
- **Committed in:** `dcc99e6`

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes were necessary to make the planned tests execute in the intended offline environment. No scope creep.

## Issues Encountered
- RED failures surfaced two setup gaps quickly: a missing local router config helper in Task 1 and missing repo-root test-mode env setup in Task 2. Both were resolved inline during TDD.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 13 success criteria SC-1, SC-2, and SC-4 now have automated coverage.
- Ready for `13-02-PLAN.md` regression sweep work.

## Self-Check: PASSED

---
*Phase: 13-polish-integration-testing*
*Completed: 2026-03-11*
