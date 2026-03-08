---
phase: rc-05-verification
type: execute
plan: RC-05-02
---

<objective>
Perform end-to-end integration testing of both applications to verify the complete workflow functions correctly after RAG consolidation.

Purpose: Verify real-world user flows work across both applications.
Output: Verified working system with documented test results.
</objective>

<execution_context>
@~/.config/opencode/skills/create-plans/workflows/execute-phase.md
@~/.config/opencode/skills/create-plans/templates/summary.md
</execution_context>

<context>
@.planning/RAG-CONSOLIDATION-BRIEF.md
@.planning/RAG-CONSOLIDATION-ROADMAP.md
@.planning/phases/rc-05-verification/RC-05-01-PLAN.md
</context>

<prerequisites>
RC-05-01 (Run all tests) should be completed first.
Both applications should be runnable.
</prerequisites>

<tasks>

<task type="auto">
  <name>Task 1: Start AURA-NOTES-MANAGER services</name>
  <files>AURA-NOTES-MANAGER/</files>
  <action>
    Start the NOTES-MANAGER backend and frontend:
    
    Terminal 1 - Backend:
    ```bash
    cd AURA-NOTES-MANAGER/api
    ../.venv/Scripts/python main.py
    ```
    
    Terminal 2 - Frontend:
    ```bash
    cd AURA-NOTES-MANAGER/frontend
    npm run dev
    ```
    
    Verify:
    - Backend running on http://127.0.0.1:8001
    - Frontend running on http://localhost:5173
    - No console errors on startup
  </action>
  <verify>Both services start without errors</verify>
  <done>NOTES-MANAGER services running</done>
</task>

<task type="auto">
  <name>Task 2: Verify NOTES-MANAGER Module CRUD</name>
  <files>N/A</files>
  <action>
    Test module management functionality:
    
    1. Open http://localhost:5173 (NOTES-MANAGER frontend)
    2. Navigate to module management
    3. Test operations:
       - [ ] View existing modules (if any)
       - [ ] Create a new test module
       - [ ] Edit module details
       - [ ] Delete test module (cleanup)
    
    All operations should work without errors.
    
    API verification:
    ```bash
    curl http://127.0.0.1:8001/api/v1/modules
    ```
  </action>
  <verify>Module CRUD operations work</verify>
  <done>Module management verified functional</done>
</task>

<task type="auto">
  <name>Task 3: Verify NOTES-MANAGER Graph Preview API</name>
  <files>N/A</files>
  <action>
    Test the new graph preview endpoints (created in RC-02):
    
    ```bash
    # Get graph data for a module
    curl http://127.0.0.1:8001/api/v1/graph-preview/modules/test-module-id
    
    # Get graph stats for a module
    curl http://127.0.0.1:8001/api/v1/graph-preview/modules/test-module-id/stats
    ```
    
    Verify:
    - Endpoints return valid JSON
    - No 500 errors
    - Response structure matches schema (nodes, edges, counts)
    
    Also check Swagger UI:
    - Open http://127.0.0.1:8001/docs
    - Verify graph-preview endpoints are listed
    - Verify NO kg-query or /v1/kg endpoints exist
  </action>
  <verify>Graph preview API returns valid responses</verify>
  <done>Graph preview API verified functional</done>
</task>

