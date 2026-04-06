# Quick Task: Wire RAGEngine to SettingsStore - Summary

**Task:** Wire AURA-CHAT RAGEngine to read user model settings from Redis SettingsStore
**Completed:** 2026-04-04

## Changes

### AURA-CHAT/server/dependencies.py

**Added import:**
```python
from model_router import resolve_use_case_config
```

**Modified `get_rag_engine()` function:**
- Added call to `resolve_use_case_config("chat")` to read admin default model/provider
- RAGEngine now initialized with `model_name` and `provider` from SettingsStore
- Fallback chain: SettingsStore → env var `LLM_CHAT_MODEL` → hardcoded default

**Before:**
```python
_rag_engine = RAGEngine(graph_manager=graph_manager)
```

**After:**
```python
config = resolve_use_case_config("chat")
_rag_engine = RAGEngine(
    graph_manager=graph_manager,
    model_name=config["model"],
    provider=config["provider"],
)
```

## Provider Propagation Path

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

## Validation Checklist

- [x] Import added for `resolve_use_case_config`
- [x] RAGEngine initialized with model_name and provider from config
- [x] Fallback chain ensures no crashes if Redis is down
- [x] Logs show model/provider on initialization

## Related

- Research: [260404-ke6-RESEARCH.md](./260404-ke6-RESEARCH.md)
- Plan: [260404-ke6-PLAN.md](./260404-ke6-PLAN.md)