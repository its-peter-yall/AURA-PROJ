# 260322-tko Summary: Fix Admin Settings Model Defaults Read Path

**Date:** 2026-03-22
**Plan:** 260322-tko
**Type:** quick-fix

## Objective

Close the read-path gap so admin model selections saved via `/settings` page take effect immediately across both AURA apps. Previously, SettingsStore values were persisted to Redis but no backend service read them.

## What Changed

### Task 1: Shared `get_default_sync` helper
**File:** `shared/model_router/src/model_router/settings_store.py`

Added synchronous `get_default_sync(use_case, redis_url=None, redis_client=None)`:
- Reads from Redis hash `aura:model_router:settings` synchronously
- 5-minute TTL in-memory cache (`_defaults_cache`) to avoid per-call Redis hits
- Graceful fallback: returns `None` on any error (Redis down, parse error, missing key)
- `clear_defaults_cache()` for test isolation
- Exported from `model_router.__init__`

### Task 2: AURA-CHAT embeddings
**File:** `AURA-CHAT/backend/utils/embeddings.py`

- `EmbeddingService.__init__()` resolves `get_default_sync("embeddings")` with Redis URL from `config.REDIS_HOST/PORT/DB`
- Stores `self._embedding_default` (dict or None)
- `_embed_batch_sync()` passes `provider=_embedding_default["provider"]` to `router.embed()` when configured
- Updates `self.model_name` from admin default when set
- Falls back to hardcoded `text-embedding-004` when no admin default

### Task 3: AURA-CHAT entity extractor
**File:** `AURA-CHAT/backend/llm_entity_extractor.py`

- `LLMEntityExtractor.__init__()` calls `_resolve_default_model()` to check SettingsStore
- Uses admin default model as primary when configured
- `_initialize_model_with_fallback()` uses resolved model name
- Falls back to `config.LLM_ENTITY_EXTRACTION_MODEL` env var when no admin default
- Test mode unchanged

### Task 4: AURA-CHAT chat router
**File:** `AURA-CHAT/server/routers/chat.py`

- `chat()`, `stream_chat()`, `stream_chitchat_response()` all check SettingsStore when `request.model` is empty
- Creates `SettingsStore(get_redis())` and calls `await store.get_default("chat")`
- Falls back to `rag_engine.model_name` when no admin default
- Logs model source (request / admin default / env fallback)
- Graceful degradation: SettingsStore errors silently fall back to env defaults

### Task 5: AURA-NOTES-MANAGER embeddings
**File:** `AURA-NOTES-MANAGER/services/embeddings.py`

- Same pattern as Task 2 but using ANM's `api.config.REDIS_URL`
- `_embed_batch_sync()` passes `provider` to `router.embed()` when admin default configured
- Falls back to hardcoded default when no admin default

### Task 6: AURA-NOTES-MANAGER entity extractor
**File:** `AURA-NOTES-MANAGER/services/llm_entity_extractor.py`

- `LLM_ENTITY_EXTRACTION_MODEL` resolved dynamically from SettingsStore
- Falls back to `os.getenv("LLM_ENTITY_EXTRACTION_MODEL", "gemini-2.5-flash-lite")` when no admin default
- Graceful degradation when Redis unavailable

## Commits

| # | Repo | Hash | Message |
|---|------|------|---------|
| 1 | shared/ | ef96c66 | feat: add sync get_default_sync helper to SettingsStore |
| 2 | AURA-CHAT | 570c4a7 | feat: wire AURA-CHAT embeddings to SettingsStore defaults |
| 3 | AURA-CHAT | d37388b | feat: wire AURA-CHAT chat router to SettingsStore defaults |
| 4 | AURA-CHAT | 28b0a30 | feat: wire AURA-CHAT entity extractor to SettingsStore defaults |
| 5 | AURA-NOTES-MANAGER | 5a55116 | feat: wire ANM embeddings to SettingsStore defaults |
| 6 | AURA-NOTES-MANAGER | dcddfb4 | feat: wire ANM entity extractor to SettingsStore defaults |
| 7 | main | acfc656 | chore: update AURA-NOTES-MANAGER submodule ref for SettingsStore wiring |

## Test Results

| Suite | Result |
|-------|--------|
| `shared/model_router/tests/test_settings_store.py` | 7 passed |
| `AURA-CHAT/tests/backend/test_llm_entity_extractor.py` | 8 passed, 1 skipped |
| `AURA-NOTES-MANAGER/api/tests/` | 32 passed |
| Graceful fallback (no Redis) | All services return None, fall back to env vars |

## Success Criteria Met

- [x] `get_default_sync()` exists in shared model_router with caching and graceful fallback
- [x] AURA-CHAT embeddings passes `provider` from admin defaults to `router.embed()`
- [x] AURA-CHAT entity extraction uses admin default model as primary
- [x] AURA-CHAT chat router checks admin defaults when no `request.model` specified
- [x] AURA-NOTES-MANAGER embeddings passes `provider` from admin defaults to `router.embed()`
- [x] AURA-NOTES-MANAGER entity extraction uses admin default model
- [x] All services degrade gracefully (return None / fall back) when Redis is unavailable
- [x] Existing tests continue to pass
