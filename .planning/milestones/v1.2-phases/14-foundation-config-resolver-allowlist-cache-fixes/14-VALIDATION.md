---
phase: 14
slug: foundation-config-resolver-allowlist-cache-fixes
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.0 + pytest-asyncio >=0.23 |
| **Config file** | `shared/model_router/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `python -m pytest shared/model_router/tests/test_settings_store.py -x` |
| **Full suite command** | `python -m pytest shared/model_router/tests/ -x && python -m pytest AURA-CHAT/server/tests/test_settings_router.py -x` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest shared/model_router/tests/test_settings_store.py -x`
- **After every plan wave:** Run `python -m pytest shared/model_router/tests/ -x && python -m pytest AURA-CHAT/server/tests/test_settings_router.py -x`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 1 | API-01 | unit | `python -m pytest AURA-CHAT/server/tests/test_settings_router.py::test_set_default_gatekeeper -x` | ❌ W0 | ⬜ pending |
| 14-01-02 | 01 | 1 | API-02 | unit | `python -m pytest AURA-CHAT/server/tests/test_settings_router.py::test_set_default_relationship_extraction -x` | ❌ W0 | ⬜ pending |
| 14-01-03 | 01 | 1 | FB-01 | unit | `python -m pytest shared/model_router/tests/test_settings_store.py::test_resolve_store_overrides_env -x` | ❌ W0 | ⬜ pending |
| 14-01-04 | 01 | 1 | FB-02 | unit | `python -m pytest shared/model_router/tests/test_settings_store.py::test_resolve_redis_down_falls_back -x` | ❌ W0 | ⬜ pending |
| 14-01-05 | 01 | 1 | SC-3 | unit | `python -m pytest shared/model_router/tests/test_settings_store.py::test_resolve_settings_store_hit -x` | ❌ W0 | ⬜ pending |
| 14-01-06 | 01 | 1 | SC-4 | unit | `python -m pytest shared/model_router/tests/test_settings_store.py::test_zombie_none_cache_recovery -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `shared/model_router/tests/test_settings_store.py` — add tests for `resolve_use_case_config()` (settings-store hit, env-var fallback, hardcoded default, Redis-down)
- [ ] `shared/model_router/tests/test_settings_store.py` — add tests for zombie-None cache fix (sentinel TTL behavior, recovery timing)
- [ ] `AURA-CHAT/server/tests/test_settings_router.py` — add tests for `gatekeeper` and `relationship_extraction` as valid use cases

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
