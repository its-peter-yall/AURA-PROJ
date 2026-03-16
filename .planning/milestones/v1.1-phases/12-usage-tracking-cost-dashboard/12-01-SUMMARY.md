---
phase: 12-usage-tracking-cost-dashboard
plan: 01
subsystem: api
tags: [redis, usage-tracking, cost-estimation, model-router, pytest]

# Dependency graph
requires:
  - phase: 10-cross-app-migration-backend-integration
    provides: router-backed shared generation APIs and Redis-backed shared config patterns
provides:
  - Redis-backed usage record persistence for model-router requests
  - Provider-aware cost estimation for Vertex AI, OpenRouter, and Ollama
  - Automatic generate/stream usage instrumentation hooks in ModelRouter
affects: [phase-12-api-endpoints, dashboard, session-cost-badge]

# Tech tracking
tech-stack:
  added: []
  patterns: [Redis sorted-set telemetry storage, late-bound router usage instrumentation, provider-specific cost estimation]

key-files:
  created: [shared/model_router/src/model_router/usage_tracker.py, shared/model_router/tests/test_usage_tracker.py, .planning/phases/12-usage-tracking-cost-dashboard/12-01-SUMMARY.md]
  modified: [shared/model_router/src/model_router/types.py, shared/model_router/src/model_router/cost_calculator.py, shared/model_router/src/model_router/router.py, shared/model_router/src/model_router/__init__.py, shared/model_router/tests/test_cost_calculator.py]

key-decisions:
  - "Use Redis sorted sets with timestamp scores for both global usage history and session-scoped summaries."
  - "Late-bind UsageTracker and CostCalculator into ModelRouter so the shared singleton can initialize before Redis is available."
  - "Fall back to character-count token estimation for streams and swallow telemetry failures so tracking never breaks responses."

patterns-established:
  - "Usage records serialize with Pydantic model_dump_json/model_validate_json for Redis round-trips."
  - "Router instrumentation computes cost after provider success and records session/user metadata from GenerateRequest.metadata."

# Metrics
duration: 2 min
completed: 2026-03-11
---

# Phase 12 Plan 01: Usage tracking foundation Summary

**Redis-backed usage telemetry with provider-aware cost estimation wired directly into shared ModelRouter generate and stream flows.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-11T09:09:46Z
- **Completed:** 2026-03-11T09:11:46Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Added a shared `UsageRecord` contract plus request metadata support for session/user attribution.
- Implemented `CostCalculator` for static Vertex AI pricing, cached OpenRouter pricing, and free Ollama requests.
- Added `UsageTracker` persistence and hooked ModelRouter `generate()`/`stream()` to record usage automatically.

## Task Commits

Each task was committed atomically:

1. **Task 1: UsageRecord type + GenerateRequest metadata + CostCalculator** - `b6af3ec` (feat)
2. **Task 2: UsageTracker Redis persistence + Router hooks** - `787ab4a` (feat)

_Plan metadata commit recorded after state/roadmap updates._

## Files Created/Modified
- `shared/model_router/src/model_router/types.py` - Adds `UsageRecord` and metadata propagation on generation requests.
- `shared/model_router/src/model_router/cost_calculator.py` - Estimates provider-specific request costs.
- `shared/model_router/src/model_router/usage_tracker.py` - Persists usage records and aggregates summaries from Redis sorted sets.
- `shared/model_router/src/model_router/router.py` - Records usage for `generate()` and `stream()` without breaking caller flows.
- `shared/model_router/src/model_router/__init__.py` - Re-exports usage tracking public API.
- `shared/model_router/tests/test_cost_calculator.py` - Covers serialization and pricing behavior.
- `shared/model_router/tests/test_usage_tracker.py` - Covers Redis persistence, aggregation, and router integration.

## Decisions Made
- Used Redis sorted sets keyed by Unix timestamp for both global and session usage timelines so later dashboard queries can use efficient time-range scans.
- Added `set_usage_tracking()` instead of constructor-only injection so the shared router singleton can be created before Redis dependencies are available.
- Kept stream usage tracking estimation-based for now and wrapped all telemetry writes in `try/except` to preserve zero-regression behavior for callers.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Shared usage tracking primitives are in place for backend usage summary endpoints in Plan 12-02.
- Session/user attribution now has a stable metadata contract for downstream API and UI wiring.

## Self-Check: PASSED

- Verified summary file exists on disk.
- Verified task commits `b6af3ec` and `787ab4a` exist in git history.
