---
phase: 01
plan: 01
wave: 0
depends_on: []
files_modified:
  - shared/model_router/src/model_router/settings_store.py
  - shared/model_router/tests/test_settings_store.py
  - shared/model_router/tests/test_multi_model_config.py
autonomous: true
requirements: null
---

# Plan 01: Backend — SettingsStore Multi-Model Extension

## Objective

Extend `SettingsStore` with `get_chat_models_config()` and `set_chat_models()` methods that support the multi-model chat configuration format (`models[]` array + `default_index`) while maintaining backward compatibility with the existing single-model format.

## Context

The current `SettingsStore` stores chat defaults as `{"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"}`. This plan adds a new multi-model schema that includes a `models` array (1-5 items) and a `default_index` field. The existing `get_default("chat")` must continue returning `{provider, model}` for backward compatibility. The new methods handle the multi-model format specifically.

## Tasks

### Task 1: Add `get_chat_models_config()` method to SettingsStore

**Type:** Implementation
**read_first:**
  - shared/model_router/src/model_router/settings_store.py (full file — understand existing `get_default`, `set_default`, Redis interaction)

**action:**
1. Add `get_chat_models_config(self) -> dict[str, Any] | None` async method to the `SettingsStore` class in `settings_store.py` after the existing `get_default()` method.
2. Method reads the `"chat"` key from Redis hash `SETTINGS_KEY`.
3. If `raw_value is None`, return `None`.
4. Parse the JSON. If `"models"` key exists in parsed dict, return the full dict as-is (already in new format).
5. If `"models"` key does NOT exist (legacy format), convert to new format:
   ```python
   return {
       "provider": parsed.get("provider", "vertex_ai"),
       "model": parsed.get("model", "gemini-2.5-flash-lite"),
       "models": [{"provider": parsed.get("provider", "vertex_ai"), "model": parsed.get("model", "gemini-2.5-flash-lite")}],
       "default_index": 0,
   }
   ```
6. Add the `from __future__ import annotations` at top of file (already exists). Ensure `Any` is imported from `typing` (already present).

**acceptance_criteria:**
- `settings_store.py` contains `async def get_chat_models_config(self) -> dict[str, Any] | None:` method inside `SettingsStore` class
- Method returns `None` when chat key is missing from Redis
- Method returns new-format dict when `"models"` key is present in stored data
- Method converts legacy `{provider, model}` format to `{"provider": ..., "model": ..., "models": [...], "default_index": 0}` when `"models"` key absent
- Existing `get_default()` method is NOT modified (backward compatibility)

### Task 2: Add `set_chat_models()` method to SettingsStore

**Type:** Implementation
**read_first:**
  - shared/model_router/src/model_router/settings_store.py (full file)

**action:**
1. Add `set_chat_models(self, models: list[dict[str, str]], default_index: int = 0) -> None` async method after `get_chat_models_config()`.
2. Validate inputs:
   - `if not models: raise ValueError("At least one model must be configured")`
   - `if len(models) > 5: raise ValueError("Maximum 5 models allowed")`
   - `if not (0 <= default_index < len(models)): raise ValueError("default_index out of range")`
3. Each item in `models` must have `"provider"` and `"model"` string keys. Raise `ValueError("Each model must have 'provider' and 'model' keys")` if validation fails.
4. Build the payload preserving backward compatibility:
   ```python
   payload = {
       "models": models,
       "default_index": default_index,
       "provider": models[default_index]["provider"],
       "model": models[default_index]["model"],
   }
   ```
5. Store using `await self._redis.hset(SETTINGS_KEY, "chat", json.dumps(payload))`
6. Invalidate the `_defaults_cache` for `"chat"` key after write to prevent stale reads.

**acceptance_criteria:**
- `settings_store.py` contains `async def set_chat_models(self, models: list[dict[str, str]], default_index: int = 0) -> None:` method
- `ValueError` raised with message `"At least one model must be configured"` when models list is empty
- `ValueError` raised with message `"Maximum 5 models allowed"` when models list has >5 items
- `ValueError` raised with message `"default_index out of range"` when default_index is out of bounds
- `ValueError` raised with message `"Each model must have 'provider' and 'model' keys"` when model entry missing required keys
- Redis write includes backward-compatible `provider` and `model` fields aliased from `models[default_index]`
- `_defaults_cache["chat"]` is cleared after successful write (add `del _defaults_cache["chat"]` or `_defaults_cache.pop("chat", None)`)

