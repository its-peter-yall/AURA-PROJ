---
wave: 2
depends_on:
  - 09-01a-PLAN.md
files_modified:
  - shared/model_router/src/model_router/cost_calculator.py
  - shared/model_router/src/model_router/__init__.py
  - shared/model_router/tests/test_general_compute_provider.py
  - shared/model_router/tests/test_import_contexts.py
autonomous: true
requirements:
  - P9-05
  - P9-09
---

# Plan 09-01b: General Compute Provider — Pricing, Exports & Tests

Completes the shared `model_router` package work: cost calculator pricing, `__init__.py` exports, and test coverage. Depends on 09-01a (core implementation must exist first).

## must_haves

- `CostCalculator` has `_GC_PRICING` dict and `_estimate_general_compute()` method; `estimate()` dispatches to it for `ProviderType.GENERAL_COMPUTE`
- `__init__.py` exports `GeneralComputeConfig` and `GeneralComputeProvider`; both in `__all__`
- `test_general_compute_provider.py` has passing tests for test-mode generate, stream, list_models, health_check, auto-registration, and exports
- `test_import_contexts.py::test_import_all_public_api` includes `GeneralComputeConfig` and `GeneralComputeProvider`
- All existing tests in `shared/model_router/tests/` pass

## Tasks

<task id="09-01b-01" title="Add General Compute pricing to CostCalculator">
<read_first>
- shared/model_router/src/model_router/cost_calculator.py (full file — 191 lines: _VERTEX_PRICING lines 39-51, estimate() lines 60-72, _estimate_vertex_ai lines 74-90, _estimate_openrouter lines 92-120)
</read_first>
<action>
Edit `cost_calculator.py`:

1. **Add `_GC_PRICING` class variable** after `_VERTEX_PRICING` (after line 51):
   ```
   _GC_PRICING: dict[str, dict[str, float]] = {
       "minimax-m2.7": {"input": 0.40, "output": 2.34},
       "deepseek-v3.2": {"input": 3.00, "output": 4.50},
       "deepseek-v3.1": {"input": 3.00, "output": 4.50},
   }
   ```

2. **Add GC branch in `estimate()`** (after the Ollama branch ~line 70):
   ```
   if provider == ProviderType.GENERAL_COMPUTE:
       return self._estimate_general_compute(usage, model)
   ```

3. **Add `_estimate_general_compute()` method** after `_estimate_openrouter()` (~after line 120):
   Same formula as Vertex AI pricing — lookup model in `_GC_PRICING`, compute `(input_tokens / 1_000_000) * input_price` + `((output_tokens + thinking_tokens) / 1_000_000) * output_price`, round to 6 decimals. Return 0.0 if model not in table.
</action>
<acceptance_criteria>
- `CostCalculator().estimate(UsageInfo(input_tokens=1_000_000, output_tokens=1_000_000), "minimax-m2.7", ProviderType.GENERAL_COMPUTE)` returns `2.74` (0.40 + 2.34)
- `CostCalculator().estimate(UsageInfo(input_tokens=1_000_000, output_tokens=1_000_000), "deepseek-v3.2", ProviderType.GENERAL_COMPUTE)` returns `7.5` (3.00 + 4.50)
- `CostCalculator().estimate(UsageInfo(input_tokens=0, output_tokens=0), "minimax-m2.7", ProviderType.GENERAL_COMPUTE)` returns `0.0`
- `CostCalculator().estimate(UsageInfo(input_tokens=1000), "unknown-model", ProviderType.GENERAL_COMPUTE)` returns `0.0`
</acceptance_criteria>
</task>

<task id="09-01b-02" title="Export GeneralComputeProvider and GeneralComputeConfig from __init__.py">
<read_first>
- shared/model_router/src/model_router/__init__.py (full file — 82 lines: imports lines 13-45, __all__ lines 47-79)
</read_first>
<action>
Edit `__init__.py`:

1. **Add imports** (after line 14, `from model_router.config import OpenRouterConfig`):
   ```
   from model_router.config import GeneralComputeConfig
   ```
   And after line 28 (`from model_router.providers.openrouter import OpenRouterProvider`):
   ```
   from model_router.providers.general_compute import GeneralComputeProvider
   ```

2. **Add to `__all__`** (alphabetical order):
   - `"GeneralComputeConfig"` (after `"EmbeddingDimensionError"`)
   - `"GeneralComputeProvider"` (after `"GeneralComputeConfig"`)
