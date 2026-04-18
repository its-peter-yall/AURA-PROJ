---
phase: 01
plan: 05
wave: 3
depends_on: ["02", "03", "04"]
files_modified:
  - AURA-CHAT/client/src/features/settings/components/ChatModelsSection.test.tsx
  - AURA-CHAT/client/src/features/chat/ChatPage.test.tsx
  - shared/model_router/tests/test_settings_store.py
  - shared/model_router/tests/test_multi_model_config.py
autonomous: true
requirements: null
---

# Plan 05: Integration & Tests — End-to-End Wiring Verification

## Objective

Write integration-level tests that verify the full multi-model configuration flow: SettingsStore → API → Frontend → ChatPage. These tests ensure that backend changes, API endpoints, and frontend components work together correctly, and guard against regressions in the multi-model and backward-compatibility paths.

## Context

Plans 01-04 implemented the full feature: SettingsStore multi-model methods (Plan 01), REST API endpoints (Plan 02), ChatModelsSection UI (Plan 03), and ChatPage integration (Plan 04). This plan writes the integration and component tests that verify the end-to-end wiring works correctly, including backward compatibility, cache invalidation, and edge cases.

## Tasks

### Task 1: Verify SettingsStore backward compatibility regression tests

**Type:** Testing
**read_first:**
  - shared/model_router/tests/test_settings_store.py (full file — understand existing tests)
  - shared/model_router/tests/test_multi_model_config.py (full file — understand new tests from Plan 01)
  - shared/model_router/src/model_router/settings_store.py (verify `set_chat_models` and `get_chat_models_config` signatures)

**action:**
1. Open `shared/model_router/tests/test_settings_store.py` and verify no existing tests are broken by the new multi-model methods.
2. Open `shared/model_router/tests/test_multi_model_config.py` and add one additional regression test:

   **Test `test_set_chat_models_does_not_break_get_defaults`:**
   - Set chat config via `set_chat_models([{"provider": "openrouter", "model": "openai/gpt-4o-mini"}, {"provider": "vertex_ai", "model": "gemini-2.5-flash"}], default_index=0)`
   - Also set an unrelated use case: `set_default("embeddings", "vertex_ai", "text-embedding-004")`
   - Call `await store.get_defaults()` and verify it returns both `chat` and `embeddings` entries
   - Verify `chat` entry still has `provider` and `model` fields (backward compat)
   - Verify `embeddings` entry is `{"provider": "vertex_ai", "model": "text-embedding-004"}`

3. Run `python -m pytest shared/model_router/tests/test_settings_store.py shared/model_router/tests/test_multi_model_config.py -x` to confirm all tests pass.

**acceptance_criteria:**
- `test_set_chat_models_does_not_break_get_defaults` test exists in `test_multi_model_config.py`
- Test verifies that `get_defaults()` includes both multi-model `chat` entry and single-model `embeddings` entry
- All existing `test_settings_store.py` tests still pass
- All `test_multi_model_config.py` tests pass

### Task 2: Write component test for ChatModelsSection

**Type:** Testing
**read_first:**
  - AURA-CHAT/client/src/features/settings/components/ChatModelsSection.tsx (the component created in Plan 03)
  - AURA-CHAT/client/src/features/settings/hooks/useSettingsApi.ts (understand hook signatures)
  - AURA-CHAT/client/vitest.config.ts (understand test setup, mocking)

**action:**
1. Create file `AURA-CHAT/client/src/features/settings/components/ChatModelsSection.test.tsx`.
2. Write the following Vitest test cases using `@testing-library/react` and mocking TanStack Query hooks:

   **Test `test_renders_loading_state`:**
   - Mock `useChatModelsConfig` to return `{ isLoading: true }`
   - Render `<ChatModelsSection />`
   - Assert skeleton/loading indicator is displayed

   **Test `test_renders_existing_config`:**
   - Mock `useChatModelsConfig` to return `{ data: { models: [{provider: "vertex_ai", model: "gemini-2.5-flash"}, {provider: "openrouter", model: "openai/gpt-4o-mini"}], default_index: 0 }, isSuccess: true }`
   - Render `<ChatModelsSection />`
   - Assert both model names are visible in the document
   - Assert the default model indicator (Star icon) is shown next to `gemini-2.5-flash`

   **Test `test_add_model_disabled_at_limit`:**
   - Mock `useChatModelsConfig` to return data with 5 models
   - Render `<ChatModelsSection />`
   - Assert the add-model picker has `pointer-events: none` or `disabled` state (opacity-50 check)

   **Test `test_remove_model_disabled_with_one`:**
   - Mock `useChatModelsConfig` to return data with 1 model
   - Render `<ChatModelsSection />`
   - Assert the remove button is disabled

   **Test `test_set_default_updates_default_index`:**
   - Mock `useChatModelsConfig` with 3 models, `default_index: 0`
   - Render `<ChatModelsSection />`
   - Click the "set as default" button on the second model
   - Assert `defaultIndex` state updates (internal state, verified by the default indicator moving)

   **Test `test_save_calls_mutation`:**
   - Mock `useUpdateChatModels` to return a spy mutation
   - Render `<ChatModelsSection />` with existing config
   - Modify the model list (add or remove a model)
   - Click save
   - Assert `updateChatModels.mutate` was called with `{ models: [...], default_index: N }`

3. Use `vi.mock` to mock hooks and API calls, `vi.fn()` for mutation spies.
4. Follow existing test patterns in the codebase (Vitest + testing-library).
5. Add mandatory TypeScript file header.

