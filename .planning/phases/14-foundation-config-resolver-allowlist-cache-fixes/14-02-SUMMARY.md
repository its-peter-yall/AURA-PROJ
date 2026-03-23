---
phase: 14-foundation-config-resolver-allowlist-cache-fixes
plan: 02
subsystem: api
tags: [settings, api, gatekeeper, relationship_extraction]

# Dependency graph
requires:
  - phase: 14-foundation-config-resolver-allowlist-cache-fixes
    provides: ALLOWED_USE_CASES expansion
provides:
  - Expanded ALLOWED_USE_CASES in both AURA-CHAT and AURA-NOTES-MANAGER settings routers
  - New integration tests for gatekeeper and relationship_extraction use cases
affects: [v1.2 Phase 15]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Shared test patterns across AURA-CHAT and AURA-NOTES-MANAGER
    - Offline test doubles (FakeAsyncRedis) for Redis-free integration testing

key-files:
  created:
    - AURA-NOTES-MANAGER/api/tests/test_settings_router.py
  modified:
    - AURA-CHAT/server/routers/settings.py
    - AURA-NOTES-MANAGER/api/routers/settings.py
    - AURA-CHAT/server/tests/test_settings_router.py

key-decisions:
  - "Both routers use identical ALLOWED_USE_CASES sets for consistent API surface"
  - "NOTES test file mirrors CHAT pattern exactly for maintainability"

patterns-established:
  - "Pattern: FakeAsyncRedis double for offline Redis-free endpoint testing"

requirements-completed: [API-01, API-02]

# Metrics
duration: 3 min
completed: 2026-03-23T05:32:30Z
---

# Phase 14 Plan 02: ALLOWED_USE_CASES Expansion Summary

**Expanded ALLOWED_USE_CASES to include `gatekeeper` and `relationship_extraction` in both AURA-CHAT and AURA-NOTES-MANAGER settings routers, with integration tests**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-23T05:29:12Z
- **Completed:** 2026-03-23T05:32:30Z
- **Tasks:** 4
- **Files modified:** 4

## Accomplishments
- Expanded `ALLOWED_USE_CASES` in AURA-CHAT settings router to include `gatekeeper` and `relationship_extraction`
- Expanded `ALLOWED_USE_CASES` in AURA-NOTES-MANAGER settings router with identical values
- Added integration tests for both new use cases in AURA-CHAT
- Created new test file for AURA-NOTES-MANAGER mirroring CHAT pattern

## Task Commits

Each task was committed atomically:

1. **Task 1: Expand ALLOWED_USE_CASES in AURA-CHAT settings router** - `88bcf64` (feat)
2. **Task 2: Expand ALLOWED_USE_CASES in AURA-NOTES-MANAGER settings router** - `aa7084f` (feat)
3. **Task 3: Add tests for gatekeeper and relationship_extraction use cases** - `a0462b3` (test)
4. **Task 4: Create AURA-NOTES-MANAGER test_settings_router.py** - `317b247` (test)

**Plan metadata:** (docs commit at completion)

## Files Created/Modified
- `AURA-CHAT/server/routers/settings.py` - Added gatekeeper and relationship_extraction to ALLOWED_USE_CASES
- `AURA-NOTES-MANAGER/api/routers/settings.py` - Added gatekeeper and relationship_extraction to ALLOWED_USE_CASES
- `AURA-CHAT/server/tests/test_settings_router.py` - Added test_set_default_gatekeeper and test_set_default_relationship_extraction tests
- `AURA-NOTES-MANAGER/api/tests/test_settings_router.py` - Created new test file with all three tests

## Decisions Made

- Both routers use identical ALLOWED_USE_CASES sets for consistent API surface across both applications
- AURA-NOTES-MANAGER test file mirrors AURA-CHAT pattern exactly for maintainability

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed successfully on first attempt.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for Phase 15 (AURA-CHAT wiring) once gatekeeper and relationship_extraction are wired into the actual router/consumer code
- Both settings routers now accept the new use cases via PUT /api/v1/settings/defaults/{use_case}

---
*Phase: 14-foundation-config-resolver-allowlist-cache-fixes*
*Completed: 2026-03-23*
