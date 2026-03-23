---
phase: quick-260323
plan: 01
subsystem: model_router
tags:
  - openrouter
  - provider-wiring
  - settings
  - api-key
dependency_graph:
  requires:
    - KeyManager (shared/model_router)
    - SettingsStore (Redis)
    - get_model() (vertex_ai_client)
  provides:
    - End-to-end provider propagation from Settings → chat → rag_engine → get_model()
    - KeyManager injection in get_default_router() singleton
  affects:
    - AURA-CHAT chat endpoints (RAG + chitchat)
    - RAGEngine model selection
    - Env var model overrides
tech-stack:
  added: []
  patterns:
    - Provider parameter propagation chain
    - Env var model name prefix detection (openai/gpt-4o)
    - Graceful KeyManager fallback (try/except)
key-files:
  created: []
  modified:
    - shared/model_router/src/model_router/router.py
    - AURA-CHAT/backend/rag_engine.py
    - AURA-CHAT/server/routers/chat.py
    - shared/model_router/src/model_router/settings_store.py
decisions:
  - Inline KeyManager import in get_default_router() to avoid circular deps
  - Try/except KeyManager creation for graceful fallback when Redis unavailable
  - Provider detection from model name prefix preserves backward compatibility
metrics:
  duration: ~3 minutes
  completed: 2026-03-23T16:01:31Z
  tasks_completed: 4
  files_modified: 4
  commits: 4
---

# Phase quick-260323 Plan 01: Fix All OpenRouter API Key Wiring Gaps Summary

## One-Liner

Provider selection from Settings page now flows end-to-end through the entire stack: SettingsStore → chat.py → rag_engine.py → get_model(), with KeyManager injection enabling lazy OpenRouter registration from UI-stored keys.

## Task Summary

| # | Task | Commit | Status |
|---|------|--------|--------|
| 1 | Wire KeyManager into get_default_router() singleton | e2cd844 | Done |
| 2 | Add provider parameter to RAGEngine.set_model() and propagate | b82e471 | Done |
| 3 | Wire provider from SettingsStore through chat endpoints | efc84b8 | Done |
| 4 | Fix _USE_CASE_ENV_VARS to detect provider from env var model names | 8eba994 | Done |

## What Was Built

### Task 1: KeyManager injection (router.py)

`get_default_router()` now creates a `KeyManager` from Redis and passes it to `ModelRouter`. This enables lazy OpenRouter registration when users store API keys via the Settings UI — the router can look up the key from KeyManager at request time instead of requiring `OPENROUTER_API_KEY` env var at startup.

Wrapped in try/except so the singleton still works without Redis or `AURA_MASTER_KEY`.

### Task 2: RAGEngine provider propagation (rag_engine.py)

`set_model()` now accepts an optional `provider` parameter and passes it to all 3 internal `get_model()` calls. The `__init__` method also accepts `provider` and threads it through.

### Task 3: Chat endpoint provider wiring (chat.py)

Both the non-streaming `chat()` endpoint and the streaming `stream_chat()` endpoint now:
- Read `_default.get("provider")` from SettingsStore alongside the model
- Pass `provider=_provider` to `rag_engine.set_model()`

The chitchat path (`stream_chitchat_response()`) also extracts and passes provider to `get_model()`. The TODO comment about provider propagation has been removed.

### Task 4: Env var provider detection (settings_store.py)

`resolve_use_case_config()` now detects provider from model name prefixes. When an env var like `LLM_ENTITY_EXTRACTION_MODEL=openai/gpt-4o` is set, the provider is extracted as `"openai"` instead of being hardcoded to `"vertex_ai"`. Plain model names (no `/`) still get the default provider.

## Verified Clean

- **Issue 7**: `semantic_router.py` — confirmed no `get_model()` calls (uses embeddings only)
- **Issue 8**: `backend/tasks/` — confirmed no `get_model()` calls (background tasks are clean)

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

All 4 files modified, all 4 commits exist, all verification checks pass.
