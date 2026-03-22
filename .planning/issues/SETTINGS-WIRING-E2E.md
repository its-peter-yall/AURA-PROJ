# [BUG] SettingsStore not wired end-to-end across AURA-CHAT and AURA-NOTES-MANAGER

## Summary

The shared `model_router` SettingsStore (Redis-backed) and the settings UI in AURA-NOTES-MANAGER expose per-use-case model/provider configuration (chat, embeddings, entity_extraction, summarization). However, **most backend consumers do not read from SettingsStore**, ignore the `provider` field, or bypass it entirely with hardcoded env vars. Only **chat in AURA-CHAT** is fully wired end-to-end. This means changing providers or models in the settings page has little to no effect on most AI features.

## Context

Both AURA-CHAT and AURA-NOTES-MANAGER share a `model_router` library at `shared/model_router/` that provides:
- **SettingsStore** (`settings_store.py`): Redis hash at `aura:model_router:settings` storing `{provider, model}` per use case
- **KeyManager** (`key_manager.py`): Encrypted API key storage in Redis at `aura:model_router:api_keys`
- **ModelRouter** (`router.py`): Routes `generate()` / `embed()` calls to the correct provider (Vertex AI, OpenRouter, Ollama) based on model name or explicit provider
- **Settings API** (both `AURA-CHAT/server/routers/settings.py` and `AURA-NOTES-MANAGER/api/settings.py`): REST endpoints for CRUD on keys and defaults

The settings UI in `AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx` provides:
- API key management per provider (Vertex AI, OpenRouter, Ollama)
- Per-use-case default model selection (chat, embeddings, entity_extraction, summarization)
- Provider status cards with model counts

Both apps are intended to be configured from this single settings page.

## The Problem

### 1. `gatekeeper` use case is not in ALLOWED_USE_CASES

**Files:**
- `AURA-CHAT/server/routers/settings.py` — `ALLOWED_USE_CASES = {"chat", "embeddings", "entity_extraction", "summarization"}`
- `AURA-NOTES-MANAGER/api/settings.py` — same

**Problem:** `AURA-CHAT/backend/llm_gatekeeper.py:143` calls `get_default_sync("gatekeeper")`, but neither settings router includes `"gatekeeper"` in `ALLOWED_USE_CASES`. An admin PUT to `/api/v1/settings/defaults/gatekeeper` returns 400. There is no way to configure the gatekeeper model via the settings UI.

**Additionally:** `llm_gatekeeper.py:153-159` explicitly skips OpenRouter with a log message:
```
"Gatekeeper skipping OpenRouter default (requires response_mime_type)"
```
Even if `gatekeeper` were added to `ALLOWED_USE_CASES`, selecting OpenRouter would be silently ignored.

### 2. `relationship_extraction` is not a SettingsStore use case at all

**Files:**
- `AURA-CHAT/backend/utils/config.py:87-88` — `LLM_RELATIONSHIP_MODEL = "gemini-2.5-flash-lite"` (env var)

**Problem:** Relationship extraction reads only from the env var `LLM_RELATIONSHIP_MODEL`. It never calls `get_default_sync()`. There is no settings API endpoint or UI to configure it. It is always locked to the env var value.

### 3. `kg_processor.py` in AURA-NOTES-MANAGER bypasses SettingsStore

**Files:**
- `AURA-NOTES-MANAGER/api/kg_processor.py:465` — imports `LLM_ENTITY_EXTRACTION_MODEL` from `api/config.py`
- `AURA-NOTES-MANAGER/api/config.py:62` — `LLM_ENTITY_EXTRACTION_MODEL = os.getenv("LLM_ENTITY_EXTRACTION_MODEL", "gemini-2.5-flash-lite")`

**Problem:** The KG processor (the main document processing pipeline in NOTES) reads its entity extraction model directly from `api/config.py`, which only checks the env var. It never calls `get_default_sync("entity_extraction")`. When an admin changes the entity extraction model in the settings page, the KG processor ignores it completely.

