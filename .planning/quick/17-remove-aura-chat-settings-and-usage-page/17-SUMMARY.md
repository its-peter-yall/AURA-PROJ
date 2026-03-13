---
phase: quick
plan: 17
name: Remove AURA-CHAT Settings and Usage Pages
subsystem: AURA-CHAT/client
completed_date: 2026-03-13
autonomous: true
depends_on: []
tags: [cleanup, refactoring, routing]
tech-stack:
  added: []
  patterns: [feature-relocation, route-simplification]
key-files:
  created:
    - AURA-CHAT/client/src/types/models.ts
    - AURA-CHAT/client/src/hooks/useModels.ts
  modified:
    - AURA-CHAT/client/src/App.tsx
    - AURA-CHAT/client/src/components/MainLayout.tsx
    - AURA-CHAT/client/src/components/RoleProtectedRoute.tsx
    - AURA-CHAT/client/src/features/chat/components/InlineModelPicker.tsx
    - AURA-CHAT/client/src/features/chat/components/InlineModelPicker.test.tsx
    - AURA-CHAT/client/src/features/chat/ChatPage.test.tsx
  deleted:
    - AURA-CHAT/client/src/features/settings/ (entire directory)
    - AURA-CHAT/client/src/features/usage/ (entire directory)
    - AURA-CHAT/client/src/types/settings.ts
    - AURA-CHAT/client/src/types/usage.ts
decisions: []
metrics:
  duration: 8
  tasks_completed: 3
  files_created: 2
  files_modified: 6
  files_deleted: 22
---

# Quick Task 17: Remove AURA-CHAT Settings and Usage Pages Summary

## Overview

Simplified AURA-CHAT by completely removing the admin-only Settings and Usage pages while preserving chat functionality through strategic relocation of shared hooks and types.

## What Was Done

### Task 1: Relocate Shared Hooks and Types (Commit: 9ef0b59)

Created new shared locations for model-related functionality:

- **Created** `src/types/models.ts` with:
  - `ProviderType` union type
  - `ModelInfo` interface
  - `ModelGroup` interface  
  - `VendorGroup` interface

- **Created** `src/hooks/useModels.ts` with:
  - `useAllModels()` - TanStack Query hook for fetching all models
  - `useGroupedModels()` - Hook for grouping models by provider/vendor
  - `groupModelsByProvider()` - Pure function for model organization
  - `settingsKeys` - Query key factory for cache consistency

- **Updated** `InlineModelPicker.tsx` to import from `@/hooks/useModels` instead of settings hooks
- **Updated** test files to mock the new hook locations

### Task 2: Remove Settings and Usage Features (Commit: b3332df)

Deleted entire feature directories and type files:

- **Deleted** `src/features/settings/` directory:
  - SettingsPage.tsx and SettingsPage.test.tsx
  - ApiKeyManager.tsx, DefaultModelSection.tsx, HierarchicalModelPicker.tsx, ProviderSettingsSection.tsx
  - useSettingsApi.ts, useSettingsApi.test.ts, useModelList.ts, useModelList.test.ts

- **Deleted** `src/features/usage/` directory:
  - UsagePage.tsx
  - DateRangeFilter.tsx, UsageSummaryCards.tsx, CostOverTimeChart.tsx, CostByProviderChart.tsx, CostByModelChart.tsx, SessionCostBadge.tsx
  - useUsageApi.ts

- **Deleted** type files:
  - `src/types/settings.ts` (types moved to models.ts)
  - `src/types/usage.ts`

### Task 3: Update Routing and Navigation (Commit: b7f8c5b)

Simplified routing and navigation:

- **Updated** `App.tsx`:
  - Removed SettingsPage and UsagePage imports
  - Removed admin-only route block
  - Changed user-only route to be default for ALL authenticated users
  - Removed `requireUser` prop from RoleProtectedRoute

- **Updated** `MainLayout.tsx`:
  - Removed Settings and BarChart3 icon imports
  - Removed settings and usage from navItems array
  - Removed admin filtering logic in renderNavItems
  - All users now see Chat, Documents, Graph in navigation
  - Sessions section no longer hidden for admins

- **Updated** `RoleProtectedRoute.tsx`:
  - Changed admin redirect from `/usage` to `/chat`
  - Removed `requireUser` prop
  - Updated file header comments

## Verification Results

| Check | Status |
|-------|--------|
| TypeScript compilation | ✅ Passed (no errors) |
| Build | ✅ Passed |
| Unit tests | ✅ 210 tests passed |
| AURA-NOTES-MANAGER impact | ✅ None (verified) |
| Chat model picker | ✅ Functional (uses relocated hooks) |

## Key Links Established

```
InlineModelPicker.tsx
  └── import { useAllModels, useGroupedModels } from '@/hooks/useModels'

RoleProtectedRoute.tsx
  └── Navigate to='/chat' (for all authenticated users)
```

## Artifacts Delivered

| Path | Type | Purpose |
|------|------|---------|
| `src/types/models.ts` | Created | Model-related type definitions |
| `src/hooks/useModels.ts` | Created | Model fetching and grouping hooks |
| `src/features/settings/` | Deleted | Admin settings page (removed) |
| `src/features/usage/` | Deleted | Admin usage page (removed) |
| `src/types/settings.ts` | Deleted | Settings types (relocated) |
| `src/types/usage.ts` | Deleted | Usage types (no longer needed) |

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check

- [x] `useModels.ts` exists with all required exports
- [x] `types/models.ts` exists with all required types
- [x] Settings directory deleted
- [x] Usage directory deleted
- [x] No TypeScript errors
- [x] Build passes
- [x] Tests pass
- [x] AURA-NOTES-MANAGER unaffected

## Commits

| Hash | Message |
|------|---------|
| 9ef0b59 | feat(quick-17): relocate model hooks and types for chat feature |
| b3332df | feat(quick-17): remove settings and usage features from AURA-CHAT |
| b7f8c5b | feat(quick-17): update routing and navigation after settings removal |

## Notes

- Admin users previously redirected to /usage are now redirected to /chat
- All authenticated users (including admins) now see the same navigation
- Model picker functionality preserved through relocated hooks
- AURA-NOTES-MANAGER settings page remains completely unaffected
