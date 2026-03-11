# Phase 10: Cross-App Migration + Backend Integration - Research

**Researched:** 2026-03-10
**Domain:** LLM provider migration, backend configuration management, API key security, model discovery
**Confidence:** HIGH

## Summary

Phase 10 is the payoff phase of the Strangler Fig migration pattern begun in Phases 8-9. The shared `model_router` package now has Vertex AI (generation + embeddings), OpenRouter (generation + streaming), a compatibility shim (`VertexCompatModel`), and a feature-flag toggle (`USE_MODEL_ROUTER`) in both apps. This phase completes the migration by: (1) rewriting all direct SDK imports to use `model_router`, (2) adding backend REST endpoints for admin-configurable defaults, model discovery with TTL caching, and encrypted API key management, and (3) verifying Celery/ARQ workers can import and use the shared package.

The codebase audit identified **14 files** across both apps that directly import `vertexai`, `google.generativeai`, `google.genai`, or `openai` SDKs. The migration is not a simple find-and-replace — several call sites use SDK-specific patterns (streaming, thinking config, safety settings, embedding models) that need careful mapping to the router's normalized API. The existing `USE_MODEL_ROUTER` shim only covers `get_model()` in the `vertex_ai_client.py` files; `generate_content_stream()`, `get_genai_client()`, embeddings, and the NOTES `genai_client.py` module are all unshimmed.

**Primary recommendation:** Migrate in three ordered waves: (1) backend config/settings endpoints + key management, (2) generation call migration in both apps, (3) embedding migration + Celery verification. Each wave can be tested independently. Remove the `USE_MODEL_ROUTER` env var and the old `vertex_ai_client.py` files at the end.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| UI-03 | Both AURA-CHAT and AURA-NOTES-MANAGER use the shared model router for all LLM calls with no direct provider imports | Migration audit in §Migration Map identifies all 14 files with direct imports and the router API surface to replace them |
| CONFIG-01 | Admin can set default provider and model for each use case (chat, embeddings, entity extraction) via a settings page | §Configuration Management covers Redis-backed settings store with REST endpoints |
| CONFIG-03 | System dynamically discovers available models from each configured provider with cached model lists | §Model Discovery/Caching covers TTL-based Redis caching on top of router.list_models() |
| CONFIG-04 | Admin can securely store, validate, and manage API keys for each provider with masked display | §API Key Management covers Fernet encryption, masked responses, validation flow |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `model_router` (shared) | 0.1.0 | Provider-agnostic LLM routing | Already built in Phases 8-9; the entire point of this phase |
| `pydantic-settings` | >=2.13.0 | Hierarchical config from env vars | Already used in AURA-CHAT server/config.py |
| `cryptography` | >=43.0 | Fernet symmetric encryption for API keys | Standard Python encryption library, well-maintained |
| `redis` / `redis.asyncio` | >=5.0 | Config store, model cache, pub/sub | Already deployed in both apps for Celery broker and caching |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pydantic` | >=2.0 | Schema validation for settings endpoints | Already a dependency of model_router and both apps |
| `fastapi` | 0.109+ | REST endpoint definitions | Already the web framework for both apps |

### No New Dependencies Needed
The migration does NOT require new pip packages. `cryptography` is the only potential addition if not already installed (it is a transitive dep of `google-auth`). Everything else is already in the dependency trees.

**Installation (if needed):**
```bash
pip install cryptography>=43.0
```

## Architecture Patterns

### Recommended Project Structure — New Files

```
shared/model_router/
├── src/model_router/
│   ├── config.py              # Extend with use-case defaults & key config
│   ├── settings_store.py      # NEW: Redis-backed settings CRUD
│   ├── key_manager.py         # NEW: Encrypted API key storage
│   └── cache.py               # NEW: TTL model list cache
│
AURA-CHAT/
├── server/
│   └── routers/
│       └── settings.py        # NEW: Admin settings REST endpoints
├── backend/
│   └── utils/
│       ├── vertex_ai_client.py  # REMOVE (after migration)
│       └── embeddings.py        # REMOVE (after migration)
│
AURA-NOTES-MANAGER/
├── api/
│   └── routers/
│       └── settings.py        # NEW: Admin settings REST endpoints (copy from CHAT)
├── services/
│   ├── vertex_ai_client.py    # REMOVE (after migration)
│   ├── genai_client.py        # REMOVE (after migration)
│   └── embeddings.py          # REMOVE (after migration)
```

### Pattern 1: Migration Façade (Transitional)

**What:** Replace `vertex_ai_client.py` exports with thin re-exports from model_router, preserving the import paths other modules use.
**When to use:** During the migration, to avoid changing every import in every file simultaneously.
**Example:**
```python
# AURA-CHAT/backend/utils/vertex_ai_client.py (transitional)
"""Façade — all LLM calls now route through model_router."""

