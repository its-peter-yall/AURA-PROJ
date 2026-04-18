---
phase: 01
plan: 03
wave: 1
depends_on: ["01"]
files_modified:
  - AURA-CHAT/client/src/types/settings.ts
  - AURA-CHAT/client/src/features/settings/api/settingsApi.ts
  - AURA-CHAT/client/src/features/settings/hooks/useSettingsApi.ts
  - AURA-CHAT/client/src/features/settings/components/ChatModelsSection.tsx
  - AURA-CHAT/client/src/features/settings/components/DefaultModelSection.tsx
autonomous: true
requirements: null
---

# Plan 03: Frontend — ChatModelsSection UI Component & API Wiring

## Objective

Create the `ChatModelsSection` component for admin settings that allows configuring 1-5 chat models with a default selection, and wire the API hooks for fetching and updating multi-model configuration. Modify `DefaultModelSection` to render `ChatModelsSection` for the chat use case instead of the standard `UseCaseSection`.

## Context

Plan 01 added `get_chat_models_config()` and `set_chat_models()` to SettingsStore. Plan 02 added REST endpoints `GET/PUT /defaults/chat/models`. This plan creates the frontend component and API layer that consume those endpoints.

## Tasks

### Task 1: Add TypeScript types for multi-model chat configuration

**Type:** Implementation
**read_first:**
  - AURA-CHAT/client/src/types/settings.ts (full file — understand existing type definitions)

**action:**
1. Open `AURA-CHAT/client/src/types/settings.ts` and add the following interfaces after the existing `DefaultModelSetting` and `ApiKeyStatus` interfaces:

   ```typescript
   export interface ChatModelEntry {
       provider: string;
       model: string;
   }

   export interface ChatModelsConfig {
       models: ChatModelEntry[];
       default_index: number;
       provider: string;
       model: string;
   }
   ```

2. Add mandatory file header if it's missing or update it to reflect the new types.

**acceptance_criteria:**
- `settings.ts` contains `interface ChatModelEntry` with `provider: string` and `model: string`
- `settings.ts` contains `interface ChatModelsConfig` with `models: ChatModelEntry[]`, `default_index: number`, `provider: string`, `model: string`
- No existing types (`DefaultModelSetting`, `ModelInfo`, etc.) are modified or removed

### Task 2: Add API functions for multi-model chat configuration

**Type:** Implementation
**read_first:**
  - AURA-CHAT/client/src/features/settings/api/settingsApi.ts (full file — understand existing API call patterns, imports, axios instance usage)

**action:**
1. Open `AURA-CHAT/client/src/features/settings/api/settingsApi.ts` and add two new export functions after the existing `validateApiKey` function:

   ```typescript
   export const fetchChatModelsConfig = async (): Promise<ChatModelsConfig> => {
       const response = await api.get<ChatModelsConfig>('/api/v1/settings/defaults/chat/models');
       return response.data;
   };

   export const updateChatModels = async (payload: {
       models: Array<{ provider: string; model: string }>;
       default_index: number;
   }): Promise<ChatModelsConfig> => {
       const response = await api.put<ChatModelsConfig>('/api/v1/settings/defaults/chat/models', payload);
       return response.data;
   };
   ```

2. Add `ChatModelsConfig` to the import from `@/types/settings`.

**acceptance_criteria:**
- `settingsApi.ts` exports `fetchChatModelsConfig` function that calls `GET /api/v1/settings/defaults/chat/models`
- `settingsApi.ts` exports `updateChatModels` function that calls `PUT /api/v1/settings/defaults/chat/models`
- Both functions return typed `ChatModelsConfig`
- `ChatModelsConfig` is imported from `@/types/settings`

### Task 3: Add TanStack Query hooks for multi-model chat configuration

**Type:** Implementation
**read_first:**
  - AURA-CHAT/client/src/features/settings/hooks/useSettingsApi.ts (full file — understand query key factory, mutation patterns, cache invalidation)
  - AURA-CHAT/client/src/features/settings/api/settingsApi.ts (understand the API functions just added)

