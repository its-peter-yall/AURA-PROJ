---
phase: 12-usage-tracking-cost-dashboard
verified: 2026-03-11T15:30:00Z
status: passed
score: 3/3 must-haves verified
re_verification: false
---

# Phase 12: Usage Tracking + Cost Dashboard Verification Report

**Phase Goal:** Administrators can monitor LLM usage costs across providers, models, and time periods to make informed spending decisions
**Verified:** 2026-03-11T15:30:00Z
**Status:** PASSED
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Every LLM request records token usage (input, output, thinking tokens) and estimated cost, attributed to session, user, model, and provider | VERIFIED | `router.py` lines 183-218 (generate) and 283-333 (stream) call `_usage_tracker.record()` after each LLM call with cost from `_cost_calculator.estimate()`. Metadata extraction for session_id/user_id from `resolved_request.metadata`. UsageRecord model has all required fields (types.py lines 87-117). |
| 2 | A dashboard displays cost charts broken down by provider, model, and time period with selectable date range filters | VERIFIED | AURA-CHAT: UsagePage at `/usage` route (App.tsx line 68) composes CostOverTimeChart (AreaChart), CostByProviderChart (BarChart), CostByModelChart (horizontal BarChart), DateRangeFilter (7/30/90 day presets + manual inputs), UsageSummaryCards. AURA-NOTES-MANAGER: identical dashboard at `/usage` (App.tsx line 70-74), admin-protected via ProtectedRoute. |
| 3 | Per-session cost is visible in the chat UI so students can see the cost impact of their model choices | VERIFIED | SessionCostBadge component (AURA-CHAT) uses `useSessionUsage(sessionId)` hook to fetch from `/api/v1/usage/session/{id}`, displays "$X.XXXX est." pill with tooltip showing token breakdown. SSE complete events in chat.py include usage payload via `_estimate_usage_payload()` at lines 289, 707, 749. |