from model_router import get_default_router, VertexCompatModel, ModelRouterError
from model_router.types import GenerateRequest

# Legacy callers import these names — re-export from model_router compat
def get_model(model_name: str) -> VertexCompatModel:
    return VertexCompatModel(model_name)

# Re-export types that legacy callers depend on
class GenerationConfig:
    """Thin shim for legacy callers still passing GenerationConfig objects."""
    def __init__(self, **kwargs):
        self._kwargs = kwargs
    def to_dict(self):
        return self._kwargs

# generate_content remains a pass-through (callers use model.generate_content())
def generate_content(model, contents, *, generation_config, safety_settings=None):
    return model.generate_content(contents, generation_config=generation_config)

# Streaming now delegates to model_router
async def generate_content_stream(*, model_name, contents, generation_config,
                                   system_instruction=None, thinking_config=None):
    router = get_default_router()
    request_kwargs = {'model': model_name, 'contents': contents}
    if system_instruction:
        request_kwargs['system_instruction'] = system_instruction
    if thinking_config:
        request_kwargs['thinking_config'] = thinking_config
    cfg = generation_config.to_dict() if hasattr(generation_config, 'to_dict') else {}
    request_kwargs.update({k: v for k, v in cfg.items()
                          if k in ('temperature', 'max_output_tokens')})
    async for chunk in router.stream(GenerateRequest(**request_kwargs)):
        yield {'type': chunk.type, 'text': chunk.text}
```

### Pattern 2: Redis-Backed Settings Store

**What:** Centralized config for use-case defaults, stored in Redis hash, read by both apps.
**When to use:** For any runtime-configurable setting that admin changes should affect without app restart.
**Example:**
```python
# shared/model_router/src/model_router/settings_store.py
"""Redis-backed settings store for admin-configurable LLM defaults."""

import json
from typing import Any

SETTINGS_KEY = 'aura:model_router:settings'

class SettingsStore:
    """Read/write LLM configuration from Redis."""

    def __init__(self, redis_client):
        self._redis = redis_client

    async def get_defaults(self) -> dict[str, Any]:
        raw = await self._redis.hgetall(SETTINGS_KEY)
        return {k: json.loads(v) for k, v in raw.items()}

    async def set_default(self, use_case: str, provider: str, model: str) -> None:
        value = json.dumps({'provider': provider, 'model': model})
        await self._redis.hset(SETTINGS_KEY, use_case, value)

    async def get_default(self, use_case: str) -> dict[str, str] | None:
        raw = await self._redis.hget(SETTINGS_KEY, use_case)
        return json.loads(raw) if raw else None
```

### Pattern 3: Fernet Encrypted Key Storage

**What:** API keys encrypted at rest in Redis using Fernet symmetric encryption.
**When to use:** For CONFIG-04 secure key storage.
**Example:**
```python
# shared/model_router/src/model_router/key_manager.py
"""Encrypted API key management for provider credentials."""

import os
from cryptography.fernet import Fernet

KEYS_HASH = 'aura:model_router:api_keys'

class KeyManager:
    def __init__(self, redis_client):
        self._redis = redis_client
        master_key = os.environ.get('AURA_MASTER_KEY', '')
        if not master_key:
            master_key = Fernet.generate_key().decode()
        self._fernet = Fernet(master_key.encode() if isinstance(master_key, str) else master_key)

    def _mask_key(self, key: str) -> str:
        if len(key) <= 8:
            return '***'
        return f'{key[:3]}...{key[-3:]}'

    async def store_key(self, provider: str, api_key: str) -> str:
        encrypted = self._fernet.encrypt(api_key.encode()).decode()
        await self._redis.hset(KEYS_HASH, provider, encrypted)
        return self._mask_key(api_key)

    async def get_key(self, provider: str) -> str | None:
        encrypted = await self._redis.hget(KEYS_HASH, provider)
        if not encrypted:
            return None
        return self._fernet.decrypt(encrypted.encode()).decode()

    async def get_masked_key(self, provider: str) -> str | None:
        key = await self.get_key(provider)
        return self._mask_key(key) if key else None

    async def delete_key(self, provider: str) -> bool:
        return bool(await self._redis.hdel(KEYS_HASH, provider))

    async def validate_key(self, provider: str) -> bool:
        """Validate by attempting provider health check."""
        key = await self.get_key(provider)
        if not key:
            return False
        # Delegate to provider-specific validation
        return True  # Actual validation via provider.health_check()
