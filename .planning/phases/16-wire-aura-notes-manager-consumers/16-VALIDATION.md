---
phase: 16
slug: wire-aura-notes-manager-consumers
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-23
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio |
| **Config file** | `AURA-NOTES-MANAGER/conftest.py` (sets AURA_TEST_MODE=true, REDIS_ENABLED=false) |
| **Quick run command** | `cd AURA-NOTES-MANAGER && python -m pytest api/tests/ -x -v` |
| **Full suite command** | `cd AURA-NOTES-MANAGER && python -m pytest -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd AURA-NOTES-MANAGER && python -m pytest api/tests/test_consumer_wiring.py -x -v`
- **After every plan wave:** Run `cd AURA-NOTES-MANAGER && python -m pytest -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 16-03-01 | 03 | 1 | PP-05/06/07/08 | unit | `pytest api/tests/test_consumer_wiring.py -x -v` | ⬜ W1 | ⬜ pending |
| 16-01-01 | 01 | 2 | PP-06 | unit | `pytest api/tests/test_consumer_wiring.py::test_entity_extractor_passes_provider -x` | ✅ after W1 | ⬜ pending |
| 16-01-02 | 01 | 2 | PP-05 | unit | `pytest api/tests/test_consumer_wiring.py::test_kg_processor_uses_resolve_config -x` | ✅ after W1 | ⬜ pending |
| 16-02-01 | 02 | 2 | PP-07 | unit | `pytest api/tests/test_consumer_wiring.py::test_embeddings_passes_provider -x` | ✅ after W1 | ⬜ pending |
| 16-02-02 | 02 | 2 | PP-08 | unit | `pytest api/tests/test_consumer_wiring.py::test_summarizer_uses_router -x` | ✅ after W1 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Tests are created in Wave 1 (Plan 16-03) before implementation runs in Wave 2. No additional Wave 0 setup needed.*

*Framework already installed — no Wave 0 framework setup needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Settings changes take effect without restart | PP-05 | Requires live Redis + running process | Change entity_extraction provider in settings UI → trigger KG processing → verify response metadata shows new provider |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-23
