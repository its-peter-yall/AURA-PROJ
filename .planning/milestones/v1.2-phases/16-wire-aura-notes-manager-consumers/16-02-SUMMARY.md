---
phase: 16-wire-aura-notes-manager-consumers
plan: "02"
subsystem: ai-integration
tags: [model-router, embeddings, summarizer, settings-store, provider-routing]

# Dependency graph
requires:
  - phase: 16-03
    provides: Integration tests verifying PP-05 through PP-08 consumer wiring
provides:
  - Embeddings service with call-time provider resolution from SettingsStore
  - Summarization service routing through ModelRouter with proper error handling
  - All 16 consumer wiring tests passing
affects:
  - AURA-NOTES-MANAGER KG processing pipeline (embeddings + summarization)
  - Future consumer wiring in AURA-CHAT

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Call-time config resolution: resolve_use_case_config() at each invocation instead of init-time get_default_sync()"
    - "ModelRouter bridging: _run_sync from model_router.compat for sync-to-async router calls"
    - "Single-router path: router.generate() replacing dual SDK (genai + vertex_ai) fallback chains"

key-files:
  created: []
  modified:
    - AURA-NOTES-MANAGER/services/embeddings.py
    - AURA-NOTES-MANAGER/services/summarizer.py
    - AURA-NOTES-MANAGER/api/tests/test_consumer_wiring.py

key-decisions:
  - "Used _run_sync from model_router.compat instead of asyncio.get_event_loop().run_until_complete() for Python 3.14 compatibility"
  - "Removed init-time get_default_sync() entirely from EmbeddingService.__init__ in favor of per-call resolve_use_case_config()"
  - "Removed _build_generation_config() helper — router.generate() accepts kwargs directly (temperature, top_p, max_output_tokens)"
  - "Updated test mocks to patch resolve_use_case_config and _run_sync at consumer module import sites rather than at definition sites"

patterns-established:
  - "Call-time provider resolution: Each consumer calls resolve_use_case_config(use_case) at invocation time, not init time"
  - "Sync-to-async bridging via _run_sync: All sync consumer functions use model_router.compat._run_sync() to call async router methods"

requirements-completed: [PP-07, PP-08]

# Metrics
duration: 20min
completed: 2026-03-23
---

# Phase 16 Plan 02: Wire Embeddings and Summarizer to ModelRouter Summary

**Embeddings and summarizer services now resolve provider config at call-time via resolve_use_case_config() and route through ModelRouter, replacing init-time SettingsStore reads and dual SDK fallback chains.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-03-23T14:18:37+05:30
- **Completed:** 2026-03-23T14:38:37+05:30
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Removed init-time `get_default_sync()` from EmbeddingService — provider now resolved at each batch via `resolve_use_case_config("embeddings")`
- Replaced summarizer dual SDK path (genai_client + vertex_ai_client) with single `router.generate()` call
- Fixed bare `except:pass` in summarizer with `logger.warning(..., exc_info=True)`
- All 16 consumer wiring integration tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Move embeddings provider resolution from init-time to call-time** - `74f826e` (feat)
2. **Task 2: Replace summarizer dual SDK path with router.generate() and fix bare except:pass** - `22c4784` (feat)

**Plan metadata:** (pending — included in final commit)

## Files Created/Modified
- `AURA-NOTES-MANAGER/services/embeddings.py` — Removed init-time `get_default_sync()`, `_embedding_default` attribute; `_embed_batch_sync()` now calls `resolve_use_case_config("embeddings")` at runtime
- `AURA-NOTES-MANAGER/services/summarizer.py` — Removed dual SDK imports, `_build_generation_config()`, and fallback chain; replaced with single `router.generate()` via `_run_sync()` with `logger.warning(..., exc_info=True)` error handling
- `AURA-NOTES-MANAGER/api/tests/test_consumer_wiring.py` — Updated test mocks to patch `resolve_use_case_config` and `_run_sync` at consumer import sites instead of `get_default_sync`

## Decisions Made
- Used `_run_sync` from `model_router.compat` instead of `asyncio.get_event_loop().run_until_complete()` for Python 3.14 compatibility (the latter raises RuntimeError when no event loop exists)
- Removed `_build_generation_config()` entirely — `router.generate()` accepts kwargs directly, making the helper unnecessary
- Updated test mocks to patch at consumer module import sites (e.g., `services.embeddings.resolve_use_case_config`) rather than definition sites, because `from x import y` creates local references unaffected by source-module patches

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed asyncio.get_event_loop() RuntimeError in Python 3.14**
- **Found during:** Task 2 (test_summarizer_uses_router failure)
- **Issue:** `asyncio.get_event_loop().run_until_complete()` raises `RuntimeError: There is no current event loop in thread 'MainThread'` in Python 3.14
- **Fix:** Replaced with `_run_sync()` from `model_router.compat` which handles sync/async bridging properly
- **Files modified:** `services/summarizer.py`
- **Verification:** All 16 tests pass

**2. [Rule 3 - Blocking] Updated stale test mocks for removed get_default_sync imports**
- **Found during:** Task 1 (full test suite run)
- **Issue:** `test_kg_processor_uses_resolve_config`, `test_entity_extractor_passes_provider`, and `test_summarizer_uses_router` patched `get_default_sync` which was removed from embeddings.py
- **Fix:** Replaced patches with `resolve_use_case_config` mocks at correct import sites; also fixed `model_router.get_default_router` → `services.llm_entity_extractor.get_default_router` for local import references
- **Files modified:** `api/tests/test_consumer_wiring.py`
- **Verification:** All 16 tests pass

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes were necessary for test compatibility with the changes. No scope creep.

## Issues Encountered
- Stale `.pyc` caches caused intermittent `NameError: name 'get_default_sync' is not defined` in llm_entity_extractor.py — resolved by running pytest with `-B` flag
- Python 3.14 removed implicit event loop creation in MainThread — `_run_sync` from model_router.compat was the correct bridge utility

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both embeddings and summarizer now route through ModelRouter with call-time provider resolution
- All 16 PP-05 through PP-08 consumer wiring tests pass
- Ready for next plan in the phase (if any) or phase completion

---
*Phase: 16-wire-aura-notes-manager-consumers*
*Completed: 2026-03-23*

## Self-Check: PASSED
