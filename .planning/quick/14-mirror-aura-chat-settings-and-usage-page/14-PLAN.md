---
phase: quick
plan: 14
type: execute
wave: 1
depends_on: []
files_modified:
  - AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx
  - AURA-NOTES-MANAGER/frontend/src/pages/UsagePage.tsx
autonomous: true
must_haves:
  truths:
    - "AURA-NOTES-MANAGER SettingsPage uses card-style containers with bg-card rounded-xl border border-border p-4 sm:p-6"
    - "SettingsPage maintains the back navigation button (NOTES-MANAGER specific)"
    - "SettingsPage uses flex flex-col h-full layout pattern from AURA-CHAT"
    - "UsagePage has responsive text sizing (text-xs sm:text-sm)"
    - "UsagePage has responsive padding (p-4 sm:p-6)"
    - "Both pages visually match AURA-CHAT styling patterns"
  artifacts:
    - path: "AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx"
      provides: "Card-style settings page with back button"
      changes:
        - "Add flex flex-col h-full wrapper structure"
        - "Wrap sections in bg-card rounded-xl border border-border p-4 sm:p-6"
        - "Add header with border-b border-border px-4 md:px-6 py-3 md:py-4"
        - "Keep back button in header section"
    - path: "AURA-NOTES-MANAGER/frontend/src/pages/UsagePage.tsx"
      provides: "Responsive usage dashboard"
      changes:
        - "Change text sizes to responsive variants (text-3xl -> text-xl sm:text-2xl)"
        - "Change p-4 md:p-8 to p-4 sm:p-6"
        - "Add responsive text classes to description text"
  key_links:
    - from: "AURA-NOTES-MANAGER/SettingsPage.tsx"
      to: "AURA-CHAT/SettingsPage.tsx"
      via: "Card-style layout pattern matching"
    - from: "AURA-NOTES-MANAGER/UsagePage.tsx"
      to: "AURA-CHAT/UsagePage.tsx"
      via: "Responsive typography and spacing"
---

<objective>
Mirror AURA-CHAT's SettingsPage and UsagePage styling patterns to AURA-NOTES-MANAGER while preserving NOTES-MANAGER-specific elements (back navigation button).

Purpose: Achieve visual consistency across both applications for a unified user experience.
Output: Updated SettingsPage.tsx and UsagePage.tsx with AURA-CHAT card-style layout and responsive patterns.
</objective>

<execution_context>
@C:/Users/Peter/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/Peter/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@AURA-CHAT/client/src/features/settings/SettingsPage.tsx
@AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx
@AURA-CHAT/client/src/features/usage/UsagePage.tsx
@AURA-NOTES-MANAGER/frontend/src/pages/UsagePage.tsx

## Key Differences to Address

### SettingsPage - AURA-CHAT (Source)
- Uses `flex flex-col h-full` container
- Header: `px-4 md:px-6 py-3 md:py-4 border-b border-border`
- Sections in cards: `bg-card rounded-xl border border-border p-4 sm:p-6`
- Grid layout: sidebar (1/3) + main content (2/3)
- Status badges with responsive sizing
- System Status and About sections

### SettingsPage - AURA-NOTES-MANAGER (Target)
- Uses `min-h-screen bg-[#0A0A0A]` layout
- Has back navigation button (keep this!)
- Sections NOT in card containers
- Simpler layout without grid structure

### UsagePage - AURA-CHAT (Source)
- Header: `text-xl sm:text-2xl` responsive sizing
- Description: `text-xs sm:text-sm mt-1`
- Padding: `p-4 sm:p-6`
- Empty state: `py-10 sm:py-16`

