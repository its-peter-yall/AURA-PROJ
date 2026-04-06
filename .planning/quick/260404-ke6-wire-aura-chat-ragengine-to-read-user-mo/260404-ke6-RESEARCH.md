# Quick Task: Wire RAGEngine to SettingsStore - Research

**Researched:** 2026-04-04
**Task:** Wire AURA-CHAT RAGEngine to read user model settings from Redis SettingsStore
**Confidence:** HIGH

## Summary

The RAGEngine singleton is currently initialized in `server/dependencies.py` without model/provider settings, causing it to fall back to environment-based defaults. The chat router (`chat.py`) already demonstrates the correct pattern for reading from SettingsStore at request time (lines 598-607). The fix requires wiring SettingsStore into the dependency injection layer at RAGEngine initialization time.

**Primary recommendation:** Use `resolve_use_case_config("chat")` in `get_rag_engine()` dependency to read model/provider at initialization, with sync fallback for startup.

## Integration Points

### 1. Current RAGEngine Initialization (server/dependencies.py:130-143)

```python
def get_rag_engine() -> RAGEngine:
    global _rag_engine
    if _rag_engine is None:
        logger.info("Initializing RAGEngine singleton...")
        graph_manager = get_graph_manager()
        _rag_engine = RAGEngine(graph_manager=graph_manager)  # <-- No model/provider
        logger.info("RAGEngine initialized successfully")
    return _rag_engine
```

**Problem:** RAGEngine is created without model/provider, so `set_model()` falls back to `config.RAG_MODEL_DEFAULT` with `provider=None`.

### 2. Working Pattern in Chat Router (server/routers/chat.py:598-607)

```python
_store = SettingsStore(get_redis())
_default = await _store.get_default("chat")
if _default and _default.get("model"):
    _provider = _default.get("provider")
    rag_engine.set_model(_default["model"], provider=_provider)
    logger.info(
        "Model from admin default: %s (provider: %s)",
        _default["model"],
        _provider,
    )
```

**This pattern works per-request but runs on every chat call.**

### 3. SettingsStore API (shared/model_router/src/model_router/settings_store.py)

| Method | Sync/Async | Use Case |
|--------|------------|----------|
| `get_default_sync(use_case)` | Sync | Startup/initialization contexts |
| `SettingsStore.get_default(use_case)` | Async | Request-time reads |
| `resolve_use_case_config(use_case)` | Sync | **Recommended** - Has fallback chain |

**Resolution order for `resolve_use_case_config("chat")`:**
1. Redis SettingsStore (authoritative)
2. Environment variable `LLM_CHAT_MODEL`
3. Hardcoded default `{"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"}`

## Recommended Implementation

### Option A: Read at Initialization (Recommended)

Modify `server/dependencies.py`:

```python
from model_router import resolve_use_case_config

def get_rag_engine() -> RAGEngine:
    global _rag_engine
    if _rag_engine is None:
        logger.info("Initializing RAGEngine singleton...")
        graph_manager = get_graph_manager()

        # Read admin default at startup with fallback chain
        config = resolve_use_case_config("chat")
        _rag_engine = RAGEngine(
            graph_manager=graph_manager,
            model_name=config["model"],
            provider=config["provider"],
        )
        logger.info(
            "RAGEngine initialized with model=%s, provider=%s",
            config["model"],
            config["provider"],
        )
    return _rag_engine
```

**Pros:**
- Settings read once at startup
- Fallback chain ensures no crashes if Redis is down
- Consistent with other initialization patterns

**Cons:**
- Requires server restart to pick up new admin settings
- Settings cached in RAGEngine singleton

### Option B: Lazy Reconfiguration (Alternative)

Add a method to RAGEngine to refresh settings:

```python
# In RAGEngine class
def refresh_from_settings(self) -> None:
    """Re-read model settings from SettingsStore."""
    config = resolve_use_case_config("chat")
    self.set_model(config["model"], provider=config["provider"])
```

Call this periodically or via admin endpoint.

## Key Constraints

1. **Sync vs Async**: `get_rag_engine()` is synchronous (FastAPI `Depends`), so must use `resolve_use_case_config()` or `get_default_sync()`, not the async `SettingsStore.get_default()`.

2. **Caching**: SettingsStore has 5-minute cache TTL for valid entries, 30s for error entries. This is acceptable for startup-time reads.

3. **Fallback Safety**: `resolve_use_case_config()` NEVER returns None and NEVER raises on Redis failure - it always returns a valid `{provider, model}` dict.

4. **sessions.py Compatibility**: The legacy `backend/routers/sessions.py` uses the same RAGEngine singleton, so fixing `server/dependencies.py` fixes both paths.

## Provider Propagation Path

The provider must flow through these layers:

```
SettingsStore (Redis)
    ↓ resolve_use_case_config("chat")
server/dependencies.py (get_rag_engine)
    ↓ RAGEngine(model_name=..., provider=...)
RAGEngine.__init__ / set_model
    ↓ self._provider = provider
generate_content_stream() call
    ↓ provider=self._provider
vertex_ai_client.py
    ↓ get_model(model_name, provider=provider)
ModelRouter (routes to correct provider)
```

**Current break:** `dependencies.py` doesn't pass provider → RAGEngine stores `None` → model router can't route OpenRouter models.

## Common Pitfalls

### Pitfall 1: Using Async Method in Sync Context
**Wrong:** `await SettingsStore(redis).get_default("chat")` in `get_rag_engine()`
**Correct:** `resolve_use_case_config("chat")` (sync with fallbacks)

### Pitfall 2: Not Passing Provider to set_model
**Wrong:** `rag_engine.set_model(model_name)` (provider defaults to None)
**Correct:** `rag_engine.set_model(model_name, provider=provider)`

### Pitfall 3: Assuming Provider from Model Name
OpenRouter models like `openai/gpt-4o` contain provider prefix, but Vertex models like `gemini-2.5-flash-lite` do not. Always use the `provider` field from SettingsStore.

## Files to Modify

| File | Change |
|------|--------|
| `AURA-CHAT/server/dependencies.py` | Import `resolve_use_case_config`, use in `get_rag_engine()` |

## Validation

After implementation:
1. Start server with Redis running
2. Set admin default: `SettingsStore(redis).set_default("chat", "openrouter", "anthropic/claude-3.5-sonnet")`
3. Restart server
4. Check logs: `RAGEngine initialized with model=anthropic/claude-3.5-sonnet, provider=openrouter`
5. Verify chat works without "No provider registered" error

## Sources

- Primary: Code review of `server/dependencies.py`, `server/routers/chat.py`, `backend/rag_engine.py`
- Secondary: `shared/model_router/src/model_router/settings_store.py` API documentation
