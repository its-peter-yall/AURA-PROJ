---
phase: quick
plan: 9
plan_name: implement-admin-vs-user-access-control-r
type: execute
wave: 1
depends_on: []
files_modified:
  - AURA-CHAT/client/src/stores/useAuthStore.ts
  - AURA-CHAT/client/src/components/RoleProtectedRoute.tsx
  - AURA-CHAT/client/src/App.tsx
  - AURA-CHAT/client/src/components/MainLayout.tsx
autonomous: true

must_haves:
  truths:
    - "Admin users CANNOT access /chat, /documents, or /graph pages"
    - "Admin users CAN ONLY access /usage and /settings pages"
    - "Non-admin users CANNOT access /usage or /settings pages"
    - "Non-admin users CAN access /chat, /documents, and /graph pages"
    - "Navigation sidebar shows only permitted items based on user role"
    - "Unauthorized access attempts redirect to an appropriate permitted page"
  artifacts:
    - path: "AURA-CHAT/client/src/stores/useAuthStore.ts"
      provides: "isAdmin() getter for admin role checking"
      min_changes: 2
    - path: "AURA-CHAT/client/src/components/RoleProtectedRoute.tsx"
      provides: "Role-based route guard component"
      exports: ["RoleProtectedRoute"]
    - path: "AURA-CHAT/client/src/App.tsx"
      provides: "Role-based routing configuration"
      pattern: "adminOnly|userOnly route props"
    - path: "AURA-CHAT/client/src/components/MainLayout.tsx"
      provides: "Role-filtered navigation items"
      pattern: "filter.*navItems.*role"
  key_links:
    - from: "useAuthStore.isAdmin()"
      to: "RoleProtectedRoute"
      via: "role check in route guard"
    - from: "RoleProtectedRoute"
      to: "App.tsx routes"
      via: "element prop on Route components"
    - from: "useAuthStore user.role"
      to: "MainLayout navItems filter"
      via: "role-based conditional rendering"
---

<objective>
Implement strict role-based access control separating admin and regular user permissions in AURA-CHAT.

**Purpose:** Enforce security boundaries where admins manage system configuration (settings, usage) while regular users access academic features (chat, documents, graph).

**Access Matrix:**
| Page | Admin | Student/Staff |
|------|-------|---------------|
| /chat | ❌ BLOCKED | ✅ ALLOWED |
| /documents | ❌ BLOCKED | ✅ ALLOWED |
| /graph | ❌ BLOCKED | ✅ ALLOWED |
| /settings | ✅ ALLOWED | ❌ BLOCKED |
| /usage | ✅ ALLOWED | ❌ BLOCKED |

**Output:** Updated auth store, new role-protected route component, modified routing, and role-aware navigation.
</objective>

<execution_context>
@C:/Users/Peter/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/Peter/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@AURA-CHAT/client/src/stores/useAuthStore.ts
@AURA-CHAT/client/src/components/ProtectedRoute.tsx
@AURA-CHAT/client/src/App.tsx
@AURA-CHAT/client/src/components/MainLayout.tsx
@AURA-CHAT/client/src/types/auth.ts

**Current State:**
- Auth store has `isStudent()`, `isStaff()` getters but no `isAdmin()`
- All routes use single `ProtectedRoute` with no role checks
- Navigation shows all items to all users
- UserRole type already includes 'admin' value

**Usage Calculation Note:** The existing UsageTracker already aggregates globally (not per-user), so admin usage view shows cumulative data across all users by default. No backend changes needed for this requirement.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add isAdmin getter and create RoleProtectedRoute component</name>
  <files>
    AURA-CHAT/client/src/stores/useAuthStore.ts
    AURA-CHAT/client/src/components/RoleProtectedRoute.tsx
  </files>
  <action>
**Part A: Add isAdmin getter to auth store**
Add to `useAuthStore` in `AURA-CHAT/client/src/stores/useAuthStore.ts`:
1. Add `isAdmin: () => boolean` to the AuthState interface (after line 47, with other computed getters)
2. Add implementation in the store object: `isAdmin: () => get().user?.role === 'admin'` (after line 71, with other computed implementations)

**Part B: Create RoleProtectedRoute component**
Create new file `AURA-CHAT/client/src/components/RoleProtectedRoute.tsx`:
- Copy structure from existing `ProtectedRoute.tsx` as base
- Add props: `requireAdmin?: boolean` and `requireUser?: boolean` (mutually exclusive)
- Implement logic:
  - If `requireAdmin` is true: allow only if `isAdmin()` returns true, otherwise redirect to `/usage`
  - If `requireUser` is true: allow only if NOT admin (student/staff), otherwise redirect to `/settings`
  - If neither specified: behave like current ProtectedRoute (any authenticated user)
- Show loading spinner while auth initializes (same as ProtectedRoute)
- Export as named export: `RoleProtectedRoute`

**Key Implementation Details:**
- Use `useAuthStore` to get `isAdmin()` and `isAuthenticated()` getters
- Use `Navigate` from react-router-dom for redirects
- Redirect admins trying user pages → `/usage` (first admin page)
- Redirect users trying admin pages → `/chat` (first user page)
- Include proper file header comment following project conventions
  </action>
  <verify>
