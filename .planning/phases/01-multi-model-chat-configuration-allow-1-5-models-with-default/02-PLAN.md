---
phase: 01
plan: 02
wave: 1
depends_on: ["01"]
files_modified:
  - AURA-CHAT/server/routers/settings.py
  - AURA-CHAT/server/routers/chat.py
  - AURA-CHAT/tests/api/test_multi_model_settings.py
autonomous: true
requirements: null
---

# Plan 02: Backend — API Endpoints for Multi-Model CRUD & Chat Config

## Objective

Add `GET /api/v1/settings/defaults/chat/models` and `PUT /api/v1/settings/defaults/chat/models` endpoints to the settings router, and update `GET /chat/config` to return `allowed_models` and `default_model` from the multi-model configuration stored in SettingsStore.

## Context

Plan 01 extended SettingsStore with `get_chat_models_config()` and `set_chat_models()`. This plan exposes those methods via REST API and integrates the multi-model config into the existing `/chat/config` endpoint. The existing `PUT /settings/defaults/{use_case}` endpoint remains untouched for backward compatibility.

## Tasks

### Task 1: Add Pydantic models for multi-model chat configuration

**Type:** Implementation
**read_first:**
  - AURA-CHAT/server/routers/settings.py (full file — understand `DefaultModelUpdate`, router prefix, dependency injection)
  - shared/model_router/src/model_router/settings_store.py (understand `set_chat_models()` signature and validation)

**action:**
1. In `AURA-CHAT/server/routers/settings.py`, add two new Pydantic models after the existing `DefaultModelUpdate` and `ApiKeyCreate` classes:

   ```python
   class ChatModelEntry(BaseModel):
       """Single model entry in multi-model chat configuration."""
       provider: str
       model: str

   class ChatModelsUpdate(BaseModel):
       """Payload for updating multi-model chat configuration."""
       models: list[ChatModelEntry]
       default_index: int = 0
   ```

2. Import `Field` from `pydantic` (already imported or add to existing pydantic imports).
3. These models enforce that each entry has `provider` (str) and `model` (str), and the payload has `models` (list of 1-5 entries) and `default_index` (int, default 0).

**acceptance_criteria:**
- `settings.py` contains `class ChatModelEntry(BaseModel):` with `provider: str` and `model: str` fields
- `settings.py` contains `class ChatModelsUpdate(BaseModel):` with `models: list[ChatModelEntry]` and `default_index: int = 0` fields
- Both classes have docstrings per AGENTS.md conventions

### Task 2: Add GET and PUT endpoints for multi-model chat configuration

**Type:** Implementation
**read_first:**
  - AURA-CHAT/server/routers/settings.py (full file — understand existing endpoints, `get_settings_store` dependency, `ALLOWED_USE_CASES` set, error handling patterns)
  - shared/model_router/src/model_router/settings_store.py (understand `get_chat_models_config()` and `set_chat_models()`)

**action:**
1. Add `GET /defaults/chat/models` endpoint to the router in `settings.py`:

   ```python
   @router.get("/defaults/chat/models")
   async def get_chat_models(
       store: SettingsStore = Depends(get_settings_store),
   ) -> dict[str, Any]:
       """Get the multi-model configuration for the chat use case."""
       config = await store.get_chat_models_config()
       if config is None:
           default = _USE_CASE_DEFAULTS["chat"]
           return {
               "models": [{"provider": default["provider"], "model": default["model"]}],
               "default_index": 0,
               "provider": default["provider"],
               "model": default["model"],
           }
       return config
   ```

   Note: `_USE_CASE_DEFAULTS` is imported from `model_router.settings_store`.

2. Add `PUT /defaults/chat/models` endpoint:

   ```python
   @router.put("/defaults/chat/models")
   async def set_chat_models(
       payload: ChatModelsUpdate,
       store: SettingsStore = Depends(get_settings_store),
   ) -> dict[str, Any]:
       """Update the multi-model configuration for chat use case."""
       if len(payload.models) < 1 or len(payload.models) > 5:
           raise HTTPException(
               status_code=400,
               detail="Chat models must contain between 1 and 5 models",
           )
       if payload.default_index >= len(payload.models):
           raise HTTPException(
               status_code=400,
               detail="default_index exceeds models list length",
           )
       
       models_data = [
           {"provider": m.provider, "model": m.model}
           for m in payload.models
       ]
       
       await store.set_chat_models(models_data, payload.default_index)
       
       return {
           "use_case": "chat",
           "models": models_data,
           "default_index": payload.default_index,
       }
   ```

