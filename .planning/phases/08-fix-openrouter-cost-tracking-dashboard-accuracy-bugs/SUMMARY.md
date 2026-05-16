---
phase: 08-fix-openrouter-cost-tracking-dashboard-accuracy-bugs
plan: 01
subsystem: api
tags: [openrouter, cost-tracking, streaming, pytest]

requires: []
provides:
  - Async OpenRouter pricing cache population in CostCalculator
  - StreamChunk usage propagation from provider to router
  - Router usage tracking now prefers real streaming usage over char-based estimates
  - Regression tests for pricing fetch and stream usage behavior
affects: [usage-dashboard, model-router, cost-estimation]

tech-stack:
  added: []
  patterns:
    - "Prefer provider-emitted usage data over heuristic token estimation"
    - "Keep char-count estimation as fallback for missing usage"

key-files:
  created: []
  modified:
    - shared/model_router/src/model_router/cost_calculator.py
    - shared/model_router/src/model_router/types.py
    - shared/model_router/src/model_router/providers/openrouter.py
    - shared/model_router/src/model_router/router.py
    - shared/model_router/tests/test_cost_calculator.py
    - shared/model_router/tests/test_router.py
    - shared/model_router/tests/test_streaming.py

key-decisions:
  - "Added lazy httpx import inside populate_openrouter_pricing to avoid hard dependency at import time"
  - "OpenRouter stream emits final empty content chunk carrying UsageInfo to avoid UI text impact"
  - "Retained len(text)//4 estimation as fallback when stream usage is unavailable"

patterns-established:
  - "Provider stream usage propagation: attach usage to final StreamChunk and consume in router"
  - "Pricing cache hydration: parse per-token strings into per-1M-token floats with validation"

requirements-completed: [BUG-01, BUG-02, BUG-04]

duration: 6 min
completed: 2026-05-16
---

# Phase 08 Plan 01: Shared Package — Pricing Cache + Streaming Usage Summary

**OpenRouter pricing now hydrates asynchronously from /models, and streaming token usage is captured from real provider chunks instead of relying on character-count estimation.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-05-16T09:09:27Z
- **Completed:** 2026-05-16T09:15:04Z
- **Tasks:** 5
- **Files modified:** 7

## Accomplishments
- Added `CostCalculator.populate_openrouter_pricing()` with resilient parsing, validation, and logging.
- Extended `StreamChunk` with optional `usage` and wired OpenRouter provider streaming to emit final usage chunk.
- Updated router `stream()` and `stream_with_usage()` to prefer real usage and keep fallback estimation.
- Added targeted tests for pricing fetch success/failure/invalid data and stream usage propagation.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add async pricing fetch method to CostCalculator** - `8f257d6` (feat)
2. **Task 2: Add usage field to StreamChunk** - `fb1dbd6` (feat)
3. **Task 3: Capture OpenRouter streaming usage in provider stream method** - `9e09250` (feat)
4. **Task 4: Update router stream/stream_with_usage to use real usage data** - `80617ea` (fix)
5. **Task 5: Write tests for pricing fetch and streaming usage extraction** - `ba01a64` (test)

## Files Created/Modified
- `shared/model_router/src/model_router/cost_calculator.py` - Added async pricing cache population method.
- `shared/model_router/src/model_router/types.py` - Added optional `usage` on `StreamChunk`.
- `shared/model_router/src/model_router/providers/openrouter.py` - Included streaming usage capture and final usage chunk yield.
- `shared/model_router/src/model_router/router.py` - Consumes real chunk usage in `stream()` and `stream_with_usage()`.
- `shared/model_router/tests/test_cost_calculator.py` - Added 4 pricing fetch/cache tests.
- `shared/model_router/tests/test_router.py` - Added 3 stream real-usage/fallback behavior tests.
- `shared/model_router/tests/test_streaming.py` - Updated schema assertion for new `StreamChunk.usage` field.

## Decisions Made
- Use `httpx.AsyncClient(timeout=15.0)` in pricing fetch with lazy import and broad failure safety (warning + continue).
- Emit usage-only terminal stream chunk with empty text to preserve display output.
- Keep existing estimation logic unchanged as fallback to preserve robustness on interrupted or non-usage streams.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Regression Fix] Updated streaming schema expectation for StreamChunk**
- **Found during:** Task 5 verification (`pytest shared/model_router/tests/ -v`)
- **Issue:** Existing streaming schema test expected only `type`/`text`, but `StreamChunk` now intentionally includes optional `usage`.
- **Fix:** Updated `test_both_providers_yield_same_chunk_schema` to expect `usage` key as part of normalized chunk schema.
- **Files modified:** `shared/model_router/tests/test_streaming.py`
- **Verification:** Re-ran full suite; regression resolved.
- **Committed in:** `ba01a64`

---

**Total deviations:** 1 auto-fixed (1 regression fix)
**Impact on plan:** No scope creep; change was required to keep existing tests aligned with planned type contract update.

## Issues Encountered
- Full suite still has **2 pre-existing failing tests** in `shared/model_router/tests/test_compat.py`:
  - `test_shim_enabled_returns_compat_model[context0]`
  - `test_shim_import_failure_fallback[context0]`
- These failures are outside the files/tasks in this plan and were not modified here.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Core pricing + streaming usage accuracy fixes are complete and validated for cost calculator/router paths.
- Ready for next plan in Phase 08.

---
*Phase: 08-fix-openrouter-cost-tracking-dashboard-accuracy-bugs*
*Completed: 2026-05-16*
