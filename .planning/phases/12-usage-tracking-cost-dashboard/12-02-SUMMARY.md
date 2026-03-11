---
phase: 12-usage-tracking-cost-dashboard
plan: 02
subsystem: api
tags: [fastapi, redis, usage-tracking, sse, cost-estimation, model-router]

# Dependency graph
requires:
  - phase: 12-usage-tracking-cost-dashboard
    provides: UsageTracker, CostCalculator, and router instrumentation hooks (Plan 01)
provides:
  - REST endpoints for querying usage data in both AURA-CHAT and AURA-NOTES-MANAGER
  - SSE complete event usage payloads with token counts and estimated costs
  - UsageTracker + CostCalculator wired into model router singleton at app startup
affects: [phase-12-frontend-dashboard, session-cost-badge, admin-usage-page]

# Tech tracking
tech-stack:
  added: []
  patterns: [FastAPI Depends usage tracker injection, SSE usage payload injection, on_event startup tracker wiring]

key-files:
  created: [AURA-CHAT/server/routers/usage.py, AURA-NOTES-MANAGER/api/routers/usage.py]
  modified: [AURA-CHAT/server/main.py, AURA-NOTES-MANAGER/api/main.py, AURA-CHAT/server/routers/chat.py]

key-decisions:
  - "Reuse get_redis() from each app's settings.py for usage tracker Redis dependency injection."
  - "Inject usage data into SSE complete events at the event_generator level rather than modifying rag_engine internals."
  - "Wrap all usage estimation in try/except to guarantee zero-regression behavior for existing streaming."

patterns-established:
  - "Usage tracker Depends injection mirrors settings_store pattern: get_usage_tracker(redis=Depends(get_redis))."
  - "SSE usage payloads use _estimate_usage_payload helper with character-count token estimation fallback."

requirements-completed: [USAGE-01, USAGE-02]

# Metrics
duration: 5 min
completed: 2026-03-11
---

# Phase 12 Plan 02: Backend API endpoints + SSE completion usage data Summary

**REST usage query endpoints (summary, session, provider, model, daily) in both apps with SSE streaming cost estimation wired into model router at startup.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-11T09:15:46Z
- **Completed:** 2026-03-11T09:21:09Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created 5 usage query endpoints in both AURA-CHAT and AURA-NOTES-MANAGER at /api/v1/usage/*.
- Wired UsageTracker + CostCalculator into the model router singleton at app startup for both applications.
- Extended all SSE streaming "complete" events in chat.py with usage objects (input_tokens, output_tokens, thinking_tokens, estimated_cost_usd).

## Task Commits

Each task was committed atomically:

1. **Task 1: Usage API endpoints + tracker wiring in both apps** - `3f6218a` (feat)
2. **Task 2: SSE complete event usage data + metadata propagation** - `a4a8007` (feat)

_Plan metadata commit recorded after state/roadmap updates._

## Files Created/Modified
- `AURA-CHAT/server/routers/usage.py` - 5 usage query endpoints with date range filtering and provider/model/daily breakdowns.
- `AURA-NOTES-MANAGER/api/routers/usage.py` - Identical usage query endpoints adapted for NOTES-MANAGER import patterns.
- `AURA-CHAT/server/main.py` - Registers usage router, wires UsageTracker + CostCalculator at lifespan startup.
- `AURA-NOTES-MANAGER/api/main.py` - Registers usage router, wires tracker via @app.on_event("startup").
- `AURA-CHAT/server/routers/chat.py` - Adds _estimate_usage_payload helper and injects usage field into all SSE complete events.

## Decisions Made
- Reused the existing get_redis() Depends pattern from settings.py for consistency across both apps rather than creating a separate Redis connection.
- Injected usage data at the event_generator level in chat.py rather than modifying the rag_engine internals, keeping the change surface minimal and non-breaking.
- Wrapped all usage estimation in try/except so failures never break existing streaming behavior -- the usage field is purely additive.
- Used AURA-NOTES-MANAGER's @app.on_event("startup") for tracker wiring since it has no lifespan context manager, while AURA-CHAT uses its existing lifespan function.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Backend usage endpoints are ready for the frontend dashboard in Plan 12-03.
- SSE complete events carry usage data that can be consumed by the chat UI for per-session cost badges.
- Both apps have the model router's usage tracking active at startup.

## Self-Check: PASSED

- Verified all 5 created/modified files exist on disk.
- Verified task commits `3f6218a` and `a4a8007` exist in git history.