Note: `AURA-NOTES-MANAGER/services/llm_entity_extractor.py:204` *does* read from SettingsStore, but `kg_processor.py` uses its own `GeminiClient` class and never reaches that code path.

### 4. Entity extraction ignores the `provider` field

**Files:**
- `AURA-CHAT/backend/llm_entity_extractor.py:307-320` — reads `get_default_sync("entity_extraction")`, uses `model` but ignores `provider`
- `AURA-NOTES-MANAGER/services/llm_entity_extractor.py:204` — same pattern

**Problem:** Even when SettingsStore returns `{provider: "openrouter", model: "anthropic/claude-3-opus"}`, the entity extractor uses only the `model` value. It relies on ModelRouter's name-based provider detection (the `/` heuristic in `_determine_provider_type()`) rather than explicitly passing the provider. This works by accident for OpenRouter (because model names contain `/`) but would fail for providers with non-standard naming conventions.

### 5. Embeddings partially ignores the provider field

**Files:**
- `AURA-CHAT/backend/utils/embeddings.py:57-61` — reads `get_default_sync("embeddings")`, overrides `model_name` but the provider field is passed to `router.embed()` inconsistently
- `AURA-NOTES-MANAGER/services/embeddings.py:84` — same pattern

**Problem:** The `provider` field from SettingsStore is used to select the provider in some code paths but the `model` field is used for logging only in others. The integration is fragile and not consistently provider-aware.

### 6. Chat config fallback is hardcoded to Vertex AI models

**Files:**
- `AURA-CHAT/server/routers/chat.py:313-337` — `GET /chat/config` endpoint
- `AURA-CHAT/backend/utils/config.py:59-63` — `RAG_ALLOWED_MODELS = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-3-flash-preview"]`

**Problem:** When the model router is unavailable (e.g., Redis down), the chat config falls back to `RAG_ALLOWED_MODELS`, which is a hardcoded list of Vertex AI models. OpenRouter models would disappear from the UI. The fallback should ideally include all registered providers' models or at minimum document this behavior.

### 7. Thinking mode model list is hardcoded to Vertex AI

**Files:**
- `AURA-CHAT/backend/utils/config.py:199-206` — `CHAT_MODELS_WITH_THINKING` hardcoded list

**Problem:** Only Vertex AI models are listed as thinking-capable. If an admin configures an OpenRouter model that supports thinking (e.g., `google/gemini-2.0-flash-thinking`), the thinking toggle won't appear in the UI because the model name won't match the hardcoded list.

## Impact

- **Settings page is misleading**: Admins can change providers/models in the UI but most features silently ignore those settings
- **OpenRouter support is incomplete**: Only chat works end-to-end. Entity extraction, embeddings, gatekeeper, and KG processing either ignore OpenRouter or explicitly skip it
- **No single source of truth**: Some features read from SettingsStore, some from env vars, some from hardcoded constants — with no way to know which without reading source code
- **Operator confusion**: "I changed the default model in settings but my documents are still processed with Gemini" — this would be a common support issue

## Proposed Fix

### Phase 1: Allow configuring all use cases via settings API

1. Add `"gatekeeper"` and `"relationship_extraction"` to `ALLOWED_USE_CASES` in both settings routers
2. Update the frontend settings page to show these additional use cases

### Phase 2: Wire AURA-NOTES-MANAGER kg_processor to SettingsStore

1. In `AURA-NOTES-MANAGER/api/kg_processor.py`, replace the `LLM_ENTITY_EXTRACTION_MODEL` import with a `get_default_sync("entity_extraction")` call
2. Pass both `provider` and `model` to the ModelRouter when making LLM calls

### Phase 3: Wire entity extraction provider passthrough

1. In both `AURA-CHAT/backend/llm_entity_extractor.py` and `AURA-NOTES-MANAGER/services/llm_entity_extractor.py`, use the `provider` field from SettingsStore to explicitly set the provider on ModelRouter calls
2. Remove the name-based provider detection fallback

