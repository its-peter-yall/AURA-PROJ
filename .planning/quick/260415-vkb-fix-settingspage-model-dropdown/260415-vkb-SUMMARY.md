# Quick Task 260415-vkb: Fix SettingsPage model dropdown

**Completed:** 2026-04-15

## Summary

Fixed two related issues in the AURA-NOTES-MANAGER Settings page model dropdown:

### Issue 1: Models not visible after tab switch
**Root cause:** TanStack Query's `gcTime` (garbage collection time) was not configured. When navigating away from the tab, the query cache was garbage collected, causing the dropdown to show "No models available" on return.

**Fix:** Added `gcTime: 10 * 60 * 1000` (10 minutes) to:
- `useAllModels` query in `useSettingsApi.ts` (line 59)
- `useDefaults` query in `useSettingsApi.ts` (line 70)
- `useProviderModels` query in `useSettingsApi.ts` (line 81)

### Issue 2: Model selection resets when switching tabs
**Root cause:** The `UseCaseSection` component's `useEffect` unconditionally synced `currentValue` to local `selected` state. During loading/refetching, `currentValue` was empty (`''`), overwriting the user's selection.

**Fix:** Guarded the `useEffect` in `DefaultModelSection.tsx` (line 129-133) to only sync when `currentValue` is truthy, preserving the local selection during loading transitions.

## Files Changed

| File | Change |
|------|--------|
| `AURA-NOTES-MANAGER/frontend/src/features/settings/hooks/useSettingsApi.ts` | Added `gcTime` to queries |
| `AURA-NOTES-MANAGER/frontend/src/features/settings/components/DefaultModelSection.tsx` | Guarded useEffect sync |

## Verification

- Build passes: `npm run build` completes successfully
- Both fixes are minimal and targeted — no breaking changes
