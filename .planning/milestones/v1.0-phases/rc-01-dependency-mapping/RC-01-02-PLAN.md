---
phase: rc-01-dependency-mapping
type: execute
plan: RC-01-02
---

<objective>
Map all frontend dependencies on kg-query feature scheduled for removal/migration.

Purpose: Identify all imports, routes, and navigation references to the kg-query feature before removal.
Output: Dependency report documenting all frontend references and migration requirements for EntityGraph.
</objective>

<execution_context>
@~/.config/opencode/skills/create-plans/workflows/execute-phase.md
@~/.config/opencode/skills/create-plans/templates/summary.md
</execution_context>

<context>
@.planning/RAG-CONSOLIDATION-BRIEF.md
@.planning/RAG-CONSOLIDATION-ROADMAP.md
@AURA-NOTES-MANAGER/frontend/src/features/kg-query/
@AURA-NOTES-MANAGER/frontend/src/App.tsx
@AURA-NOTES-MANAGER/frontend/src/routes/
</context>

<tasks>

<task type="auto">
  <name>Task 1: Map kg-query feature structure</name>
  <files>AURA-NOTES-MANAGER/frontend/src/features/kg-query/</files>
  <action>
    List all files in the kg-query feature directory:
    1. pages/ - Which pages exist
    2. components/ - Which components (especially EntityGraph.tsx for migration)
    3. hooks/ - Custom hooks
    4. api/ - API client functions
    5. types/ - TypeScript types
    
    Document the complete file tree with brief description of each file's purpose.
  </action>
  <verify>ls -la AURA-NOTES-MANAGER/frontend/src/features/kg-query/ (recursive)</verify>
  <done>Complete file tree of kg-query feature documented</done>
</task>

<task type="auto">
  <name>Task 2: Find route registration</name>
  <files>AURA-NOTES-MANAGER/frontend/src/App.tsx, AURA-NOTES-MANAGER/frontend/src/routes/</files>
  <action>
    Search for:
    1. Route definitions pointing to kg-query pages
    2. Lazy imports of KGQueryPage or similar
    3. Navigation menu items linking to kg-query routes
    
    Document:
    - Route path (e.g., "/kg-query", "/knowledge-graph")
    - Component imported
    - Where in routing config it's defined
  </action>
  <verify>grep -r "kg-query\|KGQuery\|knowledge-graph" AURA-NOTES-MANAGER/frontend/src/ --include="*.tsx" --include="*.ts"</verify>
  <done>Route registration location and path documented</done>
</task>

<task type="auto">
  <name>Task 3: Find navigation references</name>
  <files>AURA-NOTES-MANAGER/frontend/src/</files>
  <action>
    Search for navigation links to kg-query:
    1. Sidebar menu items
    2. Header navigation
    3. Button links from other pages
    4. useNavigate() calls to kg-query paths
    
    Document each reference with file path and line number.
  </action>
  <verify>grep -r "navigate.*kg\|to=.*kg\|href=.*kg" AURA-NOTES-MANAGER/frontend/src/ --include="*.tsx"</verify>
  <done>All navigation references documented for removal</done>
</task>

<task type="auto">
  <name>Task 4: Analyze EntityGraph component for migration</name>
  <files>AURA-NOTES-MANAGER/frontend/src/features/kg-query/components/EntityGraph.tsx</files>
  <action>
    Read EntityGraph.tsx and document:
    1. External dependencies (npm packages used, e.g., d3, react-force-graph)
    2. Internal imports (types, utilities from kg-query feature)
    3. Props interface
    4. API endpoints it calls
    5. Styling approach (CSS modules, styled-components, Tailwind)
    
    Assess migration complexity:
    - Can it be copied directly?
    - What internal dependencies need to also migrate?
    - What API changes are needed for AURA-CHAT?
  </action>
  <verify>Read file, document all imports</verify>
  <done>EntityGraph migration requirements documented with complexity assessment</done>
</task>

<task type="auto">
  <name>Task 5: Check for shared utilities</name>
  <files>AURA-NOTES-MANAGER/frontend/src/features/kg-query/, AURA-NOTES-MANAGER/frontend/src/utils/, AURA-NOTES-MANAGER/frontend/src/lib/</files>
  <action>
    Check if kg-query feature exports anything used by other features:
    1. Search for imports from kg-query in other features
    2. Check if any types are re-exported globally
    3. Verify EntityGraph isn't used elsewhere in the app
    
    Expected: kg-query should be self-contained (no exports to other features).
  </action>
  <verify>grep -r "from.*kg-query\|from.*features/kg-query" AURA-NOTES-MANAGER/frontend/src/ --include="*.tsx" --include="*.ts" | grep -v "kg-query/"</verify>
  <done>Confirmed kg-query has no external dependents (or documented if it does)</done>
</task>

<task type="auto">
  <name>Task 6: Create frontend dependency report</name>
  <files>.planning/phases/rc-01-dependency-mapping/FRONTEND-DEPENDENCIES.md</files>
  <action>
    Create a markdown file documenting:
    1. Complete kg-query file tree with descriptions
    2. Route registration (path and config location)
    3. Navigation references (files to update)
    4. EntityGraph migration requirements:
       - Dependencies to install in AURA-CHAT
       - Internal files to also migrate
       - API endpoint changes needed
       - Styling considerations
    5. Removal steps:
       - Files to delete
       - Route config changes
       - Navigation menu updates
  </action>
  <verify>File exists and contains all sections</verify>
  <done>FRONTEND-DEPENDENCIES.md created with complete analysis</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] kg-query feature structure fully documented
- [ ] Route and navigation references identified
- [ ] EntityGraph migration complexity assessed
- [ ] FRONTEND-DEPENDENCIES.md created
</verification>

<success_criteria>
- All tasks completed
- Clear understanding of what to delete vs migrate
- EntityGraph dependencies documented for AURA-CHAT migration
- No hidden dependencies that would break other features
</success_criteria>

<output>
After completion, create `.planning/phases/rc-01-dependency-mapping/RC-01-02-SUMMARY.md`
</output>
