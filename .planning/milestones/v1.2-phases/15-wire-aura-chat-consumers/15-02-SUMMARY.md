# Phase 15-02 SUMMARY: Wire Entity Extractor to resolve_use_case_config()

**Plan:** 15-02
**Phase:** 15-wire-aura-chat-consumers
**Completed:** 2026-03-23
**Commit:** e4310db

---

## Objective

Wire entity extractor and relationship extraction to read provider+model from `resolve_use_case_config()` and pass explicit provider through `get_model()` to ModelRouter.

---

## Changes Made

### AURA-CHAT/backend/llm_entity_extractor.py

1. **Import Change**
   - Replaced `from model_router.settings_store import get_default_sync` with `from model_router.settings_store import resolve_use_case_config`

2. **Task 1: Entity Extraction Provider Wiring**
   - `__init__` now calls `resolve_use_case_config("entity_extraction", redis_url=self._redis_url)` and stores result in `self._entity_cfg`
   - `_entity_cfg` contains `{provider: str, model: str}` dict
   - `_initialize_model_with_fallback` passes `provider=self._entity_cfg["provider"]` to `get_model()`
   - Log messages now include provider for observability
   - Removed deprecated `_resolve_default_model()` method

3. **Task 2: Relationship Extraction Independent Resolution**
   - Added new method `_resolve_relationship_model()` that:
     - Calls `resolve_use_case_config("relationship_extraction", redis_url=self._redis_url)`
     - Returns tuple of `(VertexCompatModel, provider_string)`
     - Falls back to entity extraction model on failure
   - `_extract_relationships_via_llm()` now:
     - Calls `_resolve_relationship_model()` at start
     - Uses `rel_model.generate_content()` instead of `self.model.generate_content()`
     - Logs provider in debug messages

---

## Verification

Both tasks verified with test mode:
```
entity_cfg: {'provider': 'vertex_ai', 'model': 'gemini-2.5-flash-lite'}
rel_provider: vertex_ai model: gemini-2.5-flash-lite
```

Redis unavailable falls back gracefully via `resolve_use_case_config()` error handling.

---

## Truths Confirmed

- [x] Entity extractor resolves provider from SettingsStore via `resolve_use_case_config()` and passes it to `get_model()`
- [x] Relationship extraction resolves its own provider/model independently from `resolve_use_case_config('relationship_extraction')`
- [x] Both entity and relationship extraction use explicit provider routing
- [x] SettingsStore unreachable falls back to env var then hardcoded default without crashing

---

## Files Modified

| File | Changes |
|------|---------|
| `AURA-CHAT/backend/llm_entity_extractor.py` | 59 insertions, 32 deletions |

---

## Dependencies

- `shared/model_router/src/model_router/settings_store.py`: `resolve_use_case_config()` (from Phase 14)
- `AURA-CHAT/backend/utils/vertex_ai_client.py`: `get_model()` with provider parameter (from Phase 15-01)
