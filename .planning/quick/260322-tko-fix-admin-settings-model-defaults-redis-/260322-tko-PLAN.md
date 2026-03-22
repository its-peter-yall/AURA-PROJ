---
phase: quick-fix
plan: 260322-tko
type: execute
wave: 1
depends_on: []
files_modified:
  - shared/model_router/src/model_router/settings_store.py
  - AURA-CHAT/backend/utils/embeddings.py
  - AURA-CHAT/backend/llm_entity_extractor.py
  - AURA-CHAT/server/routers/chat.py
  - AURA-NOTES-MANAGER/services/embeddings.py
  - AURA-NOTES-MANAGER/services/llm_entity_extractor.py
autonomous: true
requirements: []
user_setup: []

must_haves:
  truths:
    - "Admin can save default model selections via /settings page"
    - "Saved defaults are read by backend AI services at call time"
    - "Embedding calls use the admin-configured default embedding model"
    - "Entity extraction uses the admin-configured default entity model"
    - "Chat model falls back to admin default when no model specified in request"
    - "All services fall back to env vars when no admin default is configured"
    - "Services degrade gracefully when Redis is unavailable"
  artifacts:
    - path: "shared/model_router/src/model_router/settings_store.py"
      provides: "Sync helper for reading SettingsStore defaults"
      contains: "get_default_sync"
    - path: "AURA-CHAT/backend/utils/embeddings.py"
      provides: "Embedding service reads admin default provider/model"
      contains: "_embed_batch_sync.*provider"
    - path: "AURA-CHAT/backend/llm_entity_extractor.py"
      provides: "Entity extractor reads admin default model"
      contains: "SettingsStore"
    - path: "AURA-CHAT/server/routers/chat.py"
      provides: "Chat router reads admin default when no model specified"
      contains: "SettingsStore"
    - path: "AURA-NOTES-MANAGER/services/embeddings.py"
      provides: "ANM embedding service reads admin default"
      contains: "_embed_batch_sync.*provider"
    - path: "AURA-NOTES-MANAGER/services/llm_entity_extractor.py"
      provides: "ANM entity extractor reads admin default"
      contains: "SettingsStore"
  key_links:
    - from: "shared/model_router/settings_store.py"
      to: "AURA-CHAT/backend/utils/embeddings.py"
      via: "sync helper import and defaults lookup"
      pattern: "get_default_sync"
    - from: "SettingsStore.get_default"
      to: "router.embed(provider=...)"
      via: "provider parameter pass-through"
      pattern: "router\\.embed.*provider"
    - from: "SettingsStore.get_default"
      to: "get_model(model_name)"
      via: "model name from admin defaults"
      pattern: "get_default_sync.*model"
---

## Objective

Connect the admin settings write path (SettingsStore in Redis) to the backend AI call sites. Currently, when an admin saves model defaults via the `/settings` page, the values are persisted to Redis but no backend service reads them. Each AI call site (embeddings, entity extraction, chat) falls back to hardcoded defaults or env vars, ignoring admin configuration entirely.

**Purpose:** Close the read-path gap so admin model selections take effect immediately across both AURA apps.
**Output:** All 6 AI call sites read from SettingsStore, with graceful fallback to existing defaults.

## Context

@shared/model_router/src/model_router/settings_store.py
@AURA-CHAT/backend/utils/embeddings.py
@AURA-CHAT/backend/llm_entity_extractor.py
@AURA-CHAT/server/routers/chat.py
@AURA-NOTES-MANAGER/services/embeddings.py
@AURA-NOTES-MANAGER/services/llm_entity_extractor.py

### Architecture Notes

- `SettingsStore` (shared) uses async Redis. Both embedding services are sync.
- Both apps share the same Redis instance (`REDIS_URL` / `REDIS_HOST:PORT`).
- SettingsStore keys: `"chat"`, `"embeddings"`, `"entity_extraction"` → `{"provider": "...", "model": "..."}`
- `model_router.embed()` accepts `provider` param for routing; both embed services currently call `router.embed(texts)` without it.
- Entity extractors use `get_model(model_name)` from vertex_ai_client (AURA-CHAT) or `generate_content` (ANM).

## Tasks

