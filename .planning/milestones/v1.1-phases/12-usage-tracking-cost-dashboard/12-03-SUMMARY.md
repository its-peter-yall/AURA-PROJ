---
phase: 12-usage-tracking-cost-dashboard
plan: 03
subsystem: ui
tags: [react, recharts, tanstack-query, typescript, cost-dashboard, charts]

# Dependency graph
requires:
  - phase: 12-usage-tracking-cost-dashboard
    provides: REST usage query endpoints and SSE completion usage payloads (Plan 02)
provides:
  - Full usage dashboard at /usage with date range filtering, summary cards, and 3 chart types
  - SessionCostBadge component for per-session cost display in chat UI
  - TanStack Query hooks for all 5 usage API endpoints
affects: [phase-12-frontend-tests, chat-ui-session-cost-integration]

# Tech tracking
tech-stack:
  added: [recharts@^3.8.0]
  patterns: [Recharts ResponsiveContainer with dark theme, date range state management via useState, query key factory for usage endpoints]

key-files:
  created: [AURA-CHAT/client/src/types/usage.ts, AURA-CHAT/client/src/features/usage/hooks/useUsageApi.ts, AURA-CHAT/client/src/features/usage/UsagePage.tsx, AURA-CHAT/client/src/features/usage/components/CostOverTimeChart.tsx, AURA-CHAT/client/src/features/usage/components/CostByProviderChart.tsx, AURA-CHAT/client/src/features/usage/components/CostByModelChart.tsx, AURA-CHAT/client/src/features/usage/components/DateRangeFilter.tsx, AURA-CHAT/client/src/features/usage/components/UsageSummaryCards.tsx, AURA-CHAT/client/src/features/usage/components/SessionCostBadge.tsx]
  modified: [AURA-CHAT/client/package.json, AURA-CHAT/client/src/App.tsx, AURA-CHAT/client/src/components/MainLayout.tsx]

key-decisions:
  - "Used Recharts 3.8 AreaChart for cost-over-time and BarChart for provider/model breakdowns with Cyber Yellow (#FFD400) theming."
  - "Added Usage nav item with BarChart3 icon to MainLayout sidebar alongside existing Settings link."
  - "SessionCostBadge returns null when no usage data exists, keeping it safe to embed anywhere in chat UI."

patterns-established:
  - "Usage query key factory follows the same pattern as settingsKeys in useSettingsApi.ts."
  - "Chart components accept typed data arrays and handle empty state internally."
  - "DateRangeFilter provides both manual date inputs and preset quick-select buttons."

requirements-completed: [USAGE-02]

# Metrics
duration: 5 min
completed: 2026-03-11
---

# Phase 12 Plan 03: Frontend Cost Dashboard with Recharts and Session Cost Badge Summary

**Recharts-powered cost dashboard at /usage with area/bar charts, date range filtering, summary stat cards, and per-session cost badge component for chat UI.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-11T09:25:02Z
- **Completed:** 2026-03-11T09:30:04Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- Installed Recharts and created 6 usage TypeScript types matching backend API response shapes.
- Built 5 TanStack Query hooks for all usage API endpoints with 2-minute stale time.
- Created 5 Recharts chart/filter/card components with Cyber Yellow dark theme styling.
- Built UsagePage composing all dashboard elements with date range state management and empty state handling.
- Created SessionCostBadge component for inline per-session cost display with token breakdown tooltip.
- Added /usage route and Usage navigation item with BarChart3 icon to the sidebar.

## Task Commits

Each task was committed atomically:

1. **Task 1: Install Recharts + types + hooks + chart components** - `b2f5e12` (feat)
2. **Task 2: UsagePage + SessionCostBadge + routing** - `18f3fbf` (feat)

**Submodule update:** `e4de7ca` (feat: update AURA-CHAT submodule)

_Plan metadata commit recorded after state/roadmap updates._

## Files Created/Modified
- `AURA-CHAT/client/src/types/usage.ts` - TypeScript interfaces for all usage API response types (DailyCost, ProviderCost, ModelCost, SessionUsage, UsageSummary, UsageCompletionData).
- `AURA-CHAT/client/src/features/usage/hooks/useUsageApi.ts` - TanStack Query hooks (useUsageSummary, useSessionUsage, useDailyCosts, useCostByProvider, useCostByModel) with query key factory.
- `AURA-CHAT/client/src/features/usage/components/CostOverTimeChart.tsx` - Recharts AreaChart for daily cost trends with Cyber Yellow fill.
- `AURA-CHAT/client/src/features/usage/components/CostByProviderChart.tsx` - Recharts BarChart for provider cost breakdown.
- `AURA-CHAT/client/src/features/usage/components/CostByModelChart.tsx` - Horizontal Recharts BarChart for top 10 models by cost.
- `AURA-CHAT/client/src/features/usage/components/DateRangeFilter.tsx` - Date inputs with 7/30/90-day preset buttons.
- `AURA-CHAT/client/src/features/usage/components/UsageSummaryCards.tsx` - Grid of metric cards (Total Cost, Total Requests, Top Provider, Avg Cost/Request) with loading skeleton.
- `AURA-CHAT/client/src/features/usage/UsagePage.tsx` - Main dashboard page composing all components with date range state.
- `AURA-CHAT/client/src/features/usage/components/SessionCostBadge.tsx` - Inline badge displaying per-session estimated cost with token tooltip.
- `AURA-CHAT/client/package.json` - Added recharts@^3.8.0 dependency.
- `AURA-CHAT/client/src/App.tsx` - Added /usage route with UsagePage inside protected route group.
- `AURA-CHAT/client/src/components/MainLayout.tsx` - Added Usage nav item with BarChart3 icon.

## Decisions Made
- Used Recharts 3.8 AreaChart for cost-over-time trends and BarChart for provider/model breakdowns, all themed with Cyber Yellow (#FFD400) on dark backgrounds.
- Added Usage navigation item with BarChart3 lucide icon to the MainLayout sidebar right after Settings.
- SessionCostBadge returns null when sessionId is empty or no usage data exists, so it can safely be embedded anywhere without conditional rendering at the parent level.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Usage dashboard is fully rendered at /usage route and accessible via sidebar navigation.
- SessionCostBadge is ready to be integrated into the chat input area or message header.
- All chart components accept typed data from TanStack Query hooks connected to Plan 02 backend endpoints.
- Plan 12-04 (frontend tests) can test all components and hooks created here.

---
*Phase: 12-usage-tracking-cost-dashboard*
*Completed: 2026-03-11*

## Self-Check: PASSED

- Verified all 9 created files exist on disk.
- Verified task commits `b2f5e12` and `18f3fbf` exist in AURA-CHAT git history.
- Verified submodule update commit `e4de7ca` exists in parent repo git history.
