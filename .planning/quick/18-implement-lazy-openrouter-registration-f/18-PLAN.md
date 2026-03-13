---
phase: quick/18-implement-lazy-openrouter-registration-f
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - shared/model_router/src/model_router/router.py
  - shared/model_router/tests/test_router.py
autonomous: true

must_haves:
  truths:
    - "OpenRouter provider auto-registers lazily when slash-form model ID is used"
    - "Router fetches API key from Redis via KeyManager when OpenRouter provider is missing"
    - "Lazy registration only happens if KeyManager has a key stored"
    - "Original 'No provider registered' error still thrown if no key available"
  artifacts:
    - path: "shared/model_router/src/model_router/router.py"
      provides: "Lazy OpenRouter auto-registration logic"
      contains: ["_resolve_provider", "_maybe_lazy_register_openrouter", "KeyManager"]
    - path: "shared/model_router/tests/test_router.py"
      provides: "Lazy registration test coverage"
      contains: ["test_lazy_openrouter_registration", "test_lazy_registration_no_key"]
  key_links:
    - from: "ModelRouter._resolve_provider"
      to: "KeyManager.get_key"
      via: "_maybe_lazy_register_openrouter() helper"
      pattern: "key_manager.get_key.*openrouter"
    - from: "KeyManager"
      to: "OpenRouterProvider"
      via: "Lazy registration with fetched key"
      pattern: "OpenRouterProvider.*api_key"
---

<objective>
Enable lazy OpenRouter provider registration from Redis when slash-form model IDs are used but OpenRouter isn't pre-registered at startup.

Purpose: Allow UI-stored API keys (via KeyManager) to work without requiring OPENROUTER_API_KEY env var at router initialization.
Output: Modified router.py with lazy registration logic and comprehensive tests.
</objective>

<execution_context>
@C:/Users/Peter/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/Peter/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@shared/model_router/src/model_router/router.py
@shared/model_router/src/model_router/key_manager.py
@shared/model_router/tests/test_router.py

## Problem Statement
Currently OpenRouter provider only auto-registers at startup if OPENROUTER_API_KEY env var is set. The UI allows users to paste API keys in settings, stored in Redis via KeyManager, but the router never sees these keys.

## Flow to Fix
1. UI stores key in Redis via KeyManager
2. Router initializes without OpenRouter (no env var)
3. Request comes with slash-form model ID (e.g., "anthropic/claude-sonnet-4")
4. Router routes to ProviderType.OPENROUTER
5. But OpenRouter not in _providers dict → "No provider registered" error ❌

## Solution
Modify ModelRouter._resolve_provider() to:
1. Check if OpenRouter provider is missing but needed (slash-form model ID)
2. Fetch key from Redis via KeyManager
3. Auto-register OpenRouter provider if key exists
4. Continue with normal flow
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add lazy OpenRouter registration to ModelRouter</name>
  <files>shared/model_router/src/model_router/router.py</files>
  <action>
Modify ModelRouter class to support lazy OpenRouter auto-registration:

1. Add optional `key_manager` parameter to `__init__()` method and store it as `self._key_manager`

2. Create helper method `_maybe_lazy_register_openrouter()` that:
   - Checks if ProviderType.OPENROUTER is already in self._providers (early return if yes)
   - Checks if self._key_manager is available (early return if no)
   - Fetches key via `await self._key_manager.get_key("openrouter")`
   - If key exists, creates OpenRouterProvider with the fetched key and registers it
   - Logs the lazy registration for debugging

3. Modify `_resolve_provider()` to be async (change return type to `Awaitable[BaseProvider]`):
   - After determining provider type, if it's OPENROUTER and provider is missing
   - Call `await self._maybe_lazy_register_openrouter()` before raising error
   - Re-check self._providers after lazy registration attempt

4. Update all callers of `_resolve_provider()` to await it:
   - `generate()` method
   - `stream()` method  
   - `stream_with_usage()` method
   - Tests that call `_resolve_provider()` directly

5. Add KeyManager import at top of file

Key implementation details:
- Use existing OpenRouterProvider constructor pattern from _should_auto_register_openrouter()
- Import KeyManager with TYPE_CHECKING guard if circular import risk
- Maintain backward compatibility: key_manager is optional parameter
- Lazy registration should happen transparently without changing external API
  </action>
  <verify>
    Run pylint on modified file:
    ```bash
    cd shared/model_router && python -m pylint src/model_router/router.py
    ```
    
    Check for syntax errors:
    ```bash
    cd shared/model_router && python -c "from model_router.router import ModelRouter; print('Import OK')"
    ```
  </verify>
  <done>
    - ModelRouter accepts optional key_manager parameter
    - _maybe_lazy_register_openrouter() method exists and handles async key fetch
    - _resolve_provider() is async and attempts lazy registration
    - All callers updated to await _resolve_provider()
    - No pylint errors
  </done>
</task>

<task type="auto">
  <name>Task 2: Add tests for lazy OpenRouter registration</name>
  <files>shared/model_router/tests/test_router.py</files>
  <action>
Add comprehensive test coverage for lazy OpenRouter registration:

1. Test lazy registration succeeds when key exists in KeyManager:
   - Create router WITHOUT test_mode and WITHOUT openrouter api_key in config
   - Create mock KeyManager with "openrouter" key stored
   - Set key_manager on router
   - Call _resolve_provider() with slash-form model ID
   - Assert OpenRouterProvider is now registered and returned

2. Test lazy registration fails gracefully when no key:
   - Create router without OpenRouter registration
   - Create mock KeyManager with NO "openrouter" key
   - Set key_manager on router
   - Assert ModelUnavailableError is raised with proper message

3. Test lazy registration only runs once:
   - Create router with mock KeyManager
   - Call _resolve_provider() twice
   - Assert get_key() was only called once (provider cached after first call)

4. Test generate() triggers lazy registration:
   - Create router with mock KeyManager containing key
   - Call generate() with slash-form model ID
   - Assert response provider is OPENROUTER (not error)

Mock KeyManager implementation for tests:
```python
class MockKeyManager:
    def __init__(self, keys: dict[str, str]):
        self._keys = keys
    
    async def get_key(self, provider: str) -> str | None:
        return self._keys.get(provider)
```

Add these tests to test_router.py following existing test patterns.
  </action>
  <verify>
    Run the new tests:
    ```bash
    cd shared/model_router && python -m pytest tests/test_router.py -v -k "lazy"
    ```
    
    Run all router tests to ensure no regressions:
    ```bash
    cd shared/model_router && python -m pytest tests/test_router.py -v
    ```
  </verify>
  <done>
    - Test lazy registration with key present passes
    - Test lazy registration without key raises ModelUnavailableError
    - Test lazy registration caches provider (called once)
    - Test generate() triggers lazy registration end-to-end
    - All existing tests still pass
  </done>
</task>

</tasks>

<verification>
After both tasks complete, verify:
1. ModelRouter can accept KeyManager for lazy registration
2. Slash-form model IDs work without OPENROUTER_API_KEY env var
3. Keys stored via KeyManager are fetched and used for lazy registration
4. All existing tests pass
5. New lazy registration tests pass
</verification>

<success_criteria>
- OpenRouter provider auto-registers when slash-form model ID is used and KeyManager has key
- Router works with UI-stored API keys without env var at startup
- Proper error handling when no key available (ModelUnavailableError)
- All tests pass including new lazy registration tests
- No breaking changes to existing API
</success_criteria>

<output>
After completion, create `.planning/quick/18-implement-lazy-openrouter-registration-f/18-01-SUMMARY.md`
</output>