```

### Anti-Patterns to Avoid

- **Migrating all files at once without intermediate testing:** Each service file (`rag_engine.py`, `llm_entity_extractor.py`, etc.) should be migrated and tested individually.
- **Putting config logic in the shared package that depends on Redis:** The shared `model_router` package should remain Redis-agnostic in its core. The `settings_store.py` and `key_manager.py` modules accept a Redis client as a constructor argument — they don't import Redis themselves.
- **Encrypting keys with a key derived from the API key itself:** Use a separate `AURA_MASTER_KEY` env var. Generate it once during deployment.
- **Mixing sync and async Redis calls:** AURA-CHAT uses `redis.asyncio` (via ARQ). AURA-NOTES-MANAGER's existing `RedisClient` wrapper in `api/cache.py` is sync. The settings endpoints should use async Redis consistently.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Symmetric encryption | Custom XOR/AES wrapper | `cryptography.fernet.Fernet` | Battle-tested, handles IV, padding, HMAC verification |
| Model list caching | Custom dict with timestamp | Redis `SETEX` / `GET` with TTL | Already deployed, handles expiry, shared across processes |
| API key validation | Custom HTTP calls per provider | `provider.health_check()` from model_router | Already implemented in Phase 8-9 providers |
| Config change notification | Polling loop | Redis pub/sub or simply re-read on each request | Redis pub/sub is built-in; polling creates unnecessary load |

**Key insight:** The model_router already has `list_models()`, `health_check()`, and `get_provider()` — the backend endpoints are thin REST wrappers around these existing methods plus Redis for persistence.

## Migration Map

### AURA-CHAT — Files with Direct Provider SDK Imports

| # | File | Current Import | Router Equivalent | Migration Complexity |
|---|------|---------------|-------------------|---------------------|
| 1 | `backend/utils/vertex_ai_client.py` | `import vertexai`, `from google.genai import types`, `from vertexai.generative_models import ...` | **Replace with façade** that re-exports model_router calls. This is the hub file. | HIGH — 660 lines, many exports |
| 2 | `backend/rag_engine.py` | `from backend.utils.vertex_ai_client import get_model, GenerationConfig, generate_content_stream` + lazy `from google.genai import types` | Use router façade; change streaming to `router.stream()` yielding dicts | HIGH — Complex thinking mode logic uses genai types directly |
| 3 | `backend/llm_entity_extractor.py` | `from backend.utils.vertex_ai_client import get_model` | `from model_router import VertexCompatModel` or façade | LOW — Only uses `get_model()` |
| 4 | `backend/llm_gatekeeper.py` | `from backend.utils.vertex_ai_client import get_model` | Same as above | LOW |
| 5 | `backend/utils/embeddings.py` | Direct REST calls (no SDK import, but own REST implementation) | `from model_router import get_default_router; router.embed()` | MEDIUM — Has batching/retry logic; router handles this now |
| 6 | `server/routers/chat.py` | `from backend.utils.vertex_ai_client import get_model` (lazy) | Use façade or direct router import | LOW |
| 7 | `backend/routers/sessions.py` | `from backend.utils.vertex_ai_client import generate_content_stream, GenerationConfig` (lazy) | Router streaming | MEDIUM — Streaming chitchat path |

### AURA-NOTES-MANAGER — Files with Direct Provider SDK Imports

| # | File | Current Import | Router Equivalent | Migration Complexity |
|---|------|---------------|-------------------|---------------------|
| 8 | `services/vertex_ai_client.py` | `import vertexai`, `from vertexai.generative_models import ...` | **Replace with façade** (simpler than CHAT — no streaming) | MEDIUM — 320 lines |
| 9 | `services/genai_client.py` | `import google.generativeai as genai` / `from google import genai` | **Remove entirely** — functionality absorbed by router | MEDIUM — Used by summarizer.py |
| 10 | `services/embeddings.py` | `from vertexai.language_models import TextEmbeddingModel` | `router.embed()` from model_router | HIGH — Complex batching/retry, used heavily by kg_processor |
| 11 | `services/llm_entity_extractor.py` | `from services.vertex_ai_client import GenerationConfig, generate_content, get_model` | Façade or direct router | LOW |
| 12 | `services/coc.py` | `from services.vertex_ai_client import GenerationConfig, block_none_safety_settings, generate_content, get_model` | Façade; safety settings handled by router | LOW — `block_none_safety_settings` not needed with new SDK |
| 13 | `services/summary_service.py` | `from services.vertex_ai_client import GenerationConfig, generate_content, get_model` | Façade | LOW |
| 14 | `services/summarizer.py` | `from services.genai_client import get_genai_model` + `from services.vertex_ai_client import ...` | Façade; remove genai_client dependency | MEDIUM — Uses both old clients |
| 15 | `api/kg_processor.py` | `from services.vertex_ai_client import init_vertex_ai, get_model, generate_content, GenerationConfig` + `from services.embeddings import EmbeddingService` | Façade for generation; router.embed() for embeddings | HIGH — Massive file, many import sites |

### Summary of Migration Scope

- **Total files to modify:** 15 (7 CHAT + 8 NOTES)
- **Files to remove after migration:** 5 (`vertex_ai_client.py` × 2, `embeddings.py` × 2, `genai_client.py` × 1)
- **New files to create:** ~6 (settings store, key manager, cache module, settings router × 2, test files)
- **HIGH complexity:** 4 files (rag_engine.py, CHAT vertex_ai_client.py, NOTES embeddings.py, kg_processor.py)
- **MEDIUM complexity:** 4 files
- **LOW complexity:** 7 files

## Configuration Management

### Current State

Both apps load config from env vars at startup via plain Python classes or `pydantic_settings.BaseSettings`:
- **AURA-CHAT:** `backend/utils/config.py` (plain `Config` class) + `server/config.py` (pydantic `BaseSettings`)
- **AURA-NOTES-MANAGER:** `api/config.py` (module-level env var reads)
- **Model Router:** `model_router/config.py` (`RouterConfig.from_env()`)

### Target State for CONFIG-01

Admin-configurable defaults per use case require a **runtime store** separate from env vars:

| Use Case | Key | Default Value |
|----------|-----|---------------|
| chat | `aura:defaults:chat` | `{"provider": "vertex_ai", "model": "gemini-2.5-flash"}` |
| embeddings | `aura:defaults:embeddings` | `{"provider": "vertex_ai", "model": "text-embedding-004"}` |
| entity_extraction | `aura:defaults:entity_extraction` | `{"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"}` |

### Configuration Hierarchy (priority highest → lowest)

1. **Per-request explicit:** Caller specifies `provider` + `model` in request
2. **Redis admin settings:** Set via settings API endpoints
3. **Environment variables:** `VERTEX_PROJECT`, `OPENROUTER_API_KEY`, etc.
4. **Code defaults:** `RouterConfig` defaults in model_router

### Runtime Reload Without Restart

The router singleton (`get_default_router()`) is module-scoped. To pick up config changes:

**Option A (Recommended): Lazy config read per request.**
- Settings endpoints write to Redis.
- The router's `_determine_provider_type()` checks Redis settings store on each generate/stream call.
- Only the "default model for this use case" lookup hits Redis — the provider instances remain registered.
- This is essentially free because Redis reads are sub-millisecond.

**Option B: Reset router singleton.**
- Admin settings endpoint calls `reset_default_router()` after config change.
- Next request rebuilds the router from env + Redis.
- Simpler but loses provider connection state.

**Recommendation:** Option A for defaults, Option B only for API key changes (which actually require provider re-registration).

### Shared Config Between Two Separate FastAPI Deployments

Both apps connect to the **same Redis instance** (they already do for Celery broker). Use a shared Redis key prefix (`aura:model_router:*`) so both apps read the same admin settings. This eliminates configuration drift risk.

## API Key Management (CONFIG-04)

### Encryption Approach: Fernet

| Property | Value |
|----------|-------|
| Algorithm | AES-128-CBC with HMAC-SHA256 |
| Library | `cryptography.fernet.Fernet` |
| Master key source | `AURA_MASTER_KEY` env var (base64-encoded 32-byte key) |
| Storage location | Redis hash `aura:model_router:api_keys` |
| Key rotation | Generate new master key, re-encrypt all stored keys |

### Key Masking Rules

| Key Pattern | Masked Display |
|-------------|---------------|
| `sk-ant-api03-xxxxx...abcde` | `sk-...cde` |
| `AIzaSy...` (short) | `AIz...` |
| Keys < 8 chars | `***` |
| Empty/None | `(not set)` |

### Key Validation Flow

1. Admin POSTs API key for a provider
2. Backend encrypts and stores in Redis
3. Backend creates a temporary provider instance with the new key
4. Backend calls `provider.health_check()` to validate
5. Returns `{"valid": true, "masked_key": "sk-...abc"}` or `{"valid": false, "error": "..."}`

### REST Endpoints

```
POST   /api/v1/settings/providers/{provider}/api-key    — Store + validate key
GET    /api/v1/settings/providers/{provider}/api-key    — Get masked key
DELETE /api/v1/settings/providers/{provider}/api-key    — Remove key
POST   /api/v1/settings/providers/{provider}/validate   — Re-validate stored key
```

## Model Discovery / Caching (CONFIG-03)

### Architecture

```
Admin/Client request → FastAPI endpoint → Check Redis cache → If miss:
   → router.list_models(provider) → Store in Redis with TTL → Return