**action:**
1. Open `AURA-CHAT/client/src/features/settings/hooks/useSettingsApi.ts` and add:

   a. New query key entry in `settingsKeys`:
      ```typescript
      chatModels: () => [...settingsKeys.all, 'chatModels'] as const,
      ```

   b. `useChatModelsConfig` query hook:
      ```typescript
      export const useChatModelsConfig = () => {
          return useQuery({
              queryKey: settingsKeys.chatModels(),
              queryFn: fetchChatModelsConfig,
              staleTime: 2 * 60 * 1000,
          });
      };
      ```

   c. `useUpdateChatModels` mutation hook:
      ```typescript
      export const useUpdateChatModels = () => {
          const queryClient = useQueryClient();

          return useMutation({
              mutationFn: updateChatModels,
              onSuccess: () => {
                  toast.success('Chat models updated');
                  queryClient.invalidateQueries({ queryKey: settingsKeys.chatModels() });
                  queryClient.invalidateQueries({ queryKey: settingsKeys.defaults() });
              },
              onError: (error: Error) => {
                  toast.error(error.message || 'Failed to update chat models');
              },
          });
      };
      ```

2. Import `fetchChatModelsConfig` and `updateChatModels` from the API module at the top.
3. Add `ChatModelsConfig` to the type import if needed.

**acceptance_criteria:**
- `useSettingsApi.ts` exports `useChatModelsConfig` hook
- `useSettingsApi.ts` exports `useUpdateChatModels` hook
- `settingsKeys.chatModels` query key defined as `['settings', 'chatModels']`
- `useChatModelsConfig` calls `fetchChatModelsConfig` with 2-minute stale time
- `useUpdateChatModels` invalidates both `chatModels` and `defaults` query keys on success
- Both hooks use existing toast and queryClient patterns

### Task 4: Create `ChatModelsSection` component

