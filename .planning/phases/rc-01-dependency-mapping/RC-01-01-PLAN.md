---
phase: rc-01-dependency-mapping
type: execute
plan: RC-01-01
---

<objective>
Map all backend dependencies on RAG services scheduled for removal.

Purpose: Ensure safe removal by identifying all imports and usages before deleting files.
Output: Dependency report documenting all imports of rag_engine, answer_synthesizer, query_analyzer, and query router.
</objective>

<execution_context>
@~/.config/opencode/skills/create-plans/workflows/execute-phase.md
@~/.config/opencode/skills/create-plans/templates/summary.md
</execution_context>

<context>
@.planning/RAG-CONSOLIDATION-BRIEF.md
@.planning/RAG-CONSOLIDATION-ROADMAP.md
@AURA-NOTES-MANAGER/api/rag_engine.py
@AURA-NOTES-MANAGER/api/routers/query.py
@AURA-NOTES-MANAGER/services/answer_synthesizer.py
@AURA-NOTES-MANAGER/services/query_analyzer.py
@AURA-NOTES-MANAGER/api/main.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Find all imports of RAGEngine class</name>
  <files>AURA-NOTES-MANAGER/api/</files>
  <action>
    Search the entire AURA-NOTES-MANAGER codebase for:
    1. `from rag_engine import` or `import rag_engine`
    2. `from api.rag_engine import` or `import api.rag_engine`
    3. Any reference to `RAGEngine` class
    4. Check main.py for router registration of query endpoints
    
    Document each import with file path and line number.
    Identify if any imports are from outside the scheduled-for-removal files.
  </action>
  <verify>grep -r "rag_engine\|RAGEngine" AURA-NOTES-MANAGER/ --include="*.py"</verify>
  <done>Complete list of all files importing rag_engine, categorized as "safe to remove" or "needs refactoring"</done>
</task>

<task type="auto">
  <name>Task 2: Find all imports of AnswerSynthesizer</name>
  <files>AURA-NOTES-MANAGER/services/, AURA-NOTES-MANAGER/api/</files>
  <action>
    Search for:
    1. `from answer_synthesizer import` or `import answer_synthesizer`
    2. `from services.answer_synthesizer import`
    3. Any reference to `AnswerSynthesizer` class
    
    Expected: Only imported by rag_engine.py (which is also being removed).
    Flag any unexpected imports.
  </action>
  <verify>grep -r "answer_synthesizer\|AnswerSynthesizer" AURA-NOTES-MANAGER/ --include="*.py"</verify>
  <done>Confirmed AnswerSynthesizer is only used by files also scheduled for removal</done>
</task>

<task type="auto">
  <name>Task 3: Verify query_analyzer is dead code</name>
  <files>AURA-NOTES-MANAGER/</files>
  <action>
    Search for ANY reference to query_analyzer:
    1. `from query_analyzer import` or `import query_analyzer`
    2. `from services.query_analyzer import`
    3. Any reference to `QueryAnalyzer` class
    
    Expected: ZERO imports (confirmed dead code from prior analysis).
    Document if any imports found - would require investigation.
  </action>
  <verify>grep -r "query_analyzer\|QueryAnalyzer" AURA-NOTES-MANAGER/ --include="*.py"</verify>
  <done>Confirmed query_analyzer.py has zero imports, is safe to delete</done>
</task>

<task type="auto">
  <name>Task 4: Map query router registration and dependencies</name>
  <files>AURA-NOTES-MANAGER/api/main.py, AURA-NOTES-MANAGER/api/routers/query.py</files>
  <action>
    1. Read main.py to find how query router is registered (app.include_router)
    2. Document the router prefix and tags
    3. Check if any other routers import from query.py
    4. Check for any middleware or dependencies specific to query routes
    
    Document the removal steps needed in main.py.
  </action>
  <verify>Read main.py, identify the line registering query router</verify>
  <done>Documented exact line to remove from main.py and confirmed no cross-router dependencies</done>
</task>

<task type="auto">
  <name>Task 5: Check graph_manager and graph_visualizer dependencies</name>
  <files>AURA-NOTES-MANAGER/api/graph_manager.py, AURA-NOTES-MANAGER/api/graph_visualizer.py</files>
  <action>
    Verify these files (which we're keeping) do NOT import from files being removed:
    1. Check graph_manager.py imports
    2. Check graph_visualizer.py imports
    3. Confirm they are standalone and can continue working after removal
    
    If they DO import from rag_engine or answer_synthesizer, document refactoring needed.
  </action>
  <verify>Read imports section of both files</verify>
  <done>Confirmed graph_manager and graph_visualizer are independent of RAG services</done>
</task>

<task type="auto">
  <name>Task 6: Create dependency report</name>
  <files>.planning/phases/rc-01-dependency-mapping/BACKEND-DEPENDENCIES.md</files>
  <action>
    Create a markdown file documenting:
    1. All imports found for each file scheduled for removal
    2. Classification: "safe to remove" vs "needs refactoring first"
    3. Specific removal steps for main.py
    4. Any unexpected dependencies discovered
    5. Recommendation: proceed with removal or investigate further
  </action>
  <verify>File exists and contains all sections</verify>
  <done>BACKEND-DEPENDENCIES.md created with complete analysis</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] All 4 files searched for imports (rag_engine, answer_synthesizer, query_analyzer, query.py)
- [ ] graph_manager and graph_visualizer confirmed independent
- [ ] main.py router registration documented
- [ ] BACKEND-DEPENDENCIES.md created
</verification>

<success_criteria>
- All tasks completed
- Clear categorization of files as safe/unsafe to remove
- No unexpected dependencies that would block removal
- Actionable removal steps documented
</success_criteria>

<output>
After completion, create `.planning/phases/rc-01-dependency-mapping/RC-01-01-SUMMARY.md`
</output>
