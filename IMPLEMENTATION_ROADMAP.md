# Implementation Roadmap: Gemini 3 Thinking Mode & Conversation History Fixes

**Created:** 2026-01-26
**Based on:** `whats-next.md` (handoff document)
**Status:** Implementation Ready

---

## Phase 1: Pre-Implementation Verification

### 1.1 SDK Version Check
| Task | Command | Expected Result | Pass Criteria |
|------|---------|-----------------|---------------|
| Check Vertex AI SDK version | `pip show google-cloud-aiplatform` | Version ≥ Dec 2025 | Supports Gemini 3 `thinking_level` |
| Check Generative AI SDK | `pip show google-generative-ai` | Any version | Alternative SDK available |

**Risk:** If SDK is older than Dec 2025, Gemini 3 features will fail. May need `pip install --upgrade google-cloud-aiplatform`

---

## Phase 2: Gemini 3 Thinking Mode Fix

### 2.1 Update `_get_generation_config()` Method
**File:** `AURA-CHAT/backend/rag_engine.py`
**Lines:** 1203-1223

| Change | Current | New |
|--------|---------|-----|
| Parameter selection | Unified (uses `thinking_budget`) | Model-based branching |
| Gemini 3 models | N/A | Use `thinking_level` |
| Gemini 2.5 models | Uses `thinking_budget` | Unchanged |

**Code Change:**
```python
if should_use_thinking and model_supports_thinking:
    if "gemini-3" in model_name.lower():
        level = config.THINKING_LEVEL
        gen_config["thinking_config"] = {
            "thinking_level": level,
            "include_thoughts": True,
        }
        logger.info(f"Thinking mode enabled for {model_name} (level: {level})")
    else:
        budget = config.THINKING_BUDGET
        gen_config["thinking_config"] = {
            "thinking_budget": budget,
            "include_thoughts": True,
        }
        logger.info(f"Thinking mode enabled for {model_name} (budget: {budget})")
```

### 2.2 Update Thinking Log Messages
**File:** `AURA-CHAT/backend/rag_engine.py`
**Lines:** 1368-1372

| Current Output | New Output |
|----------------|------------|
| `budget: N/A` (for Gemini 3) | `level: HIGH` (for Gemini 3) |
| `budget: 2048` (for Gemini 2.5) | `budget: 2048` (for Gemini 2.5) |

**Code Change:**
```python
if has_thinking:
    thinking_config = gen_config.get("thinking_config", {})
    if "gemini-3" in self.model_name.lower():
        level = thinking_config.get("thinking_level", "N/A")
        logger.info(f"Native thinking enabled for model {self.model_name} (level: {level})")
    else:
        budget = thinking_config.get("thinking_budget", "N/A")
        logger.info(f"Native thinking enabled for model {self.model_name} (budget: {budget})")
```

---

## Phase 3: Conversation History Fix

### 3.1 Increase History Window
**File:** `AURA-CHAT/backend/rag_engine.py`
**Line:** 437 (in `query()` method)

| Before | After | Rationale |
|--------|-------|-----------|
| 20 messages | 50 messages | 200k token window supports 50+ messages |

### 3.2 Refactor History Formatting
**File:** `AURA-CHAT/backend/rag_engine.py`
**Lines:** 1344-1357

| Aspect | Current | New |
|--------|---------|-----|
| Format | Plain text strings | `{role, parts}` objects |
| Structure | Embedded in single prompt | Separate message array |
| Role context | Lost | Preserved |

**Code Change:**
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

### 3.3 Add Signature Injection Helper
**File:** `AURA-CHAT/backend/rag_engine.py`
**New Method:** `_build_message_history_with_signatures_v2()`

```python
def _build_message_history_with_signatures_v2(
    self, contents: List[Dict[str, Any]], session_id: str
) -> List[Dict[str, Any]]:
    """Inject thought signatures into message history for multi-turn thinking."""
    messages = list(contents)

    if session_id in self.thought_signatures:
        signatures = self.thought_signatures[session_id]
        for sig in signatures:
            part = {"text": ""}
            part["thought_signature"] = sig["signature"]
            messages.insert(len(messages) - 1, {"role": "model", "parts": [part]})

    return messages
```

