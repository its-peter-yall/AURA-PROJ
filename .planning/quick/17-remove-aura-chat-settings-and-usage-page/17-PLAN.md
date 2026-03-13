---
phase: quick
plan: 17
type: execute
wave: 1
depends_on: []
files_modified:
  - AURA-CHAT/client/src/hooks/useModels.ts (new)
  - AURA-CHAT/client/src/types/models.ts (new)
  - AURA-CHAT/client/src/features/chat/components/InlineModelPicker.tsx
  - AURA-CHAT/client/src/features/chat/components/InlineModelPicker.test.tsx
  - AURA-CHAT/client/src/features/chat/ChatPage.test.tsx
  - AURA-CHAT/client/src/App.tsx
  - AURA-CHAT/client/src/components/MainLayout.tsx
  - AURA-CHAT/client/src/components/RoleProtectedRoute.tsx
  - AURA-CHAT/client/src/features/settings/ (deleted)
  - AURA-CHAT/client/src/features/usage/ (deleted)
  - AURA-CHAT/client/src/types/usage.ts (deleted)
autonomous: true
must_haves:
  truths:
    - Settings and Usage pages are completely removed from AURA-CHAT
    - Chat feature continues to work with model picker functionality intact
    - Admin users are redirected to /chat instead of /usage
    - AURA-NOTES-MANAGER is completely unaffected by these changes
    - No TypeScript errors or broken imports remain
  artifacts:
    - path: "AURA-CHAT/client/src/hooks/useModels.ts"
      provides: "Relocated useAllModels, useGroupedModels, groupModelsByProvider"
      exports: ["useAllModels", "useGroupedModels", "groupModelsByProvider"]
    - path: "AURA-CHAT/client/src/types/models.ts"
      provides: "Model-related type definitions"
      exports: ["ProviderType", "ModelInfo", "ModelGroup", "VendorGroup"]
    - path: "AURA-CHAT/client/src/features/settings/"
      provides: "DELETED - no longer exists"
    - path: "AURA-CHAT/client/src/features/usage/"
      provides: "DELETED - no longer exists"
  key_links:
    - from: "InlineModelPicker.tsx"
      to: "@/hooks/useModels"
      via: "import { useAllModels, useGroupedModels }"
    - from: "RoleProtectedRoute.tsx"
      to: "/chat"
      via: "Navigate to='/chat'"
---

<objective>
Remove AURA-CHAT settings and usage pages completely while preserving chat functionality.

Purpose: Simplify AURA-CHAT by removing admin-only pages (settings, usage) and revoking admin access to the chat app. Admins should only use AURA-NOTES-MANAGER.

Output: Clean AURA-CHAT with only chat-related features, relocated shared hooks/types, updated routing, and no impact on AURA-NOTES-MANAGER.
</objective>

<execution_context>
@C:/Users/Peter/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/Peter/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@AURA-CHAT/client/src/features/settings/hooks/useSettingsApi.ts
@AURA-CHAT/client/src/features/settings/hooks/useModelList.ts
@AURA-CHAT/client/src/types/settings.ts
@AURA-CHAT/client/src/features/chat/components/InlineModelPicker.tsx
@AURA-CHAT/client/src/components/MainLayout.tsx
@AURA-CHAT/client/src/components/RoleProtectedRoute.tsx
@AURA-CHAT/client/src/App.tsx
</context>

<tasks>

<task type="auto">
  <name>Task 1: Relocate shared hooks and types for model selection</name>
  <files>
    AURA-CHAT/client/src/hooks/useModels.ts (new)
    AURA-CHAT/client/src/types/models.ts (new)
    AURA-CHAT/client/src/features/chat/components/InlineModelPicker.tsx
    AURA-CHAT/client/src/features/chat/components/InlineModelPicker.test.tsx
    AURA-CHAT/client/src/features/chat/ChatPage.test.tsx
  </files>
  <action>
    Create new shared location for model-related hooks and types that InlineModelPicker depends on:

    1. Create AURA-CHAT/client/src/types/models.ts:
       - Copy ProviderType, ModelInfo, ModelGroup, VendorGroup from @/types/settings.ts
       - Add file header per AGENTS.md requirements

    2. Create AURA-CHAT/client/src/hooks/useModels.ts:
       - Copy useAllModels from useSettingsApi.ts (lines 29-38)
       - Copy groupModelsByProvider and useGroupedModels from useModelList.ts (entire file)
       - Update imports to use @/types/models instead of @/types/settings
       - Keep settingsKeys.models() query key pattern for cache consistency
       - Add file header per AGENTS.md requirements

    3. Update AURA-CHAT/client/src/features/chat/components/InlineModelPicker.tsx:
       - Change: import { useAllModels } from '@/features/settings/hooks/useSettingsApi'
       - To: import { useAllModels, useGroupedModels } from '@/hooks/useModels'
       - Change: import { useGroupedModels } from '@/features/settings/hooks/useModelList'
       - To: remove this line (now imported from useModels)

    4. Update AURA-CHAT/client/src/features/chat/components/InlineModelPicker.test.tsx:
       - Update mock paths from '@/features/settings/hooks/useSettingsApi' to '@/hooks/useModels'
       - Update mock paths from '@/features/settings/hooks/useModelList' to '@/hooks/useModels'

    5. Update AURA-CHAT/client/src/features/chat/ChatPage.test.tsx:
       - Update any mock paths referencing settings hooks to use @/hooks/useModels

    Do NOT delete the original files yet - that happens in Task 2.
  </action>
  <verify>
    Run TypeScript check: cd AURA-CHAT/client && npx tsc --noEmit
    Verify InlineModelPicker imports resolve correctly.
  </verify>
  <done>
    - useModels.ts exists with useAllModels, useGroupedModels, groupModelsByProvider
    - types/models.ts exists with ProviderType, ModelInfo, ModelGroup, VendorGroup
    - InlineModelPicker.tsx imports from @/hooks/useModels
    - TypeScript compiles without errors
  </done>
