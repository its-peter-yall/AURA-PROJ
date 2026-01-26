<objective>
Execute comprehensive testing for the fixes implemented in Phase 1 (Gemini 3 Thinking Mode) and Phase 2 (Conversation History). Validate that both issues are resolved and no regressions were introduced.

Thoroughly plan and execute each test scenario. Document results meticulously. If any test fails, diagnose the root cause and fix before proceeding.
</objective>

<context>
You are validating fixes in AURA-CHAT, a student-facing academic RAG chat application with React + FastAPI + Vertex AI stack. The project uses Python 4-space indent, Google Python style. Always use the root .venv at `../../.venv/Scripts/python` for Python operations.

Phase 1 completed: Gemini 3 Thinking Mode fix
- Fixed `_get_generation_config()` to use `thinking_level` for Gemini 3, `thinking_budget` for Gemini 2.5
- Fixed logging to show correct values

Phase 2 completed: Conversation History fix
- Increased history window from 20 to 50 messages
- Refactored history from plain text string to `{role, parts}` message array
- Added `_build_message_history_with_signatures_v2()` helper

Key file: `AURA-CHAT/backend/rag_engine.py`

@see: CLAUDE.md - Project conventions and anti-patterns
@see: IMPLEMENTATION_ROADMAP.md - Testing requirements
@see: .prompts/001-gemini3-thinking-mode-fix.md - Phase 1 details
@see: .prompts/002-conversation-history-fix.md - Phase 2 details
</context>

<requirements>
Execute these test scenarios in order. Document results for each.