<task type="auto">
  <name>Task 1: Add sync SettingsStore helper to shared model_router</name>
  <files>shared/model_router/src/model_router/settings_store.py</files>
  <action>
    Add a synchronous function `get_default_sync(use_case, redis_url=None, redis_client=None)` to `settings_store.py` that:
    1. Accepts optional `redis_url` (defaults to `REDIS_URL` env var) or pre-created `redis_client`
    2. Creates a sync Redis client if needed (using `redis.Redis.from_url()`)
    3. Reads `SETTINGS_KEY` hash field for the given use_case synchronously
    4. Returns `{"provider": str, "model": str}` dict or `None` if not configured
    5. Catches all exceptions (Redis down, parse errors) and returns `None` gracefully
    6. Uses a module-level `_defaults_cache: dict[str, dict]` with TTL (5 min) to avoid per-call Redis hits
    7. Includes a `clear_defaults_cache()` function for testing

    Also update `__init__.py` to export `get_default_sync`.

    Pattern: Read hash → json.loads → cache with timestamp → return. On any error, return None.
    Do NOT change the existing async methods. This is additive only.
  </action>
  <verify>
    <automated>cd "D:\Peter\AURA Twin Proj\AURA-PROJ" && .venv\Scripts\python -c "from model_router.settings_store import get_default_sync, clear_defaults_cache; print('import ok')"</automated>
  </verify>
  <done>get_default_sync is importable, handles missing Redis gracefully (returns None), caches results for 5 minutes</done>
</task>

<task type="auto">
  <name>Task 2: Wire AURA-CHAT embedding service to SettingsStore defaults</name>
  <files>AURA-CHAT/backend/utils/embeddings.py</files>
  <action>
    Modify `_embed_batch_sync()` in the AURA-CHAT EmbeddingService to:
    1. Import `get_default_sync` from `model_router.settings_store`
    2. Add a `_settings_defaults` attribute (resolved once at init or lazily at first call)
    3. At init time, call `get_default_sync("embeddings")` with Redis config from `config.REDIS_HOST`/`config.REDIS_PORT`/`config.REDIS_DB`
    4. Store result as `self._embedding_default` (dict or None)
    5. In `_embed_batch_sync()`, if `_embedding_default` is not None:
       - Pass `provider=_embedding_default["provider"]` to `router.embed()`
       - Update `self.model_name` to `_embedding_default["model"]` if it differs from hardcoded default
    6. If `_embedding_default` is None, keep existing behavior (no provider param, hardcoded model)
    7. Log which source is used (admin default vs hardcoded)

    The provider param routes embeddings to the correct provider in the model_router.
  </action>
  <verify>
    <automated>cd "D:\Peter\AURA Twin Proj\AURA-PROJ" && .venv\Scripts\python -c "from AURA_CHAT.backend.utils.embeddings import EmbeddingService; svc = EmbeddingService(); print('init ok')"</automated>
  </verify>
  <done>EmbeddingService reads SettingsStore defaults at init, passes provider to router.embed(), falls back to hardcoded when no default configured</done>
</task>

<task type="auto">
  <name>Task 3: Wire AURA-CHAT entity extractor to SettingsStore defaults</name>
  <files>AURA-CHAT/backend/llm_entity_extractor.py</files>
  <action>
    Modify `LLMEntityExtractor.__init__()` to:
    1. Import `get_default_sync` from `model_router.settings_store`
    2. Call `get_default_sync("entity_extraction")` with Redis config from `config.REDIS_HOST`/`config.REDIS_PORT`/`config.REDIS_DB`
    3. If a default is returned, use `_default["model"]` as the primary model instead of `config.LLM_ENTITY_EXTRACTION_MODEL`
    4. Store the resolved model name and log which source was used
    5. If no default is configured, keep existing behavior (config env var)
    6. In `_initialize_model_with_fallback()`, use the resolved model name as primary

    Do NOT change the test mode logic or the fallback chain.
  </action>
  <verify>
    <automated>cd "D:\Peter\AURA Twin Proj\AURA-PROJ" && .venv\Scripts\python -c "import os; os.environ['AURA_TEST_MODE']='true'; from AURA_CHAT.backend.llm_entity_extractor import LLMEntityExtractor; e = LLMEntityExtractor(); print('init ok')"</automated>
  </verify>
  <done>LLMEntityExtractor reads SettingsStore defaults for entity_extraction use case, uses admin model as primary, falls back to env var</done>
</task>

<task type="auto">
  <name>Task 4: Wire AURA-CHAT chat router to SettingsStore defaults</name>
  <files>AURA-CHAT/server/routers/chat.py</files>
  <action>
    Modify the chat endpoint (`chat()`) and streaming endpoint (`stream_chat()`) to:
    1. Import `SettingsStore` and the existing `get_redis` from `server.routers.settings`
    2. At request time, if `request.model` is None/empty:
       - Create `SettingsStore(get_redis())` and call `await store.get_default("chat")`
       - If a default is found, use `default["model"]` as the model (pass to `rag_engine.set_model()`)
       - If no default, keep existing fallback to `rag_engine.model_name` (from RAG_MODEL_DEFAULT)
    3. Same logic in `stream_chitchat_response()` for the chitchat path
    4. Log whether model came from request, admin default, or env fallback

    The `get_redis()` function already exists in `server/routers/settings.py` and provides an async Redis client.
  </action>
  <verify>
    <automated>cd "D:\Peter\AURA Twin Proj\AURA-PROJ" && .venv\Scripts\python -c "from AURA_CHAT.server.routers.chat import router; print('import ok')"</automated>
  </verify>
  <done>Chat router checks SettingsStore for "chat" default when no model in request, falls back to rag_engine.model_name</done>
