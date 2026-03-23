---
phase: 16-wire-aura-notes-manager-consumers
plan: "01"
subsystem: ai-ml
tags: [model_router, settings_store, entity_extraction, kg_processor, provider_routing]

# Dependency graph
requires:
  - phase: 16-03
    provides: integration tests for consumer wiring (PP-05 through PP-08)
  - phase: 15
    provides: model_router with resolve_use_case_config() utility
provides:
  - llm_entity_extractor reads provider/model from SettingsStore at call time
  - kg_processor routes through ModelRouter with explicit provider parameter
  - No import-time or init-time get_default_sync() calls in entity_extraction consumers
affects:
  - Phase 16 Plan 02 (remaining consumer wiring)

# Tech tracking
tech-stack:
  added: [services/__init__.py]
  patterns:
    - "Call-time config resolution via resolve_use_case_config() replaces import-time SettingsStore reads"
    - "Explicit provider parameter routing via router.generate(provider=cfg['provider'])"
    - "Patch at import site (consumer module namespace) not definition site for unittest.mock.patch"

key-files:
  created:
    - AURA-NOTES-MANAGER/services/__init__.py
  modified:
    - AURA-NOTES-MANAGER/services/llm_entity_extractor.py
    - AURA-NOTES-MANAGER/api/kg_processor.py
    - AURA-NOTES-MANAGER/api/tests/test_consumer_wiring.py

key-decisions:
  - "Keep LLM_ENTITY_EXTRACTION_MODEL constant as constructor default only; actual LLM calls use resolve_use_case_config() at runtime"
  - "Remove GenerationConfig and generate_content imports from both consumers since router.generate() replaces them"
  - "Add services/__init__.py to fix unittest.mock.patch module resolution in Python 3.14 with namespace packages"
  - "Test patches must target import site (api.kg_processor.get_default_router) not source (model_router.get_default_router)"

patterns-established:
  - "Consumer wiring pattern: import resolve_use_case_config/get_default_router, call at method start, pass provider to router.generate()"
  - "Test mock pattern: patch at consumer import site for from-import style imports"

requirements-completed: [PP-05, PP-06]

# Metrics
duration: 45min
completed: 2026-03-23
---

# Phase 16 Plan 01: Wire AURA-NOTES-MANAGER Entity Extraction Consumers Summary

**Replaced import-time SettingsStore reads with call-time resolve_use_case_config() in both entity extraction consumers (llm_entity_extractor and kg_processor), routing all LLM calls through ModelRouter with explicit provider parameter**

## Performance

- **Duration:** 45 min
- **Started:** 2026-03-23T14:18:29Z
- **Completed:** 2026-03-23T15:03:29Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Removed import-time `get_default_sync()` block from llm_entity_extractor.py that read SettingsStore at module level
- Both `_extract_from_batch()` and `_extract_relationships_via_llm()` now call `resolve_use_case_config("entity_extraction")` at runtime and pass explicit `provider` to `router.generate()`
- GeminiClient in kg_processor.py routes `generate_text()` and `extract_entities()` through `router.generate()` with call-time config resolution
- All 16 consumer wiring integration tests pass (PP-05 through PP-08)

## Task Commits

1. **Task 1: Wire llm_entity_extractor to resolve_use_case_config at call-time** - `d45e761` (feat)
   - Removed import-time get_default_sync() block (lines 203-222)
   - Added resolve_use_case_config/get_default_router imports from model_router
   - Replaced generate_content() with router.generate() in _extract_from_batch() and _extract_relationships_via_llm()
   - Added services/__init__.py for package resolution
   - Removed unused GenerationConfig, generate_content imports

2. **Task 2: Patch KG processor to use resolve_use_case_config at runtime** - `2084f2a` (feat)
   - Added resolve_use_case_config/get_default_router imports from model_router
   - GeminiClient.generate_text() uses resolve_use_case_config("entity_extraction") at runtime
   - GeminiClient.extract_entities() uses resolve_use_case_config("entity_extraction") at runtime
   - Both pass provider=cfg["provider"] to router.generate()
   - Fixed test patches to target api.kg_processor import sites

