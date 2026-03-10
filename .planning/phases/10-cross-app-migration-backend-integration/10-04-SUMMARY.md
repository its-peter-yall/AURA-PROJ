---
phase: 10-cross-app-migration-backend-integration
plan: 04
subsystem: api
tags: [model-router, vertex-ai, embeddings, celery, audit, aura-notes-manager]

# Dependency graph
requires:
  - phase: 08-shared-package-vertex-ai
    provides: VertexCompatModel, shared router package, import-context coverage
  - phase: 10-cross-app-migration-backend-integration
    provides: AURA-CHAT model-router façade migration from 10-03
provides:
  - AURA-NOTES-MANAGER router-backed Vertex and GenAI façade modules
  - NOTES embedding service delegation to router.embed with preserved batching and retry logic
  - Cross-app no-direct-imports regression audit with Celery import-context verification
affects: [11-frontend-settings-model-ui, 13-polish-integration-testing, UI-03]

# Tech tracking
tech-stack:
  added: []
  patterns: [legacy notes façade modules delegating to model_router, AST-based import audit for non-test Python files]

key-files:
  created: [tests/test_no_direct_imports.py]
  modified: [AURA-NOTES-MANAGER/services/vertex_ai_client.py, AURA-NOTES-MANAGER/services/genai_client.py, AURA-NOTES-MANAGER/services/embeddings.py, AURA-NOTES-MANAGER/api/verify_phase_1.py]

key-decisions:
  - "Preserve AURA-NOTES-MANAGER consumer imports by rewriting the service hub files as router-backed façades instead of editing downstream modules."
  - "Use AST-based forbidden-import scanning so regression tests catch real imports without flagging string literals in verification scripts."

patterns-established:
  - "NOTES façade pattern: keep legacy exports like GenerationConfig, get_model, and get_genai_model while delegating execution to model_router."
  - "Cross-app compliance audit pattern: scan only AST import nodes in non-test Python files and pair that with working-directory import-context subprocess checks."

# Metrics
duration: 17 min
completed: 2026-03-10
---

# Phase 10 Plan 04: AURA-NOTES-MANAGER model_router façade migration Summary

**AURA-NOTES-MANAGER now routes legacy generation and embedding hub modules through model_router, and the monorepo has an automated cross-app audit proving non-test Python files no longer import provider SDKs directly.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-03-10T15:53:50Z
- **Completed:** 2026-03-10T16:11:32Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Replaced NOTES `vertex_ai_client.py`, `genai_client.py`, and `embeddings.py` with model-router façades that preserve legacy imports for existing services and KG processing.
- Verified NOTES consumer modules and Celery-style import contexts still import successfully without changing downstream code.
- Added a root-level regression test that audits both apps for forbidden direct SDK imports and validates `model_router` imports from repo root, app directories, and the NOTES Celery worker directory.

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite NOTES hub files as model-router façades** - `cfa7911` (feat), `2328d32` (fix), `ba396d0` (fix)
2. **Task 2: Celery import verification + no-direct-imports audit test** - `96a632b` (test), `e71868a` (feat)

**Plan metadata:** pending root planning metadata commit

_Note: Task 2 used the required TDD flow (failing audit test first, then passing implementation)._ 

## Files Created/Modified
- `AURA-NOTES-MANAGER/services/vertex_ai_client.py` - Router-backed Vertex façade preserving NOTES legacy exports and shim hooks.
- `AURA-NOTES-MANAGER/services/genai_client.py` - Router-backed GenAI shim with compatibility for older tests and fallback call sites.
- `AURA-NOTES-MANAGER/services/embeddings.py` - NOTES embedding orchestration preserved while batch execution delegates to `router.embed()`.
- `AURA-NOTES-MANAGER/api/verify_phase_1.py` - Verification script adjusted so compliance checks do not false-positive on their own pattern string.
- `tests/test_no_direct_imports.py` - Root regression suite auditing both apps for forbidden imports and import-context regressions.

## Decisions Made
- Preserved the existing NOTES service import contract rather than editing all consumers, because hub-file façades keep the migration localized and Celery-safe.
- Switched the no-direct-imports audit to AST import inspection, because raw text scanning incorrectly flagged verification-script string literals instead of actual imports.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Restored legacy shim hooks required by shared compatibility tests**
- **Found during:** Task 1 (Rewrite NOTES hub files as model-router façades)
- **Issue:** The initial NOTES façade removed the legacy `GenerativeModel` fallback surface and `USE_MODEL_ROUTER` shim path expected by `shared/model_router/tests/test_compat.py`.
- **Fix:** Reintroduced `GenerativeModel` as a compatibility alias and restored the shim/fallback behavior while keeping the module free of direct SDK imports.
- **Files modified:** `AURA-NOTES-MANAGER/services/vertex_ai_client.py`
- **Verification:** `cd shared/model_router && set AURA_TEST_MODE=true && ../../.venv/Scripts/python -m pytest tests/test_compat.py -q`
- **Committed in:** `2328d32`

**2. [Rule 1 - Bug] Removed a manual-audit false positive from the NOTES verifier script**
- **Found during:** Task 2 (Celery import verification + no-direct-imports audit test)
- **Issue:** The manual forbidden-import audit flagged `api/verify_phase_1.py` because its string literal contained `import google.generativeai`, even though no actual import remained.
- **Fix:** Split the verifier pattern string so manual grep-style auditing no longer reports the verifier itself.
- **Files modified:** `AURA-NOTES-MANAGER/api/verify_phase_1.py`
- **Verification:** Root manual audit command returned `TOTAL=0`
- **Committed in:** `ba396d0`

---

**Total deviations:** 2 auto-fixed (2 bug)
**Impact on plan:** Both fixes were compatibility/compliance safeguards required to satisfy UI-03 without changing downstream NOTES consumers.

## Issues Encountered
- The first RED audit version used raw line scanning and surfaced a false positive from a verification script string literal; switching to AST import scanning produced a stable compliance test.
- The shared package compatibility suite exposed an implicit legacy contract on the NOTES façade that the plan did not spell out; the façade was extended without reintroducing provider SDK imports.

## User Setup Required

None - no external service configuration required for this plan.

## Next Phase Readiness
- UI-03 is now covered across both applications by router-backed façade modules plus an automated no-direct-imports audit.
- Phase 10 now has summaries for all four plans and is ready for phase-completion transition work.

## Self-Check: PASSED

- Verified summary file exists on disk.
- Verified task commits `cfa7911`, `2328d32`, `ba396d0`, `96a632b`, and `e71868a` exist.
- Verified key files exist: `tests/test_no_direct_imports.py`, `AURA-NOTES-MANAGER/services/vertex_ai_client.py`, `AURA-NOTES-MANAGER/services/genai_client.py`, `AURA-NOTES-MANAGER/services/embeddings.py`, and `AURA-NOTES-MANAGER/api/verify_phase_1.py`.
