---
phase: 10-cross-app-migration-backend-integration
plan: 01
subsystem: api
tags: [redis, fernet, model-router, caching, pytest]

# Dependency graph
requires:
  - phase: 09-openrouter-streaming
    provides: router metadata APIs and shared provider model listing surface
provides:
  - Redis-backed default model settings store for shared admin configuration
  - Fernet-encrypted provider API key storage with masked display helpers
  - TTL-based shared model list caching helper for backend settings endpoints
affects: [phase-10-plan-02, backend-settings, celery-workers, cross-app-config]

# Tech tracking
tech-stack:
  added: [cryptography.fernet]
  patterns: [constructor-injected async Redis clients, JSON Redis payloads, offline FakeAsyncRedis tests]

key-files:
  created:
    - shared/model_router/src/model_router/settings_store.py
    - shared/model_router/src/model_router/key_manager.py
    - shared/model_router/src/model_router/cache.py
    - shared/model_router/tests/test_settings_store.py
    - shared/model_router/tests/test_key_manager.py
    - shared/model_router/tests/test_model_cache.py
    - .planning/phases/10-cross-app-migration-backend-integration/deferred-items.md
  modified:
    - shared/model_router/src/model_router/__init__.py
    - shared/model_router/tests/conftest.py

key-decisions:
  - "Use constructor-injected async Redis clients in all config helpers so shared modules stay Redis-library agnostic across both apps."
  - "Fail fast when AURA_MASTER_KEY is missing instead of generating a transient Fernet key, preventing unreadable encrypted credentials after restart."
  - "Serialize ModelInfo payloads with model_dump(mode='json') before caching so ProviderType enums round-trip through Redis safely."

patterns-established:
  - "Shared config helpers accept async dependencies rather than importing infrastructure clients directly."
  - "Offline Redis behavior is validated with FakeAsyncRedis fixtures, including simulated TTL expiry."

# Metrics
duration: 10 min
completed: 2026-03-10
---

# Phase 10 Plan 01: Shared config modules Summary

**Redis-backed defaults, Fernet-encrypted API key storage, and TTL model discovery caching for the shared model_router package**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-10T15:24:56Z
- **Completed:** 2026-03-10T15:35:08Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Added `SettingsStore` for cross-app default provider/model persistence in a shared Redis hash.
- Added `KeyManager` for encrypted provider API keys with masking, deletion, and async validation callback support.
- Added `ModelCache` and `get_cached_models()` plus 23 offline unit tests using `FakeAsyncRedis`.

## Task Commits

Each task was committed atomically:

1. **Task 1 / RED:** add failing coverage for shared config modules - `c838f8d` (test)
2. **Task 1 / GREEN:** add shared Redis-backed config modules - `53e53a1` (feat)

**Plan metadata:** recorded in the final docs commit for this plan

_Note: This plan executed as a TDD red/green cycle across the two planned tasks._

## Files Created/Modified
- `shared/model_router/src/model_router/settings_store.py` - Shared Redis hash CRUD for use-case defaults.
- `shared/model_router/src/model_router/key_manager.py` - Fernet-encrypted provider key storage and masking.
- `shared/model_router/src/model_router/cache.py` - TTL model list cache backed by Redis `setex`.
- `shared/model_router/src/model_router/__init__.py` - Public exports for config helpers.
- `shared/model_router/tests/conftest.py` - Added `FakeAsyncRedis`, `fake_redis`, and `master_key` fixtures.
- `shared/model_router/tests/test_settings_store.py` - Settings store CRUD coverage.
- `shared/model_router/tests/test_key_manager.py` - Key encryption, masking, and validation coverage.
- `shared/model_router/tests/test_model_cache.py` - Cache miss/hit/refresh/expiry coverage.
- `.planning/phases/10-cross-app-migration-backend-integration/deferred-items.md` - Logged out-of-scope pre-existing verification blocker.

## Decisions Made
- Used constructor-injected async Redis clients in every config helper so the shared package remains independent from `redis` or `redis.asyncio` imports.
- Required `AURA_MASTER_KEY` at initialization time to avoid transient encryption keys that would make stored credentials unreadable after restart.
- Serialized cached `ModelInfo` objects with `model_dump(mode='json')` so enum values round-trip cleanly through Redis JSON payloads.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added FakeAsyncRedis TTL controls for cache expiry tests**
- **Found during:** Task 2 (TDD unit tests for settings store, key manager, and model cache)
- **Issue:** The plan required offline cache-expiry verification, but no existing Redis test double could simulate TTL behavior.
- **Fix:** Added `FakeAsyncRedis` with `setex`, expiry bookkeeping, and `advance_time()` so model cache tests remain deterministic and offline.
- **Files modified:** `shared/model_router/tests/conftest.py`, `shared/model_router/tests/test_model_cache.py`
- **Verification:** `../../.venv/Scripts/python -m pytest tests/test_model_cache.py -v`
- **Committed in:** `c838f8d`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Required to satisfy the planned TTL cache verification without introducing a real Redis dependency. No scope creep.

## Issues Encountered
- Full `shared/model_router` suite currently has 3 pre-existing failures in `tests/test_compat.py` caused by unrelated dirty-worktree changes in `AURA-CHAT/backend/utils/vertex_ai_client.py` (`_GenerativeModelWrapper` missing). Logged to `deferred-items.md` and left untouched per scope boundary.
- `gsd-tools` could record the metric and roadmap update, but `state advance-plan` / `state update-progress` could not parse the legacy STATE.md shape. STATE.md was updated manually to keep planning artifacts accurate.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Shared config primitives are ready for Phase 10 Plan 02 settings endpoints.
- Full-suite regression remains blocked by the out-of-scope compat failures and should be resolved before relying on a clean package-wide green build.

## Self-Check: PASSED

---
*Phase: 10-cross-app-migration-backend-integration*
*Completed: 2026-03-10*
