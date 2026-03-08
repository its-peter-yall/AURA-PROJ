---
phase: rc-04-rag-removal
type: execute
plan: RC-04-01
---

<objective>
Remove backend RAG services from AURA-NOTES-MANAGER.

Purpose: Delete duplicate RAG/query services that are now consolidated in AURA-CHAT.
Output: Removed `rag_engine.py`, `query.py`, `answer_synthesizer.py`, `query_analyzer.py`
</objective>

<execution_context>
@~/.config/opencode/skills/create-plans/workflows/execute-phase.md
@~/.config/opencode/skills/create-plans/templates/summary.md
</execution_context>

<context>
@.planning/RAG-CONSOLIDATION-BRIEF.md
@.planning/RAG-CONSOLIDATION-ROADMAP.md
@.planning/phases/rc-01-dependency-mapping/BACKEND-DEPENDENCIES.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create backup branch (safety)</name>
  <files>N/A</files>
  <action>
    Create a git branch for easy rollback if needed:
    
    ```bash
    git checkout -b backup/pre-rag-removal
    git checkout -  # Return to previous branch
    ```
    
    This ensures we can easily revert if unexpected issues arise.
  </action>
  <verify>Branch created successfully</verify>
  <done>Backup branch exists for rollback</done>
</task>

<task type="auto">
  <name>Task 2: Delete query_analyzer.py (dead code)</name>
  <files>AURA-NOTES-MANAGER/services/query_analyzer.py</files>
  <action>
    Delete the dead code file - it has ZERO imports anywhere:
    
    ```bash
    rm AURA-NOTES-MANAGER/services/query_analyzer.py
    ```
    
    This is the safest file to delete first as it has no dependencies.
  </action>
  <verify>File deleted, no import errors when running server</verify>
  <done>query_analyzer.py removed</done>
</task>

<task type="auto">
  <name>Task 3: Delete answer_synthesizer.py</name>
  <files>AURA-NOTES-MANAGER/services/answer_synthesizer.py</files>
  <action>
    Delete the answer synthesizer service:
    
    ```bash
    rm AURA-NOTES-MANAGER/services/answer_synthesizer.py
    ```
    
    This file is only imported by rag_engine.py (which will be deleted next).
  </action>
  <verify>File deleted</verify>
  <done>answer_synthesizer.py removed</done>
</task>

<task type="auto">
  <name>Task 4: Delete rag_engine.py</name>
  <files>AURA-NOTES-MANAGER/api/rag_engine.py</files>
  <action>
    Delete the RAG engine core file:
    
    ```bash
    rm AURA-NOTES-MANAGER/api/rag_engine.py
    ```
    
    This file is only imported by routers/query.py (which will be deleted next).
  </action>
  <verify>File deleted</verify>
  <done>rag_engine.py removed</done>
</task>

<task type="auto">
  <name>Task 5: Delete query.py router</name>
  <files>AURA-NOTES-MANAGER/api/routers/query.py</files>
  <action>
    Delete the query router:
    
    ```bash
    rm AURA-NOTES-MANAGER/api/routers/query.py
    ```
    
    This router will be unregistered from main.py in RC-04-03.
  </action>
  <verify>File deleted</verify>
  <done>query.py router removed</done>
</task>

<task type="auto">
  <name>Task 6: Update routers/__init__.py</name>
  <files>AURA-NOTES-MANAGER/api/routers/__init__.py</files>
  <action>
    Remove the query_router export from __init__.py:
    
    Find and delete line 13:
    ```python
    from api.routers.query import router as query_router
    ```
    
    Also remove from __all__ if present.
  </action>
  <verify>No import errors when importing from api.routers</verify>
  <done>query_router export removed from __init__.py</done>
</task>

<task type="auto">
  <name>Task 7: Clean up documentation comments</name>
  <files>
    AURA-NOTES-MANAGER/services/embeddings.py
    AURA-NOTES-MANAGER/api/graph_manager.py
    AURA-NOTES-MANAGER/api/schemas/search.py
  </files>
  <action>
    Remove stale comment references to deleted files:
    
    1. `services/embeddings.py` (line 9) - Remove reference to rag_engine.py
    2. `api/graph_manager.py` (line 8) - Remove reference to rag_engine.py
    3. `api/schemas/search.py` (line 8) - Remove reference to rag_engine.py
    
    Update comments to reflect new architecture where applicable.
  </action>
  <verify>No stale @see references to deleted files</verify>
  <done>Documentation comments updated</done>
</task>

<task type="auto">
  <name>Task 8: Verify no import errors</name>
  <files>AURA-NOTES-MANAGER/api/</files>
  <action>
    Test that Python can import the remaining modules:
    
    ```bash
    cd AURA-NOTES-MANAGER
    python -c "from api.graph_manager import GraphManager; print('graph_manager OK')"
    python -c "from api.graph_visualizer import GraphVisualizer; print('graph_visualizer OK')"
    python -c "from api.routers.graph_preview import router; print('graph_preview OK')"
    python -c "from services.embeddings import EmbeddingService; print('embeddings OK')"
    ```
    
    All imports should succeed without errors.
  </action>
  <verify>All import commands succeed</verify>
  <done>Remaining modules import successfully</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] query_analyzer.py deleted
- [ ] answer_synthesizer.py deleted
- [ ] rag_engine.py deleted
- [ ] query.py router deleted
- [ ] routers/__init__.py updated
- [ ] Documentation comments cleaned
- [ ] Remaining modules import without errors
- [ ] Git status shows expected deletions
</verification>

<success_criteria>
- All 4 RAG-related files deleted
- No Python import errors in remaining codebase
- graph_manager.py and graph_visualizer.py still functional
- Ready for main.py cleanup in RC-04-03
</success_criteria>

<output>
After completion, create `.planning/phases/rc-04-rag-removal/RC-04-01-SUMMARY.md`
</output>
