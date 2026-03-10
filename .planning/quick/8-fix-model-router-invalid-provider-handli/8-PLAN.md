---
phase: quick
plan: 8
type: execute
wave: 1
depends_on: []
files_modified:
  - shared/model_router/tests/test_router.py
  - shared/model_router/tests/test_openrouter_provider.py
  - shared/model_router/src/model_router/router.py
  - shared/model_router/src/model_router/providers/openrouter.py
autonomous: true
must_haves:
  truths:
    - Invalid provider strings passed to router metadata APIs fail with shared router errors instead of raw enum coercion exceptions.
    - OpenRouter metadata auth failures from both `/models` and `/auth/key` surface as `AuthenticationError`.
    - OpenRouter metadata rate-limit failures from both `/models` and `/auth/key` surface as `RateLimitError`.
  artifacts:
    - path: shared/model_router/src/model_router/router.py
      provides: Guarded provider coercion for metadata APIs
      contains: get_provider/list_models/health_check invalid-provider handling
    - path: shared/model_router/src/model_router/providers/openrouter.py
      provides: HTTP status-aware metadata error mapping for OpenRouter REST endpoints
      contains: _map_openrouter_error handling for httpx metadata failures
    - path: shared/model_router/tests/test_router.py
      provides: Regression coverage for invalid provider strings in metadata APIs
      min_lines: 360
    - path: shared/model_router/tests/test_openrouter_provider.py
      provides: Regression coverage for OpenRouter metadata HTTP auth/rate-limit classification
      min_lines: 265
  key_links:
    - from: shared/model_router/src/model_router/router.py
      to: shared/model_router/tests/test_router.py
      via: invalid provider string coverage for get_provider/list_models/health_check
      pattern: ModelUnavailableError
    - from: shared/model_router/src/model_router/providers/openrouter.py
      to: shared/model_router/tests/test_openrouter_provider.py
      via: shared mapping for `/models` and `/auth/key` HTTP status failures
      pattern: HTTPStatusError|AuthenticationError|RateLimitError
---

<objective>
Harden shared model router metadata surfaces against invalid provider input and make OpenRouter metadata HTTP failures classify consistently.

Purpose: Phase 9 exposed router metadata APIs publicly, so these paths must no longer leak raw provider-coercion errors and must normalize OpenRouter REST metadata failures the same way generation errors are normalized.

Output: Guarded metadata API behavior in `ModelRouter`, consistent OpenRouter metadata error mapping, and focused regression coverage in the shared package tests.
</objective>

<execution_context>
@C:/Users/Peter/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/Peter/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/phases/09-openrouter-streaming/09-01-SUMMARY.md
@.planning/phases/09-openrouter-streaming/09-03-SUMMARY.md
@shared/model_router/src/model_router/router.py
@shared/model_router/src/model_router/providers/openrouter.py
@shared/model_router/tests/test_router.py
@shared/model_router/tests/test_openrouter_provider.py

## Locked implementation constraints

- Scope stays inside `shared/model_router` only.
- Guard invalid provider strings in router metadata APIs (`get_provider`, `list_models`, `health_check`).
- Map OpenRouter metadata HTTP auth/rate-limit failures consistently for both `/models` and `/auth/key`.
- Use the root `.venv` for Python verification commands.

## Existing behavior to preserve

- Slash-form model IDs still route to OpenRouter.
- `health_check(provider=<valid but unregistered provider>)` should keep returning `{ProviderType.X: False}`.
- Existing OpenAI-SDK exception mapping in `_map_openrouter_error()` should remain intact for generation/streaming paths.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add regression coverage for metadata-provider guards and HTTP classification</name>
  <files>shared/model_router/tests/test_router.py, shared/model_router/tests/test_openrouter_provider.py</files>
  <action>Add focused failing tests before implementation. In `shared/model_router/tests/test_router.py`, add coverage proving `get_provider('invalid-provider')`, `list_models(provider='invalid-provider')`, and `health_check(provider='invalid-provider')` do not leak raw `ValueError`; require `ModelUnavailableError` that preserves the invalid provider string for debugging. Keep the existing valid-but-unregistered `health_check()` expectation unchanged. In `shared/model_router/tests/test_openrouter_provider.py`, add metadata-path tests for `list_models()` and `get_credit_balance()` using mocked `httpx.AsyncClient` / `HTTPStatusError` responses so 401/403 map to `AuthenticationError` and 429 maps to `RateLimitError`. Reuse both metadata endpoints in assertions so the contract is consistent, and avoid live network calls.</action>
  <verify>D:\Peter\AURA Twin Proj\AURA-PROJ\.venv\Scripts\python.exe -m pytest shared/model_router/tests/test_router.py shared/model_router/tests/test_openrouter_provider.py -v</verify>
  <done>New regression tests exist for invalid metadata providers and OpenRouter metadata HTTP auth/rate-limit failures, and they fail until the production fix is implemented.</done>
</task>

<task type="auto">
  <name>Task 2: Implement guarded metadata routing and shared OpenRouter metadata error mapping</name>
  <files>shared/model_router/src/model_router/router.py, shared/model_router/src/model_router/providers/openrouter.py</files>
  <action>Update `shared/model_router/src/model_router/router.py` so all public metadata APIs use guarded provider coercion instead of leaking enum `ValueError`. Invalid provider strings must raise `ModelUnavailableError` with the original string attached; do not change routing for valid providers or generation/embed flows beyond shared helper reuse if needed. Then update `shared/model_router/src/model_router/providers/openrouter.py` so `_map_openrouter_error()` also classifies `httpx.HTTPStatusError` from metadata REST endpoints: 401/403 as `AuthenticationError`, 429 as `RateLimitError` (include `Retry-After` when available), and leave non-target statuses on the existing generic path unless an existing shared error already fits better. Reuse this mapping in both `list_models()` and `get_credit_balance()` so `/models` and `/auth/key` behave identically.</action>
  <verify>D:\Peter\AURA Twin Proj\AURA-PROJ\.venv\Scripts\python.exe -m pytest shared/model_router/tests/test_router.py shared/model_router/tests/test_openrouter_provider.py -v</verify>
  <done>Router metadata APIs reject invalid provider strings with `ModelUnavailableError`, OpenRouter metadata 401/403/429 failures are normalized consistently across both REST metadata endpoints, and the focused shared-package pytest suite passes from the root `.venv`.</done>
</task>

</tasks>

<verification>
- Invalid provider strings passed to `get_provider`, `list_models`, and `health_check` no longer surface raw enum coercion exceptions.
- OpenRouter metadata auth failures from `/models` and `/auth/key` both raise `AuthenticationError`.
- OpenRouter metadata 429 failures from `/models` and `/auth/key` both raise `RateLimitError`.
- Focused shared model_router regression tests pass via the root `.venv` interpreter.
</verification>

<success_criteria>
- `shared/model_router/tests/test_router.py` proves metadata APIs guard invalid provider strings with shared router errors.
- `shared/model_router/tests/test_openrouter_provider.py` proves metadata HTTP 401/403/429 classification is consistent across `/models` and `/auth/key`.
- `shared/model_router/src/model_router/router.py` and `shared/model_router/src/model_router/providers/openrouter.py` implement the contract without changing unrelated routing behavior.
</success_criteria>

<output>
After completion, create `.planning/quick/8-fix-model-router-invalid-provider-handli/8-SUMMARY.md`
</output>