```

### Cache Design

| Property | Value |
|----------|-------|
| Cache key pattern | `aura:models:{provider}` (e.g., `aura:models:vertex_ai`) |
| Cache value | JSON-serialized `list[ModelInfo]` |
| Default TTL | 15 minutes |
| Configurable range | 5–60 minutes (stored in `aura:model_router:settings` hash) |
| Force refresh | `POST /api/v1/settings/providers/{provider}/models?refresh=true` |

### REST Endpoints

```
GET /api/v1/settings/models                           — All models from all providers
GET /api/v1/settings/providers/{provider}/models      — Models from specific provider
GET /api/v1/settings/defaults                         — Current default model per use case
PUT /api/v1/settings/defaults/{use_case}              — Set default for use case
```

### Implementation Approach

```python
async def get_cached_models(
    provider: ProviderType,
    redis_client,
    router: ModelRouter,
    ttl_seconds: int = 900,
) -> list[ModelInfo]:
    cache_key = f'aura:models:{provider.value}'
    cached = await redis_client.get(cache_key)
    if cached:
        return [ModelInfo(**m) for m in json.loads(cached)]
    
    models = await router.list_models(provider)
    await redis_client.setex(
        cache_key,
        ttl_seconds,
        json.dumps([m.model_dump() for m in models]),
    )
    return models
