---
phase: 10-cross-app-migration-backend-integration
plan: 03
subsystem: api
tags: [model-router, vertex-ai, embeddings, aura-chat]

# Dependency graph
requires:
  - phase: 08-shared-package-vertex-ai
    provides: VertexCompatModel, shared router package, Vertex embedding provider
  - phase: 09-openrouter-streaming
    provides: normalized router streaming contracts and thinking translation helpers
provides:
  - AURA-CHAT backend Vertex façade that routes legacy imports through model_router
  - AURA-CHAT embedding service delegation to router.embed() with preserved batching/retry
  - rag_engine thinking path without direct google.genai imports
affects: [10-04-notes-migration, 11-frontend-settings-model-ui, 13-polish-integration-testing]

# Tech tracking
tech-stack:
  added: []
  patterns: [legacy facade modules delegating to model_router, app-side embedding orchestration over router.embed]

key-files:
  created: []
  modified: [AURA-CHAT/backend/utils/vertex_ai_client.py, AURA-CHAT/backend/utils/embeddings.py, AURA-CHAT/backend/rag_engine.py]

key-decisions:
  - "Preserve AURA-CHAT's existing vertex_ai_client import surface by exposing model_router-backed compatibility shims instead of changing consumer imports."
  - "Keep batching, rate limiting, and retry orchestration inside AURA-CHAT's EmbeddingService while delegating single-batch embedding execution to router.embed()."

patterns-established:
  - "Legacy façade pattern: app hub modules preserve public names while delegating to shared router compatibility adapters."
  - "Embedding migration pattern: retain app-specific orchestration, replace only the provider call with router.embed()."

# Metrics
duration: 21 min
completed: 2026-03-10
---

# Phase 10 Plan 03: AURA-CHAT model_router façade migration Summary

**AURA-CHAT now routes legacy Vertex generation, streaming, and embeddings entrypoints through model_router while preserving existing backend consumer imports.**

## Performance

- **Duration:** 21 min
- **Started:** 2026-03-10T15:24:59Z
- **Completed:** 2026-03-10T15:46:43Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Replaced `backend/utils/vertex_ai_client.py` with a model-router-backed façade that keeps legacy names like `get_model`, `GenerationConfig`, and `generate_content_stream`.
- Reworked `backend/utils/embeddings.py` so batching, retry, and rate limiting stay in AURA-CHAT while the actual embedding call delegates to `router.embed()`.
- Removed `rag_engine.py`'s remaining direct `google.genai` thinking-path dependency and routed thinking generation through the façade.

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite vertex_ai_client.py as model-router façade** - `90ea72d` (feat)
2. **Task 2: Rewrite embeddings.py to use router.embed()** - `cdc47bb` (feat)

**Plan metadata:** pending root planning metadata commit

## Files Created/Modified
- `AURA-CHAT/backend/utils/vertex_ai_client.py` - Shared-router façade preserving legacy Vertex client exports and dict-based streaming chunks.
- `AURA-CHAT/backend/utils/embeddings.py` - Embedding service that delegates batch execution to `router.embed()` while keeping batching/retry behavior local.
- `AURA-CHAT/backend/rag_engine.py` - Thinking-mode path updated to use the façade instead of direct `google.genai` types.

## Decisions Made
- Preserved the existing AURA-CHAT import contract instead of editing all downstream consumers, because the hub-file façade keeps migration risk localized.
- Kept embedding orchestration in the app layer, because AURA-CHAT still owns batch sizing, RPM throttling, and retry policy even after router adoption.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Restored legacy shim/testing surfaces on the new vertex façade**
- **Found during:** Task 1 (Rewrite vertex_ai_client.py as model-router façade)
- **Issue:** Existing regression tests and compatibility callers still expected shim-era names like `_GenerativeModelWrapper`, `_build_stream_thinking_config`, `types`, `config`, and monkeypatchable `genai.Client` behavior.
- **Fix:** Added lightweight compatibility shims and monkeypatch surfaces while still keeping zero banned provider SDK imports in the façade.
- **Files modified:** `AURA-CHAT/backend/utils/vertex_ai_client.py`
- **Verification:** `../.venv/Scripts/python -m pytest tests/unit/test_vertex_ai_location_routing.py tests/backend/test_streaming.py -q`
- **Committed in:** `90ea72d`

**2. [Rule 2 - Missing Critical] Preserved EmbeddingService compatibility attributes and aliases**
- **Found during:** Task 2 (Rewrite embeddings.py to use router.embed())
- **Issue:** Existing tests and migration verification still relied on `EmbeddingService._test_mode` and an `embed_texts()` alias while the plan focused only on `get_embedding`/`get_embeddings_batch`.
- **Fix:** Kept the compatibility attribute/alias and left public embedding methods unchanged while delegating the real work to router.embed().
- **Files modified:** `AURA-CHAT/backend/utils/embeddings.py`
- **Verification:** `../.venv/Scripts/python -m pytest tests/backend/test_embeddings.py -q`
- **Committed in:** `cdc47bb`

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical)
**Impact on plan:** Both fixes were backward-compatibility safeguards required to complete the migration without breaking existing AURA-CHAT callers or regressions.

## Issues Encountered
- The initial façade rewrite broke existing compatibility tests because older shim helper names were still part of the effective contract; the façade was expanded to preserve those names without reintroducing direct SDK imports.
- The plan audit command used `grep`, but the environment lacked the expected shell utility path for the exact pipeline, so equivalent AST/pytest-based verification was used instead.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- AURA-CHAT now uses model_router for its legacy backend LLM and embedding hub modules.
- Phase 10 Plan 04 can apply the same façade pattern to AURA-NOTES-MANAGER and complete the cross-app no-direct-import audit.

## Self-Check: PASSED

- Verified summary file exists on disk.
- Verified task commits `90ea72d` and `cdc47bb` exist in the nested `AURA-CHAT` repository.
- Verified key modified files exist: `AURA-CHAT/backend/utils/vertex_ai_client.py`, `AURA-CHAT/backend/utils/embeddings.py`, `AURA-CHAT/backend/rag_engine.py`.

---
*Phase: 10-cross-app-migration-backend-integration*
*Completed: 2026-03-10*