**acceptance_criteria:**
- File `AURA-CHAT/client/src/features/settings/components/ChatModelsSection.test.tsx` exists
- 6 test cases are implemented
- `npm run test -- ChatModelsSection` passes (or `npx vitest run ChatModelsSection`)
- Tests mock TanStack Query hooks properly
- Tests verify: loading state, config rendering, 5-model limit, 1-model remove disable, default toggle, save mutation call

### Task 3: Write integration test for ChatPage with multi-model config

**Type:** Testing
**read_first:**
  - AURA-CHAT/client/src/features/chat/ChatPage.tsx (understand config query, allowedModels derivation, model selection)
  - AURA-CHAT/client/src/lib/api.ts (understand `getChatConfig` function)
  - AURA-CHAT/client/src/types/api.ts (understand `ChatConfigResponse` interface)

**action:**
1. Create file `AURA-CHAT/client/src/features/chat/ChatPage.test.tsx` (or add to existing test file if one exists).
2. Write the following tests:

   **Test `test_allowed_models_from_config`:**
   - Mock `useQuery` for `['chatConfig']` to return a `ChatConfigResponse` with `allowed_models: ["gemini-2.5-flash", "openai/gpt-4o-mini", "gemini-2.5-flash-lite"]` and `default_model: "gemini-2.5-flash"`
   - Mock session store, auth store, and other dependencies
   - Render `<ChatPage />`
   - Verify that the `InlineModelPicker` receives `allowedModels` prop with the 3-model array

   **Test `test_effective_model_fallback_to_default`:**
   - Mock config with `allowed_models: ["gemini-2.5-flash", "openai/gpt-4o-mini"]`, `default_model: "gemini-2.5-flash"`
   - Mock `sessionModel` as `"old-deprecated-model"` (not in allowed list)
   - Verify that `effectiveModel` resolves to `"gemini-2.5-flash"` (the default)

   **Test `test_single_model_readonly_picker`:**
   - Mock config with `allowed_models: ["gemini-2.5-flash"]`, `default_model: "gemini-2.5-flash"`
   - Render `<ChatPage />`
   - Find the `InlineModelPicker` button element
   - Assert it has attribute `disabled` or class indicating read-only state

3. Mock external dependencies (API calls, auth store, session hooks) to isolate the ChatPage component logic.
4. Add mandatory file header.

**acceptance_criteria:**
- File `AURA-CHAT/client/src/features/chat/ChatPage.test.tsx` exists (or tests are added to existing ChatPage test file)
- 3 test cases are implemented
- Tests mock the `['chatConfig']` query properly with `ChatConfigResponse` data
- Tests verify: `allowedModels` prop forwarding, model fallback logic, single-model read-only state

### Task 4: Run full test suite and fix any regressions

**Type:** Verification
**read_first:**
  - All modified files from Plans 01-04

**action:**
1. Run the backend test suite:
   ```bash
   python -m pytest shared/model_router/tests/ -x
   ```
   Fix any failures.

2. Run the API test suite (if fast API tests exist):
   ```bash
   python -m pytest AURA-CHAT/tests/api/ -x
   ```
   Fix any failures.

3. Run the frontend type check:
   ```bash
   cd AURA-CHAT/client && npx tsc --noEmit
   ```
   Fix any type errors.

4. Run the frontend linter:
   ```bash
   cd AURA-CHAT/client && npm run lint
   ```
   Fix any lint errors.

5. Run the frontend build:
   ```bash
   cd AURA-CHAT/client && npm run build
   ```
   Fix any build errors.

6. Run the frontend unit tests:
   ```bash
   cd AURA-CHAT/client && npm run test
   ```
   Fix any test failures.

**acceptance_criteria:**
- `python -m pytest shared/model_router/tests/ -x` exits 0
- `python -m pytest AURA-CHAT/tests/api/ -x` exits 0 (or no API tests to run)
- `cd AURA-CHAT/client && npx tsc --noEmit` exits 0
- `cd AURA-CHAT/client && npm run lint` exits 0
- `cd AURA-CHAT/client && npm run build` exits 0
- `cd AURA-CHAT/client && npm run test` exits 0
- No regressions in existing functionality

## Verification

1. All Python tests pass: `python -m pytest shared/model_router/tests/ AURA-CHAT/tests/ -x`
2. Frontend type check passes: `cd AURA-CHAT/client && npx tsc --noEmit`
3. Frontend build succeeds: `cd AURA-CHAT/client && npm run build`
4. Frontend tests pass: `cd AURA-CHAT/client && npm run test`
5. Manual integration test: Set 3 models in Settings → verify chat page shows only those 3 models → verify default model is pre-selected

## Must-Haves

- Regression test for SettingsStore backward compatibility
- Component tests for ChatModelsSection (6 tests)
- Integration tests for ChatPage with multi-model config (3 tests)
- Full test suite verification with zero regressions

## Success Criteria

- [ ] SettingsStore backward compatibility test passes (`get_defaults` returns both chat and other use cases)
- [ ] ChatModelsSection tests: loading, config render, 5-model limit, 1-model remove disable, default toggle, save mutation
- [ ] ChatPage tests: allowedModels forwarding, model fallback, single-model read-only
- [ ] All Python tests pass
- [ ] TypeScript type check passes
- [ ] Frontend build succeeds
- [ ] Frontend unit tests pass
- [ ] No regressions in existing functionality