---
phase: rc-04-rag-removal
type: execute
plan: RC-04-03
---

<objective>
Update main.py router registration and clean up all import references.

Purpose: Remove query_router registration from main.py and ensure clean codebase.
Output: Updated main.py with query router removed, all stale imports cleaned
</objective>

<execution_context>
@~/.config/opencode/skills/create-plans/workflows/execute-phase.md
@~/.config/opencode/skills/create-plans/templates/summary.md
</execution_context>

<context>
@.planning/RAG-CONSOLIDATION-BRIEF.md
@.planning/RAG-CONSOLIDATION-ROADMAP.md
@.planning/phases/rc-01-dependency-mapping/BACKEND-DEPENDENCIES.md
@AURA-NOTES-MANAGER/api/main.py
</context>

<prerequisites>
RC-04-01 (Backend RAG removal) must be completed first.
RC-04-02 (Frontend kg-query removal) must be completed first.
</prerequisites>

<tasks>

<task type="auto">
  <name>Task 1: Remove query_router import from main.py</name>
  <files>AURA-NOTES-MANAGER/api/main.py</files>
  <action>
    Remove the query_router import from main.py.
    
    Find and delete line 98 (approximately):
    ```python
    from api.routers.query import router as query_router
    ```
    
    This import will fail anyway since query.py was deleted in RC-04-01.
  </action>
  <verify>Import statement removed</verify>
  <done>query_router import removed from main.py</done>
</task>

<task type="auto">
  <name>Task 2: Remove query_router registration from main.py</name>
  <files>AURA-NOTES-MANAGER/api/main.py</files>
  <action>
    Remove the query_router registration from main.py.
    
    Find and delete lines 145-147 (approximately):
    ```python
    app.include_router(
        query_router
    )  # KG Query API (Phase 10-04) - prefix already set in router
    ```
    
    Make sure to remove the entire block including any comments.
  </action>
  <verify>Router registration removed</verify>
  <done>query_router registration removed from main.py</done>
</task>

<task type="auto">
  <name>Task 3: Update main.py docstring/comments</name>
  <files>AURA-NOTES-MANAGER/api/main.py</files>
  <action>
    Update any module-level docstrings or comments that reference the query router.
    
    Look for:
    - References to "KG Query API" in comments
    - References to "query router" in docstrings
    - Any @see references to query.py or rag_engine.py
    
    Update or remove these references to reflect the new architecture.
  </action>
  <verify>Comments updated to reflect current state</verify>
  <done>main.py documentation updated</done>
</task>

<task type="auto">
  <name>Task 4: Verify server starts successfully</name>
  <files>AURA-NOTES-MANAGER/api/</files>
  <action>
    Start the API server to verify no import errors:
    
    ```bash
    cd AURA-NOTES-MANAGER/api && python main.py
    ```
    
    The server should start without any import errors or exceptions.
    
    Look for output like:
    ```
    INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
    ```
    
    If there are errors, fix them before proceeding.
  </action>
  <verify>Server starts without errors</verify>
  <done>API server starts successfully</done>
</task>

