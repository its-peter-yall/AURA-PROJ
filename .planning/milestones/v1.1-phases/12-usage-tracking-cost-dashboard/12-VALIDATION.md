# Phase 12: Usage Tracking + Cost Dashboard - Validation

**Generated:** 2026-03-16
**Phase:** 12-usage-tracking-cost-dashboard
**Requirements:** USAGE-01, USAGE-02

## Test Framework

| Property | Value |
|----------|-------|
| Framework (Python) | pytest 8+ / pytest-asyncio 0.23+ |
| Config file (Python) | `shared/model_router/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run (Python) | `cd shared/model_router && python -m pytest tests/ -x -q` |
| Full suite (Python) | `cd shared/model_router && python -m pytest tests/ -v` |
| Framework (Frontend) | Vitest 3.2.4 / @testing-library/react |
| Config file (Frontend) | `AURA-CHAT/client/vitest.config.ts` |
| Quick run (Frontend) | `cd AURA-CHAT/client && npx vitest run --reporter=verbose` |

## Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| USAGE-01 | UsageRecord model serialization | unit | `pytest tests/test_usage_tracker.py::test_usage_record_serialization -x` | ❌ Wave 0 |
| USAGE-01 | CostCalculator Vertex pricing | unit | `pytest tests/test_cost_calculator.py::test_vertex_pricing -x` | ❌ Wave 0 |
| USAGE-01 | CostCalculator OpenRouter pricing | unit | `pytest tests/test_cost_calculator.py::test_openrouter_pricing -x` | ❌ Wave 0 |
| USAGE-01 | UsageTracker.record() persists to Redis | unit | `pytest tests/test_usage_tracker.py::test_record_persists -x` | ❌ Wave 0 |
| USAGE-01 | Router hooks track generate() calls | integration | `pytest tests/test_router.py::test_generate_tracks_usage -x` | ❌ Wave 0 |
| USAGE-01 | Streaming usage captured | unit | `pytest tests/test_usage_tracker.py::test_stream_usage -x` | ❌ Wave 0 |
| USAGE-02 | Usage summary endpoint returns data | unit | Backend test via pytest | ❌ Wave 0 |
| USAGE-02 | Date range filtering works | unit | Backend test via pytest | ❌ Wave 0 |
| USAGE-02 | Dashboard renders with mock data | unit | `npx vitest run src/features/usage -x` | ❌ Wave 0 |
| USAGE-02 | Session cost badge displays | unit | `npx vitest run src/features/usage -x` | ❌ Wave 0 |

## Sampling Rate

- **Per task commit:** `cd shared/model_router && python -m pytest tests/ -x -q`
- **Per wave merge:** Full Python + Frontend suites
- **Phase gate:** All test suites green

## Wave 0 Gaps

- [ ] `shared/model_router/tests/test_usage_tracker.py` - covers USAGE-01
- [ ] `shared/model_router/tests/test_cost_calculator.py` - covers USAGE-01
- [ ] `AURA-CHAT/server/tests/test_usage_router.py` - covers USAGE-02
- [ ] `AURA-CHAT/client/src/features/usage/**/*.test.tsx` - covers USAGE-02
- [ ] Recharts install: `npm install recharts@^3.8.0` in both frontends