</task>

<task type="auto">
  <name>Task 5: Wire AURA-NOTES-MANAGER embedding service to SettingsStore defaults</name>
  <files>AURA-NOTES-MANAGER/services/embeddings.py</files>
  <action>
    Modify `_embed_batch_sync()` in the ANM EmbeddingService to:
    1. Import `get_default_sync` from `model_router.settings_store`
    2. At init time, call `get_default_sync("embeddings")` with Redis URL from `api.config.REDIS_URL`
    3. Store result as `self._embedding_default` (dict or None)
    4. In `_embed_batch_sync()`, if `_embedding_default` is not None:
       - Pass `provider=_embedding_default["provider"]` to `router.embed()`
       - Update `self.model_name` to `_embedding_default["model"]`
    5. If no default, keep existing behavior
    6. Log which source is used

    Same pattern as Task 2 but using ANM's Redis config (`api.config.REDIS_URL`).
  </action>
  <verify>
    <automated>cd "D:\Peter\AURA Twin Proj\AURA-PROJ" && .venv\Scripts\python -c "from AURA_NOTES_MANAGER.services.embeddings import EmbeddingService; svc = EmbeddingService(); print('init ok')"</automated>
  </verify>
  <done>ANM EmbeddingService reads SettingsStore defaults at init, passes provider to router.embed(), falls back to config default</done>
</task>

<task type="auto">
  <name>Task 6: Wire AURA-NOTES-MANAGER entity extractor to SettingsStore defaults</name>
  <files>AURA-NOTES-MANAGER/services/llm_entity_extractor.py</files>
  <action>
    Modify the entity extraction model initialization in `services/llm_entity_extractor.py` to:
    1. Import `get_default_sync` from `model_router.settings_store`
    2. Replace the direct `os.getenv("LLM_ENTITY_EXTRACTION_MODEL", "gemini-2.5-flash-lite")` with a function call:
       - Call `get_default_sync("entity_extraction")` with Redis URL from `os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")`
       - If default found, use `default["model"]`
       - If not found, fall back to `os.getenv("LLM_ENTITY_EXTRACTION_MODEL", "gemini-2.5-flash-lite")`
    3. Log which source is used

    Keep the constant name `LLM_ENTITY_EXTRACTION_MODEL` but resolve its value from SettingsStore first.
  </action>
  <verify>
    <automated>cd "D:\Peter\AURA Twin Proj\AURA-PROJ" && .venv\Scripts\python -c "import os; os.environ['AURA_TEST_MODE']='true'; from AURA_NOTES_MANAGER.services.llm_entity_extractor import LLM_ENTITY_EXTRACTION_MODEL; print(f'model: {LLM_ENTITY_EXTRACTION_MODEL}')"</automated>
  </verify>
  <done>ANM entity extractor reads SettingsStore defaults for entity_extraction use case, falls back to env var</done>
</task>

## Verification

After all tasks complete:
1. Run `python -m pytest shared/model_router/tests/test_settings_store.py` — settings store tests pass
2. Run `python -m pytest AURA-CHAT/tests/` — AURA-CHAT tests pass
3. Verify graceful degradation: with Redis unavailable, all services fall back to env var defaults without errors

## Success Criteria

- [ ] `get_default_sync()` exists in shared model_router with caching and graceful fallback
- [ ] AURA-CHAT embeddings passes `provider` from admin defaults to `router.embed()`
- [ ] AURA-CHAT entity extraction uses admin default model as primary
- [ ] AURA-CHAT chat router checks admin defaults when no `request.model` specified
- [ ] AURA-NOTES-MANAGER embeddings passes `provider` from admin defaults to `router.embed()`
- [ ] AURA-NOTES-MANAGER entity extraction uses admin default model
- [ ] All services degrade gracefully (return None / fall back) when Redis is unavailable
- [ ] Existing tests continue to pass

## Output

After completion, create `.planning/quick/260322-tko-fix-admin-settings-model-defaults-redis-/260322-tko-SUMMARY.md`
