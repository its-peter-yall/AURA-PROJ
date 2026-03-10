---
phase: 10-cross-app-migration-backend-integration
plan: 06
subsystem: api
tags: [model-router, redis, fastapi, cache, vertex-ai, openrouter, ollama]

# Dependency graph
requires:
  - phase: 10-cross-app-migration-backend-integration
    provides: shared model cache and encrypted provider key APIs from plans 10-01 and 10-02
provides:
  - Configurable shared model-cache TTL wiring for both backend settings routers
  - Central 5-60 minute TTL validation in the shared ModelCache helper
  - Provider-aware key validation responses for OpenRouter, Vertex AI, and Ollama
affects: [phase-11-frontend-settings-model-ui, admin-settings, provider-validation, integration-testing]

# Tech tracking
tech-stack:
  added: []
  patterns: [env-driven shared cache TTL bounds, provider-aware validation responses with null for non-applicable providers]

key-files:
  created: []
  modified:
    - shared/model_router/src/model_router/cache.py
    - shared/model_router/tests/test_model_cache.py
    - AURA-CHAT/server/routers/settings.py
    - AURA-CHAT/server/tests/test_settings_router.py
    - AURA-NOTES-MANAGER/api/routers/settings.py

key-decisions:
  - "Read MODEL_CACHE_TTL_SECONDS in each app router but enforce the 300-3600 second contract centrally inside shared ModelCache helpers."
  - "Return provider validation metadata plus JSON null for Ollama so the admin API distinguishes not-applicable validation from an actual failed credential check."

patterns-established:
  - "Shared cache guardrails live in model_router/cache.py while app routers only provide environment wiring."
  - "Settings APIs use provider-specific validation paths: stored-key health checks for OpenRouter, router-provider health checks for Vertex AI, and null validation for providers without API keys."

# Metrics
duration: 14 min
completed: 2026-03-10
---

# Phase 10 Plan 06: Cache TTL and provider validation gap closure Summary

**Shared model discovery now enforces 5-60 minute TTL bounds, and both settings APIs validate OpenRouter and Vertex AI while reporting Ollama validation as not applicable.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-03-10T17:28:28Z
- **Completed:** 2026-03-10T17:42:30Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Added shared TTL validation constants and bounds checks for `ModelCache` and `get_cached_models()`.
- Wired `MODEL_CACHE_TTL_SECONDS` into both AURA-CHAT and AURA-NOTES-MANAGER settings routers.
- Added provider-aware validation so OpenRouter uses stored-key health checks, Vertex AI uses router provider health checks, and Ollama returns `null` with explicit validation metadata.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add configurable TTL with 5-60 minute bounds enforcement** - `307ef09` (root feat), `7775b63` (CHAT feat), `7e410d9` (NOTES feat)
2. **Task 2: Add provider-aware API key validation for Vertex AI** - `232b741` (CHAT feat), `54168eb` (NOTES feat)

**Plan metadata:** pending root planning metadata commit

## Files Created/Modified
- `shared/model_router/src/model_router/cache.py` - Defines shared TTL constants and rejects out-of-range cache TTL values.
- `shared/model_router/tests/test_model_cache.py` - Verifies valid bounds, invalid bounds, defaults, and helper-level TTL enforcement.
- `AURA-CHAT/server/routers/settings.py` - Reads cache TTL from env and returns provider-aware validation responses.
- `AURA-CHAT/server/tests/test_settings_router.py` - Covers Vertex AI and Ollama validation behavior in the CHAT settings API.
- `AURA-NOTES-MANAGER/api/routers/settings.py` - Mirrors the TTL wiring and provider-aware validation behavior in NOTES.

## Decisions Made
- Read `MODEL_CACHE_TTL_SECONDS` in each backend router, but keep the 300-3600 second guardrail inside the shared cache layer so both apps fail consistently on misconfiguration.
- Returned `validation_method` metadata and `null` for Ollama validation so admin clients can distinguish unsupported validation from a genuinely invalid key.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- NOTES router import verification emitted pre-existing Neo4j/Firebase startup warnings under missing local env configuration, but the settings router still imported successfully and the warning path was out of scope for this plan.
- `gsd-tools` state-advance automation still could not parse the legacy `STATE.md` shape, so `STATE.md` and `ROADMAP.md` were updated manually after the task commits.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 10 gap-closure work is complete and the backend settings surface now satisfies the remaining TTL and provider-validation contracts for Phase 11.
- Frontend provider settings and model-selection work can now rely on stable cache TTL configuration and richer validation responses.

## Self-Check: PASSED

- Verified summary file exists on disk.
- Verified task commits `307ef09`, `7775b63`, `7e410d9`, `232b741`, and `54168eb` exist in the relevant repositories.
- Verified key modified files exist: `shared/model_router/src/model_router/cache.py`, `shared/model_router/tests/test_model_cache.py`, `AURA-CHAT/server/routers/settings.py`, `AURA-CHAT/server/tests/test_settings_router.py`, and `AURA-NOTES-MANAGER/api/routers/settings.py`.

---
*Phase: 10-cross-app-migration-backend-integration*
*Completed: 2026-03-10*
