---
phase: 10-cross-app-migration-backend-integration
plan: 02
subsystem: api
tags: [fastapi, redis, model-router, settings, fernet]

# Dependency graph
requires:
  - phase: 10-cross-app-migration-backend-integration
    provides: shared Redis-backed settings store, encrypted key manager, and model cache from plan 10-01
provides:
  - Shared admin settings REST endpoints in AURA-CHAT and AURA-NOTES-MANAGER
  - Cached provider model discovery and masked API key management APIs
  - ASGI integration coverage for defaults, models, and API key lifecycle
affects: [phase-10-plan-04, frontend-settings-ui, cross-app-config]

# Tech tracking
tech-stack:
  added: []
  patterns: [module-scoped async Redis dependencies, shared SettingsStore/KeyManager/ModelCache injection, cache-backed aggregate model discovery]

key-files:
  created:
    - AURA-CHAT/server/routers/settings.py
    - AURA-NOTES-MANAGER/api/routers/settings.py
    - AURA-CHAT/server/tests/test_settings_router.py
    - .planning/phases/10-cross-app-migration-backend-integration/10-USER-SETUP.md
    - .planning/phases/10-cross-app-migration-backend-integration/10-02-SUMMARY.md
  modified:
    - AURA-CHAT/server/main.py
    - AURA-NOTES-MANAGER/api/main.py
    - .planning/STATE.md
    - .planning/ROADMAP.md

key-decisions:
  - "Validate OpenRouter API keys with a temporary OpenRouterProvider health check and report other providers as unvalidated instead of exposing plaintext secrets."
  - "Serve GET /api/v1/settings/models via ModelCache fan-out per provider so aggregate discovery respects the same cache and dependency overrides as provider-scoped listings."

patterns-established:
  - "Both backends expose the same /api/v1/settings surface by wiring identical shared-model-router dependencies at the router layer."
  - "Settings endpoint tests run offline with FakeAsyncRedis plus ASGITransport dependency overrides instead of live Redis or provider credentials."

# Metrics
duration: 10 min
completed: 2026-03-10
---

# Phase 10 Plan 02: Admin settings REST endpoints Summary

**Cross-app FastAPI settings endpoints for shared defaults, cached model discovery, and encrypted provider API key management**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-10T15:53:17Z
- **Completed:** 2026-03-10T16:03:33Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments
- Added matching `/api/v1/settings` routers to AURA-CHAT and AURA-NOTES-MANAGER with defaults CRUD, model listing, API key storage, masked lookup, deletion, and validation endpoints.
- Registered both settings routers in their FastAPI applications using shared `SettingsStore`, `KeyManager`, and `ModelCache` dependency injection.
- Added offline ASGI integration coverage for defaults, provider models, aggregate models, and API key lifecycle flows.

## Task Commits

Each task was committed atomically:

1. **Task 1: AURA-CHAT admin settings router + registration** - `3192a32` (feat)
2. **Task 2: AURA-NOTES-MANAGER admin settings router + registration** - `d0a99d0` (feat)
3. **Task 3 / RED: Integration tests for settings REST endpoints** - `7b7f7e2` (test)
4. **Task 3 / GREEN: Make settings endpoints satisfy integration coverage** - `e1e9235` (feat)
5. **Task 3 / Rule 1 follow-up: Keep NOTES aggregate model listing in parity** - `dd8ac97` (fix)

**Plan metadata:** pending root planning commit

_Note: Task 3 executed as a TDD red/green cycle with one follow-up bug-fix commit discovered by the new tests._

## Files Created/Modified
- `AURA-CHAT/server/routers/settings.py` - AURA-CHAT admin settings endpoints backed by shared Redis config helpers.
- `AURA-CHAT/server/main.py` - Registers the settings router in the CHAT FastAPI app.
- `AURA-NOTES-MANAGER/api/routers/settings.py` - NOTES admin settings endpoints mirroring the CHAT surface.
- `AURA-NOTES-MANAGER/api/main.py` - Registers the settings router in the NOTES FastAPI app.
- `AURA-CHAT/server/tests/test_settings_router.py` - Offline ASGI integration tests for defaults, models, and API keys.
- `.planning/phases/10-cross-app-migration-backend-integration/10-USER-SETUP.md` - Documents required `AURA_MASTER_KEY` setup.

## Decisions Made
- Used a temporary `OpenRouterProvider` health check for API key validation so stored OpenRouter credentials can be verified without adding app-specific validation code paths.
- Aggregated `GET /api/v1/settings/models` through `ModelCache` provider fan-out so all model discovery endpoints share the same cache semantics and test overrides.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Switched aggregate model discovery to the shared cache path in both apps**
- **Found during:** Task 3 (Integration tests for settings REST endpoints)
- **Issue:** `GET /api/v1/settings/models` initially bypassed the injected `ModelCache`, so aggregate listings ignored cache overrides and NOTES parity drifted from CHAT.
- **Fix:** Updated both routers to iterate each `ProviderType` through `cache.get_models(...)`, skipping unavailable providers while preserving shared cache behavior.
- **Files modified:** `AURA-CHAT/server/routers/settings.py`, `AURA-NOTES-MANAGER/api/routers/settings.py`
- **Verification:** `../.venv/Scripts/python -m pytest server/tests/test_settings_router.py -x -v --tb=short`, router import checks in both apps
- **Committed in:** `e1e9235`, `dd8ac97`

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary to keep the cross-app settings surface consistent and to satisfy the planned aggregate model discovery contract. No scope creep.

## Issues Encountered
- NOTES router import/startup checks emitted pre-existing Neo4j/Firebase initialization warnings during module import, but the FastAPI app still loaded successfully and the settings router route count matched expectations.
- Root planning automation may still be affected by the legacy STATE.md shape already noted in 10-01; planning files were verified after update.
- The `gsd-tools` metadata commit helper parsed the commit message incorrectly under this shell, so the final planning-artifact commit was created with direct `git add`/`git commit` commands against the intended files only.

## User Setup Required

**External services require manual configuration.** See [10-USER-SETUP.md](./10-USER-SETUP.md) for:
- The shared `AURA_MASTER_KEY` environment variable
- Where to persist it for both backends
- Verification commands for the settings key manager imports

## Next Phase Readiness
- Both backend apps now expose the shared admin settings surface required by frontend settings UI and remaining NOTES migration work.
- Phase 10 Plan 04 can reuse the new settings endpoints while completing NOTES façade migration and no-direct-import verification.

## Self-Check: PASSED

---
*Phase: 10-cross-app-migration-backend-integration*
*Completed: 2026-03-10*
