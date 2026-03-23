---
phase: 15
slug: wire-aura-chat-consumers
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | Root `pytest.ini` |
| **Quick run command** | `python -m pytest AURA-CHAT/tests/backend/test_llm_entity_extractor.py AURA-CHAT/tests/test_llm_gatekeeper.py -x` |
| **Full suite command** | `python -m pytest AURA-CHAT/tests/ -x` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest AURA-CHAT/tests/backend/test_llm_entity_extractor.py AURA-CHAT/tests/test_llm_gatekeeper.py -x`
- **After every plan wave:** Run `python -m pytest AURA-CHAT/tests/ -x`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 1 | PP-01 | unit | `python -m pytest AURA-CHAT/tests/backend/test_llm_entity_extractor.py -x` | ✅ | ⬜ pending |
| 15-01-02 | 01 | 1 | PP-02 | unit | `python -m pytest AURA-CHAT/tests/test_llm_gatekeeper.py -x` | ✅ | ⬜ pending |
| 15-01-03 | 01 | 1 | PP-03 | unit | `python -m pytest AURA-CHAT/tests/backend/test_llm_embeddings_provider.py -x` | ❌ W0 | ⬜ pending |
| 15-01-04 | 01 | 1 | PP-04 | unit | `python -m pytest AURA-CHAT/tests/backend/test_llm_relationship_extractor.py -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `AURA-CHAT/tests/backend/test_llm_embeddings_provider.py` — stubs for PP-03 confirming `provider` is passed to `router.embed()` when SettingsStore is configured
- [ ] `AURA-CHAT/tests/test_llm_gatekeeper.py` — extend with test for OpenRouter provider path (currently all tests mock `get_model` and don't test provider routing)
- [ ] `AURA-CHAT/tests/backend/test_llm_relationship_extractor.py` — extend with test confirming `resolve_use_case_config("relationship_extraction")` is called independently

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| OpenRouter JSON mode works for gatekeeper | PP-02 | Requires live OpenRouter API key and model that supports JSON mode | Set gatekeeper provider to OpenRouter in settings, send a query that triggers structured output, verify JSON parse succeeds |
| Changing provider takes effect without restart | Success Criteria #5 | Requires running server with live Redis | Change entity_extraction provider in settings page, trigger a document processing run, check response metadata shows new provider |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