<task type="auto">
  <name>Task 4: Verify kg-query route is removed</name>
  <files>N/A</files>
  <action>
    Confirm the kg-query feature is completely removed:
    
    1. In browser, navigate to http://localhost:5173/kg-query
       - Should show 404 or redirect (NOT the old KG query page)
    
    2. Check Swagger UI at http://127.0.0.1:8001/docs
       - Should NOT have any /v1/kg/* endpoints
       - Should NOT have RAG/query endpoints
    
    3. Search codebase for remnants:
       ```bash
       grep -r "kg-query" AURA-NOTES-MANAGER/frontend/src/ --include="*.tsx" --include="*.ts"
       grep -r "/v1/kg" AURA-NOTES-MANAGER/api/ --include="*.py"
       ```
       Both should return empty results.
  </action>
  <verify>kg-query completely removed from both frontend and backend</verify>
  <done>kg-query removal verified</done>
</task>

<task type="auto">
  <name>Task 5: Start AURA-CHAT services</name>
  <files>AURA-CHAT/</files>
  <action>
    Start the AURA-CHAT backend and frontend:
    
    Terminal 3 - Backend:
    ```bash
    cd AURA-CHAT/server
    ../.venv/Scripts/python main.py
    ```
    
    Terminal 4 - Frontend:
    ```bash
    cd AURA-CHAT/client
    npm run dev
    ```
    
    Verify:
    - Backend running on http://127.0.0.1:8000
    - Frontend running on http://localhost:5174 (or different port)
    - No console errors on startup
  </action>
  <verify>Both AURA-CHAT services start without errors</verify>
  <done>AURA-CHAT services running</done>
</task>

<task type="auto">
  <name>Task 6: Verify AURA-CHAT Graph visualization</name>
  <files>N/A</files>
  <action>
    Test the graph visualization feature:
    
    1. Open AURA-CHAT frontend
    2. Navigate to Graph page (Knowledge Graph)
    3. Verify:
       - [ ] Graph loads without errors
       - [ ] Nodes and edges display correctly
       - [ ] Layout controls work (radial, hierarchical, etc.)
       - [ ] Node type filters work
       - [ ] Node details panel opens on click
       - [ ] Zoom/pan controls work
    
    4. Test module filtering (added in RC-03):
       - [ ] If a module is selected, graph shows filtered data
       - [ ] Module name displays in header
       - [ ] "Clear filter" button works (if implemented)
  </action>
  <verify>Graph visualization fully functional</verify>
  <done>AURA-CHAT graph visualization verified</done>
</task>

<task type="auto">
  <name>Task 7: Verify AURA-CHAT RAG/Chat functionality</name>
  <files>N/A</files>
  <action>
    Test the RAG chat feature (should be unchanged):
    
    1. Navigate to Chat page
    2. Select a module (if module selection exists)
    3. Submit a test query
    4. Verify:
       - [ ] Query is processed without errors
       - [ ] Response is generated
       - [ ] Citations appear (if documents exist)
       - [ ] Thinking mode works (if enabled)
    
    This verifies the AURA-CHAT RAG is unaffected by removing 
    NOTES-MANAGER's duplicate RAG.
  </action>
  <verify>Chat/RAG functionality works correctly</verify>
  <done>AURA-CHAT RAG verified functional</done>
</task>

<task type="auto">
  <name>Task 8: Verify graph API with module_id filter</name>
  <files>N/A</files>
  <action>
    Test the module filtering added to graph API (RC-03-03):
    
    ```bash
    # Without module filter (full graph)
    curl "http://127.0.0.1:8000/graph/data?limit=100"
    
    # With module filter
    curl "http://127.0.0.1:8000/graph/data?module_id=test-module&limit=100"
    ```
    
    Verify:
    - Both requests return valid JSON
    - Filtered request returns subset of data (or empty if module doesn't exist)
    - No errors in server logs
  </action>
  <verify>Graph API module filtering works</verify>
  <done>Graph API module_id parameter verified</done>
</task>

<task type="auto">
  <name>Task 9: Cross-application verification</name>
  <files>N/A</files>
  <action>
    Verify both applications can run simultaneously:
    
    1. Both backends running (ports 8000 and 8001)
    2. Both frontends running (ports 5173 and 5174)
    3. No port conflicts
    4. No shared state issues
    
    Verify they use same Neo4j database:
    - Create/update data in NOTES-MANAGER
    - Verify it appears in AURA-CHAT graph
    
    (This may require existing data or manual data creation)
  </action>
  <verify>Both apps run simultaneously without conflicts</verify>
  <done>Cross-application operation verified</done>
</task>

<task type="auto">
  <name>Task 10: Final verification checklist</name>
  <files>N/A</files>
  <action>
    Complete the final verification checklist from the roadmap:
    
    ### AURA-NOTES-MANAGER
    - [ ] Module CRUD works
    - [ ] KG processing works (if testable)
    - [ ] Graph preview API returns data
    - [ ] No /kg-query routes exist
    - [ ] No RAG endpoints exist
    - [ ] Frontend builds without errors
    - [ ] Backend starts without import errors
    
    ### AURA-CHAT
    - [ ] RAG queries work (unchanged)
    - [ ] Graph visualization displays entities
    - [ ] Module filtering works in graph
    - [ ] Chat sessions work
    - [ ] Frontend builds without errors
    - [ ] Backend starts without import errors
    
    ### Codebase
    - [ ] No broken imports in either codebase
    - [ ] No dead code remnants (stale references)
    - [ ] All tests pass
    - [ ] Git status is clean (all changes committed)
  </action>
  <verify>All checklist items verified</verify>
  <done>Final verification complete</done>
</task>

<task type="auto">
  <name>Task 11: Document completion and cleanup</name>
  <files>N/A</files>
  <action>
    Prepare final documentation:
    
    1. Update roadmap progress to show Phase 5 complete
    2. Document any issues found and their resolutions
    3. List any follow-up tasks or improvements identified
    4. Summarize total files deleted and lines of code removed
    
    Summary metrics:
    - Backend files deleted: 4
    - Frontend files deleted: 9
    - Total lines removed: ~5,000+ (estimated)
    - New files created: 2 (graph_preview router + schemas)
    - Files modified: ~10 (main.py, App.tsx, types, etc.)
  </action>
  <verify>Documentation complete</verify>
  <done>Final documentation created</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] NOTES-MANAGER services start and run
- [ ] NOTES-MANAGER module CRUD works
- [ ] NOTES-MANAGER graph preview API works
- [ ] kg-query completely removed
- [ ] AURA-CHAT services start and run
- [ ] AURA-CHAT graph visualization works
- [ ] AURA-CHAT RAG/chat works
- [ ] Graph API module filtering works
- [ ] Both apps run simultaneously
- [ ] Final checklist complete
- [ ] Documentation updated
</verification>

<success_criteria>
- Both applications fully functional
- All user flows work correctly
- No regressions from refactoring
- Clean codebase with no dead code
- RAG functionality consolidated in AURA-CHAT only
- NOTES-MANAGER focused on document/module management
</success_criteria>

<output>
After completion, create `.planning/phases/rc-05-verification/RC-05-02-SUMMARY.md`

Also update `.planning/RAG-CONSOLIDATION-ROADMAP.md` to mark Phase 5 complete.
</output>