```

## Celery Worker Integration

### Current State

| App | Task Queue | Worker Package | LLM Usage in Workers |
|-----|-----------|---------------|---------------------|
| AURA-CHAT | ARQ (async) | `backend/tasks/worker.py` | `document_processor.py` → `embeddings.py` → REST API |
| AURA-NOTES-MANAGER | Celery 5.3.6 | `api/tasks/document_processing_tasks.py` | `kg_processor.py` → `vertex_ai_client.py` + `embeddings.py` |

### Key Concerns

1. **Editable install in workers:** The `pip install -e shared/model_router` editable install must be visible in the Python path used by Celery workers. Both apps run workers from the monorepo root or app subdirectory.
   - **AURA-CHAT (ARQ):** Worker config is in `backend/tasks/worker.py`, started from project root. Editable install should resolve.
   - **AURA-NOTES-MANAGER (Celery):** Worker started via `celery -A api.tasks worker`. The `sys.path.insert` in `document_processing_tasks.py` adds parent directories. Editable install should also resolve.

2. **Config changes and worker restart:** 
   - Celery workers fork processes. Config changes in Redis are visible on next request (no restart needed for settings).
   - API key changes that require provider re-registration: use `reset_default_router()` or send SIGHUP to workers.
   - **Recommendation:** For key changes, document that workers should be restarted (`celery control shutdown` + restart), or use Celery's `--autoreload` in development.

3. **Async vs sync mismatch:**
   - The model_router is async-first (`async def generate()`, `async def embed()`).
   - Celery tasks in NOTES are sync (regular functions).
   - The `VertexCompatModel` already handles this via `_run_sync()` which bridges sync → async.
   - For embeddings, we need a similar sync bridge: `asyncio.run(router.embed(texts))`.

4. **Import verification test:** Phase 8 already created `test_import_contexts.py` that verifies model_router imports from multiple directories. Extend this to verify import from a simulated Celery worker context.

### Celery Worker Sync Bridge Pattern

```python
# In kg_processor.py or any sync Celery task context:
import asyncio
from model_router import get_default_router

def get_embeddings_sync(texts: list[str]) -> list[list[float]]:
    """Sync wrapper for async router embeddings, safe for Celery workers."""
    router = get_default_router()
    return asyncio.run(router.embed(texts))
