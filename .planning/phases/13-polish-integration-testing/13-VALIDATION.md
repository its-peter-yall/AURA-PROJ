# Phase 13: Polish + Integration Testing — Validation

**Generated from:** 13-RESEARCH.md Validation Architecture section

## Test Framework

| Property | Value |
|----------|-------|
| Framework (Python) | pytest 8.x + pytest-asyncio 0.23+ |
| Framework (Frontend) | Vitest 3.2.4 + React Testing Library 16.3.1 |
| Framework (E2E) | Playwright (Chromium, Firefox, WebKit + mobile) |
| Config (shared) | `shared/model_router/pyproject.toml` |
| Config (CHAT backend) | `AURA-CHAT/pytest.ini` |
| Config (CHAT frontend) | `AURA-CHAT/client/vitest.config.ts` |
| Config (NOTES backend) | `AURA-NOTES-MANAGER/conftest.py` |
| Config (NOTES frontend) | `AURA-NOTES-MANAGER/frontend/jest.config.cjs` (Firestore rules only) / Vitest (all other tests) |
| Config (E2E CHAT) | `AURA-CHAT/client/playwright.config.ts` |
| Config (E2E NOTES) | `AURA-NOTES-MANAGER/e2e/playwright.config.ts` + `AURA-NOTES-MANAGER/frontend/playwright.config.ts` |

## Quick Run Commands

| Scope | Command |
|-------|---------|
| shared/model_router | `cd shared/model_router && ../../.venv/Scripts/python -m pytest tests/ -x --tb=short` |
| AURA-CHAT backend | `cd AURA-CHAT && ../.venv/Scripts/python -m pytest tests/ server/tests/ -x --tb=short` |
| AURA-CHAT frontend | `cd AURA-CHAT/client && npx vitest run --reporter=verbose` |
| AURA-NOTES-MANAGER backend | `cd AURA-NOTES-MANAGER && ../.venv/Scripts/python -m pytest tests/ -x --tb=short` |
| AURA-NOTES-MANAGER frontend | `cd AURA-NOTES-MANAGER/frontend && npx vitest run --reporter=verbose` |
| Cross-app imports | `.venv/Scripts/python -m pytest tests/test_no_direct_imports.py -x --tb=short` |
| E2E CHAT | `cd AURA-CHAT/client && npx playwright test` |
| E2E NOTES | `cd AURA-NOTES-MANAGER/e2e && npx playwright test` |
| Full suite | Run all commands above in sequence |

## Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SC-1 | Mid-session provider switch: no errors, no lost context | integration | `pytest tests/test_cross_provider_integration.py -x` | ❌ Plan 13-01 creates |
| SC-2 | Thinking mode UI parity for Gemini and Claude | integration + unit | `pytest shared/model_router/tests/test_integration_flows.py -x` | ❌ Plan 13-01 creates |
| SC-3 | Both apps pass full test suites (unit + E2E) | regression | All quick run commands above (unit) + Playwright commands (E2E) | ✅ existing suites |
| SC-4 | Router overhead < 10ms | benchmark | `pytest tests/test_router_performance.py -x` | ❌ Plan 13-01 creates |
| REQ-VERIFY | CONFIG-01, CONFIG-03, CONFIG-04, UI-03 confirmed | verification | `pytest tests/test_no_direct_imports.py -x` + codebase grep | ✅ partially |

## Sampling Rate

- **Per task commit:** Quick run for the affected test scope
- **Per wave merge:** Full suite across all 4+ test roots
- **Phase gate:** All suites green + new integration tests green + E2E pass (or documented prerequisites)

## Wave 0 Gaps

- [ ] `tests/test_cross_provider_integration.py` — Multi-provider flow tests (SC-1)
- [ ] `tests/test_router_performance.py` — Router overhead benchmark (SC-4)
- [ ] `shared/model_router/tests/test_integration_flows.py` — Thinking mode parity + multi-concern flows (SC-2)
- [ ] Verify and fix any pre-existing failures in `shared/model_router/tests/test_compat.py`
- [ ] Update REQUIREMENTS.md traceability table for CONFIG-01, CONFIG-03, CONFIG-04, UI-03
- [ ] Run existing Playwright E2E suites for both apps to confirm no regressions (SC-3)

## E2E Test Inventory

Existing Playwright spec files that must pass for SC-3 "unit + E2E":

**AURA-CHAT** (7 specs in `AURA-CHAT/client/e2e/`):
- `chat.spec.ts` — Core chat flow
- `documents.spec.ts` — Document management
- `graph.spec.ts` — Knowledge graph
- `health.spec.ts` — Health check
- `mobile.spec.ts` — Mobile responsive
- `notes.spec.ts` — Notes feature
- `performance.spec.ts` — Performance checks

**AURA-NOTES-MANAGER** (8 specs across two dirs):
- `e2e/tests/`: `audio.spec.ts`, `explorer.spec.ts`, `api.spec.ts`
- `frontend/e2e/`: `rbac.spec.ts`, `kg-processing.spec.ts`, `health.spec.ts`, `explorer.spec.ts`, `auth.spec.ts`

**Prerequisites:** Playwright E2E tests require running backend servers. If backends are unavailable during automated sweep, document pass/fail status and defer to manual UAT.
