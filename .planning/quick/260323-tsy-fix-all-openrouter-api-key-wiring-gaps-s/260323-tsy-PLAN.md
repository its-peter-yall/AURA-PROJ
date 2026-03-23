---
phase: quick-260323
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - shared/model_router/src/model_router/router.py
  - AURA-CHAT/backend/rag_engine.py
  - AURA-CHAT/server/routers/chat.py
  - shared/model_router/src/model_router/settings_store.py
autonomous: true
requirements: []
user_setup: []

must_haves:
  truths:
    - "get_default_router() creates ModelRouter with a KeyManager so UI-stored OpenRouter keys can lazy-register"
    - "rag_engine.set_model() accepts and propagates provider to all internal get_model() calls"
    - "Chat RAG endpoint reads and passes provider from SettingsStore to rag_engine.set_model()"
    - "Chitchat endpoint reads and passes provider from SettingsStore to get_model()"
    - "Env var model overrides (e.g. LLM_ENTITY_EXTRACTION_MODEL=openai/gpt-4o) resolve correct provider"
    - "semantic_router.py confirmed clean — uses embeddings only, no get_model() calls"
    - "Background task pipeline confirmed clean — no get_model() calls in tasks/"
  artifacts:
    - path: "shared/model_router/src/model_router/router.py"
      provides: "KeyManager injection into get_default_router() singleton"
    - path: "AURA-CHAT/backend/rag_engine.py"
      provides: "set_model() provider parameter + all 3 get_model() calls pass provider"
    - path: "AURA-CHAT/server/routers/chat.py"
      provides: "Chat and chitchat paths read provider from SettingsStore and pass through"
    - path: "shared/model_router/src/model_router/settings_store.py"
      provides: "Env var provider detection instead of hardcoded vertex_ai"
  key_links:
    - from: "AURA-CHAT/server/routers/chat.py"
      to: "AURA-CHAT/backend/rag_engine.py"
      via: "rag_engine.set_model(model, provider=provider)"
      pattern: "set_model.*provider"
    - from: "AURA-CHAT/backend/rag_engine.py"
      to: "backend/utils/vertex_ai_client.py"
      via: "get_model(model, provider=provider)"
      pattern: "get_model.*provider"
    - from: "shared/model_router/src/model_router/router.py"
      to: "shared/model_router/src/model_router/key_manager.py"
      via: "KeyManager injection in get_default_router()"
      pattern: "KeyManager"
---

<objective>
Fix all 8 OpenRouter API key wiring gaps so that provider selection from the Settings page flows correctly through the entire stack: settings → chat router → rag_engine → get_model(), and the model_router singleton can lazy-register OpenRouter with UI-stored keys.

Purpose: The v1.2 Settings Wiring milestone shipped provider+model resolution via `resolve_use_case_config()`, but the chat endpoints and rag_engine only propagated the model name — not the provider. This means OpenRouter models selected in Settings silently fall back to Vertex AI. Additionally, `get_default_router()` never receives a `KeyManager`, preventing lazy OpenRouter registration from UI-stored API keys.

Output: 4 files modified. Provider flows end-to-end from SettingsStore → chat.py → rag_engine.py → get_model().
</objective>

<execution_context>
@~/.config/opencode/get-shit-done/workflows/execute-plan.md
@~/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md

Key interfaces already in place:
- `get_model(model_name: str, provider: str | None = None)` in `backend/utils/vertex_ai_client.py:237`
- `ModelRouter.__init__(config, key_manager: KeyManager | None)` in `shared/model_router/src/model_router/router.py:66`
- `KeyManager.__init__(redis_client)` in `shared/model_router/src/model_router/key_manager.py:37`
- `SettingsStore.get_default(use_case)` returns `{"provider": str, "model": str} | None`
- `resolve_use_case_config()` already resolves provider correctly from SettingsStore/Redis
- `llm_gatekeeper.py` and `llm_entity_extractor.py` already pass provider correctly
- Background tasks (`backend/tasks/`) confirmed: no `get_model()` calls — clean
- `semantic_router.py` confirmed: uses embeddings only, no `get_model()` calls — clean
</context>

<tasks>

<task type="auto">
  <name>Task 1: Wire KeyManager into get_default_router() singleton</name>
  <files>shared/model_router/src/model_router/router.py</files>
  <action>
