---
phase: 13-configure-and-implement-tailwind-css-v4-
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - AURA-NOTES-MANAGER/frontend/package.json
  - AURA-NOTES-MANAGER/frontend/tailwind.config.js
  - AURA-NOTES-MANAGER/frontend/postcss.config.js
  - AURA-NOTES-MANAGER/frontend/src/styles/index.css
  - AURA-NOTES-MANAGER/frontend/src/pages/UsagePage.tsx
  - AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx
  - AURA-NOTES-MANAGER/frontend/src/features/usage/components/*.tsx
  - AURA-NOTES-MANAGER/frontend/src/features/settings/components/*.tsx
autonomous: true

must_haves:
  truths:
    - "Tailwind CSS v4 is installed and configured"
    - "Custom theme colors match existing design system"
    - "UsagePage and SettingsPage use Tailwind utility classes"
    - "Build passes without errors"
  artifacts:
    - path: "AURA-NOTES-MANAGER/frontend/tailwind.config.js"
      provides: "Tailwind theme configuration with Cyber Yellow palette"
    - path: "AURA-NOTES-MANAGER/frontend/postcss.config.js"
      provides: "PostCSS configuration for Tailwind"
    - path: "AURA-NOTES-MANAGER/frontend/src/styles/index.css"
      provides: "Tailwind directives and base styles"
  key_links:
    - from: "tailwind.config.js"
      to: "index.css"
      via: "@import 'tailwindcss'"
---

<objective>
Configure Tailwind CSS v4 for AURA-NOTES-MANAGER frontend with a custom theme matching the existing Cyber Yellow design system, then migrate Usage and Settings pages to use Tailwind utility classes.

Purpose: Standardize styling with Tailwind's utility-first approach while preserving the existing visual design and maintaining consistency with the project's dark theme.
Output: Tailwind configuration, updated CSS entry point, and refactored page components.
</objective>

<execution_context>
@C:/Users/Peter/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/Peter/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@AURA-NOTES-MANAGER/frontend/package.json
@AURA-NOTES-MANAGER/frontend/src/styles/index.css

# Existing CSS design system values (to preserve):
# Primary: #FFD400 (Cyber Yellow)
# Backgrounds: #0a0a0a, #111111, #1a1a1a
# Text: #ffffff, #b0b0b0, #666666
# Border: #2a2a2a, #333333
# Status: success #22c55e, error #ef4444, warning #f59e0b, info #3b82f6
</context>

<tasks>

<task type="auto">
  <name>Task 1: Install Tailwind CSS v4 and Create Configuration</name>
  <files>
    AURA-NOTES-MANAGER/frontend/package.json
    AURA-NOTES-MANAGER/frontend/tailwind.config.js
    AURA-NOTES-MANAGER/frontend/postcss.config.js
  </files>
  <action>
    1. Install Tailwind CSS v4 and PostCSS:
       - Run `npm install -D tailwindcss@4 postcss autoprefixer` in AURA-NOTES-MANAGER/frontend
    
    2. Create tailwind.config.js with Cyber Yellow theme:
       - Primary: #FFD400 (and variants: #E6BF00 hover, rgba(255,212,0,0.15) dim, rgba(255,212,0,0.3) glow)
       - Backgrounds: #0a0a0a (primary), #111111 (secondary), #1a1a1a (tertiary), #252525 (hover)
       - Text: #ffffff (primary), #b0b0b0 (secondary), #666666 (muted), #FFD400 (accent)
       - Border: #2a2a2a (default), #333333 (light), #FFD400 (hover)
       - Status colors: success #22c55e, error #ef4444, warning #f59e0b, info #3b82f6
       - Font family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif
       - Border radius: 4px sm, 8px md, 12px lg
       - Spacing: 4px xs, 8px sm, 16px md, 24px lg, 32px xl
       
    3. Create postcss.config.js:
       - Configure with plugins: tailwindcss, autoprefixer
       - Use ESM format (type: module in package.json)
       
    4. Note: Preserve existing tailwind-merge dependency (already at v3.4.0)
  </action>
  <verify>
    - Run `cat tailwind.config.js` and verify theme.colors structure exists
    - Run `cat postcss.config.js` and verify plugins are configured
    - Run `npm list tailwindcss` and verify v4 is installed
  </verify>
  <done>
    Tailwind CSS v4 installed, tailwind.config.js and postcss.config.js exist with custom Cyber Yellow theme
  </done>
</task>

<task type="auto">
  <name>Task 2: Update CSS Entry Point with Tailwind Directives</name>
  <files>
    AURA-NOTES-MANAGER/frontend/src/styles/index.css
  </files>
  <action>
    1. Update index.css to use Tailwind v4 directives:
       - Add `@import "tailwindcss"` at the top
       - Add `@theme` block to define CSS variables and theme tokens
       - Keep existing custom properties for backwards compatibility during migration
       
    2. Preserve essential global styles:
       - Keep scrollbar styling (::webkit-scrollbar)
       - Keep selection styling (::selection with #FFD400 background)
       - Keep focus-visible outline (2px solid #FFD400)
       - Keep mobile overflow prevention (@media max-width: 768px for html, body, #root)
       - Keep reset for *, *::before, *::after (box-sizing: border-box)
       - Keep body and #root base styles
       
    3. Remove redundant utility classes that Tailwind provides:
       - All .flex, .flex-col, .items-center, .justify-*, .gap-* classes
       - All .text-*, .font-*, .uppercase, .tracking-* classes
       - All .rounded-*, .shadow-*, .border-* utility classes
       - All .w-*, .h-*, .p-*, .m-*, .space-* utility classes
       - All .grid, .grid-cols-* classes
       - All .card, .btn-* classes (these may be used by components, keep for now if needed)
       - All modal utility classes (may be used elsewhere, keep for now)
       
    4. Structure the file:
       - Section 1: @import "tailwindcss"
       - Section 2: @theme with custom CSS variables
       - Section 3: Reset & Base styles
       - Section 4: Scrollbar, Selection, Focus styles
       - Section 5: Mobile overflow prevention
       - Section 6: Legacy component classes (modal, card) - to be deprecated later
       
    5. Note: The @theme block in Tailwind v4 should define CSS custom properties that Tailwind uses
  </action>
  <verify>
    - Build passes: `npm run build` exits with code 0
    - No Tailwind-related errors in build output
    - Check that @import "tailwindcss" is present in index.css
  </verify>
  <done>
    index.css updated with Tailwind directives, essential styles preserved, build passes
  </done>
</task>

<task type="auto">
  <name>Task 3: Migrate Usage and Settings Pages to Tailwind</name>
  <files>
    AURA-NOTES-MANAGER/frontend/src/pages/UsagePage.tsx
    AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx
    AURA-NOTES-MANAGER/frontend/src/features/usage/components/UsageSummaryCards.tsx
    AURA-NOTES-MANAGER/frontend/src/features/usage/components/DateRangeFilter.tsx
    AURA-NOTES-MANAGER/frontend/src/features/usage/components/CostOverTimeChart.tsx
    AURA-NOTES-MANAGER/frontend/src/features/usage/components/CostByProviderChart.tsx
    AURA-NOTES-MANAGER/frontend/src/features/usage/components/CostByModelChart.tsx
    AURA-NOTES-MANAGER/frontend/src/features/settings/components/DefaultModelSection.tsx
    AURA-NOTES-MANAGER/frontend/src/features/settings/components/ApiKeyManager.tsx
    AURA-NOTES-MANAGER/frontend/src/features/settings/components/ProviderSettingsSection.tsx
    AURA-NOTES-MANAGER/frontend/src/features/settings/components/HierarchicalModelPicker.tsx
  </files>
  <action>
    1. Read each file first to understand current styling:
       - Note existing className patterns
       - Identify custom utility classes being used (from legacy index.css)
       - Map custom classes to Tailwind equivalents
       
    2. Migrate UsagePage.tsx:
       - Replace custom .flex, .flex-col, .gap-* with Tailwind classes
       - Replace custom color classes (text-primary, bg-secondary-theme) with Tailwind
       - Use arbitrary values for custom colors not in default Tailwind: text-[#FFD400], bg-[#0a0a0a]
       - Keep layout structure identical
       
    3. Migrate SettingsPage.tsx:
       - Same approach as UsagePage
       - Preserve form input styling (use Tailwind form patterns)
       - Update navigation links and buttons
       
    4. Migrate usage/components/*.tsx:
       - UsageSummaryCards: Card layouts, typography, spacing
       - DateRangeFilter: Form controls, layout
       - CostOverTimeChart: Chart container styling
       - CostByProviderChart: Chart container styling
       - CostByModelChart: Chart container styling
       
    5. Migrate settings/components/*.tsx:
       - DefaultModelSection: Form layout, selects, buttons
       - ApiKeyManager: Input fields, buttons, status indicators
       - ProviderSettingsSection: Card layout, toggles, forms
       - HierarchicalModelPicker: Tree navigation, selection UI
       
    6. Common Tailwind mappings for this project:
       - .text-primary (white) -> text-white
       - .text-secondary (#b0b0b0) -> text-gray-400 or text-[#b0b0b0]
       - .text-muted (#666666) -> text-gray-600 or text-[#666666]
       - .text-accent (#FFD400) -> text-[#FFD400]
       - .bg-primary-theme (#0a0a0a) -> bg-[#0a0a0a]
       - .bg-secondary-theme (#111111) -> bg-[#111111]
       - .bg-tertiary-theme (#1a1a1a) -> bg-[#1a1a1a]
       - .border (from CSS) -> border border-[#2a2a2a]
       - .card -> bg-[#111111] border border-[#2a2a2a] rounded-lg
       - .btn-primary -> bg-[#FFD400] text-black hover:bg-[#E6BF00]
       - .btn-secondary -> bg-[#1a1a1a] border border-[#2a2a2a] hover:border-[#FFD400]
       
    7. Use cn() utility from lib/cn.ts for conditional classes (already available)
    
    8. Ensure all transitions use Tailwind transition classes
    
    9. Keep existing component logic and structure - only change styling
  </action>
  <verify>
    - Build passes: `npm run build` exits with code 0
    - No TypeScript errors
    - Lint passes: `npm run lint` (or note any pre-existing issues)
    - Visual check: Compare UsagePage and SettingsPage appearance to screenshots
  </verify>
  <done>
    All Usage and Settings page components migrated to Tailwind classes, build passes, visual appearance preserved
  </done>
</task>

</tasks>

<verification>
1. Build verification:
   - Run `npm run build` in AURA-NOTES-MANAGER/frontend
   - Must complete with exit code 0
   - No Tailwind or PostCSS errors
   
2. Visual verification:
   - SettingsPage maintains dark theme with Cyber Yellow accents
   - UsagePage maintains chart layouts and styling
   - Focus rings appear in Cyber Yellow (#FFD400)
   - Scrollbars styled consistently
   - Selection highlight in Cyber Yellow
   
3. Functionality preservation:
   - All interactive elements work (buttons, forms, selects)
   - Navigation between pages works
   - No console errors related to styling
   
4. Code quality:
   - No inline styles (use Tailwind classes instead)
   - Consistent class ordering (use cn() utility)
   - No unused imports
</verification>

<success_criteria>
- [ ] Tailwind CSS v4 installed with PostCSS configuration
- [ ] tailwind.config.js created with custom Cyber Yellow theme
- [ ] index.css updated with @import "tailwindcss" and essential styles preserved
- [ ] UsagePage.tsx uses Tailwind utility classes exclusively
- [ ] SettingsPage.tsx uses Tailwind utility classes exclusively
- [ ] All usage/components/*.tsx use Tailwind classes
- [ ] All settings/components/*.tsx use Tailwind classes
- [ ] Build passes without errors
- [ ] Visual appearance matches existing design system
- [ ] No regression in functionality
</success_criteria>

<output>
After completion, create `.planning/quick/13-configure-and-implement-tailwind-css-v4-/13-01-SUMMARY.md` with:
- Files modified
- Tailwind configuration summary
- Migration notes for future components
- Any manual verification performed
</output>
