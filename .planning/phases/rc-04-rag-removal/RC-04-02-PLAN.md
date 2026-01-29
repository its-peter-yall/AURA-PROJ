---
phase: rc-04-rag-removal
type: execute
plan: RC-04-02
---

<objective>
Remove frontend kg-query feature from AURA-NOTES-MANAGER.

Purpose: Delete the entire kg-query feature directory and route registration.
Output: Removed `frontend/src/features/kg-query/` directory and App.tsx references
</objective>

<execution_context>
@~/.config/opencode/skills/create-plans/workflows/execute-phase.md
@~/.config/opencode/skills/create-plans/templates/summary.md
</execution_context>

<context>
@.planning/RAG-CONSOLIDATION-BRIEF.md
@.planning/RAG-CONSOLIDATION-ROADMAP.md
@.planning/phases/rc-01-dependency-mapping/FRONTEND-DEPENDENCIES.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Document files to be deleted</name>
  <files>AURA-NOTES-MANAGER/frontend/src/features/kg-query/</files>
  <action>
    List all files in the kg-query feature for deletion confirmation:
    
    ```
    frontend/src/features/kg-query/
    ├── api/
    │   └── kg-query.api.ts           (347 lines)
    ├── components/
    │   ├── EntityGraph.tsx           (465 lines) - NOT migrated (AURA-CHAT has Reagraph)
    │   ├── GraphFilterPanel.tsx      (355 lines)
    │   ├── KGSearchBar.tsx           (523 lines)
    │   ├── SearchResultsList.tsx     (497 lines)
    │   └── UnifiedGraphView.tsx      (605 lines)
    ├── hooks/
    │   └── useKGQuery.ts             (226 lines)
    ├── pages/
    │   └── KGQueryPage.tsx           (386 lines)
    └── types/
        └── kg-query.types.ts         (347 lines)
    ```
    
    Total: 9 files, ~3,751 lines to delete
    
    Note: EntityGraph migration was SKIPPED because AURA-CHAT already has a 
    superior Reagraph-based implementation (GraphPage.tsx, 712 lines).
  </action>
  <verify>File list documented</verify>
  <done>All files to delete are identified</done>
</task>

<task type="auto">
  <name>Task 2: Update App.tsx - Remove import</name>
  <files>AURA-NOTES-MANAGER/frontend/src/App.tsx</files>
  <action>
    Remove the KGQueryPage import from App.tsx.
    
    Find and delete line 35 (approximately):
    ```typescript
    import { KGQueryPage } from './features/kg-query/pages/KGQueryPage'
    ```
  </action>
  <verify>Import statement removed</verify>
  <done>KGQueryPage import removed from App.tsx</done>
</task>

<task type="auto">
  <name>Task 3: Update App.tsx - Remove route</name>
  <files>AURA-NOTES-MANAGER/frontend/src/App.tsx</files>
  <action>
    Remove the kg-query route from App.tsx.
    
    Find and delete line 42 (approximately):
    ```tsx
    <Route path="/kg-query" element={<KGQueryPage />} />
    ```
  </action>
  <verify>Route element removed</verify>
  <done>kg-query route removed from App.tsx</done>
</task>

<task type="auto">
  <name>Task 4: Update App.tsx - Clean JSDoc</name>
  <files>AURA-NOTES-MANAGER/frontend/src/App.tsx</files>
  <action>
    Update the JSDoc comment to remove kg-query reference.
    
    Find line 25 (approximately) and update:
    ```diff
    - *    - Internal: pages/ExplorerPage, features/kg-query/pages/KGQueryPage
    + *    - Internal: pages/ExplorerPage
    ```
  </action>
  <verify>JSDoc updated</verify>
  <done>JSDoc comment cleaned in App.tsx</done>
</task>

<task type="auto">
  <name>Task 5: Delete kg-query feature directory</name>
  <files>AURA-NOTES-MANAGER/frontend/src/features/kg-query/</files>
  <action>
    Delete the entire kg-query feature directory:
    
    ```bash
    rm -rf AURA-NOTES-MANAGER/frontend/src/features/kg-query/
    ```
    
    This removes all 9 files (~3,751 lines of code).
  </action>
  <verify>Directory deleted, does not exist</verify>
  <done>kg-query feature directory removed</done>
</task>

<task type="auto">
  <name>Task 6: Verify TypeScript compilation</name>
  <files>AURA-NOTES-MANAGER/frontend/</files>
  <action>
    Run TypeScript type checking to ensure no broken imports:
    
    ```bash
    cd AURA-NOTES-MANAGER/frontend && npm run type-check
    ```
    
    Or if type-check script doesn't exist:
    ```bash
    cd AURA-NOTES-MANAGER/frontend && npx tsc --noEmit
    ```
    
    Fix any TypeScript errors before proceeding.
  </action>
  <verify>TypeScript compilation succeeds with no errors</verify>
  <done>Frontend type-checks successfully</done>
</task>

<task type="auto">
  <name>Task 7: Verify build succeeds</name>
  <files>AURA-NOTES-MANAGER/frontend/</files>
  <action>
    Run the production build to ensure everything compiles:
    
    ```bash
    cd AURA-NOTES-MANAGER/frontend && npm run build
    ```
    
    The build should complete successfully without errors.
  </action>
  <verify>Build completes without errors</verify>
  <done>Frontend builds successfully</done>
</task>

<task type="auto">
  <name>Task 8: Verify lint passes</name>
  <files>AURA-NOTES-MANAGER/frontend/</files>
  <action>
    Run ESLint to check for any issues:
    
    ```bash
    cd AURA-NOTES-MANAGER/frontend && npm run lint
    ```
    
    Fix any lint errors (unused imports, etc.) before proceeding.
  </action>
  <verify>Lint passes without errors</verify>
  <done>Frontend passes lint check</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] KGQueryPage import removed from App.tsx
- [ ] kg-query route removed from App.tsx
- [ ] JSDoc comment cleaned in App.tsx
- [ ] kg-query directory deleted (9 files, ~3,751 lines)
- [ ] TypeScript compilation succeeds
- [ ] Build succeeds
- [ ] Lint passes
- [ ] Git status shows expected deletions
</verification>

<success_criteria>
- All kg-query files deleted
- App.tsx has no references to kg-query
- Frontend builds and type-checks successfully
- No console errors when running dev server
- Navigating to /kg-query shows 404 (expected)
</success_criteria>

<output>
After completion, create `.planning/phases/rc-04-rag-removal/RC-04-02-SUMMARY.md`
</output>
