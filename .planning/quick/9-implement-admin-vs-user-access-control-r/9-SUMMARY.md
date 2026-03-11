---
phase: quick
plan: 9
plan_name: implement-admin-vs-user-access-control-r
subsystem: AURA-CHAT Frontend
status: complete
tags: [auth, rbac, security, react]
dependency_graph:
  requires: []
  provides: [role-based-access-control]
  affects: [AURA-CHAT routing, AURA-CHAT navigation]
tech_stack:
  added: []
  patterns:
    - "Role-based route guards with RoleProtectedRoute component"
    - "Zustand auth store with isAdmin() getter"
    - "Conditional navigation rendering based on user role"
key_files:
  created:
    - AURA-CHAT/client/src/components/RoleProtectedRoute.tsx
  modified:
    - AURA-CHAT/client/src/stores/useAuthStore.ts
    - AURA-CHAT/client/src/App.tsx
    - AURA-CHAT/client/src/components/MainLayout.tsx
decisions:
  - "Created separate RoleProtectedRoute component rather than modifying ProtectedRoute to maintain backward compatibility"
  - "Used requireAdmin/requireUser boolean props for clear intent over string-based role checking"
  - "Redirect admins trying user pages to /usage, users trying admin pages to /chat"
  - "Admin role badge styled with purple color to distinguish from staff (blue) and student (green)"
metrics:
  duration_minutes: 15
  completed_date: "2026-03-11"
  tasks_completed: 3
  files_created: 1
  files_modified: 3
---

# Quick Task 9: Implement Admin vs User Access Control Summary

**One-liner:** Implemented strict role-based access control separating admin and regular user permissions with route guards and role-filtered navigation.

## Overview

This quick task implemented comprehensive role-based access control (RBAC) for AURA-CHAT, ensuring:
- **Admin users** can only access system management pages (Settings, Usage)
- **Regular users** (students/staff) can only access academic features (Chat, Documents, Graph)
- Unauthorized access attempts automatically redirect to appropriate permitted pages

## Implementation Details

### Task 1: isAdmin Getter + RoleProtectedRoute Component

**Changes to `useAuthStore.ts`:**
- Added `isAdmin: () => boolean` to AuthState interface
- Implemented `isAdmin: () => get().user?.role === 'admin'` getter

**New `RoleProtectedRoute.tsx` component:**
- Supports `requireAdmin` and `requireUser` mutually exclusive props
- Shows loading spinner during Firebase auth initialization
- Redirects non-authenticated users to `/login`
- Redirects non-admins from admin pages to `/chat`
- Redirects admins from user pages to `/usage`
- Uses `Navigate` from react-router-dom for client-side redirects

### Task 2: Role-Based Routing Configuration

**Changes to `App.tsx`:**
- Replaced `ProtectedRoute` with `RoleProtectedRoute` for all protected routes
- User-only routes (`/`, `/chat`, `/documents`, `/graph`) use `requireUser` prop
- Admin-only routes (`/settings`, `/usage`) use `requireAdmin` prop
- Each route group has its own `MainLayout` to handle role-specific rendering

### Task 3: Role-Filtered Navigation

**Changes to `MainLayout.tsx`:**
- Added `isAdmin` getter from useAuthStore
- Filtered `navItems` array based on user role:
  - Admins see only: Settings, Usage
  - Non-admins see only: Chat, Documents, Graph
- Hidden "Recent" sessions section for admins (they don't have chat access)
- Added admin role badge styling (purple) to distinguish from staff (blue) and student (green)
- Applied role filtering to both desktop sidebar and mobile drawer navigation

## Access Matrix Verification

| Page | Admin | Student/Staff | Verified |
|------|-------|---------------|----------|
| /chat | ❌ BLOCKED | ✅ ALLOWED | ✓ |
| /documents | ❌ BLOCKED | ✅ ALLOWED | ✓ |
| /graph | ❌ BLOCKED | ✅ ALLOWED | ✓ |
| /settings | ✅ ALLOWED | ❌ BLOCKED | ✓ |
| /usage | ✅ ALLOWED | ❌ BLOCKED | ✓ |

## Technical Architecture

```
User Navigates to Route
    ↓
RoleProtectedRoute (with requireAdmin/requireUser)
    ↓
Authentication Check → Redirect to /login if not authenticated
    ↓
Role Check:
    - requireAdmin + not admin → Redirect to /chat
    - requireUser + is admin → Redirect to /usage
    ↓
Render MainLayout
    ↓
Role-Filtered Navigation Items
```

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Hash | Message | Files |
|------|---------|-------|
| 8c7acc4 | feat(quick-9): add isAdmin getter and RoleProtectedRoute component | useAuthStore.ts, RoleProtectedRoute.tsx |
| 50cfbf2 | feat(quick-9): implement role-based routing in App.tsx | App.tsx |
| b15a2c7 | feat(quick-9): implement role-filtered navigation in MainLayout | MainLayout.tsx |

## Verification

- ✅ TypeScript compilation passes with no errors
- ✅ Production build completes successfully
- ✅ No console warnings or errors
- ✅ All route guards implemented as specified
- ✅ Navigation filtering applied to both desktop and mobile

## Notes for Future Maintenance

1. **Route redirects:** When adding new routes, ensure they are placed in the appropriate role-protected section
2. **Navigation items:** Update `navItems` array and filtering logic when adding new navigation items
3. **Role expansion:** If adding new roles, extend the boolean props approach or switch to array-based allowedRoles
4. **Testing:** Add E2E tests for role-based routing scenarios (admin blocked from chat, user blocked from settings)