<task type="auto">
  <name>Task 5: Verify Swagger docs reflect changes</name>
  <files>N/A</files>
  <action>
    With the server running, open Swagger UI:
    
    http://127.0.0.1:8001/docs
    
    Verify:
    1. ✅ KG Query endpoints are GONE (no /v1/kg/* endpoints)
    2. ✅ Graph Preview endpoints EXIST (/api/v1/graph-preview/*)
    3. ✅ All other endpoints still present (modules, documents, etc.)
    
    Take a mental note or screenshot of the available endpoints.
  </action>
  <verify>Swagger shows correct endpoints</verify>
  <done>API documentation reflects RAG removal</done>
</task>

<task type="auto">
  <name>Task 6: Verify graph_preview router is still registered</name>
  <files>AURA-NOTES-MANAGER/api/main.py</files>
  <action>
    Confirm that the graph_preview router (created in RC-02) is still registered:
    
    Look for in main.py:
    ```python
    from api.routers.graph_preview import router as graph_preview_router
    # ... and ...
    app.include_router(graph_preview_router)
    ```
    
    If missing, add it (should have been added in RC-02-01).
  </action>
  <verify>graph_preview_router is registered</verify>
  <done>graph_preview router confirmed active</done>
</task>

<task type="auto">
  <name>Task 7: Test graph preview endpoints</name>
  <files>N/A</files>
  <action>
    Test that the graph preview API still works:
    
    ```bash
    curl http://127.0.0.1:8001/api/v1/graph-preview/modules/test-module
    curl http://127.0.0.1:8001/api/v1/graph-preview/modules/test-module/stats
    ```
    
    Both should return valid JSON responses (even if empty data).
    
    This confirms the kept graph functionality still works.
  </action>
  <verify>Graph preview endpoints respond correctly</verify>
  <done>Graph preview API functional</done>
</task>

<task type="auto">
  <name>Task 8: Run existing backend tests</name>
  <files>AURA-NOTES-MANAGER/tests/</files>
  <action>
    Run existing backend tests to check for regressions:
    
    ```bash
    cd AURA-NOTES-MANAGER && python -m pytest tests/ -v
    ```
    
    Note: Some tests related to RAG/query may fail since those files are deleted.
    These test failures are EXPECTED and will be addressed in RC-05.
    
    Focus on ensuring non-RAG tests pass:
    - Module CRUD tests
    - Document upload tests
    - Graph preview tests
  </action>
  <verify>Non-RAG tests pass, RAG test failures are expected</verify>
  <done>Backend tests reviewed, expected failures documented</done>
</task>

<task type="auto">
  <name>Task 9: Clean up any remaining stale references</name>
  <files>AURA-NOTES-MANAGER/</files>
  <action>
    Search for any remaining references to removed files:
    
    ```bash
    grep -r "rag_engine\|RAGEngine" AURA-NOTES-MANAGER/ --include="*.py" | grep -v ".pyc"
    grep -r "query_analyzer\|QueryAnalyzer" AURA-NOTES-MANAGER/ --include="*.py" | grep -v ".pyc"
    grep -r "answer_synthesizer\|AnswerSynthesizer" AURA-NOTES-MANAGER/ --include="*.py" | grep -v ".pyc"
    grep -r "from api.routers.query" AURA-NOTES-MANAGER/ --include="*.py" | grep -v ".pyc"
    ```
    
    Fix any remaining references found.
  </action>
  <verify>No active references to deleted files</verify>
  <done>All stale references cleaned up</done>
</task>

<task type="auto">
  <name>Task 10: Git status and summary</name>
  <files>N/A</files>
  <action>
    Review all changes for Phase 4:
    
    ```bash
    git status
    git diff --stat
    ```
    
    Expected changes:
    - Deleted: api/rag_engine.py
    - Deleted: api/routers/query.py
    - Deleted: services/answer_synthesizer.py
    - Deleted: services/query_analyzer.py
    - Deleted: frontend/src/features/kg-query/ (9 files)
    - Modified: api/main.py
    - Modified: api/routers/__init__.py
    - Modified: frontend/src/App.tsx
    - Modified: Various files (comment cleanup)
    
    Do NOT commit yet - wait for user instruction.
  </action>
  <verify>Git status shows expected changes</verify>
  <done>All Phase 4 changes reviewed</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] query_router import removed from main.py
- [ ] query_router registration removed from main.py
- [ ] main.py comments/docstrings updated
- [ ] Server starts without errors
- [ ] Swagger shows correct endpoints (no KG Query)
- [ ] graph_preview router still registered and working
- [ ] Non-RAG backend tests pass
- [ ] No stale references to deleted files
- [ ] Git status reviewed
</verification>

<success_criteria>
- All Phase 4 files deleted (4 backend + 9 frontend = 13 files)
- main.py updated with no broken imports
- API server starts and runs correctly
- Graph preview API functional
- Both applications buildable and runnable
- Ready for Phase 5 verification
</success_criteria>

<output>
After completion, create `.planning/phases/rc-04-rag-removal/RC-04-03-SUMMARY.md`
</output>