3. Import `Any` from `typing` at the top of the file (verify it's imported; add if missing).

**acceptance_criteria:**
- `settings.py` contains `@router.get("/defaults/chat/models")` endpoint handler function `get_chat_models`
- `settings.py` contains `@router.put("/defaults/chat/models")` endpoint handler function `set_chat_models`
- `get_chat_models` returns fallback default when SettingsStore has no chat config
- `set_chat_models` returns HTTP 400 with `"Chat models must contain between 1 and 5 models"` when models count is 0 or >5
- `set_chat_models` returns HTTP 400 with `"default_index exceeds models list length"` when default_index out of range
- `set_chat_models` calls `await store.set_chat_models(models_data, payload.default_index)`
- Both endpoints use `Depends(get_settings_store)` for dependency injection

### Task 3: Update `/chat/config` endpoint to populate `allowed_models` from multi-model config

**Type:** Implementation
**read_first:**
  - AURA-CHAT/server/routers/chat.py (lines 323-413 — the current `get_config()` endpoint)
  - shared/model_router/src/model_router/settings_store.py (understand `get_chat_models_config()` return format)

**action:**
1. In `AURA-CHAT/server/routers/chat.py`, modify the `get_config()` endpoint to fetch the multi-model chat configuration and use it to populate `allowed_models` and `default_model`.

2. Replace the current logic (lines ~393-402) that fetches a single default:
   ```python
   # Fetch default from SettingsStore to reflect Admin UI selection
   default_model = config.RAG_MODEL_DEFAULT
   try:
       _store = SettingsStore(get_redis())
       _default = await _store.get_default("chat")
       if _default and _default.get("model"):
           default_model = _default["model"]
           logger.info("Config using admin default model: %s", default_model)
   except Exception as e:
       logger.warning("Failed to fetch admin default model for config: %s", e)
   ```

   With multi-model-aware logic:
   ```python
   # Fetch multi-model chat config from SettingsStore
   default_model = config.RAG_MODEL_DEFAULT
   allowed_models = []
   try:
       _store = SettingsStore(get_redis())
       _chat_config = await _store.get_chat_models_config()
       if _chat_config and _chat_config.get("models"):
           models_list = _chat_config["models"]
           default_idx = _chat_config.get("default_index", 0)
           if 0 <= default_idx < len(models_list):
               default_model = models_list[default_idx]["model"]
           allowed_models = [m["model"] for m in models_list]
           logger.info(
               "Config using admin chat models: %s (default: %s)",
               allowed_models, default_model,
           )
       else:
           # Fallback: try single-model config
           _default = await _store.get_default("chat")
           if _default and _default.get("model"):
               default_model = _default["model"]
   except Exception as e:
       logger.warning("Failed to fetch chat models config: %s", e)
   ```

3. After the multi-model lookup, if `allowed_models` is still empty (no admin config at all), fall back to the current auto-discovery logic that populates `allowed_models` from ModelCache. Move the existing model-discovery block to be a fallback when `allowed_models` is empty. The final return structure remains the same:
   ```python
   return {
       "allowed_models": allowed_models,  # Now from admin config OR auto-discovery
       "default_model": default_model,
       "thinking": {
           "enabled": config.ENABLE_THINKING,
           "supported_models": supported_models,
           "model_capabilities": model_capabilities,
           "enabled_modes": config.THINKING_ENABLED_MODES,
       },
   }
   ```

4. The logic flow should be:
   - Try to get multi-model config from SettingsStore → populate `allowed_models` and `default_model`
   - If no admin config exists (`allowed_models` is empty), fall through to existing model discovery logic to get all available models
   - If admin config exists but SettingsStore fails → fall through to existing model discovery logic

**acceptance_criteria:**
- `chat.py`'s `get_config()` function calls `store.get_chat_models_config()` as primary source for `allowed_models`
- When admin config exists with models, `allowed_models` is populated from the stored `models` array (model names only)
- When admin config exists, `default_model` equals `models[default_index]["model"]`
- When admin config is missing/null, falls back to existing auto-discovery logic (all ModelCache models)
- When SettingsStore is unreachable, falls back to existing auto-discovery logic without crashing
- Response structure (`allowed_models`, `default_model`, `thinking`) remains unchanged

### Task 4: Write API tests for the new multi-model endpoints

**Type:** Testing
**read_first:**
  - AURA-CHAT/tests/ (understand test directory structure)
  - AURA-CHAT/server/routers/settings.py (verify endpoint signatures)
  - shared/model_router/tests/test_settings_store.py (understand `fake_redis` fixture pattern)

**action:**
1. Create file `AURA-CHAT/tests/api/test_multi_model_settings.py`.
2. Write the following tests using `httpx.AsyncClient` with the FastAPI test app pattern:

   **Test `test_get_chat_models_default_config`:**
   - GET `/api/v1/settings/defaults/chat/models` when no config is stored
   - Assert response 200 with `models` list of length 1, `default_index=0`, `provider="vertex_ai"`, `model="gemini-2.5-flash-lite"` (matches `_USE_CASE_DEFAULTS["chat"]`)

   **Test `test_put_chat_models_single`:**
   - PUT `/api/v1/settings/defaults/chat/models` with `{"models": [{"provider": "vertex_ai", "model": "gemini-2.5-flash"}], "default_index": 0}`
   - Assert response 200 with `models` list of length 1 and `default_index=0`

   **Test `test_put_chat_models_multiple`:**
   - PUT `/api/v1/settings/defaults/chat/models` with 3 models, `default_index=1`
   - Assert response 200 with `models` list of length 3, `default_index=1`

   **Test `test_put_chat_models_empty_list_400`:**
   - PUT with `{"models": [], "default_index": 0}`
   - Assert response 400 with detail containing `"between 1 and 5"`

   **Test `test_put_chat_models_over_five_400`:**
   - PUT with `{"models": [...6 items...], "default_index": 0}`
   - Assert response 400 with detail containing `"between 1 and 5"`

   **Test `test_put_chat_models_invalid_default_index_400`:**
   - PUT with `{"models": [...3 items...], "default_index": 5}`
   - Assert response 400 with detail containing `"default_index exceeds models list length"`

3. Add file header docstring per AGENTS.md Python file header conventions.

**acceptance_criteria:**
- File `AURA-CHAT/tests/api/test_multi_model_settings.py` exists
- All 6 tests are present
- Tests use async httpx client against FastAPI test app
- `python -m pytest AURA-CHAT/tests/api/test_multi_model_settings.py -x` exits 0
- File has mandatory Python file header docstring

## Verification

1. Run `python -m pytest AURA-CHAT/tests/api/test_multi_model_settings.py -x` — all tests pass
2. Start local server, hit `GET /api/v1/settings/defaults/chat/models` → returns default fallback
3. Hit `PUT /api/v1/settings/defaults/chat/models` with valid payload → 200
4. Hit `PUT /api/v1/settings/defaults/chat/models` with 6 models → 400
5. Verify existing `GET /settings/defaults` and `PUT /settings/defaults/{use_case}` still work (no regression)

## Must-Haves

- Two new API endpoints: `GET /defaults/chat/models` and `PUT /defaults/chat/models`
- `/chat/config` returns `allowed_models` from admin config when present
- API validates 1-5 model limit and default_index bounds
- Backward compatibility: existing single-model endpoints unaffected

## Success Criteria

- [ ] `GET /api/v1/settings/defaults/chat/models` returns fallback when no config stored
- [ ] `PUT /api/v1/settings/defaults/chat/models` stores multi-model config
- [ ] `/chat/config` populates `allowed_models` from admin-selected models
- [ ] `/chat/config` falls back to auto-discovery when no admin config
- [ ] API returns 400 for invalid model count or default_index
- [ ] All 6 API tests pass
- [ ] Existing settings endpoints still work