In `get_default_router()` (lines 469-474), create a `KeyManager` from the Redis client and pass it to `ModelRouter(RouterConfig.from_env(), key_manager=km)`.

Changes:
- Import `KeyManager` from `model_router.key_manager` at top of file (or inline in function)
- Import `get_redis` or use a compatible Redis client factory. Check existing project pattern: `from model_router.settings_store import get_redis` or `from backend.utils.config import get_redis_client`. Use the project's Redis factory.
- In `get_default_router()`:
  ```python
  def get_default_router() -> ModelRouter:
      """Return a process-wide router singleton built from environment config."""
      global _default_router
      if _default_router is None:
          _km = None
          try:
              from model_router.key_manager import KeyManager
              import redis.asyncio as aioredis
              import os
              _redis = aioredis.from_url(os.getenv("REDIS_URL", "redis://127.0.0.1:6379"))
              _km = KeyManager(_redis)
          except Exception:
              logger.debug("KeyManager unavailable for default router", exc_info=True)
          _default_router = ModelRouter(RouterConfig.from_env(), key_manager=_km)
      return _default_router
  ```
  - Wrap KeyManager creation in try/except so the singleton still works without AURA_MASTER_KEY or Redis
  - If KeyManager creation fails, log at debug level and continue with `key_manager=None`
  </action>
  <verify>
<automated>python -c "from shared.model_router.src.model_router.router import get_default_router; r = get_default_router(); print('KeyManager:', r._key_manager is not None)"</automated>
  </verify>
  <done>get_default_router() creates ModelRouter with KeyManager when AURA_MASTER_KEY and Redis are available; falls back gracefully to key_manager=None otherwise</done>
</task>

<task type="auto">
  <name>Task 2: Add provider parameter to RAGEngine.set_model() and propagate</name>
  <files>AURA-CHAT/backend/rag_engine.py</files>
  <action>
Modify `set_model()` signature and all 3 internal `get_model()` calls to pass `provider`.

Changes to `set_model()` (line 177):
- Change signature from `def set_model(self, model_name: Optional[str]) -> str:` to `def set_model(self, model_name: Optional[str], provider: Optional[str] = None) -> str:`
- Line 169: `self.model = get_model(requested_model)` → `self.model = get_model(requested_model, provider=provider)`
- Line 189: `self.model = get_model(requested)` → `self.model = get_model(requested, provider=provider)`
- Line 211: `self.model = get_model(default_model)` → `self.model = get_model(default_model, provider=provider)`

Also update the `__init__` path (line 169) to accept and pass provider if it's in a set_model call path. The init at line 169 is inside `__init__` — check if it calls set_model or does inline model init. If inline, add provider parameter to `__init__` as well. Based on the code, line 169 is in `__init__` directly — also add `provider: Optional[str] = None` parameter there and pass it through.

Update docstring to document the new provider parameter.
  </action>
  <verify>
<automated>cd AURA-CHAT && python -c "from backend.rag_engine import RAGEngine; import inspect; sig = inspect.signature(RAGEngine.set_model); print('provider' in sig.parameters)"</automated>
  </verify>
  <done>set_model() accepts optional provider parameter; all internal get_model() calls pass provider through</done>
</task>

<task type="auto">
  <name>Task 3: Wire provider from SettingsStore through chat endpoints</name>
  <files>AURA-CHAT/server/routers/chat.py</files>
  <action>
Read provider from SettingsStore defaults and pass to rag_engine.set_model() / get_model().

**Chat RAG path** (around lines 367-372):
- Current: `_default = await _store.get_default("chat")` → reads model only
- Fix: Extract both model and provider:
  ```python
  _default = await _store.get_default("chat")
  if _default and _default.get("model"):
      _provider = _default.get("provider")
      rag_engine.set_model(_default["model"], provider=_provider)
      logger.info("Model from admin default: %s (provider: %s)", _default["model"], _provider)
  ```

**Chitchat path** (around lines 227-243):
- Current: reads `_default["model"]` but not `_default["provider"]`, then `model = get_model(model_name)` with no provider
- Fix: Extract provider and pass to get_model:
  ```python
  _default = await _store.get_default("chat")
  if _default and _default.get("model"):
      model_name = _default["model"]
      _provider = _default.get("provider")
      logger.info("Chitchat model from admin default: %s (provider: %s)", model_name, _provider)
  ...
  model = get_model(model_name, provider=_provider if '_provider' in locals() else None)
  ```
  - Initialize `_provider = None` before the if/else block so it's always defined
  - Remove the TODO comment at line 244-246 since provider propagation is now handled
  </action>
  <verify>