### 3.4 Update Thinking Mode Block
**File:** `AURA-CHAT/backend/rag_engine.py`
**Lines:** 1406-1421

| Before | After |
|--------|-------|
| Uses `user_content` (string) | Uses `contents` (message array) |
| Signature injection not integrated | Calls new helper method |

### 3.5 Update Non-Thinking Mode Block
**File:** `AURA-CHAT/backend/rag_engine.py`
**Lines:** 1422-1453

| Before | After |
|--------|-------|
| Passes `user_content` (string) | Passes `contents` (message array) |

---

## Phase 4: Testing & Validation

### 4.1 Unit Tests
| Test | Description | Pass Criteria |
|------|-------------|---------------|
| SDK Check | Verify installed version | No errors, correct version |
| Config Test | Verify model branching | Both Gemini 2.5/3 paths work |
| History Format | Verify message array structure | Valid `{role, parts}` format |
| Signature Injection | Verify helper method | Correct signature placement |

### 4.2 Integration Tests
| Test | Steps | Pass Criteria |
|------|-------|---------------|
| **Thinking Mode (Gemini 3)** | 1. Query with thinking enabled | No `thinking_level` errors |
| | 2. Check logs | `level: HIGH` shown |
| | 3. Verify response | Thought process in debug logs |
| **Conversation History** | 1. Say "My name is Peter" | Acknowledged |
| | 2. Ask "SAY MY NAME" | Responds "Peter" |
| | 3. Check 50+ messages | Works correctly |
| **Multi-turn with Thinking** | 1. Enable thinking | No conflicts |
| | 2. Multi-turn query | Signatures preserved |

### 4.3 Regression Tests
| Test | Description | Pass Criteria |
|------|-------------|---------------|
| Gemini 2.5 | Verify 2.5 models still work | `thinking_budget` works correctly |
| Non-thinking mode | Verify fallback | No regressions |
| Empty history | Edge case | Handles gracefully |

---

## Phase 5: Build & Deploy

### 5.1 Pre-Deployment Checklist
- [ ] `lsp_diagnostics` clean on `rag_engine.py`
- [ ] Python syntax check passes
- [ ] All tests pass
- [ ] No new warnings introduced

### 5.2 Deployment Steps
1. **Stage changes:** `git add AURA-CHAT/backend/rag_engine.py`
2. **Commit:** With descriptive message
3. **Build:** If frontend changes needed
4. **Test:** E2E tests pass
5. **Deploy:** Via CI/CD system

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SDK too old | Medium | High | Pre-check SDK version, upgrade if needed |
| Thought signature format wrong | Low | Medium | Iteration after first test run |
| Token limit exceeded | Low | Medium | Start with 50, reduce to 35 if needed |
| Performance degradation | Low | Low | Monitor latency, cache if needed |

---

## Success Criteria

1. ✅ No `Unknown field for ThinkingConfig: thinking_level` errors
2. ✅ Log shows correct config (`level: HIGH` for Gemini 3, `budget: 2048` for 2.5)
3. ✅ "SAY MY NAME" test passes (model remembers conversation)
4. ✅ 50-message history window works
5. ✅ Thinking mode with multi-turn preserves signatures
6. ✅ No regressions with Gemini 2.5 models
7. ✅ `lsp_diagnostics` clean

---

## Timeline Estimate

| Phase | Effort | Duration |
|-------|--------|----------|
| Pre-Implementation | 5 min | Verify SDK |
| Phase 1 (Thinking Mode) | 30 min | Edit + test |
| Phase 2 (History) | 45 min | Edit + test |
| Phase 3 (Testing) | 30 min | Integration tests |
| Phase 4 (Deploy) | 15 min | Build + commit |
| **Total** | **~2 hours** | |

---

**Ready for Implementation:** Yes - All tasks actionable, risks identified, success criteria defined.