**Type:** Implementation
**read_first:**
  - AURA-CHAT/client/src/features/settings/components/DefaultModelSection.tsx (full file — understand structure, USE_CASES array, UseCaseSection pattern)
  - AURA-CHAT/client/src/features/settings/components/HierarchicalModelPicker.tsx (understand the picker's props interface)
  - AURA-CHAT/client/src/features/settings/hooks/useSettingsApi.ts (understand hooks just added)
  - AURA-CHAT/client/src/features/settings/hooks/useModelList.ts (understand `groupModelsByProvider` function)
  - AURA-CHAT/client/src/types/settings.ts (understand `ChatModelEntry`, `ChatModelsConfig`, `ModelInfo`, `ModelGroup` types)

**action:**
1. Create file `AURA-CHAT/client/src/features/settings/components/ChatModelsSection.tsx`.

2. Implement the component per UI-SPEC.md requirements:
   - **State**: `selectedModels` (array of `{provider, model}`), `defaultIndex` (number)
   - **Data fetching**: `useChatModelsConfig()` for loading existing config, `useAllModels()` for model catalog, `useUpdateChatModels()` for saving
   - **Effects**: On config load, set `selectedModels` and `defaultIndex` from response data
   - **Handlers**:
     - `handleAddModel(provider, model)`: If `selectedModels.length >= 5`, show `toast.error("Maximum 5 models allowed")` and return. Otherwise append.
     - `handleRemoveModel(index)`: Filter out model at index. If `defaultIndex >= newLength`, set `defaultIndex = max(0, newLength - 1)`. If only 1 model remains, disable remove.
     - `handleSetDefault(index)`: Set `defaultIndex = index`.
     - `handleSave()`: Call `updateChatModels.mutate({ models: selectedModels, default_index: defaultIndex })`.
   - **UI layout** (per UI-SPEC.md):
     - Section title "Chat Models" with description "Configure up to 5 models available to users in the chat interface"
     - List of selected models in `flex-col space-y-2`, each item a horizontal row (`flex items-center justify-between`) in `p-3 bg-card/50 rounded-md border border-border/10`:
       - Drag handle icon (GripVertical, `w-4 h-4 text-muted-foreground/40 hidden sm:block`)
       - Model name (`font-semibold text-sm`)
       - Provider badge or text (`text-xs text-muted-foreground`)
       - "Default" indicator: If `defaultIndex === index`, show `Star` icon with `text-primary fill-primary/30` and "Default" label. If not default, show `<button>` with `Star` icon outline that calls `handleSetDefault(index)`
       - Remove button: `X` icon button, disabled when `selectedModels.length === 1`, calls `handleRemoveModel(index)`
     - Below the list: `HierarchicalModelPicker` for adding new models, disabled (opacity-50, pointer-events-none) when `selectedModels.length >= 5`
     - Save button: calls `handleSave()`, disabled when `selectedModels.length === 0` or `updateChatModels.isPending`, shows loading spinner when pending
   - **Animations**: Wrap the models list in `framer-motion` `<AnimatePresence>` with `initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }}` for each `<motion.div layout>` item
   - **Accessibility**: `aria-label` on remove buttons (`aria-label="Remove model {model name}"`) and default toggle buttons (`aria-label="Set {model name} as default"`)
   - **Responsive**: On mobile (`< 640px`), "Set as Default" button becomes just a `Star` icon with `aria-label`; provider badge hidden

3. Add mandatory file header per AGENTS.md TypeScript file header conventions.

4. Export as named export: `export function ChatModelsSection() { ... }`

**acceptance_criteria:**
- File `AURA-CHAT/client/src/features/settings/components/ChatModelsSection.tsx` exists
- Component renders a list of selected models with add/remove/set-default actions
- "Add model" picker is disabled when 5 models selected (`opacity-50`, `pointer-events-none`)
- Remove button disabled when only 1 model remains
- `toast.error("Maximum 5 models allowed")` shown when attempting to add 6th model
- `handleSave` calls `updateChatModels.mutate()` with correct payload format
- `framer-motion` `<AnimatePresence>` wraps model list items
- All interactive elements have `aria-label` attributes
- Named export `ChatModelsSection` (no default export)
- File has mandatory TypeScript file header

### Task 5: Modify `DefaultModelSection` to render `ChatModelsSection` for chat use case

**Type:** Implementation
**read_first:**
  - AURA-CHAT/client/src/features/settings/components/DefaultModelSection.tsx (full file)
  - AURA-CHAT/client/src/features/settings/components/ChatModelsSection.tsx (just created)

**action:**
1. Open `AURA-CHAT/client/src/features/settings/components/DefaultModelSection.tsx`.
2. Import `ChatModelsSection` from `./ChatModelsSection`.
3. In the `DefaultModelSection` component's render, modify the `{USE_CASES.map(...)}` block to conditionally render `ChatModelsSection` for the chat use case:

   Replace the current rendering logic:
   ```jsx
   {USE_CASES.map(useCase => (
       <UseCaseSection
           key={useCase.id}
           useCase={useCase}
           currentValue={defaults?.[useCase.id]?.model || ''}
           groupedModels={groupModelsByProvider(allModels || [], USE_CASE_MODEL_TYPES[useCase.id])}
           allModels={allModels || []}
       />
   ))}
   ```

   With:
   ```jsx
   {USE_CASES.map(useCase => {
       if (useCase.id === 'chat') {
           return <ChatModelsSection key={useCase.id} />;
       }
       return (
           <UseCaseSection
               key={useCase.id}
               useCase={useCase}
               currentValue={defaults?.[useCase.id]?.model || ''}
               groupedModels={groupModelsByProvider(allModels || [], USE_CASE_MODEL_TYPES[useCase.id])}
               allModels={allModels || []}
           />
       );
   })}
   ```

4. Keep all existing imports and exports intact.

**acceptance_criteria:**
- `DefaultModelSection.tsx` imports `ChatModelsSection` from `./ChatModelsSection`
- When `useCase.id === 'chat'`, renders `<ChatModelsSection />` instead of `<UseCaseSection />`
- All other use cases (embeddings, entity_extraction, gatekeeper, relationship_extraction) still render `<UseCaseSection />`
- No other changes to `DefaultModelSection` component behavior

## Verification

1. Run `cd AURA-CHAT/client && npm run build` — TypeScript compiles without errors
2. Run `cd AURA-CHAT/client && npx tsc --noEmit` — type check passes
3. Run `cd AURA-CHAT/client && npm run lint` — no lint errors
4. Verify `ChatModelsSection` component renders in settings page within the "Chat Model" section
5. Verify other use case sections still render the standard `UseCaseSection`

## Must-Haves

- `ChatModelsSection` component with 1-5 model list management
- API hooks `useChatModelsConfig` and `useUpdateChatModels` for data fetching/saving
- TypeScript types `ChatModelEntry` and `ChatModelsConfig`
- `DefaultModelSection` renders `ChatModelsSection` for chat, `UseCaseSection` for all others

## Success Criteria

- [ ] `ChatModelEntry` and `ChatModelsConfig` types added to `settings.ts`
- [ ] `fetchChatModelsConfig` and `updateChatModels` API functions added
- [ ] `useChatModelsConfig` and `useUpdateChatModels` hooks added
- [ ] `ChatModelsSection` component handles add/remove/set-default/save with validation
- [ ] `DefaultModelSection` shows `ChatModelsSection` for chat use case
- [ ] TypeScript type check passes (`npx tsc --noEmit`)
- [ ] No lint errors (`npm run lint`)
- [ ] Build succeeds (`npm run build`)