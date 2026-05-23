---
phase: 09
slug: i-want-to-add-another-provider-in-the-settings-page-along-wi
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-23
---

# Phase 09 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (Python) / vitest (Frontend) |
| **Config file** | `pyproject.toml` / `vitest.config.ts` |
| **Quick run command** | `python -m pytest AURA-CHAT/tests/ -x` / `npm test` |
| **Full suite command** | `python -m pytest AURA-CHAT/tests/ AURA-NOTES-MANAGER/api/tests/` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick command
- **After every plan wave:** Run full suite command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | — | — | API key stored securely, never logged | unit | `python -m pytest tests/ -k general_compute` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `shared/model_router/tests/test_general_compute.py` — provider tests
- [ ] Existing infrastructure covers most requirements

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| All behaviors have automated verification | — | — | — |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
