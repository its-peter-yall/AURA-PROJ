<objective>
Fix the Gemini 3 Thinking Mode failure in the AURA-CHAT RAG engine. The issue causes an error "Unknown field for ThinkingConfig: thinking_level" and confusing log output showing "budget: N/A" for Gemini 3 models. This fix is critical because thinking mode is a key feature for academic reasoning tasks.

Thoroughly analyze the problem before implementing. Consider multiple approaches and validate each step before proceeding to the next.
</objective>

<context>
You are fixing a production bug in AURA-CHAT, a student-facing academic RAG chat application with React + FastAPI + Vertex AI stack. The project uses Python 4-space indent, Google Python style. Always use the root .venv at `../../.venv/Scripts/python` for Python operations.

The user has already completed research and identified:
- Gemini 3 uses `thinking_level` parameter (not `thinking_budget`)
- Gemini 2.5 uses `thinking_budget` parameter
- These are mutually exclusive - using the wrong one returns 400 error
- Configuration in config.py is already correct

Key file to modify: `AURA-CHAT/backend/rag_engine.py`
Supporting file to reference: `AURA-CHAT/backend/utils/config.py`

@see: CLAUDE.md - Project conventions and anti-patterns
</context>

<requirements>
Complete these tasks in order:

1. **SDK Version Verification** (BLOCKER - must pass before proceeding)
   - Run: `../../.venv/Scripts/python -m pip show google-cloud-aiplatform`
   - Verify version supports Gemini 3 (released Dec 2025 or later)
   - If version is too old, upgrade: `../../.venv/Scripts/python -m pip install --upgrade google-cloud-aiplatform`
   - Document the installed version in your findings

2. **Read and Understand Current Implementation**
   - Read `AURA-CHAT/backend/rag_engine.py` lines 1180-1250 to understand `_get_generation_config()` method
   - Read `AURA-CHAT/backend/rag_engine.py` lines 1360-1380 to understand logging for thinking mode
   - Read `AURA-CHAT/backend/utils/config.py` lines 193-237 to verify thinking configuration

3. **Implement Thinking Config Fix**
   - Modify `_get_generation_config()` to use model-based branching:
     - If model name contains "gemini-3": use `thinking_level` with value from `config.THINKING_LEVEL`
     - If model name contains "gemini-2.5": use `thinking_budget` with value from `config.THINKING_BUDGET`
   - Include `include_thoughts: True` in both cases
   - Add appropriate logging for each branch

4. **Fix Logging for Gemini 3**
   - Update the logging block to show correct values:
     - For Gemini 3: log "level: {thinking_level}" not "budget: N/A"
     - For Gemini 2.5: log "budget: {thinking_budget}"
   - Maintain clear, informative log output

5. **Verification Steps**
   - Run Python syntax check: `../../.venv/Scripts/python -m py_compile AURA-CHAT/backend/rag_engine.py`
   - Run lsp_diagnostics on the file
   - Verify no new errors introduced

</requirements>

<implementation>
Follow these guidelines:

- **Use extended thinking** - deeply consider edge cases (e.g., model name variations, case sensitivity)
- **Research-first approach** - verify SDK version before touching code
- **Preserve existing structure** - don't refactor unrelated code, only fix the thinking config
- **Add logging clarity** - log messages should clearly indicate which parameter is being used
- **Maintain config access** - use `config.THINKING_LEVEL` and `config.THINKING_BUDGET` from utils.config
- **Model name detection** - use `"gemini-3" in model_name.lower()` pattern for case-insensitive matching

Why this matters:
- Using the wrong parameter causes API 400 errors and breaks thinking mode entirely
- SDK version must support Gemini 3 features or code changes will fail at runtime
- Clear logging helps future debugging when models behave unexpectedly
</requirements>

<output>
Create/modify files with relative paths:
- `AURA-CHAT/backend/rag_engine.py` - Update `_get_generation_config()` and logging blocks
- No other files should be modified for Phase 1

Save verification findings to:
- `./phase1-sdk-findings.md` - Document SDK version check results
</output>

<verification>
Before declaring complete, verify your work:

1. SDK Verification:
   - [ ] Google Cloud AIPlatform SDK version is Dec 2025 or later
   - [ ] If upgrade was needed, confirm new version installed

2. Code Changes:
   - [ ] `_get_generation_config()` uses `thinking_level` for Gemini 3 models
   - [ ] `_get_generation_config()` uses `thinking_budget` for Gemini 2.5 models
   - [ ] Both branches include `include_thoughts: True`
   - [ ] Logging shows correct values (level for Gemini 3, budget for 2.5)

3. Diagnostics:
   - [ ] Python syntax check passes
   - [ ] lsp_diagnostics shows no new errors on rag_engine.py
   - [ ] File compiles without ImportError

4. Documentation:
   - [ ] phase1-sdk-findings.md created with SDK version info
</verification>

<success_criteria>
- ✅ No "Unknown field for ThinkingConfig: thinking_level" errors
- ✅ Log output shows correct parameter (level for Gemini 3, budget for Gemini 2.5)
- ✅ Both Gemini 2.5 and Gemini 3 thinking modes work correctly
- ✅ Python compilation passes
- ✅ lsp_diagnostics clean
- ✅ SDK version documented
</success_criteria>
