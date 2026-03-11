---
phase: 11-add-navigation-to-settings-and-usage-pag
plan: 11
type: execute
wave: 1
depends_on: []
files_modified: ["AURA-NOTES-MANAGER/frontend/src/pages/AdminDashboard.tsx"]
autonomous: false
requirements: [UI-01, UI-02, USAGE-01, USAGE-02]
must_haves:
  truths:
    - "Admin can see 'Settings' button in AdminDashboard header"
    - "Admin can see 'Usage' button in AdminDashboard header"
    - "Clicking 'Settings' navigates to /settings"
    - "Clicking 'Usage' navigates to /usage"
    - "Buttons are styled with Cyber Yellow (#FFD400) theme"
  artifacts:
    - path: "AURA-NOTES-MANAGER/frontend/src/pages/AdminDashboard.tsx"
      provides: "Navigation to admin pages"
---

<objective>
Add navigation buttons in the AdminDashboard header to allow admins to quickly access the Settings and Usage pages in the AURA-NOTES-MANAGER frontend.
</objective>

<execution_context>
@./.gemini/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@AURA-NOTES-MANAGER/frontend/src/pages/AdminDashboard.tsx
@AURA-NOTES-MANAGER/frontend/src/App.tsx
@AURA-NOTES-MANAGER/frontend/src/styles/index.css
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add Navigation Buttons to AdminDashboard Header</name>
  <files>AURA-NOTES-MANAGER/frontend/src/pages/AdminDashboard.tsx</files>
  <action>
    1. Update imports: Add `Link` to the `react-router-dom` import line.
    2. Locate the header section (around line 1050).
    3. In the `<div className="header-actions">` block, add the following components before the Logout button:
       ```tsx
       <Link to="/settings" className="btn btn-primary">
           Settings
       </Link>
       <Link to="/usage" className="btn btn-primary">
           Usage
       </Link>
       ```
    4. Ensure the buttons use the `btn btn-primary` classes to inherit the Cyber Yellow (#FFD400) styling from `index.css`.
  </action>
  <verify>
    <automated>grep -E "Link to=\"/(settings|usage)\"" AURA-NOTES-MANAGER/frontend/src/pages/AdminDashboard.tsx</automated>
    <manual>Verify buttons are added to the JSX in the correct location.</manual>
    <sampling_rate>run after this task commits</sampling_rate>
  </verify>
  <done>Settings and Usage navigation buttons are added to the AdminDashboard header code.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task 2: Verify Navigation and Styling</name>
  <what-built>Navigation buttons in AdminDashboard header</what-built>
  <how-to-verify>
    1. Start the AURA-NOTES-MANAGER frontend (e.g., `cd AURA-NOTES-MANAGER/frontend && npm run dev`).
    2. Log in as an admin and navigate to the Admin Dashboard (`/admin`).
    3. Confirm the "Settings" and "Usage" buttons appear in the top-right header, next to Logout.
    4. Confirm they are styled with the Cyber Yellow (#FFD400) background and black text.
    5. Click "Settings" and verify it navigates to `/settings`.
    6. Go back and click "Usage" and verify it navigates to `/usage`.
  </how-to-verify>
  <resume-signal>approved</resume-signal>
</task>

</tasks>

<success_criteria>
- AdminDashboard header contains functional 'Settings' and 'Usage' links.
- Buttons match the Cyber Yellow design system.
- Navigation correctly directs users to the respective pages.
</success_criteria>

<output>
After completion, create `.planning/quick/11-add-navigation-to-settings-and-usage-pag/11-SUMMARY.md`
</output>
