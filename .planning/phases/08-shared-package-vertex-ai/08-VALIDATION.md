# Phase 8: Shared Package Foundation + Vertex AI Migration — Validation

**Created:** 2026-03-10
**Phase:** 08-shared-package-vertex-ai

## Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio |
| Config (AURA-CHAT) | `AURA-CHAT/pytest.ini` + `AURA-CHAT/pyproject.toml` |
| Config (AURA-NOTES-MANAGER) | `AURA-NOTES-MANAGER/conftest.py` (env vars only) |
| Config (shared package) | `shared/model_router/pyproject.toml` [tool.pytest.ini_options] |
| Quick run (AURA-CHAT) | `cd AURA-CHAT && ../.venv/Scripts/python -m pytest tests/ -x --tb=short` |
| Quick run (NOTES) | `cd AURA-NOTES-MANAGER && ../.venv/Scripts/python -m pytest tests/ -x --tb=short` |
| Quick run (shared) | `cd shared/model_router && ../../.venv/Scripts/python -m pytest tests/ -x` |

## Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ROUTER-01 | `router.generate(model="gemini-2.0-flash")` returns correct shape | unit | `pytest shared/model_router/tests/test_router.py::test_generate_vertex_ai -x` | ❌ Wave 0 |
| ROUTER-02 | `router.embed()` returns 768-dim, rejects runtime provider switch | unit | `pytest shared/model_router/tests/test_router.py::test_embed_dimension_validation -x` | ❌ Wave 0 |
| ROUTER-04 | Provider errors surface as typed exceptions | unit | `pytest shared/model_router/tests/test_errors.py -x` | ❌ Wave 0 |
| PROV-01 | All 210+ existing tests pass through shims | integration | `cd AURA-CHAT && ../.venv/Scripts/python -m pytest tests/ -x` | ✅ (existing) |
| PROV-01 | AURA-NOTES-MANAGER tests pass through shims | integration | `cd AURA-NOTES-MANAGER && ../.venv/Scripts/python -m pytest tests/ -x` | ✅ (existing) |
| PROV-01 | Shared package importable from both app contexts | smoke | `pytest shared/model_router/tests/test_import_contexts.py -x` | ❌ Wave 0 |

## Sampling Rate

- **Per task commit:** Run shared package tests + one app's quick suite
- **Per wave merge:** Full suite of both apps + shared package
- **Phase gate:** All three test suites green before phase completion

## Wave 0 Gaps

- [ ] `shared/model_router/tests/conftest.py` — shared fixtures, AURA_TEST_MODE setup
- [ ] `shared/model_router/tests/test_types.py` — GenerateRequest, GenerateResponse validation
- [ ] `shared/model_router/tests/test_errors.py` — error hierarchy mapping from google.genai errors
- [ ] `shared/model_router/tests/test_router.py` — ModelRouter routing, generate, embed
- [ ] `shared/model_router/tests/test_vertex_ai_provider.py` — VertexAIProvider in test mode
- [ ] `shared/model_router/tests/test_import_contexts.py` — verify import from different cwd paths
- [ ] `shared/model_router/pyproject.toml` — pytest configuration section
- [ ] Framework install: `pip install -e shared/model_router[all,dev]`