</task>

<task type="auto">
  <name>Task 2: Remove settings and usage features</name>
  <files>
    AURA-CHAT/client/src/features/settings/ (deleted)
    AURA-CHAT/client/src/features/usage/ (deleted)
    AURA-CHAT/client/src/types/usage.ts (deleted)
  </files>
  <action>
    Safely delete all settings and usage related files:

    1. Delete entire directory: AURA-CHAT/client/src/features/settings/
       - SettingsPage.tsx
       - SettingsPage.test.tsx
       - components/ (ApiKeyManager, DefaultModelSection, HierarchicalModelPicker, ProviderSettingsSection)
       - hooks/useSettingsApi.ts
       - hooks/useSettingsApi.test.ts
       - hooks/useModelList.ts
       - hooks/useModelList.test.ts

    2. Delete entire directory: AURA-CHAT/client/src/features/usage/
       - UsagePage.tsx
       - components/ (DateRangeFilter, UsageSummaryCards, CostOverTimeChart, CostByProviderChart, CostByModelChart, SessionCostBadge)
       - hooks/useUsageApi.ts

    3. Delete file: AURA-CHAT/client/src/types/usage.ts

    4. Clean up @/types/settings.ts - check if any types are still needed:
       - Keep the file if other types (UseCase, DefaultModelSetting, ApiKeyStatus) are used elsewhere
       - If file becomes empty after removal, delete it

    IMPORTANT: AURA-NOTES-MANAGER has its own settings page - do NOT touch anything in AURA-NOTES-MANAGER/ directory.
  </action>
  <verify>
    Verify directories are deleted:
    - ls AURA-CHAT/client/src/features/settings/ should fail
    - ls AURA-CHAT/client/src/features/usage/ should fail
    - ls AURA-CHAT/client/src/types/usage.ts should fail
  </verify>
  <done>
    - AURA-CHAT/client/src/features/settings/ directory does not exist
    - AURA-CHAT/client/src/features/usage/ directory does not exist
    - AURA-CHAT/client/src/types/usage.ts does not exist
  </done>
</task>

<task type="auto">
  <name>Task 3: Update routing and navigation</name>
  <files>
    AURA-CHAT/client/src/App.tsx
    AURA-CHAT/client/src/components/MainLayout.tsx
    AURA-CHAT/client/src/components/RoleProtectedRoute.tsx
  </files>
  <action>
    Update routing to remove settings/usage routes and fix admin redirect:

    1. Update AURA-CHAT/client/src/App.tsx:
       - Remove import: import { SettingsPage } from '@/features/settings/SettingsPage'
       - Remove import: import { UsagePage } from '@/features/usage/UsagePage'
       - Remove entire admin-only route block (lines 72-79):
         ```tsx
         {/* Admin-only routes (settings, usage) - block regular users */}
         <Route element={<RoleProtectedRoute requireAdmin />}>
           <Route path="/" element={<MainLayout />}>
             <Route index element={<UsagePage />} />
             <Route path="usage" element={<UsagePage />} />
             <Route path="settings" element={<SettingsPage />} />
           </Route>
         </Route>
         ```
       - Update the user-only route to be the default for ALL authenticated users:
         Change comment from "User-only routes (chat, documents, graph) - block admins"
         to "Protected routes for all authenticated users"
       - Remove `requireUser` prop from RoleProtectedRoute - admins will now access chat too

    2. Update AURA-CHAT/client/src/components/MainLayout.tsx:
       - Remove Settings icon import
       - Remove BarChart3 icon import
       - Remove settings and usage entries from navItems array (lines 66-77)
       - Remove admin filtering logic in renderNavItems (lines 165-179)
       - Simplify to show all remaining nav items (Chat, Documents, Graph) to all users
       - Remove comment about "Admins only see Usage and Settings"

    3. Update AURA-CHAT/client/src/components/RoleProtectedRoute.tsx:
       - Line 54: Change `return <Navigate to="/usage" replace />;`
       - To: `return <Navigate to="/chat" replace />;`
       - Update comment on line 6 from "redirects admins to /usage" to "redirects admins to /chat"
       - Consider removing requireAdmin/requireUser props entirely since we're simplifying access
  </action>
  <verify>
    Run TypeScript check: cd AURA-CHAT/client && npx tsc --noEmit
    Run build: cd AURA-CHAT/client && npm run build
  </verify>
  <done>
    - App.tsx has no /settings or /usage routes
    - MainLayout.tsx shows Chat, Documents, Graph to all users
    - RoleProtectedRoute redirects admins to /chat (not /usage)
    - Build completes without errors
  </done>
</task>

</tasks>

<verification>
[Post-execution verification]
1. AURA-CHAT build passes: cd AURA-CHAT/client && npm run build
2. TypeScript has no errors: cd AURA-CHAT/client && npx tsc --noEmit
3. Tests pass: cd AURA-CHAT/client && npm test (if tests exist for chat feature)
4. AURA-NOTES-MANAGER is untouched - verify no files modified in that directory
</verification>

<success_criteria>
- SettingsPage and UsagePage are completely removed from AURA-CHAT
- Chat feature model picker continues to work (uses relocated hooks)
- All users (including admins) see Chat, Documents, Graph in navigation
- Admin users accessing user routes are redirected to /chat (not /usage)
- No TypeScript compilation errors
- Build completes successfully
- AURA-NOTES-MANAGER settings page is completely unaffected
</success_criteria>

<output>
After completion, create `.planning/quick/17-remove-aura-chat-settings-and-usage-page/17-SUMMARY.md`
</output>
