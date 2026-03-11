---
quick_task: 10
description: Fix backend to allow admin login while maintaining route restrictions
created: "2026-03-11"
---

# Quick Task 10: Fix Admin Login

## Problem
Backend blocks admin users at `/auth/sync` endpoint with error "Admin users cannot access AURA Chat. Please use the Admin Panel."

This prevents admins from logging in entirely, but they should be able to log in and access usage/settings pages.

## Solution
Remove the admin block from `/auth/sync` endpoint. Frontend routing already restricts admin access to user pages.

## Tasks

### Task 1: Remove admin block from auth.py
**Files:** `AURA-CHAT/server/routers/auth.py`
**Action:** Remove lines 321-326 that block admin users from syncing
**Verify:** Admin users can successfully call `/auth/sync` and receive user data

### Task 2: Verify require_student_or_staff is used appropriately
**Files:** `AURA-CHAT/server/auth/dependencies.py`
**Action:** Ensure `require_student_or_staff` is used on chat/documents/graph API endpoints
**Verify:** Admin API calls to user-only endpoints return 403

## Notes
- Frontend already has RoleProtectedRoute preventing admin access to /chat, /documents, /graph
- Admin users should be able to access /usage and /settings (no backend restriction needed)
- `require_student_or_staff` dependency should remain for API endpoints that serve user-only features
