# Phase 10 — Validation Architecture

## Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8+ with pytest-asyncio |
| Shared config | `shared/model_router/pyproject.toml` [tool.pytest.ini_options] |
| Quick run | `cd shared/model_router && python -m pytest tests/ -x -q` |
| Full suite | `cd shared/model_router && python -m pytest tests/ -v` |
| CHAT router tests | `cd AURA-CHAT && python -m pytest server/tests/ -x -v` |
| NOTES router tests | `cd AURA-NOTES-MANAGER && python -m pytest tests/ -x -v` |
| Root-level audit | `python -m pytest tests/test_no_direct_imports.py -v` |

## Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | Plan | File Exists? |
|--------|----------|-----------|-------------------|------|-------------|
| CONFIG-01 | Settings store CRUD (unit) | unit | `cd shared/model_router && python -m pytest tests/test_settings_store.py -x` | 10-01 | ❌ Wave 0 |
| CONFIG-01 | Admin set/get defaults via REST | integration | `cd AURA-CHAT && python -m pytest server/tests/test_settings_router.py -x -k defaults` | 10-02 | ❌ Wave 0 |
| CONFIG-03 | Model list cached with TTL (unit) | unit | `cd shared/model_router && python -m pytest tests/test_model_cache.py -x` | 10-01 | ❌ Wave 0 |
| CONFIG-03 | Model list endpoint with caching | integration | `cd AURA-CHAT && python -m pytest server/tests/test_settings_router.py -x -k models` | 10-02 | ❌ Wave 0 |
| CONFIG-04 | API key encrypt/store/mask/validate (unit) | unit | `cd shared/model_router && python -m pytest tests/test_key_manager.py -x` | 10-01 | ❌ Wave 0 |
| CONFIG-04 | API key REST endpoints | integration | `cd AURA-CHAT && python -m pytest server/tests/test_settings_router.py -x -k api_key` | 10-02 | ❌ Wave 0 |
| UI-03 | No direct provider imports in either app | smoke | `python -m pytest tests/test_no_direct_imports.py -x` | 10-04 | ❌ Wave 0 |
| UI-03 | Celery workers import model_router | integration | `python -c "from model_router import get_default_router; print('OK')"` | 10-04 | ✅ (test_import_contexts.py partial) |

## Sampling Rate

| Trigger | Action |
|---------|--------|
| Per task commit | `cd shared/model_router && python -m pytest tests/ -x -q` (shared unit tests) |
| Per plan completion | Full suite for affected app: shared + app-specific tests |
| Wave 1 complete | Plans 01 + 03: shared unit tests + CHAT consumer import checks |
| Wave 2 complete | Plans 02 + 04: integration tests + grep audit for direct imports |
| Phase gate | Zero direct provider imports outside shared/model_router + all new tests green + both apps start without import errors |

## Wave 0 Gap Analysis

These test files do NOT exist yet. Each must be created by its owning plan before the plan's implementation tasks can claim "verified":

| Gap File | Covers | Owner Plan | Status |
|----------|--------|------------|--------|
| `shared/model_router/tests/test_settings_store.py` | CONFIG-01 unit: CRUD for use-case defaults in Redis hash | 10-01 Task 2 | ❌ |
| `shared/model_router/tests/test_key_manager.py` | CONFIG-04 unit: Fernet encryption, masking rules, validation | 10-01 Task 2 | ❌ |
| `shared/model_router/tests/test_model_cache.py` | CONFIG-03 unit: TTL caching, cache miss/hit, force refresh | 10-01 Task 2 | ❌ |
| `AURA-CHAT/server/tests/test_settings_router.py` | CONFIG-01, CONFIG-03, CONFIG-04 integration: REST endpoint behavior | 10-02 Task 3 | ❌ |
| `tests/test_no_direct_imports.py` | UI-03 smoke: grep-based audit of both apps' non-test files | 10-04 Task 2 | ❌ |

## Test Strategy by Plan

### Plan 01 (Wave 1): Shared Config Modules
- **Unit tests** for all three modules using FakeAsyncRedis (no running Redis)
- TDD approach: write tests first, then implement
- Verify: `cd shared/model_router && python -m pytest tests/test_settings_store.py tests/test_key_manager.py tests/test_model_cache.py -v`

### Plan 02 (Wave 2): REST Endpoints
- **Integration tests** using `httpx.AsyncClient` with ASGI transport (no running server)
- Mock shared modules via FastAPI `dependency_overrides`
- Tests cover: defaults CRUD (GET/PUT), model listing (GET), API key lifecycle (POST/GET/DELETE)
- Verify: `cd AURA-CHAT && python -m pytest server/tests/test_settings_router.py -v`

### Plan 03 (Wave 1): CHAT SDK Migration
- **No new test files** — verification via import checks and AST analysis
- Verify: zero SDK imports in non-test files + all consumer imports succeed

### Plan 04 (Wave 2): NOTES SDK Migration + Audit
- **Audit test** at repo root: `tests/test_no_direct_imports.py`
- Tests scan both apps for forbidden import patterns
- Tests verify model_router importable from multiple working directories (including Celery context)
- Verify: `python -m pytest tests/test_no_direct_imports.py -v`

## Phase Gate Criteria

All of these must pass for phase 10 to be considered complete:

```bash
# 1. Shared module unit tests (20+ tests)
cd shared/model_router && set AURA_TEST_MODE=true && python -m pytest tests/test_settings_store.py tests/test_key_manager.py tests/test_model_cache.py -v

# 2. Full shared suite passes (no regressions, 132+ existing + 20+ new)
cd shared/model_router && set AURA_TEST_MODE=true && python -m pytest tests/ -v

# 3. Settings router integration tests (8+ tests)
cd AURA-CHAT && set AURA_TEST_MODE=true && python -m pytest server/tests/test_settings_router.py -v

# 4. UI-03 audit passes
set AURA_TEST_MODE=true && python -m pytest tests/test_no_direct_imports.py -v

# 5. Both apps start without import errors
cd AURA-CHAT && set AURA_TEST_MODE=true && python -c "from server.main import app; print(f'CHAT routes: {len(app.routes)}')"
cd AURA-NOTES-MANAGER && set AURA_TEST_MODE=true && python -c "from api.main import app; print(f'NOTES routes: {len(app.routes)}')"
```