**Test 1: Thinking Mode with Gemini 3**
- Objective: Verify Gemini 3 thinking mode works without errors
- Steps:
  1. Start the AURA-CHAT server (or ensure it's running)
  2. Configure model to `gemini-3-flash-preview` if not default
  3. Enable thinking mode (should be enabled by default in tutor/assistant modes)
  4. Query: "Explain the relationship between thermodynamics and quantum mechanics in detail"
  5. Check server logs for: "Native thinking enabled for model gemini-3-flash-preview (level: HIGH)"
  6. Verify no "Unknown field for ThinkingConfig: thinking_level" errors
  7. Verify response shows deeper reasoning (compare with non-thinking mode if possible)
- Expected Results:
  - [ ] Log shows correct parameter (level: HIGH)
  - [ ] No API errors
  - [ ] Response reflects thinking/reasoning
- Document: Response quality, any errors, log excerpts

**Test 2: Conversation History Retention ("SAY MY NAME")**
- Objective: Verify model remembers conversation context
- Steps:
  1. Start a new chat session
  2. Query: "My name is [YOUR_NAME]" (use a distinctive name)
  3. Assistant should acknowledge
  4. Query 2-3 other questions (different topics)
  5. Query: "SAY MY NAME"
  6. Assistant should respond with the name from step 2
  7. Repeat with 50+ messages to test history window
- Expected Results:
  - [ ] Model correctly identifies user's name
  - [ ] Works with 50+ messages in history
  - [ ] Context from documents doesn't override conversation memory
- Document: Session ID, conversation flow, response accuracy

**Test 3: History Window Bounds**
- Objective: Verify 50-message limit works correctly
- Steps:
  1. Create a session with 60+ messages (mix of user/assistant)
  2. Ask a question that references information from message #5 (early history)
  3. Ask a question that references information from message #55 (recent history)
  4. Verify both are answered correctly (50 message window should include #5-55)
  5. Verify messages #1-4 are NOT accessible (outside window)
- Expected Results:
  - [ ] Messages 5-55 are accessible (within 50-message window)
  - [ ] Messages 1-4 are not in current request
  - [ ] ChatManager still retains full history server-side
- Document: Message counts, test queries, results

**Test 4: Thinking Mode with Multi-Turn Conversation**
- Objective: Verify thinking mode works correctly with conversation history
- Steps:
  1. Enable thinking mode
  2. Multi-turn query requiring reasoning across turns
  3. Verify thought signatures are preserved
  - Query 1: "What are the main principles of machine learning?"
  - Query 2: "Explain how neural networks implement one of those principles"
  - Query 3: "How does backpropagation relate to gradient descent?"
  4. Check logs for thinking-related entries
  5. Verify no conflicts between thinking_config and message history
- Expected Results:
  - [ ] Thought signatures preserved across turns
  - [ ] Previous conversation context available during thinking
  - [ ] No conflicts or errors
- Document: Thought signature handling, response coherence

**Test 5: Regression Test - Gemini 2.5 Models**
- Objective: Verify Gemini 2.5 models still work correctly
- Steps:
  1. Configure model to `gemini-2.5-flash` or `gemini-2.5-flash-lite`
  2. Enable thinking mode
  3. Query with complex reasoning requirement
  4. Check logs for: "Native thinking enabled for model gemini-2.5... (budget: 2048)"
  5. Verify no errors
- Expected Results:
  - [ ] Log shows correct parameter (budget: 2048)
  - [ ] No API errors
  - [ ] Thinking mode works as before (no regression)
- Document: Model used, log excerpts, any issues

**Test 6: Non-Thinking Mode Fallback**
- Objective: Verify fallback when thinking mode fails
- Steps:
  1. Query with thinking enabled
  2. If thinking fails, verify graceful fallback to non-thinking mode
  3. Response should still be generated (possibly less detailed)
- Expected Results:
  - [ ] System recovers gracefully from thinking failures
  - [ ] User still gets a response
- Document: Any failures, fallback behavior, response quality

</requirements>

<implementation>
Follow these guidelines:

- **Systematic testing** - Follow each test procedure exactly, document all results
- **Evidence-based** - Capture log excerpts, response samples, error messages
- **Thorough diagnosis** - If tests fail, dig deep to find root cause
- **Parallel execution** - Run independent tests simultaneously where possible
- **Clear documentation** - Record pass/fail, evidence, and any issues for each test

Why this matters:
- Testing validates that expensive implementation work actually fixes user-facing issues
- Regression testing prevents new fixes from breaking existing functionality
- Documented results provide evidence for release decisions
</requirements>

<output>
Create/modify files with relative paths:
- `./test-results/` directory for evidence
- `./test-results/phase3-test-report.md` - Comprehensive test report

Include in test report:
- Test environment (model versions, SDK versions, configuration)
- Each test with: objective, steps, expected results, actual results, evidence (logs, responses)
- Pass/fail status for each test
- Root cause analysis for any failures
- Recommendations for any issues found
</output>

<verification>
Before declaring complete, verify your work:

1. Test Execution:
   - [ ] Test 1 (Gemini 3 Thinking) completed and documented
   - [ ] Test 2 ("SAY MY NAME") completed and documented
   - [ ] Test 3 (History Window) completed and documented
   - [ ] Test 4 (Thinking + History) completed and documented
   - [ ] Test 5 (Gemini 2.5 Regression) completed and documented
   - [ ] Test 6 (Fallback) completed and documented (if applicable)

2. Results Documentation:
   - [ ] All tests have pass/fail status
   - [ ] Evidence captured (logs, responses, errors)
   - [ ] Root cause analysis for any failures
   - [ ] Recommendations for issues

3. Overall Assessment:
   - [ ] Critical tests pass (Test 1, Test 2)
   - [ ] No blocking regressions (Test 5)
   - [ ] Test report is complete and actionable
</verification>

<success_criteria>
- ✅ Phase 1 fix validated (no "Unknown field for ThinkingConfig" errors)
- ✅ Phase 2 fix validated ("SAY MY NAME" works correctly)
- ✅ 50-message history window works as expected
- ✅ Thinking mode with multi-turn conversation works
- ✅ No regressions with Gemini 2.5 models
- ✅ Test report complete with evidence
- ✅ Ready for deployment (all critical tests pass)
</success_criteria>