### Task 3: Write unit tests for multi-model SettingsStore methods

**Type:** Testing
**read_first:**
  - shared/model_router/tests/test_settings_store.py (full file — understand test patterns, `fake_redis` fixture)
  - shared/model_router/tests/conftest.py (understand `fake_redis` fixture setup)
  - shared/model_router/src/model_router/settings_store.py (verify method signatures)

**action:**
1. Create new file `shared/model_router/tests/test_multi_model_config.py`.
2. Write the following pytest-asyncio tests using the existing `fake_redis` fixture pattern:

   **Test `test_set_chat_models_single_model`:**
   - Call `await store.set_chat_models([{"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"}], default_index=0)`
   - Verify `await store.get_chat_models_config()` returns dict with `models` array of length 1, `default_index=0`, plus backward-compat `provider`/`model` fields.

   **Test `test_set_chat_models_multiple_models`:**
   - Call `await store.set_chat_models([{"provider": "vertex_ai", "model": "gemini-2.5-flash"}, {"provider": "openrouter", "model": "openai/gpt-4o-mini"}, {"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"}], default_index=1)`
   - Verify returned config has 3 models, `default_index=1`, backward-compat `provider="openrouter"`, `model="openai/gpt-4o-mini"`.

   **Test `test_set_chat_models_empty_list_raises`:**
   - Assert `ValueError` raised with message containing `"At least one model must be configured"` when calling `set_chat_models([], 0)`.

   **Test `test_set_chat_models_over_five_raises`:**
   - Assert `ValueError` raised with message containing `"Maximum 5 models allowed"` when calling `set_chat_models` with 6 model entries.

   **Test `test_set_chat_models_invalid_default_index_raises`:**
   - Assert `ValueError` raised with message containing `"default_index out of range"` when default_index=5 for a 3-model list.

   **Test `test_set_chat_models_missing_keys_raises`:**
   - Assert `ValueError` raised when model entry lacks `"provider"` or `"model"` key.

   **Test `test_get_chat_models_config_legacy_format_migration`:**
   - Set a legacy single-model default using `await store.set_default("chat", "vertex_ai", "gemini-2.5-flash")`.
   - Call `await store.get_chat_models_config()` and verify it returns a dict with `models` array of length 1, `default_index=0`, and backward-compat fields matching the legacy values.

   **Test `test_get_chat_models_config_missing_returns_none`:**
   - Verify `await store.get_chat_models_config()` returns `None` for an empty Redis hash.

   **Test `test_set_chat_models_backward_compat_get_default`:**
   - Set multi-model config with `set_chat_models([{"provider": "openrouter", "model": "openai/gpt-4o-mini"}, {"provider": "vertex_ai", "model": "gemini-2.5-flash"}], default_index=0)`.
   - Verify `await store.get_default("chat")` returns `{"provider": "openrouter", "model": "openai/gpt-4o-mini"}` (backward-compatible single-model view).

3. Add file header docstring per AGENTS.md Python file header conventions.

**acceptance_criteria:**
- File `shared/model_router/tests/test_multi_model_config.py` exists
- All 9 tests are present and test the exact behaviors described
- `python -m pytest shared/model_router/tests/test_multi_model_config.py -x` exits 0
- Each test uses the `fake_redis` fixture from conftest
- File has mandatory Python file header docstring

## Verification

1. Run `python -m pytest shared/model_router/tests/test_multi_model_config.py -x` — all tests pass
2. Run `python -m pytest shared/model_router/tests/test_settings_store.py -x` — existing tests still pass (no regression)
3. Verify `get_default("chat")` still works after `set_chat_models()` — backward compatibility confirmed

## Must-Haves

- `SettingsStore.get_chat_models_config()` returns multi-model config with legacy migration
- `SettingsStore.set_chat_models()` validates 1-5 models and stores backward-compatible payload
- `_defaults_cache invalidated on write
- All new and existing unit tests pass

## Success Criteria

- [ ] `get_chat_models_config()` method exists in SettingsStore
- [ ] `set_chat_models()` validates 1-5 models, default_index bounds, required keys
- [ ] Legacy format auto-converts to multi-model format on read
- [ ] Backward-compatible `provider`/`model` fields written alongside `models[]`/`default_index`
- [ ] Cache invalidation on write
- [ ] All 9 new tests pass
- [ ] All existing SettingsStore tests still pass