---
phase: 17
slug: frontend-cross-app-validation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Playwright 1.49+ (E2E), Vitest (frontend unit), pytest (backend) |
| **Config file** | `AURA-CHAT/client/playwright.config.ts`, `AURA-NOTES-MANAGER/frontend/playwright.config.ts` |
| **Quick run command** | `npx playwright test --grep "settings"` |
| **Full suite command** | `npm run test:e2e` (both apps) + `python -m pytest tests/` |
| **Estimated runtime** | ~120 seconds (E2E) + ~60 seconds (pytest) |

---

## Sampling Rate

- **After every task commit:** `npm run build` (type check) + `npm run lint`
- **After every plan wave:** `npx playwright test` (relevant specs) + `python -m pytest tests/test_no_direct_imports.py`
- **Before `/gsd-verify-work`:** Full suites green — `npm run test` + `npm run test:e2e` in both apps + `python -m pytest tests/`
- **Max feedback latency:** 180 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 17-01-01 | 01 | 1 | API-01 | unit | `npx tsc --noEmit` | ❌ W0 | ⬜ pending |
| 17-01-02 | 01 | 1 | API-02 | unit | `npx tsc --noEmit` | ❌ W0 | ⬜ pending |
| 17-02-01 | 02 | 1 | SC-01 | e2e | `npx playwright test --grep "settings"` | ❌ W0 | ⬜ pending |
| 17-02-02 | 02 | 1 | SC-02 | e2e | `npx playwright test --grep "gatekeeper"` | ❌ W0 | ⬜ pending |
| 17-03-01 | 03 | 2 | SC-03 | e2e | `npx playwright test --grep "settings.*behavior"` | ❌ W0 | ⬜ pending |
| 17-03-02 | 03 | 2 | SC-04 | integration | `python -m pytest tests/test_redis_fallback.py` | ❌ W0 | ⬜ pending |
| 17-03-03 | 03 | 2 | AST | unit | `python -m pytest tests/test_no_direct_imports.py` | ✅ | ⬜ pending |
| 17-03-04 | 03 | 2 | SC-05 | full | `npm run test` + `npm run test:e2e` + `python -m pytest tests/` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `AURA-CHAT/client/src/types/settings.ts` — UseCase, ProviderType, ModelInfo types
- [ ] `AURA-CHAT/client/src/features/settings/` — Full feature directory (api, hooks, components, page)
- [ ] `AURA-CHAT/client/src/App.tsx` — `/settings` route registration
- [ ] `AURA-NOTES-MANAGER/frontend/src/types/settings.ts` — Extended UseCase type
- [ ] `AURA-NOTES-MANAGER/frontend/e2e/settings.spec.ts` — NOTES settings E2E tests
- [ ] `AURA-CHAT/client/e2e/settings.spec.ts` — CHAT settings E2E tests
- [ ] `tests/test_redis_fallback.py` or integration test for SC-04

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SC-03 settings→behavior with live backend | SC-03 | Requires live LLM provider and real KG processing | Set entity_extraction to OpenRouter in UI, trigger KG processing, verify response metadata shows `provider: "openrouter"` |
| SC-04 Redis stop/start with live Redis | SC-04 | Requires real Redis process control | Stop Redis, verify consumer logs warning + uses env var, restart Redis, verify SettingsStore values resume within 30s |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
