---
phase: 01
plan: 04
wave: 2
depends_on: ["02", "03"]
files_modified:
  - AURA-CHAT/client/src/types/api.ts
  - AURA-CHAT/client/src/features/chat/ChatPage.tsx
  - AURA-CHAT/client/src/features/chat/components/InlineModelPicker.tsx
autonomous: true
requirements: null
---

# Plan 04: Frontend — Chat Page Integration with Multi-Model Config

## Objective

Update the chat page (`ChatPage.tsx`) to consume the `allowed_models` array and `default_model` from the `/chat/config` API response, passing `allowedModels` to `InlineModelPicker` and initializing new sessions with the admin-configured default model. Also ensure `InlineModelPicker` correctly handles the case when `allowedModels` has exactly 1 model (read-only mode) and prefers admin-configured models.

## Context

Plans 01-03 established the backend multi-model config and frontend settings UI. The `/chat/config` endpoint already returns `allowed_models` and `default_model`. Currently `ChatPage.tsx` constructs `allowedModels` as `[config.default_model]` (single-element array) at line 255. This plan changes that to use the full `allowed_models` array from the config response. The `InlineModelPicker` already accepts an `allowedModels` prop and handles `isReadOnly` when length is 1.

## Tasks

### Task 1: Update `ChatConfigResponse` type to include `allowed_models` array

**Type:** Implementation
**read_first:**
  - AURA-CHAT/client/src/types/api.ts (lines 134-143 — current `ChatConfigResponse` interface)

**action:**
1. Open `AURA-CHAT/client/src/types/api.ts` and find the `ChatConfigResponse` interface.
2. The `allowed_models` field is already typed as `string[]` — verify this is correct. No change needed if already correct.
3. Verify `default_model` is typed as `string` — no change needed if already correct.

**acceptance_criteria:**
- `ChatConfigResponse.allowed_models` is typed as `string[]`
- `ChatConfigResponse.default_model` is typed as `string`
- No regression to existing type definitions

### Task 2: Update `ChatPage` to use `allowed_models` from config

**Type:** Implementation
**read_first:**
  - AURA-CHAT/client/src/features/chat/ChatPage.tsx (full file — especially lines 107-111 for config query, line 255 for current `allowedModels` derivation, lines 257-260 for model selection logic, lines 661-666 for InlineModelPicker usage)
  - AURA-CHAT/client/src/stores/useModelStore.ts (understand session-model persistence)
  - AURA-CHAT/client/src/features/chat/components/InlineModelPicker.tsx (understand `allowedModels` prop)

**action:**
1. Open `AURA-CHAT/client/src/features/chat/ChatPage.tsx`.
2. Replace the current `allowedModels` derived state (line 255):

   Current:
   ```typescript
   const allowedModels = config?.default_model ? [config.default_model] : undefined;
   ```

   New:
   ```typescript
   const allowedModels = config?.allowed_models && config.allowed_models.length > 0
       ? config.allowed_models
       : undefined;
   ```

   This uses the full `allowed_models` array from the backend config (which is now populated from the admin multi-model settings). When `undefined`, InlineModelPicker shows all available models (existing fallback behavior).

3. Replace the `effectiveModel` derivation (line 257-260):

   Current:
   ```typescript
   let effectiveModel = configState.model || sessionModel || config?.default_model || '';
   if (allowedModels && !allowedModels.includes(effectiveModel) && config?.default_model) {
       effectiveModel = config.default_model;
   }
   ```

   New:
   ```typescript
   let effectiveModel = configState.model || sessionModel || config?.default_model || '';
   if (allowedModels && !allowedModels.includes(effectiveModel)) {
       effectiveModel = config?.default_model || (allowedModels.length > 0 ? allowedModels[0] : '');
   }
   ```

   This ensures that if the user's stored session model is not in the admin-allowed list, we fall back to the configured default model. If no default, fall back to the first allowed model.

4. No other changes needed — the `InlineModelPicker` component already accepts `allowedModels` as a prop and already handles the `isReadOnly` case when `allowedModels.length === 1`.

**acceptance_criteria:**
- `ChatPage.tsx` derives `allowedModels` from `config.allowed_models` array (not from single `config.default_model`)
- If `config.allowed_models` is empty or undefined, `allowedModels` is `undefined` (shows all models)
- `effectiveModel` falls back to `config.default_model` or first allowed model when stored model is invalid
- `InlineModelPicker` receives `allowedModels` prop correctly (no changes needed to InlineModelPicker)

