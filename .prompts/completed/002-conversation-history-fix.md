<objective>
Fix the Conversation History issue in AURA-CHAT RAG engine where history is formatted as plain text strings instead of proper message objects. The bug prevents the LLM from accessing previous conversation context - when users ask "SAY MY NAME" expecting the model to remember their name from earlier, it fails because history is embedded as text like "User: content\nModel: content\n..." instead of proper Gemini API format [{role: 'user', parts: [{text: '...'}]}, {role: 'model', parts: [{text: '...'}]}].

Thoroughly analyze the problem before implementing. Consider multiple approaches and validate each step before proceeding to the next.
</objective>

<context>
You are fixing a production bug in AURA-CHAT, a student-facing academic RAG chat application with React + FastAPI + Vertex AI stack. The project uses Python 4-space indent, Google Python style. Always use the root .venv at `../../.venv/Scripts/python` for Python operations.

The user has already completed research and identified:
- Current implementation formats history as plain text string
- Gemini API requires contents: [{role, parts}] format for proper multi-turn handling
- ChatManager already stores messages in correct format, just needs proper integration
- History retrieval is limited to 20 messages, should be 50 for 200k token window

Key file to modify: `AURA-CHAT/backend/rag_engine.py`
Supporting file to reference: `AURA-CHAT/backend/chat_manager.py` (already correct format)
Supporting file to reference: `AURA-CHAT/backend/utils/config.py`

@see: CLAUDE.md - Project conventions and anti-patterns
@see: .prompts/001-gemini3-thinking-mode-fix.md - Phase 1 (already completed)
</context>

<requirements>
Complete these tasks in order:

1. **Read and Understand Current Implementation**
   - Read `AURA-CHAT/backend/rag_engine.py` lines 430-450 to understand history retrieval in `query()` method
   - Read `AURA-CHAT/backend/rag_engine.py` lines 1340-1380 to understand current history formatting in `_generate_response()`
   - Read `AURA-CHAT/backend/rag_engine.py` lines 1400-1460 to understand thinking/non-thinking mode blocks
   - Read `AURA-CHAT/backend/chat_manager.py` to confirm message format (already correct)
   - Identify all locations where history is used

2. **Increase History Window**
   - Change history retrieval from 20 to 50 messages (line 437 area)
   - Rationale: 200k token window supports 50+ messages comfortably

3. **Refactor History Formatting**
   - Convert history from plain text string to proper message array format:
     ```
     # Old format (WRONG):
     "User: content\nModel: content\nUser: content"

     # New format (CORRECT):
     [
         {"role": "user", "parts": [{"text": "content"}]},
         {"role": "model", "parts": [{"text": "content"}]},
     ]
     ```
   - Update lines 1344-1357 to build `contents` array instead of `history_str`
   - Preserve context embedding in final user message

4. **Add Signature Injection Helper**
   - Create new method: `_build_message_history_with_signatures_v2(contents, session_id)`
   - Purpose: Inject thought signatures into message history for multi-turn thinking mode
   - Logic: Iterate through `self.thought_signatures[session_id]` and insert signatures into appropriate positions

5. **Update Thinking Mode Block**
   - Modify lines 1406-1421 to use `contents` array instead of `user_content` string
   - Call `_build_message_history_with_signatures_v2()` for signature injection
   - Pass `contents` to `_call_gemini()`

6. **Update Non-Thinking Mode Block**
   - Modify lines 1422-1453 to use `contents` array instead of `user_content` string
   - Pass `contents` to `_call_gemini()`

7. **Verification Steps**
   - Run Python syntax check
   - Run lsp_diagnostics on rag_engine.py
   - Verify no new errors introduced
   - Document the "SAY MY NAME" test scenario for integration testing

</requirements>

<implementation>
Follow these guidelines:

- **Use extended thinking** - deeply consider edge cases (e.g., role alternation, empty messages, context embedding)
- **Research-first approach** - read current implementation thoroughly before changing
- **Preserve existing structure** - don't refactor unrelated code, only fix history formatting
- **Maintain config access** - use `config` constants where appropriate
- **Message array structure** - use `{"role": msg["role"], "parts": [{"text": msg["content"]}]}`
- **Role preservation** - use `msg["role"]` from ChatManager (already "user" or "model")
- **Context embedding** - embed context in final user message, not as separate system message

Why this matters:
- Plain text string is treated as documentation/context, not conversation turns
- Gemini API requires `{role, parts}` format for proper multi-turn handling
- 50 messages fit in 200k token window (~5,000-10,000 tokens)
- Model cannot distinguish plain text history from actual conversation turns
</requirements>

<output>
Create/modify files with relative paths:
- `AURA-CHAT/backend/rag_engine.py` - Update history retrieval, formatting, and mode blocks
- Add new method: `_build_message_history_with_signatures_v2()`

Save findings to:
- `./phase2-implementation-notes.md` - Document approach and integration test scenarios
</output>

<verification>
Before declaring complete, verify your work:

1. Code Understanding:
   - [ ] Current history formatting identified and understood
   - [ ] All locations where history is used identified
   - [ ] ChatManager message format confirmed correct

2. Code Changes:
   - [ ] History retrieval changed from 20 to 50 messages
   - [ ] History formatted as `[{role, parts}]` array, not plain text string
   - [ ] New helper method `_build_message_history_with_signatures_v2()` created
   - [ ] Thinking mode block uses `contents` array
   - [ ] Non-thinking mode block uses `contents` array

3. Diagnostics:
   - [ ] Python syntax check passes
   - [ ] lsp_diagnostics shows no new errors on rag_engine.py
   - [ ] File compiles without ImportError

4. Documentation:
   - [ ] phase2-implementation-notes.md created with test scenarios
</verification>

<success_criteria>
- ✅ "SAY MY NAME" test scenario works (model remembers conversation)
- ✅ History window increased from 20 to 50 messages
- ✅ History formatted as `{role, parts}` objects, not plain text
- ✅ Both thinking and non-thinking modes use message array
- ✅ Python compilation passes
- ✅ lsp_diagnostics clean
- ✅ No regressions with existing functionality
</success_criteria>

<examples>
**Example: Current (WRONG) implementation:**
```python
history_lines = [
    f"{msg['role'].capitalize()}: {msg['content']}"
    for msg in history[-20:]
]
history_str = "\n".join(history_lines)

user_content = f"""Context:
{context_str if context else "No relevant documents found."}

Previous conversation:
{history_str}  # ❌ Embedded as text string

User: {query}"""
```

**Example: Fixed (CORRECT) implementation:**
```python
# Build proper multi-turn conversation contents array
contents = []

# Add conversation history as structured messages (last 50)
for msg in history[-50:]:
    contents.append({
        "role": msg["role"],
        "parts": [{"text": msg["content"]}]
    })

# Build current user message with context
current_user_content = f"""Context from documents:
{context_str if context else "No relevant documents found."}

User's question: {query}"""

# Add current query as final user message
contents.append({
    "role": "user",
    "parts": [{"text": current_user_content}]
})
```
</examples>