Type check: `cd AURA-CHAT/client && npx tsc --noEmit`
Verify no errors in modified files.
  </verify>
  <done>
- [ ] `isAdmin()` getter exists in useAuthStore and returns correct boolean
- [ ] `RoleProtectedRoute.tsx` exists with proper TypeScript types
- [ ] Component handles all three cases: admin-only, user-only, any-authenticated
- [ ] File header comment present with @see and @note
  </done>
</task>

<task type="auto">
  <name>Task 2: Update App.tsx with role-based routing</name>
  <files>AURA-CHAT/client/src/App.tsx</files>
  <action>
Update `AURA-CHAT/client/src/App.tsx` to use `RoleProtectedRoute` with role restrictions:

**Current routes to modify:**
- `/chat` (index), `/documents`, `/graph` → Add `requireUser` prop (block admins)
- `/settings`, `/usage` → Add `requireAdmin` prop (block regular users)

**Implementation:**
1. Import `RoleProtectedRoute` from `@/components/RoleProtectedRoute`
2. Replace `ProtectedRoute` with `RoleProtectedRoute` for all protected routes
3. Add `requireUser` prop to chat, documents, graph routes
4. Add `requireAdmin` prop to settings, usage routes
5. Keep the route structure identical (nested under MainLayout)

**Example structure:**
```tsx
<Route element={<RoleProtectedRoute requireUser />}>
  <Route path="chat" element={<ChatPage />} />
  ...
</Route>
<Route element={<RoleProtectedRoute requireAdmin />}>
  <Route path="settings" element={<SettingsPage />} />
  ...
</Route>
```

**Note:** The index route (`/`) should also use `requireUser` since it redirects to chat.
  </action>
  <verify>
Type check: `cd AURA-CHAT/client && npx tsc --noEmit`
Build check: `cd AURA-CHAT/client && npm run build`
  </verify>
  <done>
- [ ] All user pages (chat, documents, graph) use `requireUser` prop
- [ ] All admin pages (settings, usage) use `requireAdmin` prop
- [ ] Build passes without errors
- [ ] Routing structure preserved (routes still nested under MainLayout)
  </done>
</task>

<task type="auto">
  <name>Task 3: Update MainLayout with role-filtered navigation</name>
  <files>AURA-CHAT/client/src/components/MainLayout.tsx</files>
  <action>
Update `AURA-CHAT/client/src/components/MainLayout.tsx` to conditionally show navigation items based on user role:

**Current behavior:** `navItems` array (lines 47-78) is rendered for all users.

**Changes needed:**
1. Import `useAuthStore` (already imported, just add `isAdmin` getter access)
2. Add `isAdmin` getter from auth store: `const isAdmin = useAuthStore((s) => s.isAdmin);`
3. Filter `navItems` before rendering in `renderNavItems`:
   - Admin users should ONLY see: `/settings`, `/usage`
   - Non-admin users should see: `/` (chat), `/documents`, `/graph`
   - Both roles can see settings and usage in their respective views

**Implementation approach:**
- Create filtered nav items based on `isAdmin()` result:
  - If admin: filter to only items with path `/settings` or `/usage`
  - If not admin: filter to exclude `/settings` and `/usage`
- Apply this filter in `renderNavItems` before mapping over items

**Edge cases to handle:**
- Mobile menu (drawer) should also respect role filtering
- Hide "Recent" sessions section for admins (they don't have chat access)
- Keep user profile section visible for all (shows role badge)

**Visual indicator:**
- The existing role badge (lines 363-370) already shows "staff" or "student" — this is fine, admins will see their role displayed
  </action>
  <verify>
Type check: `cd AURA-CHAT/client && npx tsc --noEmit`
Build check: `cd AURA-CHAT/client && npm run build`
  </verify>
  <done>
- [ ] Admins see only Settings and Usage in navigation
- [ ] Non-admins see only Chat, Documents, Graph in navigation
- [ ] "Recent" sessions section hidden for admins
- [ ] Mobile navigation also respects role filtering
- [ ] Build passes without errors
  </done>
</task>

</tasks>

<verification>
**Manual verification steps:**
1. Login as admin user → Should redirect to /usage, see only Settings/Usage in nav
2. Try to navigate to /chat as admin → Should redirect to /usage
3. Login as student/staff → Should redirect to /chat, see only Chat/Documents/Graph in nav
4. Try to navigate to /settings as student → Should redirect to /chat
5. Usage page shows cumulative data (already working - no backend change needed)

**Automated verification:**
- TypeScript compilation passes
- Build completes successfully
</verification>

<success_criteria>
- Admin users are blocked from chat, documents, graph pages (auto-redirect)
- Admin users can access settings and usage pages
- Non-admin users are blocked from settings and usage pages (auto-redirect)
- Non-admin users can access chat, documents, graph pages
- Navigation sidebar shows only role-appropriate items
- No console errors or TypeScript issues
</success_criteria>

<output>
After completion, create `.planning/quick/9-implement-admin-vs-user-access-control-r/9-SUMMARY.md`
</output>
