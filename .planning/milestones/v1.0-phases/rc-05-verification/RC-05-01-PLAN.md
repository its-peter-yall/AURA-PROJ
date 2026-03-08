---
phase: rc-05-verification
type: execute
plan: RC-05-01
---

<objective>
Run all existing tests across both applications and fix any failures caused by the RAG removal refactoring.

Purpose: Verify no regressions were introduced by the refactoring.
Output: All tests passing (or documented pre-existing failures), clean test reports.
</objective>

<execution_context>
@~/.config/opencode/skills/create-plans/workflows/execute-phase.md
@~/.config/opencode/skills/create-plans/templates/summary.md
</execution_context>

<context>
@.planning/RAG-CONSOLIDATION-BRIEF.md
@.planning/RAG-CONSOLIDATION-ROADMAP.md
@.planning/phases/rc-04-rag-removal/RC-04-01-SUMMARY.md
@.planning/phases/rc-04-rag-removal/RC-04-02-SUMMARY.md
@.planning/phases/rc-04-rag-removal/RC-04-03-SUMMARY.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Run AURA-NOTES-MANAGER backend tests</name>
  <files>AURA-NOTES-MANAGER/tests/</files>
  <action>
    Run the backend test suite:
    
    ```bash
    cd AURA-NOTES-MANAGER
    ../.venv/Scripts/python -m pytest tests/ -v --tb=short
    ```
    
    Expected outcomes:
    - Tests for deleted files (rag_engine, query router) should NOT exist or should fail
    - Tests for graph_preview.py (created in RC-02) should PASS
    - Tests for modules, documents, hierarchy should PASS
    
    Document:
    1. Total tests run
    2. Tests passed
    3. Tests failed (with reasons)
    4. Tests skipped
  </action>
  <verify>Test results documented</verify>
  <done>NOTES-MANAGER backend tests executed and results recorded</done>
</task>

<task type="auto">
  <name>Task 2: Remove/update stale backend tests</name>
  <files>AURA-NOTES-MANAGER/tests/</files>
  <action>
    Handle test files that reference deleted modules:
    
    1. Search for tests importing deleted files:
       ```bash
       grep -r "rag_engine\|query_analyzer\|answer_synthesizer" AURA-NOTES-MANAGER/tests/ --include="*.py"
       ```
    
    2. For each found test file:
       - If entire file tests deleted functionality → DELETE the test file
       - If only some tests reference deleted code → REMOVE those specific tests
    
    Common files to check:
    - `tests/test_rag_engine.py` → DELETE if exists
    - `tests/test_query_router.py` → DELETE if exists
    - `tests/test_answer_synthesizer.py` → DELETE if exists
    - `tests/test_query_analyzer.py` → DELETE if exists
  </action>
  <verify>No tests reference deleted modules</verify>
  <done>Stale test files removed or updated</done>
</task>

<task type="auto">
  <name>Task 3: Re-run AURA-NOTES-MANAGER backend tests</name>
  <files>AURA-NOTES-MANAGER/tests/</files>
  <action>
    After removing stale tests, run the test suite again:
    
    ```bash
    cd AURA-NOTES-MANAGER
    ../.venv/Scripts/python -m pytest tests/ -v --tb=short
    ```
    
    All remaining tests should pass. Fix any failures.
  </action>
  <verify>All backend tests pass</verify>
  <done>NOTES-MANAGER backend tests all passing</done>
</task>

<task type="auto">
  <name>Task 4: Run AURA-NOTES-MANAGER frontend tests</name>
  <files>AURA-NOTES-MANAGER/frontend/</files>
  <action>
    Run the frontend test suite:
    
    ```bash
    cd AURA-NOTES-MANAGER/frontend && npm test -- --run
    ```
    
    Or if using Vitest:
    ```bash
    cd AURA-NOTES-MANAGER/frontend && npm run test:run
    ```
    
    Expected: Tests for kg-query feature should be deleted or not exist.
    
    Document results.
  </action>
  <verify>Frontend tests documented</verify>
  <done>NOTES-MANAGER frontend tests executed</done>
</task>

