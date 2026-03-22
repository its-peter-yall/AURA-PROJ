# Technology Stack: SettingsStore Wiring Patterns

**Project:** AURA v1.2 — Settings Wiring E2E
**Researched:** 2026-03-23
**Focus:** Patterns to wire SettingsStore consistently across all backend consumers

---

## Problem Summary

Only chat in AURA-CHAT reads SettingsStore end-to-end. Six other consumers
(entity extraction, embeddings, gatekeeper, KG processor, summarization,
relationship extraction) either bypass SettingsStore with hardcoded env vars,
ignore the `provider` field, or are missing from `ALLOWED_USE_CASES` entirely.

The `ModelRouter.generate()` already supports `provider` on `GenerateRequest`
and `_determine_provider_type()` checks it first — callers just never pass it.

---

## Recommended Pattern: `resolve_use_case_config()`

### Core Idea

Add a single utility function to `shared/model_router/` that every consumer
calls to get `{provider, model}` for a use case. The resolution chain:

```
SettingsStore (Redis) → env var override → hardcoded default → never None
```

Both sync and async call-sites get a clean entry point.

### Implementation Location

Add to `shared/model_router/src/model_router/settings_store.py`:

```python
# Use-case to env-var mapping for fallback resolution
_USE_CASE_ENV_VARS: dict[str, str] = {
    "chat": "RAG_MODEL_DEFAULT",
    "embeddings": "EMBEDDING_MODEL",
    "entity_extraction": "LLM_ENTITY_EXTRACTION_MODEL",
    "summarization": "LLM_SUMMARIZATION_MODEL",
    "gatekeeper": "LLM_GATEKEEPER_MODEL",
    "relationship_extraction": "LLM_RELATIONSHIP_MODEL",
}

_USE_CASE_DEFAULT_MODELS: dict[str, str] = {
    "chat": "gemini-2.5-flash-lite",
    "embeddings": "text-embedding-004",
    "entity_extraction": "gemini-2.5-flash-lite",
    "summarization": "gemini-2.5-flash-lite",
    "gatekeeper": "gemini-2.5-flash-lite",
    "relationship_extraction": "gemini-2.5-flash-lite",
}

_USE_CASE_DEFAULT_PROVIDER: str = "vertex_ai"


def resolve_use_case_config(
    use_case: str,
    redis_url: str | None = None,
    redis_client: Any = None,
    env_overrides: dict[str, str] | None = None,
) -> dict[str, str]:
    """Resolve provider+model for a use case with fallback chain.

    Resolution order:
      1. SettingsStore (Redis) — admin-configured default
      2. Environment variable — per-use-case env override
      3. Hardcoded default — last resort

    Args:
        use_case: Logical use case (chat, embeddings, etc.)
        redis_url: Redis connection URL override.
        redis_client: Pre-created sync Redis client.
        env_overrides: Optional dict of env var name->value overrides
            for testing. When None, reads from os.environ.

    Returns:
        Dict with "provider" and "model" keys. Never returns None;
        falls back to hardcoded defaults.
    """
    # 1. Try SettingsStore
    default = get_default_sync(use_case, redis_url, redis_client)
    if default and default.get("model"):
        return {
            "provider": default.get("provider", _USE_CASE_DEFAULT_PROVIDER),
            "model": default["model"],
        }

    # 2. Try env var
    env_var_name = _USE_CASE_ENV_VARS.get(use_case)
    if env_var_name:
        env_val: str | None = None
        if env_overrides is not None:
            env_val = env_overrides.get(env_var_name)
        else:
            env_val = os.getenv(env_var_name)
        if env_val:
            return {
                "provider": _USE_CASE_DEFAULT_PROVIDER,
                "model": env_val,
            }

    # 3. Hardcoded default
    return {
        "provider": _USE_CASE_DEFAULT_PROVIDER,
        "model": _USE_CASE_DEFAULT_MODELS.get(
            use_case, "gemini-2.5-flash-lite"
        ),
    }
```

### Why This Pattern

| Concern | How It's Handled |
|---------|-----------------|
| Sync consumers | Direct call — no async needed |
| Async consumers | Same function works; can also use `SettingsStore.get_default()` directly |
| Redis down | Falls through to env var → hardcoded default |
| Missing env var | Falls through to hardcoded default |
| Provider always set | Returns `provider` in every case — no "accidentally works" name-based routing |
| Testable | `env_overrides` dict avoids global state mutation in tests |