</action>
<acceptance_criteria>
- `from model_router import GeneralComputeConfig` succeeds
- `from model_router import GeneralComputeProvider` succeeds
- `"GeneralComputeConfig" in model_router.__all__` is True
- `"GeneralComputeProvider" in model_router.__all__` is True
</acceptance_criteria>
</task>

<task id="09-01b-03" title="Create test_general_compute_provider.py">
<read_first>
- shared/model_router/tests/test_openrouter_provider.py (full file — 436 lines: imports, FakeAsyncClient, make_config, make_router, make_http_status_error, test cases)
- shared/model_router/tests/conftest.py (AURA_TEST_MODE fixture)
- shared/model_router/src/model_router/providers/general_compute.py (from task 09-01a-03)
</read_first>
<action>
Create `shared/model_router/tests/test_general_compute_provider.py` following the `test_openrouter_provider.py` pattern. Required tests:

1. **`test_generate_returns_correct_shape`**: Create provider in test mode, call `generate()`, assert result is `GenerateResponse` with `provider=ProviderType.GENERAL_COMPUTE`
2. **`test_generate_uses_request_model`**: Verify `model_used` matches request model
3. **`test_stream_yields_chunks`**: Call `stream()`, collect chunks, assert at least one `StreamChunk` yielded
4. **`test_list_models_returns_curated_models`**: Call `list_models()`, assert 3 models returned: `minimax-m2.7`, `deepseek-v3.2`, `deepseek-v3.1`
5. **`test_list_models_thinking_support`**: Assert `deepseek-v3.2` and `deepseek-v3.1` have `thinking_supported=True`, `minimax-m2.7` has `thinking_supported=False`
6. **`test_health_check_passes`**: Assert `health_check()` returns `True` in test mode
7. **`test_router_auto_registers_gc_in_test_mode`**: Create `ModelRouter(RouterConfig(test_mode=True))`, assert `ProviderType.GENERAL_COMPUTE` is in registered providers
8. **`test_public_exports_include_gc_symbols`**: Assert `GeneralComputeProvider` and `GeneralComputeConfig` are importable from `model_router`
9. **`test_config_from_env`**: Monkeypatch `GENERALCOMPUTE_API_KEY`, assert `GeneralComputeConfig.from_env().api_key` matches
10. **Error mapping tests**: `test_auth_error_mapping` (401→AuthenticationError), `test_rate_limit_error_mapping` (429→RateLimitError)

Helpers: `make_config()` returns `GeneralComputeConfig(api_key="test-key")`, `make_router()` returns `ModelRouter(RouterConfig(test_mode=True))`

File header: Standard Python docstring header.
</action>
<acceptance_criteria>
- `python -m pytest shared/model_router/tests/test_general_compute_provider.py -v` passes all tests
- At least 10 test functions exist in the file
- No test relies on network access (all use test mode or mocks)
</acceptance_criteria>
</task>

<task id="09-01b-04" title="Update test_import_contexts.py for GC exports">
<read_first>
- shared/model_router/tests/test_import_contexts.py (full file — 78 lines: test_import_all_public_api lines 67-77)
</read_first>
<action>
Edit `test_import_contexts.py`, update the `test_import_all_public_api` function (line 67) to include `GeneralComputeConfig` and `GeneralComputeProvider` in the import command string.

Current import string (lines 69-75):
```
'from model_router import '
'AuthenticationError, BaseEmbeddingProvider, BaseProvider, '
'ContentPolicyError, EmbeddingDimensionError, GenerateRequest, '
'GenerateResponse, ModelInfo, ModelRouter, ModelRouterError, '
'ModelUnavailableError, ProviderTimeoutError, ProviderType, '
'RateLimitError, StreamChunk, UsageInfo, VertexCompatModel, '
"get_default_router, reset_default_router; print('ALL OK')"
```

Updated: Add `GeneralComputeConfig, GeneralComputeProvider, ` after `EmbeddingDimensionError, ` in the import command string. Keep alphabetical order.
</action>
<acceptance_criteria>
- `python -m pytest shared/model_router/tests/test_import_contexts.py::test_import_all_public_api -v` passes
- The import string includes `GeneralComputeConfig` and `GeneralComputeProvider`
</acceptance_criteria>
</task>

## Verification

```bash
# Per-task verification
python -m pytest shared/model_router/tests/test_general_compute_provider.py -v

# Full suite
python -m pytest shared/model_router/tests/ -v

# Import verification
python -c "from model_router import GeneralComputeProvider, GeneralComputeConfig; print('OK')"
```
