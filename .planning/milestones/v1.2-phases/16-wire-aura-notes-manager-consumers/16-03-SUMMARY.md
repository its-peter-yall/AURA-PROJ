---
phase: 16-wire-aura-notes-manager-consumers
plan: "03"
subsystem: testing
tags: [integration-tests, settings-store, model-router, consumer-wiring, pytest]

# Dependency graph
requires:
  - phase: 16-wire-aura-notes-manager-consumers-01
    provides: SettingsStore and resolve_use_case_config() utility
  - phase: 16-wire-aura-notes-manager-consumers-02
    provides: Consumer wiring for entity_extractor, embeddings, summarizer
provides:
  - Integration tests verifying PP-05 through PP-08 consumer wiring
  - Redis fallback test coverage for all 4 consumers
  - Provider parameter verification for router.embed() calls
affects: testing infrastructure, CI regression coverage

# Tech tracking
tech-stack:
  added: []
  patterns: [mock-patching-at-import-site, get_default_sync-bypass]

key-files:
  created:
    - AURA-NOTES-MANAGER/api/tests/test_consumer_wiring.py
  modified: []

key-decisions:
  - "Patch get_default_sync and get_default_router at import site (services.embeddings, services.summarizer) not definition site, because 'from x import y' creates local references unaffected by source-module patches"
  - "Mock _run_sync at import site (services.embeddings._run_sync) to avoid asyncio.run on MagicMock coroutines in Python 3.14+"

patterns-established:
  - "Pattern: When testing consumers that import via 'from x import y', patch the target module's namespace (patch('consumer_module.y')), not the source module (patch('source_module.y'))"

requirements-completed: [PP-05, PP-06, PP-07, PP-08]

# Metrics
duration: 28min
completed: 2026-03-23
---

# Phase 16 Plan 03: Consumer Wiring Integration Tests Summary

**16 integration tests verifying all 4 AURA-NOTES-MANAGER consumers read from SettingsStore and route through ModelRouter with explicit provider, covering Redis-available and Redis-down fallback scenarios**

## Performance

- **Duration:** 28 min
- **Started:** 2026-03-23T08:02:00Z
- **Completed:** 2026-03-23T08:30:30Z
- **Tasks:** 1
- **Files modified:** 1 (642 lines)

## Accomplishments

- Created `test_consumer_wiring.py` with 16 test functions covering PP-05 through PP-08
- PP-05: `test_kg_processor_uses_resolve_config` — verifies GeminiClient routes through router.generate
- PP-06: `test_entity_extractor_passes_provider` — verifies LLMEntityExtractor uses SettingsStore config
- PP-07: `test_embeddings_passes_provider` — verifies EmbeddingService passes `provider="vertex_ai"` to router.embed()
- PP-08: `test_summarizer_uses_router` — verifies generate_university_notes routes through model router
- Redis fallback tests for entity_extraction (env var), embeddings (hardcoded), summarization (env var)
- Graceful fallback test verifying all 3 use cases return hardcoded defaults when Redis down + no env vars
- Provider parameter verification via captured call arguments in router.embed()
- No bare except:pass AST check on summarizer.py
- Cache invalidation test for clear_defaults_cache()

## Task Commits

1. **Task 1: Create integration test file for consumer wiring** - `73f932d` (test)
   - 16 test functions in `AURA-NOTES-MANAGER/api/tests/test_consumer_wiring.py`
   - All pass: 16/16 consumer wiring + 51/51 full suite (no regressions)

**Plan metadata:** (included in task commit)

## Files Created/Modified

- `AURA-NOTES-MANAGER/api/tests/test_consumer_wiring.py` - 642 lines, 16 test functions covering PP-05 through PP-08

## Decisions Made

- **Patch at import site, not definition site:** `from x import y` creates a local reference. Patching `source.y` doesn't affect `consumer.y`. Must patch `consumer_module.y` instead.
- **Mock _run_sync at import site:** Same import-site issue. `_run_sync` from `model_router.compat` imported into `services.embeddings` must be patched as `services.embeddings._run_sync`.
- **Python 3.14 asyncio.run compatibility:** `asyncio.get_event_loop().run_until_complete()` fails in Python 3.14 (no default loop). Used `@pytest.mark.asyncio` with `async def` instead.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed truncated test file (syntax error)**
- **Found during:** Task 1 (initial test run)
- **Issue:** `test_cache_invalidation_on_clear` was incomplete at line 508 — `_defaults_cache["entity_extraction"] = {` was never closed
- **Fix:** Completed the function and all remaining test functions
- **Files modified:** `AURA-NOTES-MANAGER/api/tests/test_consumer_wiring.py`
- **Verification:** pytest collection succeeds, no SyntaxError
- **Committed in:** 73f932d

**2. [Rule 3 - Blocking] Patched get_default_sync at import site to bypass Redis**
- **Found during:** Task 1 (test failure: Redis connection refused)
- **Issue:** `patch("model_router.settings_store.get_default_sync")` didn't affect consumers because `from model_router.settings_store import get_default_sync` creates local references
- **Fix:** Patched at import sites: `services.embeddings.get_default_sync`, `services.summarizer.get_default_sync`, `services.llm_entity_extractor.get_default_sync`
- **Files modified:** `AURA-NOTES-MANAGER/api/tests/test_consumer_wiring.py`
- **Verification:** All Redis connection errors eliminated from test output
- **Committed in:** 73f932d

**3. [Rule 3 - Blocking] Patched _run_sync and get_default_router at import sites**
- **Found during:** Task 1 (test failure: TypeError "awaitable is required")
- **Issue:** `_run_sync` and `get_default_router` also imported via `from x import y` — source-module patches didn't take effect
- **Fix:** Patched `services.embeddings._run_sync`, `services.embeddings.get_default_router`, `services.summarizer.get_genai_model`, `services.summarizer.get_model`
- **Files modified:** `AURA-NOTES-MANAGER/api/tests/test_consumer_wiring.py`
- **Verification:** `test_embeddings_passes_provider` and `test_router_embed_receives_provider` pass with provider captured correctly
- **Committed in:** 73f932d

**4. [Rule 3 - Blocking] Python 3.14 asyncio.run compatibility**
- **Found during:** Task 1 (RuntimeError: no current event loop)
- **Issue:** `asyncio.get_event_loop().run_until_complete()` fails in Python 3.14
- **Fix:** Changed `test_kg_processor_uses_resolve_config` to `async def` with `@pytest.mark.asyncio`
- **Files modified:** `AURA-NOTES-MANAGER/api/tests/test_consumer_wiring.py`
- **Verification:** Test passes with `await client.generate_text()`
- **Committed in:** 73f932d

---

**Total deviations:** 4 auto-fixed (4 blocking)
**Impact on plan:** All auto-fixes were necessary for test correctness in the offline test environment (no Redis, Python 3.14). No scope creep — fixes stayed within the test file.

## Issues Encountered

None beyond the deviations above.

## Next Phase Readiness

- Consumer wiring test coverage complete for PP-05 through PP-08
- Full test suite green (51/51)
- Ready for next plan in Phase 16 or phase transition

---

*Phase: 16-wire-aura-notes-manager-consumers*
*Completed: 2026-03-23*

## Self-Check: PASSED

- `test_consumer_wiring.py` exists (642 lines)
- `16-03-SUMMARY.md` exists
- Commit `73f932d` found in AURA-NOTES-MANAGER
- Commit `025ea55` found in root repo
- All 16 tests pass, full suite 51/51 green