### New Constants Are Single Source of Truth

The `_USE_CASE_ENV_VARS` and `_USE_CASE_DEFAULT_MODELS` dicts centralize
what was previously scattered across `AURA-CHAT/backend/utils/config.py` and
`AURA-NOTES-MANAGER/api/config.py`. After wiring:

- `config.LLM_ENTITY_EXTRACTION_MODEL` → still read as env fallback, but via
  `resolve_use_case_config("entity_extraction")` instead of direct import
- `config.RAG_ALLOWED_MODELS` → still used for chat config fallback list
- `config.CHAT_MODELS_WITH_THINKING` → needs expansion (see below)

---

## Pattern for Each Consumer Type

### Type A: Sync Consumers (most of them)

These call `get_model()` directly or use Vertex AI SDK synchronously.

**Files:** `llm_entity_extractor.py` (both apps), `llm_gatekeeper.py`,
`embeddings.py` (both apps), `kg_processor.py`, `summarizer.py`

**Before (broken):**
```python
# Reads model from env var, ignores provider entirely
LLM_ENTITY_EXTRACTION_MODEL = os.getenv(
    "LLM_ENTITY_EXTRACTION_MODEL", "gemini-2.5-flash-lite"
)
model = get_model(LLM_ENTITY_EXTRACTION_MODEL)
```

**After (wired):**
```python
from model_router.settings_store import resolve_use_case_config

_cfg = resolve_use_case_config("entity_extraction")
_model = _cfg["model"]
_provider = _cfg["provider"]  # Always present

# When using ModelRouter directly:
from model_router import get_default_router, GenerateRequest

router = get_default_router()
response = await router.generate(
    GenerateRequest(
        model=_model,
        provider=_provider,  # Explicit — no name-based guessing
        contents=prompt,
        response_mime_type="application/json",
    )
)
```

### Type B: Async FastAPI Consumers (chat already works)

**Files:** `AURA-CHAT/server/routers/chat.py`

Chat already uses async `SettingsStore.get_default("chat")` via DI.
The fix is minor: ensure `provider` is passed through to
`rag_engine.set_model()` or the underlying `GenerateRequest`.

**Current wiring (mostly correct):**
```python
_store = SettingsStore(get_redis())
_default = await _store.get_default("chat")
if _default and _default.get("model"):
    rag_engine.set_model(_default["model"])
    # _default["provider"] is available but not explicitly passed
```

**Fix:** Add provider passthrough to `RAGEngine` so that when it builds
`GenerateRequest` internally, it includes the provider. Or use
`resolve_use_case_config()` for consistency.

### Type C: Background Task Consumers (ARQ workers)

**Files:** `AURA-CHAT/backend/tasks/document_tasks.py`

Background tasks run in separate processes. They should call
`resolve_use_case_config()` at task start (not at module import time)
to get fresh config from Redis.

**Pattern:**
```python
async def process_document_task(ctx, document_id: str):
    _cfg = resolve_use_case_config("entity_extraction")
    extractor = LLMEntityExtractor(
        model_name=_cfg["model"],
        provider=_cfg["provider"],
    )
    # ... process
```

---

## Provider Passthrough: Critical Detail

The `ModelRouter._determine_provider_type()` already handles the `provider`
field on `GenerateRequest`:

```python
# router.py:196-207
def _determine_provider_type(self, request: GenerateRequest) -> ProviderType:
    if request.provider:          # <- Explicit provider wins
        return _coerce_provider_type(request.provider)
    # Fallback: name-based heuristics
    if "/" in model_name:
        return ProviderType.OPENROUTER
    return self._config.default_provider
```

**The problem is callers never set `request.provider`.** The fix is simple:
every consumer must pass `provider` from `resolve_use_case_config()` into
the `GenerateRequest` or `router.embed()` call.

### Where `provider` Must Be Passed

| Consumer | Current Provider Handling | Fix Needed |
|----------|--------------------------|------------|
| `llm_entity_extractor.py` (CHAT) | Ignores `_default["provider"]` at line 307 | Pass to `GenerateRequest.provider` |
| `llm_entity_extractor.py` (NOTES) | Reads `_default["provider"]` at line 204, ignores it | Pass to `GenerateRequest.provider` |
| `embeddings.py` (CHAT) | Passes `provider=` to `router.embed()` at line 158 | Already correct — verify |
| `embeddings.py` (NOTES) | Passes `provider=` to `router.embed()` | Already correct — verify |
| `llm_gatekeeper.py` | Skips OpenRouter explicitly at line 153 | Remove skip + pass provider |
| `kg_processor.py` | Uses `GeminiClient` — bypasses router entirely | Refactor to use router |
| `summarizer.py` | Uses `genai_client` — bypasses router entirely | Refactor to use router |