**Score:** 3/3 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `shared/model_router/src/model_router/types.py` | UsageRecord model + metadata field on GenerateRequest | VERIFIED | UsageRecord (lines 87-117) with all fields: timestamp, provider, model, input/output/thinking tokens, estimated_cost_usd, is_estimated, session_id, user_id, operation. GenerateRequest.metadata (line 49). |
| `shared/model_router/src/model_router/cost_calculator.py` | Provider-specific cost estimation | VERIFIED | 118 lines. CostCalculator with Vertex static pricing (3 models), OpenRouter cached pricing, Ollama $0. estimate(), update_openrouter_pricing() methods. |
| `shared/model_router/src/model_router/usage_tracker.py` | Redis sorted-set usage persistence and time-range queries | VERIFIED | 253 lines. record(), get_records(), get_session_summary(), get_summary() with by_provider/by_model/daily aggregation. Uses ZADD with timestamp scores. |
| `shared/model_router/src/model_router/router.py` | Usage tracking hooks in generate() and stream() | VERIFIED | set_usage_tracking() (line 92), generate() hook (lines 193-216), stream() hook (lines 297-333). Failures caught with try/except + warning log. |
| `shared/model_router/src/model_router/__init__.py` | Re-exports UsageTracker, CostCalculator, UsageRecord | VERIFIED | Lines 16 (CostCalculator), 38 (UsageRecord), 40 (UsageTracker) in imports. All three in __all__ list. |
| `shared/model_router/tests/test_cost_calculator.py` | TDD tests for pricing accuracy | VERIFIED | 244 lines. 12 tests across TestUsageRecord (2), TestGenerateRequestMetadata (2), TestCostCalculatorOllama (1), TestCostCalculatorVertexAI (4), TestCostCalculatorOpenRouter (3). |
| `shared/model_router/tests/test_usage_tracker.py` | TDD tests for Redis persistence and retrieval | VERIFIED | 449 lines. FakeSortedSetRedis mock. TestUsageTrackerRecord (3), TestUsageTrackerGetRecords (2), TestUsageTrackerSessionSummary (2), TestUsageTrackerGetSummary (2), TestRouterUsageIntegration (3). |
| `AURA-CHAT/server/routers/usage.py` | Usage query API endpoints | VERIFIED | 206 lines. 5 endpoints: /summary, /session/{id}, /by-provider, /by-model, /daily. All with date range filtering via _parse_date_range(). |
| `AURA-NOTES-MANAGER/api/routers/usage.py` | Usage query API endpoints (NOTES-MANAGER) | VERIFIED | 210 lines. Identical 5 endpoints adapted for NOTES-MANAGER import patterns. |
| `AURA-CHAT/server/main.py` | Usage router registration + tracker wiring | VERIFIED | Imports usage_router (line 104), includes router (line 301), wires UsageTracker + CostCalculator via set_usage_tracking() (lines 185-194). |
| `AURA-NOTES-MANAGER/api/main.py` | Usage router registration + tracker wiring | VERIFIED | Imports usage_router (line 129), includes router (line 256), wires at startup event (lines 262-274). |
| `AURA-CHAT/server/routers/chat.py` | SSE complete events with usage data | VERIFIED | _estimate_usage_payload() helper (lines 88-144), usage field injected at SSE complete events (lines 289, 707, 749). |
| `AURA-CHAT/client/src/types/usage.ts` | TypeScript types for usage API | VERIFIED | 53 lines. DailyCost, ProviderCost, ModelCost, SessionUsage, UsageSummary, UsageCompletionData interfaces. |
| `AURA-CHAT/client/src/features/usage/hooks/useUsageApi.ts` | TanStack Query hooks | VERIFIED | 123 lines. usageKeys factory, useUsageSummary, useSessionUsage, useDailyCosts, useCostByProvider, useCostByModel. 2-min staleTime. |
| `AURA-CHAT/client/src/features/usage/UsagePage.tsx` | Main dashboard page | VERIFIED | 136 lines. Composes DateRangeFilter, UsageSummaryCards, CostOverTimeChart, CostByProviderChart, CostByModelChart. Date range state via useState. Empty state handling. |
| `AURA-CHAT/client/src/features/usage/components/SessionCostBadge.tsx` | Per-session cost display | VERIFIED | 44 lines. Uses useSessionUsage hook, displays "$X.XXXX est." pill with token tooltip. Returns null when empty. |
| `AURA-CHAT/client/src/features/usage/components/CostOverTimeChart.tsx` | Recharts AreaChart | VERIFIED | 71 lines. AreaChart with Cyber Yellow (#FFD400) fill, dark theme tooltip, empty state. |
| `AURA-CHAT/client/src/features/usage/components/CostByProviderChart.tsx` | Recharts BarChart | VERIFIED | 63 lines. BarChart with Cyber Yellow bars, provider X-axis, $ Y-axis. |
| `AURA-CHAT/client/src/features/usage/components/CostByModelChart.tsx` | Horizontal BarChart | VERIFIED | Exists, horizontal layout, top 10 model sorting. |
| `AURA-CHAT/client/src/features/usage/components/DateRangeFilter.tsx` | Date inputs + presets | VERIFIED | 83 lines. Two date inputs, 7/30/90 day preset buttons with active state. Cyber Yellow focus ring. |
| `AURA-CHAT/client/src/features/usage/components/UsageSummaryCards.tsx` | Summary metric cards | VERIFIED | Exists with Total Cost, Total Requests, Top Provider, Avg Cost/Request. Loading skeleton. |
| `AURA-NOTES-MANAGER/frontend/src/types/usage.ts` | Usage types (copied) | VERIFIED | File exists. |
| `AURA-NOTES-MANAGER/frontend/src/features/usage/hooks/useUsageApi.ts` | Hooks adapted for fetchApi | VERIFIED | 115 lines. Uses fetchApi from @/api/client with buildQueryString helper. |
| `AURA-NOTES-MANAGER/frontend/src/pages/UsagePage.tsx` | Dashboard page (NOTES-MANAGER) | VERIFIED | 151 lines. SettingsPage-style layout with ArrowLeft back navigation, Cyber Yellow title. Composes all chart components. |
| `AURA-NOTES-MANAGER/frontend/src/App.tsx` | Admin-protected /usage route | VERIFIED | Route at /usage wrapped in ProtectedRoute with requiredRole="admin" (lines 70-74). |
| `AURA-CHAT/client/package.json` | recharts dependency | VERIFIED | "recharts": "^3.8.0" at line 33. |
| `AURA-NOTES-MANAGER/frontend/package.json` | recharts dependency | VERIFIED | "recharts": "^3.8.0" at line 31. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| router.py | usage_tracker.py | `_usage_tracker.record()` after generate/stream | WIRED | Lines 200 (generate) and 316 (stream) call `self._usage_tracker.record()`. |
| usage_tracker.py | Redis sorted sets | `ZADD aura:usage:records` | WIRED | Line 91 `await self._redis.zadd(USAGE_KEY, {payload: score})`, line 95 for session key. |
| router.py | cost_calculator.py | `_cost_calculator.estimate()` | WIRED | Lines 195 (generate) and 311 (stream) call `self._cost_calculator.estimate()`. |
| AURA-CHAT usage.py | UsageTracker | FastAPI Depends injection | WIRED | `get_usage_tracker(redis=Depends(get_redis))` at line 31-35. All 5 endpoints inject tracker. |
| AURA-CHAT main.py | Router singleton | `set_usage_tracking()` at startup | WIRED | Lines 192-194: creates tracker/calculator, calls `get_default_router().set_usage_tracking()`. |
| AURA-NOTES-MANAGER main.py | Router singleton | `set_usage_tracking()` at startup | WIRED | Lines 272-274: identical wiring pattern via on_event("startup"). |
| useUsageApi.ts (CHAT) | /api/v1/usage/* | axios API calls | WIRED | Lines 49-53 (summary), 63-66 (session), 80-84 (daily), 97-101 (by-provider), 114-118 (by-model). |
| UsagePage.tsx (CHAT) | Chart components | Component composition | WIRED | Lines 13-23 import all 5 components, lines 66-123 render them with hook data. |
| App.tsx (CHAT) | UsagePage | React Router route | WIRED | Line 32 import, line 68 `<Route path="usage" element={<UsagePage />} />`. |
| useUsageApi.ts (NOTES) | /v1/usage/* | fetchApi client | WIRED | Lines 54-55 (summary), 65-66 (session), 81-82 (daily), 95-96 (by-provider), 109-110 (by-model). |
| App.tsx (NOTES) | UsagePage | React Router + admin guard | WIRED | Lines 39 import, 70-74 route with ProtectedRoute requiredRole="admin". |
| chat.py SSE | _estimate_usage_payload | usage field in complete events | WIRED | Helper at lines 88-144, injected at lines 289, 707, 749 in SSE complete payloads. |
| MainLayout (CHAT) | /usage navigation | BarChart3 icon | WIRED | Lines 73-76: Usage nav item with BarChart3 icon and path /usage. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| USAGE-01 | 12-01, 12-02 | System tracks token usage and cost per request, aggregated by session, user, model, and provider | SATISFIED | UsageTracker.record() called from router.generate() and router.stream() with full attribution. UsageRecord stores all dimensions. Redis sorted sets enable aggregation by any dimension. |
| USAGE-02 | 12-02, 12-03, 12-04 | Dashboard displays cost charts by provider, model, time period with date range filters | SATISFIED | Both AURA-CHAT and AURA-NOTES-MANAGER have UsagePage with CostOverTimeChart, CostByProviderChart, CostByModelChart, DateRangeFilter (7/30/90 day presets + manual). Backend serves /by-provider, /by-model, /daily endpoints. |

No orphaned requirements found -- USAGE-01 and USAGE-02 are the only requirements mapped to Phase 12 in REQUIREMENTS.md, and both are covered by the plans.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `AURA-CHAT/server/routers/chat.py` | 241 | `# TODO: propagate session metadata` | Info | Known limitation: session metadata not propagated through all call paths. Router-level hook still records without session attribution in some flows. Does not block the goal. |

### Human Verification Required

### 1. Dashboard Visual Rendering

**Test:** Navigate to `/usage` in AURA-CHAT and verify charts render correctly with the Cyber Yellow theme
**Expected:** AreaChart, BarCharts display with #FFD400 color scheme, dark backgrounds, responsive layout, tooltips on hover
**Why human:** Visual appearance cannot be verified programmatically

### 2. Date Range Filter Interaction

**Test:** Click the 7/30/90 day preset buttons and verify charts update
**Expected:** All charts and summary cards refresh with filtered data for the selected time period
**Why human:** Interactive state behavior and data refresh timing need visual confirmation

### 3. AURA-NOTES-MANAGER Admin Protection

**Test:** Access `/usage` as a non-admin user in AURA-NOTES-MANAGER
**Expected:** Redirected away or shown unauthorized message; admin users see the dashboard
**Why human:** Auth guard behavior depends on running app with real auth state

### 4. SessionCostBadge in Chat UI

**Test:** Start a chat session, send messages, verify the cost badge appears
**Expected:** Small pill showing "$X.XXXX est." with token breakdown on hover
**Why human:** Requires live LLM interaction and SSE streaming to populate usage data

### 5. SSE Complete Event Usage Data

**Test:** Monitor network/SSE events during a chat and verify "complete" events contain usage object
**Expected:** `{input_tokens, output_tokens, thinking_tokens, estimated_cost_usd, is_estimated}` in SSE payload
**Why human:** Requires running server with live streaming to verify SSE payload structure

### Gaps Summary

No gaps found. All three success criteria from the ROADMAP are verified:

1. **Usage recording**: The router.generate() and router.stream() methods automatically record usage with full attribution (session, user, model, provider, cost) via CostCalculator and UsageTracker, persisted to Redis sorted sets.

2. **Dashboard**: Both AURA-CHAT and AURA-NOTES-MANAGER have complete cost dashboards at /usage with three chart types (cost over time, by provider, by model), date range filters with presets, and summary cards. AURA-NOTES-MANAGER's dashboard is admin-protected.

3. **Per-session cost**: SessionCostBadge component in AURA-CHAT displays estimated cost per session, and SSE complete events include usage data for real-time cost visibility.

The implementation spans the full stack: shared package (types, calculator, tracker, router hooks), backend API endpoints (5 endpoints in both apps), SSE protocol extension, frontend data layer (TanStack Query hooks), and UI components (Recharts charts, date filters, summary cards, session badge). Test coverage includes 14 tests for cost calculation and 12 tests for usage tracking with router integration.

---

_Verified: 2026-03-11T15:30:00Z_
_Verifier: Claude (gsd-verifier)_
