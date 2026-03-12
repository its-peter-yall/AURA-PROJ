---
phase: quick
plan: 15
subsystem: AURA-NOTES-MANAGER
tags: [settings, health-monitoring, ui-parity, rewrite]
dependency_graph:
  requires: [quick-13, quick-14]
  provides: [settings-health-monitoring, system-status-panel]
  affects: [AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx, AURA-NOTES-MANAGER/frontend/src/api/client.ts]
tech-stack:
  added: [checkHealth polling, StatusBadge component]
  patterns: [TanStack Query auto-refresh, 1/3+2/3 grid layout]
key-files:
  created: []
  modified:
    - AURA-NOTES-MANAGER/frontend/src/api/client.ts
    - AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx
decisions:
  - "Map health endpoints: /health (liveness) → API Server, /ready (readiness) → services_ready, /health/redis → neo4j_connected"
  - "No back button in rewritten page — matches AURA-CHAT conventions"
  - "About section updated from Notes Manager-specific text to AURA (Academic Research Assistant)"
metrics:
  duration: ~8 min
  completed: 2026-03-12
  tasks_completed: 3
  files_modified: 2
---

# Phase Quick Plan 15: Rewrite AURA-NOTES-MANAGER SettingsPage Summary

One-liner: Rewrote AURA-NOTES-MANAGER SettingsPage.tsx to exactly mirror AURA-CHAT's SettingsPage.tsx — adding System Status health monitoring with auto-refresh, StatusBadge component, and updated About section, while preserving all existing configuration sections.

## What Was Done

### Task 1: Add checkHealth function to API client

Added `HealthStatus` interface and `checkHealth()` async function to `frontend/src/api/client.ts`:

- **HealthStatus interface**: `{ status, version, neo4j_connected, services_ready }`
- **checkHealth()**: Queries three backend health endpoints (`/health`, `/ready`, `/health/redis`) to compose a comprehensive health status
- Graceful fallback returns `degraded` status if any endpoint fails
- Follows existing typed `fetchApi` wrapper patterns

**Commit:** `2dfd0e9`

### Task 2: Rewrite SettingsPage.tsx to match AURA-CHAT structure

Completely rewrote `frontend/src/pages/SettingsPage.tsx` (96 → 206 lines):

**Added:**
- System Status section with real-time health monitoring
- StatusBadge inline component (green/red badges)
- Health query using TanStack Query `useQuery` with 30s auto-refresh
- Manual refresh button with spinning animation
- Three status rows: API Server, Neo4j Database, Backend Services
- Updated About section to "AURA (Academic Research Assistant)" with feature list

**Removed:**
- Back button (ArrowLeft navigation) — AURA-CHAT doesn't have it

**Preserved:**
- Provider Configuration section with ProviderSettingsSection
- Default Models section with DefaultModelSection
- API Credentials section with ApiKeyManager
- 1/3 sidebar + 2/3 main config grid layout
- All existing imports and component usage

**Commit:** `50ec4cc`

### Task 3: Verify build passes

- TypeScript type check (`npx tsc --noEmit`): ✅ No errors
- ESLint (`npm run lint`): ✅ No errors

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fix cn import path convention**
- **Found during:** Task 2
- **Issue:** Initially imported `cn` from `../lib/cn` using relative path
- **Fix:** Changed to `@/lib/cn` to match project convention (all other files use `@/` alias)
- **Files modified:** SettingsPage.tsx
- **Commit:** `50ec4cc`

**2. [Rule 3 - Blocking] Fix checkHealth import path convention**
- **Found during:** Task 2
- **Issue:** Initially imported `checkHealth` from `../api/client` using relative path
- **Fix:** Changed to `@/api/client` to match project convention
- **Files modified:** SettingsPage.tsx
- **Commit:** `50ec4cc`

**3. [Rule 1 - Bug] Fix typo in checkHealth variable name**
- **Found during:** Task 1
- **Issue:** Typo `neojConnected` instead of `neo4jConnected` in Redis health check catch block
- **Fix:** Corrected to `neo4jConnected`
- **Files modified:** client.ts
- **Commit:** `2dfd0e9`

## Authentication Gates

None — no authentication required for this task.

## Verification Checklist

- [x] SettingsPage.tsx renders System Status with live health data
- [x] StatusBadge shows green/red based on service status
- [x] About section describes AURA (Academic Research Assistant)
- [x] Grid layout is 1/3 sidebar + 2/3 main config
- [x] No back button present (matching AURA-CHAT)
- [x] TypeScript compiles cleanly
- [x] Lint passes

## Key Decisions

1. **Health endpoint mapping**: AURA-NOTES-MANAGER doesn't have a combined health endpoint like AURA-CHAT. Mapped three separate endpoints: `/health` → liveness, `/ready` → Firestore readiness, `/health/redis` → cache status → composed into HealthStatus shape.

2. **Layout parity**: Kept the existing `lg:order-2` and `lg:order-1` grid ordering to place System Status + About on the right (sidebar) and configuration on the left (main), matching AURA-CHAT's visual structure.

## Self-Check: PASSED

- ✅ `AURA-NOTES-MANAGER/frontend/src/api/client.ts` — FOUND (313 lines, checkHealth exported)
- ✅ `AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx` — FOUND (206 lines, StatusBadge component present)
- ✅ Commit `2dfd0e9` — FOUND (checkHealth function)
- ✅ Commit `50ec4cc` — FOUND (SettingsPage rewrite)