---

## `ALLOWED_USE_CASES` Expansion

**Current (both settings routers):**
```python
ALLOWED_USE_CASES = {"chat", "embeddings", "entity_extraction", "summarization"}
```

**Required additions:**
```python
ALLOWED_USE_CASES = {
    "chat",
    "embeddings",
    "entity_extraction",
    "summarization",
    "gatekeeper",               # NEW
    "relationship_extraction",  # NEW
}
```

**Files to change:**
- `AURA-CHAT/server/routers/settings.py:55`
- `AURA-NOTES-MANAGER/api/settings.py` (does not exist — needs creation or
  use AURA-CHAT's settings router via shared mounting)

**Impact:** The settings UI in AURA-NOTES-MANAGER reads use cases from the
API, so adding them to `ALLOWED_USE_CASES` auto-populates the UI.

---

## Gatekeeper: OpenRouter Structured Output Issue

The gatekeeper skips OpenRouter because it requires
`response_mime_type: "application/json"` for structured output.

**Resolution (HIGH confidence):** OpenRouter now supports `response_mime_type`
for Gemini models (passes through to Google's API). The blanket skip at
lines 153-159 should be removed.

**Instead of blanket skip, use provider-aware error handling:**

```python
# Remove lines 153-159 (the OpenRouter skip)
# Let ModelRouter route to OpenRouter if configured
# If a specific model doesn't support it, the provider raises a clear error

try:
    response = await router.generate(
        GenerateRequest(
            model=_gatekeeper_model,
            provider=_gatekeeper_provider,
            contents=prompt,
            response_mime_type="application/json",
        )
    )
except ModelRouterError as exc:
    if "response_mime_type" in str(exc).lower():
        # Specific model doesn't support structured output
        logger.warning(
            "Model %s doesn't support response_mime_type, "
            "falling back to text extraction",
            _gatekeeper_model,
        )
        response = await router.generate(
            GenerateRequest(
                model=_gatekeeper_model,
                provider=_gatekeeper_provider,
                contents=prompt,
            )
        )
        # Parse JSON from text response manually
    else:
        raise
```

---

## Chat Config Fallback Fix

**Problem:** When Redis is down, `/chat/config` returns hardcoded Vertex AI
models (`RAG_ALLOWED_MODELS`) and thinking mode lists only Vertex AI models.

**Recommended approach — Dynamic with graceful degradation:**

```python
@router.get("/config")
async def get_config():
    try:
        router_inst = get_default_router()
        model_infos = await router_inst.list_models()
        allowed_models = [m.id for m in model_infos]
    except Exception:
        # Fallback: try resolve_use_case_config for chat default
        # + env-based model list
        _cfg = resolve_use_case_config("chat")
        allowed_models = [_cfg["model"]] + config.RAG_ALLOWED_MODELS
        allowed_models = list(dict.fromkeys(allowed_models))  # dedupe

    # Thinking models: known list expanded for multi-provider
    thinking_models = list(config.CHAT_MODELS_WITH_THINKING)
    _OPENROUTER_THINKING_MODELS = [
        "google/gemini-2.0-flash-thinking",
        "google/gemini-2.5-flash",
        "google/gemini-2.5-pro",
    ]
    thinking_models.extend(_OPENROUTER_THINKING_MODELS)

    return {
        "allowed_models": allowed_models,
        "default_model": config.RAG_MODEL_DEFAULT,
        "thinking": {
            "enabled": config.ENABLE_THINKING,
            "supported_models": thinking_models,
            "enabled_modes": config.THINKING_ENABLED_MODES,
        },
    }
```

**Longer-term:** Add a `supports_thinking` flag to `ModelInfo` metadata
so the thinking capability list is derived from provider capabilities,
not hardcoded.

---

## Integration with Existing ModelRouter

### What Already Works (Do NOT Change)
- `ModelRouter.generate()` accepts `provider` on `GenerateRequest`
- `ModelRouter.embed()` accepts `provider` as keyword argument
- `_determine_provider_type()` checks `request.provider` first
- Lazy OpenRouter registration from `KeyManager` works
- `get_default_sync()` provides 5-minute cached Redis reads
- `SettingsStore` async class API is complete
- `GenerateRequest.provider` field exists at `types.py:41`

### What Needs Addition
1. `resolve_use_case_config()` — centralized resolution function
   in `shared/model_router/src/model_router/settings_store.py`
2. `ALLOWED_USE_CASES` expansion — add `gatekeeper` and
   `relationship_extraction` to both settings routers
3. Provider passthrough in all consumers — 6 files need `_provider` passed
   to `GenerateRequest.provider` or `router.embed(provider=...)`
4. `kg_processor.py` — refactor `GeminiClient` to use ModelRouter for
   entity extraction (embeddings already go through router)
5. `summarizer.py` — refactor from `genai_client` to ModelRouter

### What Should NOT Change
- `ModelRouter` internals — routing logic is correct
- `SettingsStore` class — async API is fine as-is
- `KeyManager` — no changes needed
- `GenerateRequest` / `GenerateResponse` types — provider field exists
- Embedding services — provider passthrough already works

---

## Module-Level vs Instance-Level SettingsStore Reads

### Anti-Pattern: Module-Level Read (Current in NOTES entity extractor)

```python
# services/llm_entity_extractor.py:204-222
# This runs ONCE at import time — never updates without restart
_LLM_ENTITY_EXTRACTION_DEFAULT = get_default_sync("entity_extraction", ...)
LLM_ENTITY_EXTRACTION_MODEL = _LLM_ENTITY_EXTRACTION_DEFAULT["model"]
```

**Problem:** Settings read at import time. If admin changes the setting,
the process must restart to pick it up. The 5-minute cache in
`get_default_sync` doesn't help because the cached value is assigned
to a module-level constant.

**Fix:** Move to instance-level or function-level reads:

```python
class LLMEntityExtractor:
    def __init__(self, model_name: str | None = None):
        if model_name is None:
            _cfg = resolve_use_case_config("entity_extraction")
            model_name = _cfg["model"]
            self._provider = _cfg["provider"]
        # ...
```

### Pattern: Instance-Level Read (Recommended)

```python
class SomeProcessor:
    def __init__(self):
        _cfg = resolve_use_case_config("entity_extraction")
        self._model = _cfg["model"]
        self._provider = _cfg["provider"]
        # Each instance gets fresh config from SettingsStore cache
```

The 5-minute TTL cache in `get_default_sync` handles performance — each
call doesn't hit Redis, but the value can update within 5 minutes of
an admin change.

---

## Recommended Dependency Additions

No new packages needed. The wiring uses only existing shared packages:

```python
# Already available — just import from shared model_router
from model_router.settings_store import resolve_use_case_config  # NEW function
from model_router.settings_store import get_default_sync          # EXISTS
from model_router import get_default_router, GenerateRequest      # EXISTS
```

---

## Sources

| Claim | Source | Confidence |
|-------|--------|------------|
| `ModelRouter._determine_provider_type()` checks `request.provider` first | `shared/model_router/src/model_router/router.py:196-207` | HIGH |
| `GenerateRequest` has `provider` field | `shared/model_router/src/model_router/types.py:41` | HIGH |
| `get_default_sync()` returns `{provider, model}` | `shared/model_router/src/model_router/settings_store.py:45-101` | HIGH |
| Chat wiring reads from SettingsStore | `AURA-CHAT/server/routers/chat.py:368-379` | HIGH |
| Gatekeeper skips OpenRouter | `AURA-CHAT/backend/llm_gatekeeper.py:153-159` | HIGH |
| Entity extraction ignores provider | `AURA-CHAT/backend/llm_entity_extractor.py:307-320` | HIGH |
| KG processor bypasses SettingsStore | `AURA-NOTES-MANAGER/api/kg_processor.py:465` | HIGH |
| Module-level SettingsStore read (anti-pattern) | `AURA-NOTES-MANAGER/services/llm_entity_extractor.py:204-222` | HIGH |
| Embeddings passes provider to router | `AURA-CHAT/backend/utils/embeddings.py:154-161` | HIGH |
| `ALLOWED_USE_CASES` missing gatekeeper | `AURA-CHAT/server/routers/settings.py:55` | HIGH |
| OpenRouter supports response_mime_type for Gemini | OpenRouter API docs (verified 2026-03) | HIGH |
| NOTES-MANAGER has no settings.py router | File search confirmed absence | HIGH |
