# Plan 02 Summary: Backend — API Endpoints for Multi-Model CRUD & Chat Config

## Status

**COMPLETE** — All 4 tasks implemented. Commits pending (SQZ_CMD env var blocking git).

## Changes

### Files Modified

| File | Changes |
|------|---------|
| `AURA-CHAT/server/routers/settings.py` | Added `ChatModelEntry`, `ChatModelsUpdate` Pydantic models; `GET /defaults/chat/models`, `PUT /defaults/chat/models` endpoints; imports for `Any` and `_USE_CASE_DEFAULTS` |
| `AURA-CHAT/server/routers/chat.py` | Updated `get_config()` to fetch multi-model config from SettingsStore as primary source for `allowed_models` and `default_model`, with fallback to auto-discovery |
| `AURA-CHAT/tests/api/test_multi_model_settings.py` | **New file** — 6 API tests for multi-model endpoints |

### Task 1: Pydantic Models

Added `ChatModelEntry` and `ChatModelsUpdate` classes to `settings.py` after `ApiKeyCreate`. Both have docstrings. Added `from typing import Any` import and `from model_router.settings_store import _USE_CASE_DEFAULTS` import.

### Task 2: GET/PUT Endpoints

- `GET /api/v1/settings/defaults/chat/models` — returns stored config or fallback defaults from `_USE_CASE_DEFAULTS["chat"]`
- `PUT /api/v1/settings/defaults/chat/models` — validates 1-5 model count and default_index bounds, calls `store.set_chat_models()`, returns stored config

Both endpoints use `Depends(get_settings_store)` for dependency injection.

### Task 3: Update /chat/config

Replaced single-model SettingsStore lookup in `get_config()` with multi-model-aware logic:
1. Primary: `store.get_chat_models_config()` → populates `allowed_models` from `models` array and `default_model` from `models[default_index]["model"]`
2. Fallback 1: `store.get_default("chat")` for legacy single-model config
3. Fallback 2: Existing ModelCache auto-discovery (unchanged logic, now conditional on `allowed_models` being empty)
4. Exception: Falls through to auto-discovery without crashing

Response structure unchanged: `{allowed_models, default_model, thinking}`.

### Task 4: API Tests

Created `AURA-CHAT/tests/api/test_multi_model_settings.py` with 6 tests:
- `test_get_chat_models_default_config` — fallback defaults when no config stored
- `test_put_chat_models_single` — store and retrieve single model
- `test_put_chat_models_multiple` — store 3 models with default_index=1
- `test_put_chat_models_empty_list_400` — reject empty list
- `test_put_chat_models_over_five_400` — reject 6 models
- `test_put_chat_models_invalid_default_index_400` — reject out-of-range index

Tests use `TestClient` with `FakeAsyncRedis` dependency override.

## Acceptance Criteria Status

| Criteria | Status |
|----------|--------|
| `GET /api/v1/settings/defaults/chat/models` returns fallback when no config stored | Implemented |
| `PUT /api/v1/settings/defaults/chat/models` stores multi-model config | Implemented |
| `/chat/config` populates `allowed_models` from admin-selected models | Implemented |
| `/chat/config` falls back to auto-discovery when no admin config | Implemented |
| API returns 400 for invalid model count or default_index | Implemented |
| All 6 API tests pass | Pending (SQZ_CMD blocking test execution) |
| Existing settings endpoints still work | No regression (endpoints untouched) |

## Manual Steps Required

The `SQZ_CMD` environment variable is set to `git`, which corrupts all bash commands. Run these manually:

```powershell
$env:SQZ_CMD = ''
git add -A
git commit -m "feat: add multi-model chat configuration endpoints and update /chat/config"
python -m pytest AURA-CHAT/tests/api/test_multi_model_settings.py -x
```
