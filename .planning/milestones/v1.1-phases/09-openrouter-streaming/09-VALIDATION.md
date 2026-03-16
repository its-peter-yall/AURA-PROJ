# Phase 09: OpenRouter Provider + Streaming Normalization - Validation

**Generated:** 2026-03-16
**Phase:** 09-openrouter-streaming
**Requirements:** PROV-02, ROUTER-03, PROV-03

## Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio |
| Config file | `shared/model_router/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `cd shared/model_router && ../../.venv/Scripts/python -m pytest tests/ -x` |
| Full suite command | `cd shared/model_router && ../../.venv/Scripts/python -m pytest tests/ -v` |

## Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PROV-02 | OpenRouter generate returns correct response shape | unit | `pytest shared/model_router/tests/test_openrouter_provider.py::test_generate_returns_correct_shape -x` | ❌ Wave 0 |
| PROV-02 | OpenRouter stream yields StreamChunk objects | unit | `pytest shared/model_router/tests/test_openrouter_provider.py::test_stream_yields_chunks -x` | ❌ Wave 0 |
| PROV-02 | OpenRouter list_models returns ModelInfo list | unit | `pytest shared/model_router/tests/test_openrouter_provider.py::test_list_models -x` | ❌ Wave 0 |
| PROV-02 | OpenRouter credit balance retrieval | unit | `pytest shared/model_router/tests/test_openrouter_provider.py::test_credit_balance -x` | ❌ Wave 0 |
| PROV-02 | OpenRouter error mapping (auth, rate limit, etc.) | unit | `pytest shared/model_router/tests/test_openrouter_provider.py::test_error_mapping -x` | ❌ Wave 0 |
| ROUTER-03 | Router.stream() yields identical StreamChunk from both providers | unit | `pytest shared/model_router/tests/test_streaming.py::test_both_providers_yield_same_chunk_type -x` | ❌ Wave 0 |
| ROUTER-03 | OpenRouter streaming normalizes delta.content to StreamChunk | unit | `pytest shared/model_router/tests/test_streaming.py::test_openrouter_content_normalization -x` | ❌ Wave 0 |
| ROUTER-03 | OpenRouter streaming normalizes delta.reasoning_content to thinking chunks | unit | `pytest shared/model_router/tests/test_streaming.py::test_openrouter_reasoning_normalization -x` | ❌ Wave 0 |
| PROV-03 | Thinking config translates to Claude reasoning.effort | unit | `pytest shared/model_router/tests/test_thinking.py::test_claude_thinking_config -x` | ❌ Wave 0 |
| PROV-03 | Thinking config gracefully degrades for unsupported models | unit | `pytest shared/model_router/tests/test_thinking.py::test_unsupported_model_no_thinking -x` | ❌ Wave 0 |
| PROV-03 | DeepSeek R1 reasoning content arrives as thinking chunks | unit | `pytest shared/model_router/tests/test_thinking.py::test_deepseek_reasoning -x` | ❌ Wave 0 |
| PROV-02 | Router resolves slash-model to OpenRouter provider | unit | `pytest shared/model_router/tests/test_router.py::test_router_resolve_openrouter_slash -x` | ✅ (exists but tests error path) |

## Sampling Rate

- **Per task commit:** `cd shared/model_router && ../../.venv/Scripts/python -m pytest tests/ -x`
- **Per wave merge:** Full shared package suite + both app quick suites
- **Phase gate:** Full suite green before `/gsd:verify-work`

## Wave 0 Gaps

- [ ] `shared/model_router/tests/test_openrouter_provider.py` - covers PROV-02
- [ ] `shared/model_router/tests/test_streaming.py` - covers ROUTER-03
- [ ] `shared/model_router/tests/test_thinking.py` - covers PROV-03
- [ ] `openai>=1.51.0` added to `pyproject.toml` optional deps
- [ ] Update `shared/model_router/tests/test_router.py` - add OpenRouter generate/stream delegation tests