### Task 3: Ensure `InlineModelPicker` handles `allowedModels` with multi-provider models correctly

**Type:** Verification/Minor Enhancement
**read_first:**
  - AURA-CHAT/client/src/features/chat/components/InlineModelPicker.tsx (full file — especially lines 57-59 for the filtering logic)
  - AURA-CHAT/client/src/features/chat/ChatPage.tsx (understand how `allowedModels` is passed)

**action:**
1. Open `AURA-CHAT/client/src/features/chat/components/InlineModelPicker.tsx`.
2. Review the `allowedModels` filter logic at lines 57-60:
   ```typescript
   const models = useMemo(() => {
       if (!allowedModels || allowedModels.length === 0) return allModels;
       return allModels.filter(m => allowedModels.includes(m.name));
   }, [allModels, allowedModels]);
   ```
3. Verify this correctly filters `allModels` by `m.name` matching entries in the `allowedModels` string array. The `allowed_models` from backend contains model name strings (e.g., `"gemini-2.5-flash"`, `"openai/gpt-4o-mini"`), and `m.name` is the model identifier. This should work correctly.
4. Verify the `isReadOnly` logic at line 115:
   ```typescript
   const isReadOnly = allowedModels?.length === 1;
   ```
   When admin configures only 1 model, this renders the picker as read-only (no dropdown arrow, no click to open). This is correct per UI-SPEC.md.
5. No code changes required unless bugs are found during verification.

**acceptance_criteria:**
- `InlineModelPicker` correctly filters models by name matching `allowedModels` array
- `isReadOnly` is `true` when `allowedModels.length === 1` (single model — no dropdown)
- `isReadOnly` is `false` when `allowedModels.length > 1` or `allowedModels` is `undefined`
- The model display name shows correctly for models from different providers (e.g., OpenRouter models with vendor prefix)

### Task 4: Initialize session model from config default on new session creation

**Type:** Implementation
**read_first:**
  - AURA-CHAT/client/src/features/chat/ChatPage.tsx (lines 68-73 for session/model state, lines 107-111 for config query, understand `useModelStore` usage)
  - AURA-CHAT/client/src/stores/useModelStore.ts (understand `setSessionModel` and `sessionModels` record)

**action:**
1. Open `AURA-CHAT/client/src/features/chat/ChatPage.tsx`.
2. Add a `useEffect` that initializes the session model from config default when a new session is selected and no model has been chosen yet. Place this after the existing config query (after ~line 111):

   ```typescript
   // Initialize session model from config default on session change
   useEffect(() => {
       if (currentSessionId && config?.default_model && !sessionModel) {
           setSessionModel(currentSessionId, config.default_model);
       }
   }, [currentSessionId, config?.default_model, sessionModel, setSessionModel]);
   ```

   This ensures that when a user creates or switches to a session, if they haven't already picked a model, the admin-configured default is used.

3. The existing `handleSetModel` function already persists model selection via `setSessionModel`, so user overrides are preserved.

**acceptance_criteria:**
- `ChatPage.tsx` has a `useEffect` that calls `setSessionModel(sessionId, default_model)` when session changes and no model is selected
- The effect dependency array is `[currentSessionId, config?.default_model, sessionModel, setSessionModel]`
- User model selections in existing sessions are preserved (not overwritten)
- New sessions start with the admin-configured default model

## Verification

1. Run `cd AURA-CHAT/client && npx tsc --noEmit` — type check passes
2. Run `cd AURA-CHAT/client && npm run lint` — no lint errors
3. Run `cd AURA-CHAT/client && npm run build` — build succeeds
4. Manual: Navigate to chat → create new session → model picker shows admin-configured models
5. Manual: Select a non-default model → model persists for that session
6. Manual: Switch sessions → each session remembers its model choice

## Must-Haves

- `ChatPage` uses `config.allowed_models` (1-5 model array) for `InlineModelPicker`
- New sessions initialize with admin-configured default model
- When `allowedModels` has 1 model, `InlineModelPicker` enters read-only mode
- Fallback to all models when no admin config exists

## Success Criteria

- [ ] `allowedModels` derived from `config.allowed_models` array, not single `config.default_model`
- [ ] `effectiveModel` falls back to `config.default_model` when stored model not in allowed list
- [ ] New session initializes with admin default model via `useEffect`
- [ ] `InlineModelPicker` read-only mode works with single-model allowed list
- [ ] TypeScript type check passes
- [ ] No lint errors
- [ ] Build succeeds