### UsagePage - AURA-NOTES-MANAGER (Target)
- Header: `text-3xl` (not responsive)
- Padding: `p-4 md:p-8` (different breakpoint)
- Has back navigation button (keep this!)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Update SettingsPage.tsx with Card-Style Layout</name>
  <files>AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx</files>
  <action>
    Transform AURA-NOTES-MANAGER SettingsPage.tsx to use AURA-CHAT's card-style layout:

    1. **Change container structure**:
       - Replace `min-h-screen bg-[#0A0A0A]` wrapper with `flex flex-col h-full`
       - Add outer wrapper: `<div className="flex flex-col h-full">`
       - Keep dark background: Add `bg-[#0A0A0A]` to appropriate element or rely on inherited theme

    2. **Add header section** (matching AURA-CHAT pattern):
       - Create `<header className="px-4 md:px-6 py-3 md:py-4 border-b border-border">`
       - Move back button and title into header
       - Title style: `text-xl font-semibold` (AURA-CHAT uses this, NOT NOTES-MANAGER's `text-3xl font-bold text-[#FFD400]`)
       - Keep back button: `<button onClick={() => navigate(-1)} className="...">`
       - Add subtitle: `<p className="text-sm text-muted-foreground">Configure AI providers...</p>`

    3. **Add content wrapper**:
       - Wrap main content in: `<div className="flex-1 overflow-y-auto p-4 md:p-6">`
       - Add inner container: `<div className="max-w-7xl mx-auto">`

    4. **Wrap sections in cards**:
       - Provider Configuration: Wrap in `<section className="bg-card rounded-xl border border-border p-4 sm:p-6">`
       - Default Models: Wrap in `<section className="bg-card rounded-xl border border-border p-4 sm:p-6">`
       - API Credentials: Wrap in `<section className="bg-card rounded-xl border border-border p-4 sm:p-6">`

    5. **Add section headers with icons** (optional but matches AURA-CHAT):
       - Use heading style: `text-base sm:text-lg font-semibold flex items-center gap-2 mb-4`
       - Provider: Add `<Shield className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />`
       - Models: Add `<Cpu className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />`
       - API Keys: Add `<Key className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />`

    6. **Import needed icons**:
       - Add: `import { Shield, Cpu, Key } from 'lucide-react';`

    7. **Preserve NOTES-MANAGER specific elements**:
       - Keep back button and navigate(-1) handler
       - Keep `max-w-4xl` constraint if desired (AURA-CHAT uses `max-w-7xl`)

    DO NOT:
    - Remove the back button
    - Change the component logic or API calls
    - Modify ProviderSettingsSection, DefaultModelSection, or ApiKeyManager internals
  </action>
  <verify>
    Run build in AURA-NOTES-MANAGER/frontend:
    ```bash
    cd AURA-NOTES-MANAGER/frontend && npm run build
    ```
    Verify no TypeScript or build errors.
  </verify>
  <done>
    SettingsPage.tsx uses:
    - [ ] `flex flex-col h-full` wrapper structure
    - [ ] Header with `px-4 md:px-6 py-3 md:py-4 border-b border-border`
    - [ ] Back button preserved in header
    - [ ] Content in `flex-1 overflow-y-auto p-4 md:p-6`
    - [ ] All three sections wrapped in `bg-card rounded-xl border border-border p-4 sm:p-6`
    - [ ] Section headings with icons (Shield, Cpu, Key)
    - [ ] Build passes without errors
  </done>
</task>

<task type="auto">
  <name>Task 2: Update UsagePage.tsx with Responsive Styling</name>
  <files>AURA-NOTES-MANAGER/frontend/src/pages/UsagePage.tsx</files>
  <action>
    Update AURA-NOTES-MANAGER UsagePage.tsx to match AURA-CHAT's responsive styling:

    1. **Update header structure**:
       - Current: `<h1 className="text-3xl font-bold tracking-tight text-[#FFD400]">`
       - Change to: `<h1 className="text-xl sm:text-2xl font-bold text-white">`
       - Remove `tracking-tight` and `text-[#FFD400]` (AURA-CHAT uses white text)

    2. **Update subtitle/description**:
       - Current: `<p className="text-muted-foreground">`
       - Change to: `<p className="text-gray-400 text-xs sm:text-sm mt-1">`
       - Add `mt-1` for spacing consistency

    3. **Update outer padding**:
       - Current: `p-4 md:p-8`
       - Change to: `p-4 sm:p-6`
       - Keep `min-h-screen bg-[#0A0A1A]` on container

    4. **Update empty state padding**:
       - Current: `py-16`
       - Change to: `py-10 sm:py-16`

    5. **Update empty state icon**:
       - Current: `w-16 h-16 mb-4`
       - Change to: `w-12 h-12 sm:w-16 sm:h-16 mb-4`

    6. **Preserve NOTES-MANAGER specific elements**:
       - Keep back button: `<button onClick={() => navigate(-1)}>...</button>`
       - Keep header structure with back button (NOTES-MANAGER pattern)
       - Don't change the grid structure or chart components

    7. **Optional: Add consistent container wrapper**:
       - Consider wrapping in `<div className="flex-1 overflow-y-auto min-h-0">` if layout needs it
       - Check if the page renders correctly with current structure first

    DO NOT:
    - Remove the back button
    - Change chart components or data fetching logic
    - Modify DateRangeFilter, UsageSummaryCards, or chart components
    - Change the color scheme beyond header text color
  </action>
  <verify>
    Run build in AURA-NOTES-MANAGER/frontend:
    ```bash
    cd AURA-NOTES-MANAGER/frontend && npm run build
    ```
    Verify no TypeScript or build errors.
  </verify>
  <done>
    UsagePage.tsx uses:
    - [ ] Header: `text-xl sm:text-2xl` (responsive, not fixed `text-3xl`)
    - [ ] Description: `text-xs sm:text-sm mt-1`
    - [ ] Outer padding: `p-4 sm:p-6` (uses sm breakpoint)
    - [ ] Empty state: `py-10 sm:py-16`
    - [ ] Empty state icon: `w-12 h-12 sm:w-16 sm:h-16`
    - [ ] Back button preserved
    - [ ] Build passes without errors
  </done>
</task>

</tasks>

<verification>
After both tasks complete:

1. **Visual comparison** (manual check):
   - AURA-CHAT SettingsPage at `http://127.0.0.1:5173/settings`
   - AURA-NOTES-MANAGER SettingsPage at `http://127.0.0.1:5173/settings`
   - AURA-CHAT UsagePage at `http://127.0.0.1:5173/usage`
   - AURA-NOTES-MANAGER UsagePage at `http://127.0.0.1:5174/usage` (or 5173)

2. **Verify responsive behavior**:
   - Resize browser to mobile width (<640px)
   - Verify padding and text sizes adapt correctly
   - Check that back buttons are visible and functional

3. **Build verification**:
   - Both pages compile without TypeScript errors
   - No broken imports or missing dependencies
</verification>

<success_criteria>
- SettingsPage.tsx has card-style layout matching AURA-CHAT
- SettingsPage retains back navigation button
- UsagePage.tsx has responsive text and padding classes
- UsagePage retains back navigation button
- Both pages build successfully
- Visual consistency achieved between applications
</success_criteria>

<output>
After completion, create `.planning/quick/14-mirror-aura-chat-settings-and-usage-page/14-SUMMARY.md`
</output>
