---
phase: quick
plan: 260322-re3
subsystem: model-router
tags:
  - embeddings
  - model-routing
  - settings-ui
  - type-system
dependency_graph:
  requires:
    - shared/model_router (existing model router package)
    - AURA-NOTES-MANAGER settings feature (existing)
  provides:
    - ModelInfo.model_type field (Python + TypeScript)
    - Embedding model listing via model router
    - Per-use-case model filtering in settings UI
  affects:
    - GET /api/v1/settings/models response shape
    - Settings page dropdown filtering
tech_stack:
  added:
    - model_type: Literal["generation", "embedding"] field on ModelInfo
    - VertexAIEmbeddingProvider.list_models() method
  patterns:
    - Provider model listing for embedding models
    - Client-side model filtering by type
key_files:
  created: []
  modified:
    - shared/model_router/src/model_router/types.py
    - shared/model_router/src/model_router/providers/base.py
    - shared/model_router/src/model_router/providers/vertex_ai.py
    - shared/model_router/src/model_router/router.py
    - AURA-NOTES-MANAGER/frontend/src/types/settings.ts
    - AURA-NOTES-MANAGER/frontend/src/features/settings/hooks/useModelList.ts
    - AURA-NOTES-MANAGER/frontend/src/features/settings/components/DefaultModelSection.tsx
decisions: []
---

# Phase Quick Plan 260322-re3: Embeddings Model Dropdown Shows Generation Models Summary

## One-Liner

Add `model_type` field to ModelInfo and filter settings dropdowns so Chat/Entity Extraction show only generation models and Embeddings shows only embedding models.

## What Was Done

### Task 1: Backend — Add model_type to ModelInfo and surface embedding models

**Commit:** `b153ae8`

- Added `model_type: Literal["generation", "embedding"] = "generation"` field to `ModelInfo` in `types.py` — defaults to `"generation"` so existing generation models need no changes
- Added abstract `list_models()` method to `BaseEmbeddingProvider` in `base.py`
- Added `_EMBEDDING_MODELS` constant with 3 Vertex AI embedding models (`text-embedding-004`, `text-embedding-005`, `text-multilingual-embedding-002`), each with `model_type="embedding"`
- Added `list_models()` to `VertexAIEmbeddingProvider` returning `_EMBEDDING_MODELS`
- Updated `ModelRouter.list_models()` to also iterate `self._embedding_provider` when listing all models

**Verification:** All 67 existing tests pass (`pytest tests/ -x -q`).

### Task 2: Frontend — Add model_type filtering to settings dropdowns

**Commit:** `6dac031` (submodule) + `4187cd4` (parent ref)

- Added `model_type: 'generation' | 'embedding'` to frontend `ModelInfo` interface in `settings.ts`
- Added optional `modelType` parameter to `groupModelsByProvider()` and `useGroupedModels()` — filters models by type before grouping
- Added `USE_CASE_MODEL_TYPES` mapping: `chat` → `'generation'`, `embeddings` → `'embedding'`, `entity_extraction` → `'generation'`
- Updated `DefaultModelSection` to pass `USE_CASE_MODEL_TYPES[useCase.id]` to `useGroupedModels()` per use case

**Verification:** TypeScript type check passes clean (`npx tsc --noEmit`).

## Deviations from Plan

None — plan executed exactly as written.

## Success Criteria Met

- [x] `GET /api/v1/settings/models` returns embedding models with `model_type: "embedding"`
- [x] Chat Model dropdown: shows generation models only
- [x] Embeddings Model dropdown: shows embedding models only (text-embedding-004, text-embedding-005, etc.)
- [x] Entity Extraction dropdown: shows generation models only
- [x] All existing backend tests pass (67/67)
- [x] TypeScript compilation passes

## Self-Check: PASSED

All 7 modified files verified present. All 4 commits verified in git log (`b153ae8`, `4187cd4`, `6dac031`, `9417dd4`). Backend 67/67 tests pass. Frontend TypeScript compiles clean.