```

## Common Pitfalls

### Pitfall 1: Circular Import with router.embed() in Embedding-Heavy Modules

**What goes wrong:** `kg_processor.py` imports `EmbeddingService` which currently imports `vertexai.language_models`. Replacing with model_router creates a different import chain that may conflict with existing `sys.path` hacks.
**Why it happens:** AURA-NOTES-MANAGER has aggressive `sys.path.insert()` to handle import from different working directories.
**How to avoid:** The migration façade approach means changing only the *implementation* of `EmbeddingService`, not its import path. Other modules keep importing `from services.embeddings import EmbeddingService` — the class just delegates to model_router internally.
**Warning signs:** `ModuleNotFoundError` or `ImportError` during tests from `api/` directory.

### Pitfall 2: Safety Settings Removal Breaking Behavior

**What goes wrong:** `services/coc.py` uses `block_none_safety_settings()` to disable content filtering. The model_router doesn't expose safety settings (they're provider-specific).
**Why it happens:** The new `google-genai` SDK used by the router handles safety differently than the old `vertexai.generative_models` SDK.
**How to avoid:** The new SDK's `GenerateContentConfig` doesn't require explicit safety settings to disable filtering for Vertex AI enterprise projects. Verify in test mode that content isn't being blocked. If needed, add a `safety_settings` pass-through field to `GenerateRequest`.
**Warning signs:** Content blocked errors from Vertex AI that didn't occur before.

### Pitfall 3: Embedding Batching/Retry Logic Lost in Migration

**What goes wrong:** Both apps' embedding services have sophisticated batching, rate limiting, and retry logic. The router's `VertexAIEmbeddingProvider._embed_sync()` does a single REST call with no batching or retry.
**Why it happens:** The shared router was designed for single-batch requests; the apps add higher-level orchestration.
**How to avoid:** Keep a thin `EmbeddingService` class in each app that handles batching and rate limiting, but delegates the actual API call to `router.embed()`. Don't remove the batching logic — move it up.
**Warning signs:** Rate limit errors (429) during KG processing that didn't occur before.

### Pitfall 4: `generate_content_stream` Dict Shape vs StreamChunk Model

**What goes wrong:** AURA-CHAT's `generate_content_stream()` yields `dict[str, Any]` with `{"type": "thinking"|"content", "text": "..."}`. The model_router yields `StreamChunk` pydantic models with the same fields.
**Why it happens:** The streaming endpoints and RAG engine check `chunk.get("type")` and `chunk.get("text")` — dict access, not attribute access.
**How to avoid:** The façade must convert `StreamChunk` → dict for backward compatibility OR change consumers to use `chunk.type`/`chunk.text`. The façade approach is safer.
**Warning signs:** `AttributeError: 'dict' object has no attribute 'type'` or vice versa.

### Pitfall 5: Test Mode Precedence During Migration

**What goes wrong:** With `AURA_TEST_MODE=true`, the old `get_model()` returns `_TestGenerativeModel` BEFORE checking `USE_MODEL_ROUTER`. If we remove the test mode check, test behavior changes.
**Why it happens:** The Strangler Fig shim deliberately kept test mode first.
**How to avoid:** The model_router's `VertexAIProvider` already handles test mode internally (returns canned responses). After migration, remove the app-level test mode checks in favor of the router's.
**Warning signs:** Tests that pass with old code fail after migration because test mode behavior differs.

### Pitfall 6: Master Key Management for Fernet Encryption

**What goes wrong:** `AURA_MASTER_KEY` not set in production → auto-generated key changes every restart → stored keys become unreadable.
**Why it happens:** Developer forgets to configure the env var.
**How to avoid:** Fail fast on startup if `AURA_MASTER_KEY` is not set and there are stored keys. Generate and persist the key during initial deployment. Document this clearly.
**Warning signs:** `InvalidToken` errors from Fernet when reading stored API keys after restart.

## Code Examples

### Example 1: Admin Settings Router (FastAPI)

```python
# AURA-CHAT/server/routers/settings.py
"""Admin settings endpoints for LLM provider configuration."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix='/api/v1/settings', tags=['Settings'])

class DefaultModelUpdate(BaseModel):
    provider: str
    model: str

class ApiKeyCreate(BaseModel):
    api_key: str

@router.get('/defaults')
async def get_defaults(store = Depends(get_settings_store)):
    return await store.get_defaults()

@router.put('/defaults/{use_case}')
async def set_default(use_case: str, body: DefaultModelUpdate,
                      store = Depends(get_settings_store)):
    if use_case not in ('chat', 'embeddings', 'entity_extraction'):
        raise HTTPException(400, f'Unknown use case: {use_case}')
    await store.set_default(use_case, body.provider, body.model)
    return {'use_case': use_case, **body.model_dump()}

@router.get('/providers/{provider}/models')
async def list_models(provider: str, refresh: bool = False,
                      cache = Depends(get_model_cache)):
    return await cache.get_models(provider, force_refresh=refresh)

@router.post('/providers/{provider}/api-key')
async def store_api_key(provider: str, body: ApiKeyCreate,
                        km = Depends(get_key_manager)):
    masked = await km.store_key(provider, body.api_key)
    valid = await km.validate_key(provider)
    return {'provider': provider, 'masked_key': masked, 'valid': valid}

@router.get('/providers/{provider}/api-key')
async def get_api_key(provider: str, km = Depends(get_key_manager)):
    masked = await km.get_masked_key(provider)
    if not masked:
        raise HTTPException(404, f'No API key configured for {provider}')
    return {'provider': provider, 'masked_key': masked}

@router.delete('/providers/{provider}/api-key')
async def delete_api_key(provider: str, km = Depends(get_key_manager)):
    deleted = await km.delete_key(provider)
    if not deleted:
        raise HTTPException(404, f'No API key configured for {provider}')
    return {'provider': provider, 'deleted': True}
```

### Example 2: Migrating a LOW-Complexity File

```python
# BEFORE: AURA-CHAT/backend/llm_gatekeeper.py
from backend.utils.vertex_ai_client import get_model

# AFTER: AURA-CHAT/backend/llm_gatekeeper.py  
from model_router.compat import VertexCompatModel

# ... later in code:
# BEFORE: model = get_model(model_name)
# AFTER:  model = VertexCompatModel(model_name)
# (generate_content() interface is identical)
```

### Example 3: Migrating Embeddings (NOTES)

```python
# BEFORE: services/embeddings.py (imports vertexai.language_models)
# AFTER: services/embeddings.py (delegates to model_router)

from model_router import get_default_router
import asyncio

class EmbeddingService:
    """Embedding service — now backed by shared model router."""
    
    def __init__(self):
        self._test_mode = os.getenv("AURA_TEST_MODE", "").lower() == "true"
        self.batch_size = EMBEDDING_BATCH_SIZE
        # ... keep batching/rate-limiting config ...

    def _embed_batch_sync(self, texts: list[str]) -> list[list[float]]:
        """Delegate to model router with sync bridge."""
        router = get_default_router()
        return asyncio.run(router.embed(texts))

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch texts into groups and embed each group."""
        all_vectors = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            vectors = self._embed_batch_sync(batch)
            all_vectors.extend(vectors)
        return all_vectors
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `vertexai.generative_models.GenerativeModel` | `google.genai.Client` (new SDK) | June 2025 | Old SDK deprecated; new SDK in use via model_router |
| `USE_MODEL_ROUTER` env var toggle | Direct model_router imports | This phase | Removes feature flag; clean migration |
| Per-app embedding REST clients | Shared `router.embed()` | This phase | Single source of truth for embeddings |
| Env-var-only config | Redis-backed runtime config | This phase | Admin can change defaults without redeployment |
| Plaintext API keys in env | Fernet-encrypted in Redis | This phase | Keys encrypted at rest, masked in responses |

