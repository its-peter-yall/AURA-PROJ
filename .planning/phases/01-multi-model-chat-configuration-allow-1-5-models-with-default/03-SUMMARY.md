# Plan 03 Summary: Frontend — ChatModelsSection UI Component & API Wiring

**Phase:** 01 (multi-model-chat-configuration-allow-1-5-models-with-default)
**Plan:** 03
**Date:** 2026-04-18
**Status:** Implementation Complete — Commits Blocked by Shell Configuration Issue

## Tasks Executed

### Task 1: Add TypeScript types for multi-model chat configuration
**File:** `AURA-CHAT/client/src/types/settings.ts`
**Status:** ✅ Implemented
**Changes:**
- Added `ChatModelEntry` interface with `provider: string` and `model: string`
- Added `ChatModelsConfig` interface with `models: ChatModelEntry[]`, `default_index: number`, `provider: string`, `model: string`
- No existing types modified or removed

### Task 2: Add API functions for multi-model chat configuration
**File:** `AURA-CHAT/client/src/features/settings/api/settingsApi.ts`
**Status:** ✅ Implemented
**Changes:**
- Added `ChatModelsConfig` to imports from `@/types/settings`
- Added `fetchChatModelsConfig()` — calls `GET /api/v1/settings/defaults/chat/models`
- Added `updateChatModels()` — calls `PUT /api/v1/settings/defaults/chat/models` with `{ models, default_index }` payload
- Both functions return typed `ChatModelsConfig`

### Task 3: Add TanStack Query hooks for multi-model chat configuration
**File:** `AURA-CHAT/client/src/features/settings/hooks/useSettingsApi.ts`
**Status:** ✅ Implemented
**Changes:**
- Added imports for `fetchChatModelsConfig` and `updateChatModels` from API module
- Added `ChatModelsConfig` to type imports
- Added `settingsKeys.chatModels()` query key: `['settings', 'chatModels']`
- Added `useChatModelsConfig()` hook with 2-minute stale time
- Added `useUpdateChatModels()` mutation with toast notifications and cache invalidation for both `chatModels` and `defaults` query keys

### Task 4: Create ChatModelsSection component
**File:** `AURA-CHAT/client/src/features/settings/components/ChatModelsSection.tsx`
**Status:** ✅ Implemented (NEW FILE)
**Features:**
- State management: `selectedModels` array, `defaultIndex` number
- Data fetching: `useChatModelsConfig()`, `useAllModels()`, `useUpdateChatModels()`
- `handleAddModel()`: Validates max 5 models, shows toast error, prevents duplicates
- `handleRemoveModel()`: Handles default index adjustment, disables when only 1 model remains
- `handleSetDefault()`: Updates default index
- `handleSave()`: Calls mutation with correct payload format
- UI Layout:
  - Section title "Chat Models" with description
  - Model list with drag handle, model name, provider, default indicator, remove button
  - `HierarchicalModelPicker` disabled at max capacity (opacity-50, pointer-events-none)
  - Save button with loading state
- Animations: `framer-motion` `<AnimatePresence>` with layout animations
- Accessibility: `aria-label` attributes on all interactive elements
- Named export (no default export)
- Mandatory TypeScript file header included

### Task 5: Modify DefaultModelSection to render ChatModelsSection for chat use case
**File:** `AURA-CHAT/client/src/features/settings/components/DefaultModelSection.tsx`
**Status:** ✅ Implemented
**Changes:**
- Added import for `ChatModelsSection` from `./ChatModelsSection`
- Modified USE_CASES.map rendering to conditionally render `<ChatModelsSection />` when `useCase.id === 'chat'`
- All other use cases continue to render `<UseCaseSection />` unchanged

## Files Modified

| File | Change Type |
|------|-------------|
| `AURA-CHAT/client/src/types/settings.ts` | Modified — Added types |
| `AURA-CHAT/client/src/features/settings/api/settingsApi.ts` | Modified — Added API functions |
| `AURA-CHAT/client/src/features/settings/hooks/useSettingsApi.ts` | Modified — Added hooks |
| `AURA-CHAT/client/src/features/settings/components/ChatModelsSection.tsx` | Created — New component |
| `AURA-CHAT/client/src/features/settings/components/DefaultModelSection.tsx` | Modified — Conditional rendering |

## Acceptance Criteria Status

- [x] `ChatModelEntry` and `ChatModelsConfig` types added to `settings.ts`
- [x] `fetchChatModelsConfig` and `updateChatModels` API functions added
- [x] `useChatModelsConfig` and `useUpdateChatModels` hooks added
- [x] `ChatModelsSection` component handles add/remove/set-default/save with validation
- [x] `DefaultModelSection` shows `ChatModelsSection` for chat use case
- [ ] TypeScript type check passes (`npx tsc --noEmit`) — **Blocked by shell issue**
- [ ] No lint errors (`npm run lint`) — **Blocked by shell issue**
- [ ] Build succeeds (`npm run build`) — **Blocked by shell issue**

## Issues Encountered

### Shell Configuration Issue
The bash tool has a persistent shell configuration problem where `SQZ_CMD=git` is being prepended to all commands, causing them to fail with "not recognized" errors in PowerShell. This prevented:
- Running git commits
- Running TypeScript type checks
- Running lint checks
- Running build commands

**Recommended Resolution:**
1. Check shell profile/configuration for `SQZ_CMD` environment variable setup
2. Run the following commands manually to complete the plan:
   ```bash
   cd "D:\Peter\AURA Twin Proj\AURA-PROJ"
   git add AURA-CHAT/client/src/types/settings.ts
   git commit -m "feat: add ChatModelEntry and ChatModelsConfig types for multi-model chat configuration"
   
   git add AURA-CHAT/client/src/features/settings/api/settingsApi.ts
   git commit -m "feat: add fetchChatModelsConfig and updateChatModels API functions"
   
   git add AURA-CHAT/client/src/features/settings/hooks/useSettingsApi.ts
   git commit -m "feat: add useChatModelsConfig and useUpdateChatModels TanStack Query hooks"
   
   git add AURA-CHAT/client/src/features/settings/components/ChatModelsSection.tsx
   git commit -m "feat: create ChatModelsSection component for multi-model chat configuration"
   
   git add AURA-CHAT/client/src/features/settings/components/DefaultModelSection.tsx
   git commit -m "feat: render ChatModelsSection for chat use case in DefaultModelSection"
   
   cd AURA-CHAT/client && npm run build
   npx tsc --noEmit
   npm run lint
   ```

## Implementation Notes

- All changes follow existing code patterns and conventions from the codebase
- TypeScript strict mode compliance maintained
- Named exports used throughout (no default exports per project conventions)
- File headers included per AGENTS.md requirements
- Component uses existing `HierarchicalModelPicker` and follows the established `UseCaseSection` pattern
- Toast notifications use the existing `sonner` integration
- Query key factory pattern consistent with existing hooks
- Animations use `framer-motion` consistent with other components in the project
