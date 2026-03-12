---
phase: quick
plan: 15
type: execute
wave: 1
depends_on: []
files_modified:
  - AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx
  - AURA-NOTES-MANAGER/frontend/src/api/client.ts
autonomous: true
must_haves:
  truths:
    - "Settings page shows System Status panel with API Server, Neo4j Database, and Backend Services health"
    - "System Status auto-refreshes every 30 seconds with manual refresh button"
    - "About section describes AURA Notes Manager capabilities"
    - "Provider Configuration, Default Models, and API Credentials sections remain intact"
    - "Layout uses 1/3 sidebar (Status + About) + 2/3 main config columns matching AURA-CHAT"
  artifacts:
    - path: "AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx"
      provides: "Settings page with System Status, About, and config sections"
      contains: "checkHealth, StatusBadge, useQuery"
    - path: "AURA-NOTES-MANAGER/frontend/src/api/client.ts"
      provides: "API client with checkHealth function"
      exports: ["checkHealth"]
  key_links:
    - from: "SettingsPage.tsx"
      to: "api/client.ts"
      via: "checkHealth import for health monitoring"
      pattern: "import.*checkHealth.*from.*api/client"
---

<objective>
Rewrite AURA-NOTES-MANAGER SettingsPage.tsx to exactly mirror AURA-CHAT SettingsPage.tsx styling, structure, and layout

Purpose: Achieve visual and structural parity between the two apps' settings pages
Output: Updated SettingsPage.tsx with System Status monitoring, StatusBadge, About section
</objective>

<execution_context>
@C:/Users/Peter/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/Peter/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@AURA-CHAT/client/src/features/settings/SettingsPage.tsx
@AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx
@AURA-NOTES-MANAGER/frontend/src/api/client.ts
</context>

<tasks>

<task type="auto">
  <name>Add checkHealth function to AURA-NOTES-MANAGER API client</name>
  <files>AURA-NOTES-MANAGER/frontend/src/api/client.ts</files>
  <action>
    Read the existing client.ts to understand current patterns, then add a checkHealth() function that calls GET /api/health endpoint. The function should return { status: string, version: string, neo4j_connected: boolean, services_ready: boolean }. Follow existing typed fetch wrapper patterns in the file. Use the existing fetchApi or raw fetch pattern — whichever the file currently uses.
  </action>
  <verify>Read client.ts to confirm checkHealth function exists with correct return type</verify>
  <done>checkHealth function is exported from api/client.ts with proper typing</done>
</task>

<task type="auto">
  <name>Rewrite SettingsPage.tsx to match AURA-CHAT structure exactly</name>
  <files>AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx</files>
  <action>
    Rewrite the entire SettingsPage.tsx to mirror AURA-CHAT's SettingsPage.tsx exactly. Key changes:

    1. **Remove** the back button (ArrowLeft navigation) — AURA-CHAT doesn't have it
    2. **Add** System Status section in the sidebar with:
       - Health query using TanStack Query (useQuery) with 30s auto-refresh
       - Manual refresh button with spinning animation
       - Three status rows: API Server (version + health), Neo4j Database (connected/disconnected), Backend Services (ready/not ready)
       - StatusBadge component (inline, green/red badges)
    3. **Update** About section text from "AURA Notes Manager" to "AURA (Academic Research Assistant)" with feature list matching AURA-CHAT's About section
    4. **Keep** Provider Configuration, Default Models, and API Credentials sections intact
    5. **Keep** the 1/3 sidebar + 2/3 main config grid layout
    6. **Match** all CSS classes, responsive breakpoints (sm:, md:, lg:), and spacing exactly from AURA-CHAT's SettingsPage.tsx

    Import checkHealth from api/client. Import useQuery from @tanstack/react-query. Import icons: Settings, Database, Zap, CheckCircle, XCircle, RefreshCw, Shield, Cpu, Key from lucide-react. Import cn from lib/utils.

    Use Tailwind CSS classes exactly as AURA-CHAT does. Keep the existing ProviderSettingsSection, DefaultModelSection, ApiKeyManager imports.
  </action>
  <verify>Read SettingsPage.tsx and compare structure line-by-line with AURA-CHAT's version. Confirm: System Status section exists, StatusBadge component exists, About section updated, health query with 30s interval, no back button.</verify>
  <done>SettingsPage.tsx structurally matches AURA-CHAT's SettingsPage.tsx with all sections (System Status, About, Provider Configuration, Default Models, API Credentials)</done>
</task>

<task type="auto">
  <name>Verify build passes after changes</name>
  <files>AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx</files>
  <action>
    Run TypeScript type check to ensure no errors: `cd AURA-NOTES-MANAGER/frontend && npx tsc --noEmit`. If errors appear, fix them before proceeding. Also run lint: `npm run lint`.
  </action>
  <verify>TypeScript compiles without errors, lint passes with no errors</verify>
  <done>Build verification complete — no type errors, no lint errors</done>
</task>

</tasks>

<verification>
- SettingsPage.tsx renders System Status with live health data
- StatusBadge shows green/red based on service status
- About section describes AURA Notes Manager
- Grid layout is 1/3 sidebar + 2/3 main config
- No back button present (matching AURA-CHAT)
- TypeScript compiles cleanly
</verification>

<success_criteria>
- System Status section with health monitoring (API Server, Neo4j, Backend Services)
- Auto-refresh every 30s + manual refresh button with spinner animation
- StatusBadge component with green/red status indicators
- About section matching AURA-CHAT's About section
- 3-column responsive grid layout (sidebar 1/3, main 2/3)
- No back button
- TypeScript compiles with no errors
- Lint passes
</success_criteria>

<output>
After completion, create `.planning/quick/15-entirely-rewrite-aura-notes-manager-sett/15-SUMMARY.md`
</output>