**Deprecated/outdated after this phase:**
- `AURA-CHAT/backend/utils/vertex_ai_client.py` — Replaced by model_router + thin façade
- `AURA-CHAT/backend/utils/embeddings.py` — Replaced by model_router embed()
- `AURA-NOTES-MANAGER/services/vertex_ai_client.py` — Replaced by model_router + thin façade
- `AURA-NOTES-MANAGER/services/genai_client.py` — Fully absorbed by model_router
- `AURA-NOTES-MANAGER/services/embeddings.py` — Replaced by model_router embed()
- `USE_MODEL_ROUTER` env var — No longer needed; model_router is the only path

## Open Questions

1. **Safety settings pass-through**
   - What we know: `coc.py` uses `block_none_safety_settings()` to disable Vertex AI content filtering. The new google-genai SDK handles this differently.
   - What's unclear: Whether enterprise Vertex AI projects auto-disable safety filtering, or whether we need explicit config.
   - Recommendation: Test with a live call in dev. If safety filtering blocks content, add a `safety_settings` field to `GenerateRequest` and pass through to the google-genai config.

2. **Master key bootstrap for Fernet encryption**
   - What we know: Fernet needs a 32-byte base64-encoded key.
   - What's unclear: Deployment workflow for generating and distributing the key.
   - Recommendation: Add a CLI command or startup check that generates and prints a key if `AURA_MASTER_KEY` is not set. Store in deployment environment (e.g., Docker secrets).