## Files Created/Modified
- `AURA-NOTES-MANAGER/services/__init__.py` - Package init file for proper unittest.mock.patch resolution
- `AURA-NOTES-MANAGER/services/llm_entity_extractor.py` - Removed import-time config, added call-time routing
- `AURA-NOTES-MANAGER/api/kg_processor.py` - Added call-time config resolution to GeminiClient methods
- `AURA-NOTES-MANAGER/api/tests/test_consumer_wiring.py` - Fixed mock patch targets to import sites

## Decisions Made
- Keep LLM_ENTITY_EXTRACTION_MODEL as constructor default only; actual routing uses resolve_use_case_config()
- Remove GenerationConfig and generate_content imports (replaced by router.generate)
- Add services/__init__.py to fix Python 3.14 namespace package mock.patch resolution
- Test patches must target import site not definition site for from-import style imports

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created services/__init__.py for package resolution**
- **Found during:** Task 1 (verifying test_entity_extractor_passes_provider)
- **Issue:** unittest.mock.patch("services.llm_entity_extractor.get_default_router") failed because services directory had no __init__.py, causing Python 3.14 namespace package resolution to fail
- **Fix:** Created services/__init__.py with package docstring
- **Files modified:** AURA-NOTES-MANAGER/services/__init__.py
- **Verification:** Test passes after __init__.py creation
- **Committed in:** d45e761 (Task 1 commit)

**2. [Rule 3 - Blocking] Installed missing dependencies (json_repair, pymupdf, neo4j, python-dotenv, firebase-admin)**
- **Found during:** Task 1 and Task 2 (running verification tests)
- **Issue:** Multiple missing Python dependencies prevented module imports and test execution
- **Fix:** Installed json_repair, pymupdf, neo4j, python-dotenv, firebase-admin via pip
- **Files modified:** None (environment only)
- **Verification:** All 16 consumer wiring tests pass
- **Committed in:** d45e761, 2084f2a

**3. [Rule 1 - Bug] Fixed test mock patch targets to use import sites**
- **Found during:** Task 2 (test_kg_processor_uses_resolve_config failed)
- **Issue:** Test patched model_router.get_default_router (definition site) instead of api.kg_processor.get_default_router (import site). Python's from-import creates local references unaffected by source-module patches.
- **Fix:** Updated test patches: model_router.get_default_router → api.kg_processor.get_default_router, services.embeddings.resolve_use_case_config → api.kg_processor.resolve_use_case_config
- **Files modified:** AURA-NOTES-MANAGER/api/tests/test_consumer_wiring.py
- **Verification:** test_kg_processor_uses_resolve_config passes
- **Committed in:** 2084f2a (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (3 blocking)
**Impact on plan:** All deviations were necessary for correctness. No scope creep — each fix directly enabled the planned task to complete.

## Issues Encountered
- Python 3.14 namespace package resolution differs from 3.10-3.13, requiring explicit __init__.py for unittest.mock.patch compatibility
- Missing dependencies in the environment required multiple pip installs before tests could run

## Next Phase Readiness
- PP-05 (kg_processor) and PP-06 (entity_extractor) are complete
- PP-07 (embeddings) and PP-08 (summarizer) were already wired in prior plans
- All 16 consumer wiring tests pass — Phase 16 consumer wiring is functionally complete
- Ready for Phase 16 Plan 02 or transition to next phase

---
*Phase: 16-wire-aura-notes-manager-consumers*
*Completed: 2026-03-23*

## Self-Check: PASSED
- services/__init__.py: FOUND
- 16-01-SUMMARY.md: FOUND
- Commit d45e761: FOUND
- Commit 2084f2a: FOUND