<task type="auto">
  <name>Task 5: Run AURA-CHAT server tests</name>
  <files>AURA-CHAT/server/tests/</files>
  <action>
    Run the AURA-CHAT backend test suite:
    
    ```bash
    cd AURA-CHAT
    ../.venv/Scripts/python -m pytest server/tests/ -v --tb=short
    ```
    
    Focus on:
    - Graph router tests (module_id filtering added in RC-03-03)
    - RAG/chat tests (should be unchanged)
    - Session tests (should be unchanged)
    
    All tests should pass. The module_id changes shouldn't break existing tests.
  </action>
  <verify>AURA-CHAT backend tests pass</verify>
  <done>AURA-CHAT server tests all passing</done>
</task>

<task type="auto">
  <name>Task 6: Run AURA-CHAT client tests</name>
  <files>AURA-CHAT/client/</files>
  <action>
    Run the AURA-CHAT frontend test suite:
    
    ```bash
    cd AURA-CHAT/client && npm test -- --run
    ```
    
    Or:
    ```bash
    cd AURA-CHAT/client && npm run test:run
    ```
    
    Focus on:
    - GraphPage tests (module filtering added in RC-03-04)
    - ChatPage tests (should be unchanged)
    
    Document results.
  </action>
  <verify>AURA-CHAT frontend tests pass</verify>
  <done>AURA-CHAT client tests all passing</done>
</task>

<task type="auto">
  <name>Task 7: Run AURA-CHAT E2E tests</name>
  <files>AURA-CHAT/client/e2e/</files>
  <action>
    Run Playwright E2E tests if available:
    
    ```bash
    cd AURA-CHAT/client && npm run test:e2e
    ```
    
    Or:
    ```bash
    cd AURA-CHAT/client && npx playwright test
    ```
    
    These tests verify the full user flow works correctly.
    
    Note: E2E tests may require both backend and frontend running.
    Skip if infrastructure not available, but document the skip.
  </action>
  <verify>E2E tests pass or skipped with documentation</verify>
  <done>AURA-CHAT E2E tests verified</done>
</task>

<task type="auto">
  <name>Task 8: Run AURA-NOTES-MANAGER E2E tests</name>
  <files>AURA-NOTES-MANAGER/e2e/</files>
  <action>
    Run Playwright E2E tests if available:
    
    ```bash
    cd AURA-NOTES-MANAGER && npm run test:e2e
    ```
    
    Or:
    ```bash
    cd AURA-NOTES-MANAGER/e2e && npx playwright test
    ```
    
    E2E tests should pass without kg-query routes.
    
    Note: Any E2E tests for kg-query should have been removed with the feature.
  </action>
  <verify>E2E tests pass or skipped with documentation</verify>
  <done>NOTES-MANAGER E2E tests verified</done>
</task>

<task type="auto">
  <name>Task 9: Document test results summary</name>
  <files>N/A</files>
  <action>
    Create a summary of all test results:
    
    ```
    ## Test Results Summary
    
    ### AURA-NOTES-MANAGER
    | Suite | Passed | Failed | Skipped | Notes |
    |-------|--------|--------|---------|-------|
    | Backend (pytest) | X | 0 | Y | |
    | Frontend (vitest) | X | 0 | Y | |
    | E2E (playwright) | X | 0 | Y | |
    
    ### AURA-CHAT
    | Suite | Passed | Failed | Skipped | Notes |
    |-------|--------|--------|---------|-------|
    | Backend (pytest) | X | 0 | Y | |
    | Frontend (vitest) | X | 0 | Y | |
    | E2E (playwright) | X | 0 | Y | |
    
    ### Deleted Test Files
    - tests/test_rag_engine.py
    - tests/test_query_router.py
    - (etc.)
    
    ### Pre-existing Failures (Not from refactoring)
    - (list any)
    ```
  </action>
  <verify>Test summary documented</verify>
  <done>Complete test results documented in summary</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] NOTES-MANAGER backend tests pass (stale tests removed)
- [ ] NOTES-MANAGER frontend tests pass
- [ ] AURA-CHAT backend tests pass
- [ ] AURA-CHAT frontend tests pass
- [ ] E2E tests pass or documented skip
- [ ] No test failures caused by refactoring
- [ ] Test results summary created
</verification>

<success_criteria>
- All tests pass (excluding pre-existing failures)
- Stale tests referencing deleted code removed
- Both applications test suites green
- Test coverage maintained for non-deleted features
</success_criteria>

<output>
After completion, create `.planning/phases/rc-05-verification/RC-05-01-SUMMARY.md`
</output>