3. **rag_engine.py thinking mode direct SDK usage**
   - What we know: `rag_engine.py` line 1960 does `from google.genai import types` to build `ThinkingConfig` directly. This is the most complex migration site.
   - What's unclear: Whether the model_router's `thinking_config: dict` field properly translates to all thinking scenarios the RAG engine uses.
   - Recommendation: The router already handles `thinking_config` dict → `ThinkingConfig` in `_build_generate_config_kwargs`. Verify with test cases for `thinking_budget` and `thinking_level` parameters.

4. **Embedding batching ownership**
   - What we know: Both apps have sophisticated batching with rate limiting. The router's embed() processes a single batch.
   - What's unclear: Whether to move batching into the shared router or keep it app-side.
   - Recommendation: Keep batching app-side for now. The apps have different batch sizes and rate limits. Shared batching can be a v1.2 improvement.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8+ with pytest-asyncio |
| Config file | `shared/model_router/pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `cd shared/model_router && python -m pytest tests/ -x -q` |
| Full suite command | `cd shared/model_router && python -m pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-03 | No direct provider imports in either app | smoke | `grep -rn "from vertexai\|from google.generativeai\|from google.genai\|import openai" AURA-CHAT/backend AURA-CHAT/server AURA-NOTES-MANAGER/api AURA-NOTES-MANAGER/services --include="*.py" \| grep -v test \| grep -v __pycache__` | ❌ Wave 0 |
| CONFIG-01 | Admin set/get defaults via REST | integration | `pytest AURA-CHAT/server/tests/test_settings_router.py -x` | ❌ Wave 0 |
| CONFIG-03 | Model list cached with TTL | unit | `pytest shared/model_router/tests/test_model_cache.py -x` | ❌ Wave 0 |
| CONFIG-04 | API key encrypt/store/mask/validate | unit | `pytest shared/model_router/tests/test_key_manager.py -x` | ❌ Wave 0 |
| CONFIG-04 | API key REST endpoints | integration | `pytest AURA-CHAT/server/tests/test_settings_router.py::test_api_key_lifecycle -x` | ❌ Wave 0 |
| UI-03 (Celery) | Celery workers import model_router | integration | `python -c "from model_router import get_default_router; print('OK')"` | ✅ (test_import_contexts.py covers partial) |

### Sampling Rate
- **Per task commit:** `cd shared/model_router && python -m pytest tests/ -x -q`
- **Per wave merge:** Full suite for shared package + grep audit for direct imports
- **Phase gate:** Zero direct provider imports outside shared/model_router + all new tests green

### Wave 0 Gaps
- [ ] `shared/model_router/tests/test_settings_store.py` — covers CONFIG-01 unit logic
- [ ] `shared/model_router/tests/test_key_manager.py` — covers CONFIG-04 encryption/masking
- [ ] `shared/model_router/tests/test_model_cache.py` — covers CONFIG-03 TTL caching
- [ ] `AURA-CHAT/server/tests/test_settings_router.py` — covers CONFIG-01, CONFIG-04 REST
- [ ] `tests/test_no_direct_imports.py` — grep-based audit test for UI-03

## Sources

### Primary (HIGH confidence)
- Codebase audit: All 15 files identified via `grep` across both apps
- `shared/model_router/` source code: router.py, config.py, compat.py, providers/
- Phase 08 and 09 planning docs and summaries
- `REQUIREMENTS.md` for requirement definitions

### Secondary (MEDIUM confidence)
- `cryptography.fernet` documentation for encryption patterns
- pydantic-settings patterns from existing `server/config.py` usage
- Redis caching patterns from existing `api/cache.py` usage

### Tertiary (LOW confidence)
- None — all findings verified from codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in use
- Architecture: HIGH — verified against existing codebase patterns
- Migration map: HIGH — comprehensive grep audit of both apps
- Pitfalls: HIGH — based on actual code analysis, not speculation
- Config/Key/Cache patterns: MEDIUM — patterns are standard but implementations untested

**Research date:** 2026-03-10
**Valid until:** 2026-04-10 (stable — no fast-moving dependencies)
