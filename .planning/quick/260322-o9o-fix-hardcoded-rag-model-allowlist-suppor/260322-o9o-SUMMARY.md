---
phase: quick
plan: 260322-o9o
subsystem: rag-engine
tags: [rag, model-router, allowlist, chat-api]
dependency_graph:
  requires: [model_router]
  provides: [dynamic-model-allowlist]
  affects: [chat-api, rag-engine, frontend-model-picker]
tech_stack:
  added: []
  patterns: [model-router-list-models, pass-through-validation]
key_files:
  modified:
    - AURA-CHAT/backend/rag_engine.py
    - AURA-CHAT/server/routers/chat.py
    - AURA-CHAT/tests/backend/test_rag_engine_response_parsing.py
decisions:
  - Kept `allowed_models` in `/config` response (not removed) because
    `InputArea.tsx` depends on it for the model dropdown. Populated
    dynamically via `router.list_models()` with static fallback.
  - Did NOT remove `RAG_ALLOWED_MODELS` from config.py — still used
    as fallback in `/config` endpoint and referenced elsewhere.
metrics:
  duration: ~8 min
  completed: "2026-03-22"
  tasks_completed: 3
  files_changed: 3
  lines_delta: "+30 -22"
---

# Phase quick Plan 260322-o9o: Fix Hardcoded RAG Model Allowlist Summary

## One-Liner

Removed the hardcoded 3-model allowlist gate from `set_model()` and made
the `/config` endpoint return a dynamic model list from the model router.

---

## Tasks Completed

### Task 1: Remove hardcoded allowlist from set_model()
**Commit:** `ed5062a`

Replaced the `allowed_models` validation block (14 lines) with a 2-line
pass-through that trusts the `get_model()` try/except as the sole
validation gate. Any model the model_router can resolve is now accepted;
truly invalid models still fall back to `RAG_MODEL_DEFAULT`.

### Task 2: Make /config endpoint use dynamic model list
**Commit:** `f230d1b`

Updated `GET /chat/config` to call `router.list_models()` and extract
model IDs dynamically. Falls back to `config.RAG_ALLOWED_MODELS` when the
router is unavailable (e.g. Redis down, provider API unreachable).

**Deviation from plan:** The plan suggested removing `allowed_models` from
the `/config` response entirely. However, `InputArea.tsx` uses
`config?.allowed_models` for the model selector dropdown, so removing it
would break the frontend. Instead, kept the field and populated it
dynamically.

### Task 3: Update allowlist test to verify pass-through
**Commit:** `c504e9c`

Replaced `test_can_instantiate_with_each_allowed_model` (which asserted
`RAG_ALLOWED_MODELS` must be defined) with two new tests:
- `test_set_model_accepts_any_model_name` — verifies any model name
  passes through without rejection
- `test_set_model_none_falls_back_to_default` — verifies `None` falls
  back to `RAG_MODEL_DEFAULT`

---

## Deviations from Plan

### Task 2: Kept `allowed_models` in /config response

- **Plan said:** "Preferred approach (simpler): Remove `allowed_models`
  from the `/config` response"
- **What happened:** Frontend `InputArea.tsx` (line 211) maps
  `config?.allowed_models` to the model dropdown options. Removing the
  field would disable model selection. Verified with grep — this is the
  primary model picker, not a fallback.
- **Fix:** Populated `allowed_models` dynamically from
  `router.list_models()` instead of removing it. Static fallback
  preserved for resilience.

### RAG_ALLOWED_MODELS retained in config.py

- **Plan said:** "Do NOT remove `RAG_ALLOWED_MODELS` from `config.py`"
- **Followed:** Yes — still used as fallback in `/config` endpoint and
  referenced by other consumers.

---

## Verification

| Check | Result |
|-------|--------|
| `rag_engine.py` has no `RAG_ALLOWED_MODELS` references | ✅ |
| `get_model()` try/except is sole validation gate | ✅ |
| `/config` test passes | ✅ |
| Full backend test suite (398 pass, 7 skip) | ✅ |
| Frontend `allowed_models` field preserved | ✅ |

---

## Self-Check: PASSED

- [x] `AURA-CHAT/backend/rag_engine.py` — allowlist removed
- [x] `AURA-CHAT/server/routers/chat.py` — dynamic model list
- [x] `AURA-CHAT/tests/backend/test_rag_engine_response_parsing.py` — pass-through tests
- [x] Commit `ed5062a` — exists in log
- [x] Commit `f230d1b` — exists in log
- [x] Commit `c504e9c` — exists in log