### Phase 4: Wire embeddings provider passthrough

1. In both `AURA-CHAT/backend/utils/embeddings.py` and `AURA-NOTES-MANAGER/services/embeddings.py`, pass the `provider` field from SettingsStore to `router.embed()` consistently

### Phase 5: Wire gatekeeper properly

1. Remove the OpenRouter skip in `AURA-CHAT/backend/llm_gatekeeper.py:153-159`
2. Investigate why `response_mime_type` was considered required — add provider-specific handling if needed rather than blanket skip
3. Add `"gatekeeper"` to `ALLOWED_USE_CASES` (from Phase 1)

### Phase 6: Wire relationship_extraction to SettingsStore

1. In `AURA-CHAT/backend/`, add a `get_default_sync("relationship_extraction")` call where relationship extraction models are resolved
2. Fall back to `config.LLM_RELATIONSHIP_MODEL` env var if SettingsStore returns None

### Phase 7: Fix chat config fallback

1. When model router is unavailable, return a graceful error or cached model list instead of hardcoded Vertex AI models
2. Update `CHAT_MODELS_WITH_THINKING` to be dynamically generated from the model router's capabilities metadata, or at minimum include common OpenRouter thinking models

## Acceptance Criteria

- [ ] All use cases (`chat`, `embeddings`, `entity_extraction`, `summarization`, `gatekeeper`, `relationship_extraction`) can be configured via the settings page
- [ ] Changing a use-case default in settings takes effect immediately in both AURA-CHAT and AURA-NOTES-MANAGER backends
- [ ] Selecting OpenRouter as provider for any use case routes LLM calls through the OpenRouter API
- [ ] `kg_processor.py` in AURA-NOTES-MANAGER respects the entity_extraction setting
- [ ] No feature silently falls back to hardcoded env vars when SettingsStore has a configured value
- [ ] Gatekeeper works with OpenRouter (no silent skip)
- [ ] Chat config fallback handles model router unavailability gracefully

## Related Files

### Shared
- `shared/model_router/src/model_router/settings_store.py` — SettingsStore implementation
- `shared/model_router/src/model_router/key_manager.py` — KeyManager implementation
- `shared/model_router/src/model_router/router.py` — ModelRouter (provider routing)

### AURA-CHAT Backend
- `AURA-CHAT/backend/llm_entity_extractor.py` — entity extraction (line 307)
- `AURA-CHAT/backend/llm_gatekeeper.py` — gatekeeper (lines 138-166)
- `AURA-CHAT/backend/utils/embeddings.py` — embeddings (line 57)
- `AURA-CHAT/backend/utils/config.py` — hardcoded defaults (lines 59-88, 130, 199-206)
- `AURA-CHAT/backend/rag_engine.py` — RAG engine model resolution (line 184)

### AURA-CHAT Server
- `AURA-CHAT/server/routers/settings.py` — ALLOWED_USE_CASES (settings API)
- `AURA-CHAT/server/routers/chat.py` — chat config endpoint (lines 313-337)

### AURA-NOTES-MANAGER API
- `AURA-NOTES-MANAGER/api/kg_processor.py` — KG processing (line 465)
- `AURA-NOTES-MANAGER/api/config.py` — hardcoded config (lines 62, 66, 70)
- `AURA-NOTES-MANAGER/api/settings.py` — ALLOWED_USE_CASES (settings API)

### AURA-NOTES-MANAGER Services
- `AURA-NOTES-MANAGER/services/llm_entity_extractor.py` — entity extraction (line 204)
- `AURA-NOTES-MANAGER/services/embeddings.py` — embeddings (line 84)
- `AURA-NOTES-MANAGER/services/summarizer.py` — summarization (line 66)

### AURA-NOTES-MANAGER Frontend
- `AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx` — settings UI
- `AURA-NOTES-MANAGER/frontend/src/features/settings/` — settings components and hooks