<automated>cd AURA-CHAT && python -c "
import ast, sys
with open('server/routers/chat.py') as f:
    src = f.read()
# Verify provider is referenced in the file
count = src.count('provider')
print(f'provider references: {count}')
assert count >= 4, f'Expected >= 4 provider references, found {count}'
print('OK')
"</automated>
  </verify>
  <done>Both chat and chitchat paths read provider from SettingsStore and pass it to get_model/set_model calls</done>
</task>

<task type="auto">
  <name>Task 4: Fix _USE_CASE_ENV_VARS to detect provider from env var model names</name>
  <files>shared/model_router/src/model_router/settings_store.py</files>
  <action>
Fix the env var fallback in `resolve_use_case_config()` (line 162-167) so that when a model name contains a provider prefix (e.g., `openai/gpt-4o`), the provider is extracted from the model name instead of hardcoded to `"vertex_ai"`.

Current code (line 162-167):
```python
env_spec = _USE_CASE_ENV_VARS.get(use_case)
if env_spec:
    env_var, provider = env_spec
    env_model = os.getenv(env_var)
    if env_model:
        return {"provider": provider, "model": env_model}
```

Fix: After getting `env_model`, check if it contains a `/` separator (OpenRouter format `provider/model`):
```python
env_spec = _USE_CASE_ENV_VARS.get(use_case)
if env_spec:
    env_var, default_provider = env_spec
    env_model = os.getenv(env_var)
    if env_model:
        # Detect provider from model name (e.g., "openai/gpt-4o" → provider="openai")
        if "/" in env_model:
            detected_provider, _ = env_model.split("/", 1)
            provider = detected_provider
        else:
            provider = default_provider
        return {"provider": provider, "model": env_model}
```

This preserves backward compatibility: plain model names (e.g., `gemini-2.5-flash-lite`) still get the default provider, while prefixed names (e.g., `openai/gpt-4o`) extract the correct provider.
  </action>
  <verify>
<automated>cd . && python -c "
import os
os.environ['LLM_ENTITY_EXTRACTION_MODEL'] = 'openai/gpt-4o'
from shared.model_router.src.model_router.settings_store import resolve_use_case_config
# Force skip Redis by not having one
result = resolve_use_case_config('entity_extraction', redis_url='redis://invalid:9999')
print('Result:', result)
assert result['provider'] == 'openai', f'Expected openai, got {result[\"provider\"]}'
assert result['model'] == 'openai/gpt-4o', f'Expected openai/gpt-4o, got {result[\"model\"]}'
print('OK - provider correctly detected from env var model name')
"</automated>
  </verify>
  <done>Env var model overrides with provider prefixes (e.g. openai/gpt-4o) resolve correct provider instead of forcing vertex_ai</done>
</task>

</tasks>

<verification>
After all 4 tasks:
1. Run `python -m pytest AURA-CHAT/tests/ -x -q` to ensure no regressions
2. Verify `semantic_router.py` — grep confirms no `get_model()` calls (audit of issue 7)
3. Verify `backend/tasks/` — grep confirms no `get_model()` calls (audit of issue 8)
</verification>

<success_criteria>
- `get_default_router()` includes KeyManager (issue 1)
- `set_model()` accepts `provider` param, all 3 internal `get_model()` calls pass it (issues 4, 5)
- Chat RAG endpoint reads `provider` from SettingsStore, passes to `rag_engine.set_model(model, provider=provider)` (issue 2)
- Chitchat endpoint reads `provider` from SettingsStore, passes to `get_model(model_name, provider=provider)` (issue 3)
- `_USE_CASE_ENV_VARS` fallback detects provider from `provider/model` format env vars (issue 6)
- `semantic_router.py` confirmed clean — no `get_model()` calls (issue 7)
- Background tasks confirmed clean — no `get_model()` calls (issue 8)
- All existing tests pass with no regressions
</success_criteria>

<output>
After completion, create `.planning/phases/quick-260323/quick-260323-01-SUMMARY.md`
</output>
