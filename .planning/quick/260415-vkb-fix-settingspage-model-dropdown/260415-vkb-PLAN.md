---
phase: quick-260415
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - AURA-NOTES-MANAGER/frontend/src/features/settings/hooks/useSettingsApi.ts
  - AURA-NOTES-MANAGER/frontend/src/features/settings/components/DefaultModelSection.tsx
autonomous: true
requirements: []
must_haves:
  truths:
    - "Models are visible in SettingsPage model dropdown"
    - "Selected model persists when switching browser tabs"
    - "No page refresh/reset when navigating back to SettingsPage"
  artifacts:
    - path: "AURA-NOTES-MANAGER/frontend/src/features/settings/hooks/useSettingsApi.ts"
      provides: "TanStack Query hooks with gcTime configuration"
      change: "Add gcTime to prevent garbage collection on tab switch"
    - path: "AURA-NOTES-MANAGER/frontend/src/features/settings/components/DefaultModelSection.tsx"
      provides: "Model selection UI with stable state"
      change: "Fix loading state handling to preserve selected value"
  key_links:
    - from: "useSettingsApi.ts"
      to: "TanStack Query cache"
      via: "gcTime configuration"
      pattern: "gcTime:"
    - from: "DefaultModelSection.tsx UseCaseSection"
      to: "currentValue prop"
      via: "useState initialization and useEffect sync"
      pattern: "useState\\(currentValue\\)"
---

<objective>
Fix two related bugs in SettingsPage model dropdown:
1. Models not visible in dropdown (empty dropdown)
2. Page refreshes/resets when switching browser tabs (selected model lost)

Purpose: Ensure stable, persistent model selection in SettingsPage that survives tab navigation.
Output: Working model dropdown with preserved state across tab switches.
</objective>

<execution_context>
@$HOME/.config/opencode/get-shit-done/workflows/execute-plan.md
@$HOME/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@AURA-NOTES-MANAGER/frontend/src/features/settings/hooks/useSettingsApi.ts
@AURA-NOTES-MANAGER/frontend/src/features/settings/components/DefaultModelSection.tsx
@AURA-NOTES-MANAGER/frontend/src/features/settings/components/HierarchicalModelPicker.tsx
</context>

<root_cause_analysis>
## Problem 1: Models Not Visible
- `useAllModels` query at line 51-60 has `staleTime: 5 * 60 * 1000` but NO `gcTime`
- When component unmounts on tab switch, TanStack Query garbage collects the data
- On remount, query refetches but may show loading state or empty data initially

## Problem 2: Page Refreshes on Tab Switch
- `UseCaseSection` has local `useState(selected)` initialized from `currentValue` prop
- During refetch loading state, `currentValue` becomes empty/undefined (line 106: `defaults?.[useCase.id]?.model || ''`)
- `useEffect` at line 130-132 syncs local state with `currentValue`, resetting selection
- No `gcTime` means data is lost on unmount, causing full refetch with loading state

## Fix Strategy
1. Add `gcTime` to all settings queries in `useSettingsApi.ts` (keeps data in cache for 10+ minutes)
2. Fix `UseCaseSection` to preserve local state during loading transitions
</root_cause_analysis>

<tasks>

<task type="auto">
  <name>Task 1: Add gcTime to settings queries</name>
  <files>AURA-NOTES-MANAGER/frontend/src/features/settings/hooks/useSettingsApi.ts</files>
  <action>
Add `gcTime` (garbage collection time) to ALL queries in useSettingsApi.ts to prevent data from being garbage collected when the user switches tabs.

Changes required:
1. `useAllModels` (lines 51-60): Add `gcTime: 10 * 60 * 1000` (10 minutes)
2. `useDefaults` (lines 62-70): Add `gcTime: 5 * 60 * 1000` (5 minutes)  
3. `useProviderModels` (lines 72-80): Add `gcTime: 10 * 60 * 1000`
4. `useApiKeyStatus` (lines 82-91): Add `gcTime: 2 * 60 * 1000`

Note: `gcTime` (formerly `cacheTime`) defines how long unused data stays in cache before garbage collection. Default is 5 minutes - we set higher to survive tab navigation.

Example for useAllModels:
```typescript
export const useAllModels = (refresh: boolean = false) => {
    return useQuery({
        queryKey: [...settingsKeys.models(), refresh],
        queryFn: async () => {
            const query = refresh ? '?refresh=true' : '';
            return await fetchApi<ModelInfo[]>(`/v1/settings/models${query}`);
        },
        staleTime: refresh ? 0 : 5 * 60 * 1000,
        gcTime: 10 * 60 * 1000, // Keep in cache for 10 minutes after unmount
    });
};
```
  </action>
  <verify>
    <automated>cd AURA-NOTES-MANAGER/frontend && npm run build</automated>
  </verify>
  <done>All four query hooks have gcTime configured, TypeScript compiles without errors</done>
</task>

<task type="auto">
  <name>Task 2: Fix UseCaseSection state preservation</name>
  <files>AURA-NOTES-MANAGER/frontend/src/features/settings/components/DefaultModelSection.tsx</files>
  <action>
Fix UseCaseSection to NOT sync local state when currentValue is empty during loading/refetch.

The bug: Line 130-132 syncs `currentValue` to local state unconditionally. During loading, currentValue becomes empty string, wiping the user's selection.

Change the useEffect to ONLY sync when currentValue is a valid non-empty string:

```typescript
// Sync local state when server default changes (e.g. via another tab)
// BUT skip if currentValue is empty (loading state) to preserve existing selection
useEffect(() => {
    if (currentValue && currentValue.trim() !== '') {
        setSelected(currentValue);
    }
}, [currentValue, setSelected]);
```

Also update the loading skeleton check on line 76:
- Currently: `if (loadingDefaults || (loadingModels && !isRefreshing))`
- Keep this but ensure the loading state doesn't cause currentValue resets
- The real fix is the useEffect guard above

This ensures:
1. Initial load populates from server
2. Tab switch preserves local selection (gcTime keeps cache alive)
3. Actual server changes (from another tab) still sync to local state
4. Loading states with empty currentValue don't wipe the selection
  </action>
  <verify>
    <automated>cd AURA-NOTES-MANAGER/frontend && npm run build && npm test -- --run</automated>
  </verify>
  <done>
    - useEffect only syncs when currentValue is non-empty
    - Build passes without TypeScript errors
    - Tests pass (or pre-existing test status documented)
  </done>
</task>

</tasks>

<verification>
1. Open SettingsPage in browser
2. Verify models appear in dropdown (not empty)
3. Select a model from dropdown
4. Switch to another browser tab
5. Switch back to SettingsPage
6. Verify selected model is still shown (not reset)
7. Verify no loading spinner or page refresh occurred
</verification>

<success_criteria>
- [ ] gcTime added to useAllModels, useDefaults, useProviderModels, useApiKeyStatus
- [ ] UseCaseSection useEffect guards against empty currentValue
- [ ] TypeScript build passes
- [ ] Models visible in dropdown
- [ ] Selection persists across tab switches
</success_criteria>

<output>
After completion, create `.planning/quick/260415-vkb-fix-settingspage-model-dropdown/260415-vkb-SUMMARY.md`
</output>