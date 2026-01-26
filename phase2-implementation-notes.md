# Phase 2: Conversation History Bug Fix - Implementation Notes

## Overview

This document describes the implementation of the conversation history fix for the AURA-CHAT RAG engine. The bug caused multi-turn conversations to fail because history was formatted as plain text strings instead of proper Gemini API message objects.

## Problem Statement

**Original Issue**: When users asked "SAY MY NAME" expecting the model to remember their name from earlier conversation, it failed because:

1. History was embedded as text like `"User: content\nModel: content\n..."` 
2. Gemini API expects `[{role: 'user', parts: [{text: '...'}]}, {role: 'model', parts: [{text: '...'}]}]` format
3. ChatManager already stored messages correctly, but the integration was wrong
4. History window was limited to 20 messages instead of leveraging the 200k token window

## Changes Made

### 1. History Window Increase (Line 440-441)

**Before:**
```python
history = self.chat_manager.get_last_n_messages(session_id, n=20)
```

**After:**
```python
# Retrieve last 50 messages for 200k token window
history = self.chat_manager.get_last_n_messages(session_id, n=50)
```

**Rationale**: Gemini 2.5 Flash/Pro supports 200k+ token context windows. 50 messages provides more conversation context while remaining well within limits.

### 2. New Helper Method: `_build_message_history_with_signatures_v2()` (Lines 1322-1358)

Added a new method to inject thought signatures into the structured `contents` array for multi-turn thinking mode:

```python
def _build_message_history_with_signatures_v2(
    self, contents: List[Dict[str, Any]], session_id: str
) -> List[Dict[str, Any]]:
    """
    Build message history with thought signatures for multi-turn thinking mode.
    
    Injects thought signatures into appropriate positions in the conversation
    history. Signatures are added after model messages to preserve turn order.
    """
```

This method:
- Takes the structured `contents` array (not a plain string)
- Injects thought signatures after model messages
- Preserves conversation turn order

### 3. History Formatting Refactor (Lines 1384-1402)

**Before:**
```python
history_lines = [
    f"{msg['role'].capitalize()}: {msg['content']}" for msg in history[-20:]
]
history_str = "\n".join(history_lines)

user_content = f"""Context:
{context_str if context else "No relevant documents found."}

Previous conversation:
{history_str}

User: {query}"""
```

**After:**
```python
# Build proper multi-turn conversation contents array for Gemini API
# Format: [{role: 'user'|'model', parts: [{text: '...'}]}, ...]
contents: List[Dict[str, Any]] = []

# Add conversation history as structured messages (last 50, from query())
# Map 'assistant' role to 'model' for Gemini API compatibility
for msg in history:
    role = "model" if msg["role"] == "assistant" else msg["role"]
    contents.append({"role": role, "parts": [{"text": msg["content"]}]})

# Build current user message with context embedded
current_user_content = (
    f"Context from documents:\n"
    f"{context_str if context else 'No relevant documents found.'}\n\n"
    f"User's question: {query}"
)

# Add current query as final user message
contents.append({"role": "user", "parts": [{"text": current_user_content}]})
```

**Key Changes:**
- History is now a proper `[{role, parts}]` array
- Role mapping: `"assistant"` → `"model"` for Gemini API
- Context embedded in final user message, not as separate system message
- Removed redundant history slicing (already done in query())

### 4. Thinking Mode Block Update (Lines 1458-1478)

**Before:**
```python
messages = self._build_message_history_with_signatures(
    user_content, session_id
)
```

**After:**
```python
# Inject thought signatures into contents array for multi-turn thinking
messages = self._build_message_history_with_signatures_v2(
    contents, session_id
)
```

Uses the new v2 method with structured contents array.

### 5. Non-Thinking Mode Block Update (Lines 1479-1509)

All calls to `_call_gemini()` now pass `contents` instead of `user_content`:

**Before:**
```python
response = await _call_gemini(
    content=user_content,
    generation_config=generation_config,
)
```

**After:**
```python
response = await _call_gemini(
    content=contents,
    generation_config=generation_config,
)
```

### 6. Tutor Retry Block Update (Lines 1554-1567)

Updated the tutor mode refusal retry block to also use `contents` array:

**Before:**
```python
retry_response = await self.model.generate_content_async(
    contents=user_content,
    ...
)
```

**After:**
```python
retry_response = await self.model.generate_content_async(
    contents=contents,
    ...
)
```

## Test Scenarios

### Test 1: "SAY MY NAME" Scenario

1. User: "Hi, my name is Peter"
2. Model: "Hello Peter! Nice to meet you..."
3. User: "SAY MY NAME"
4. **Expected**: "Peter" (model should remember from conversation history)
5. **Before Fix**: Would fail - history was plain text, not structured messages
6. **After Fix**: Should work - history is proper `{role, parts}` array

### Test 2: Multi-Turn Conversation

1. User: "What is machine learning?"
2. Model: [Response about ML]
3. User: "How does it relate to what you just said?"
4. **Expected**: Model references previous response
5. **After Fix**: Full conversation context available as structured messages

### Test 3: Extended Conversation (50 messages)

1. Conduct 25+ turn conversation
2. Reference something from early in conversation
3. **Expected**: Model should still have access to early context
4. **Before Fix**: Only 20 messages, easily lost context
5. **After Fix**: 50 messages, much better context retention

## Technical Notes

### Role Mapping

ChatManager uses `"assistant"` for model responses, but Gemini API expects `"model"`:

```python
role = "model" if msg["role"] == "assistant" else msg["role"]
```

### Thought Signatures

For thinking mode, the v2 method injects thought signatures after model messages to maintain multi-turn reasoning continuity:

```python
if msg.get("role") == "model" and sig_index < len(signatures):
    sig_part = {"text": ""}
    sig_part["thought_signature"] = signatures[sig_index]["signature"]
    result.append({"role": "model", "parts": [sig_part]})
```

### Backward Compatibility

- Original `_build_message_history_with_signatures()` method preserved for any other uses
- New v2 method added without breaking existing code
- Fallback behavior maintained in error handlers

## Verification

- [x] History retrieval changed from 20 to 50 messages
- [x] History formatted as `[{role, parts}]` array, not plain text string
- [x] New helper method `_build_message_history_with_signatures_v2()` created
- [x] Thinking mode block uses `contents` array
- [x] Non-thinking mode block uses `contents` array
- [x] Tutor retry block uses `contents` array
- [x] Role mapping: `"assistant"` → `"model"`
- [x] Context embedded in final user message

## Files Modified

- `AURA-CHAT/backend/rag_engine.py` - Main changes (lines 440, 1322-1358, 1384-1402, 1458-1509, 1554-1567)

## Date

Implementation completed: 2026-01-26
