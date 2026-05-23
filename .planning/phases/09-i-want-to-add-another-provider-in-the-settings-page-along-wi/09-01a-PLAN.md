---
wave: 1
depends_on: []
files_modified:
  - shared/model_router/src/model_router/types.py
  - shared/model_router/src/model_router/config.py
  - shared/model_router/src/model_router/providers/general_compute.py
  - shared/model_router/src/model_router/router.py
autonomous: true
requirements:
  - P9-01
  - P9-02
  - P9-03
  - P9-04
---

# Plan 09-01a: General Compute Provider — Core Implementation

Implements the core General Compute provider in the shared `model_router` package: enum, config, provider implementation, and router registration.

## must_haves

- `ProviderType.GENERAL_COMPUTE = "general_compute"` enum member exists in `types.py`
- `GeneralComputeConfig` class exists in `config.py` with `api_key`, `base_url`, `from_env()` reading `GENERALCOMPUTE_API_KEY` and `GENERALCOMPUTE_BASE_URL`
- `RouterConfig` has `general_compute: GeneralComputeConfig` field and `from_env()` populates it
- `GeneralComputeProvider` class in `providers/general_compute.py` implements `generate()`, `stream()`, `list_models()`, `health_check()` with test-mode support
- `ModelRouter.__init__()` calls `_should_auto_register_generalcompute()` and registers provider; lazy registration via `_maybe_lazy_register_generalcompute()` wired into `_resolve_provider()` and `list_models()`

## Tasks

<task id="09-01a-01" title="Add GENERAL_COMPUTE to ProviderType enum">
<read_first>
- shared/model_router/src/model_router/types.py (lines 20-25 — current ProviderType enum)
</read_first>
<action>
In `types.py`, add `GENERAL_COMPUTE = "general_compute"` as a new member of the `ProviderType` enum, after the `OLLAMA = "ollama"` line (line 25). The result should be:

```
class ProviderType(str, Enum):
    VERTEX_AI = "vertex_ai"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    GENERAL_COMPUTE = "general_compute"
```
</action>
<acceptance_criteria>
- `from model_router.types import ProviderType; assert ProviderType.GENERAL_COMPUTE.value == "general_compute"` succeeds
- `ProviderType("general_compute") is ProviderType.GENERAL_COMPUTE` is True
- Existing enum members (`VERTEX_AI`, `OPENROUTER`, `OLLAMA`) still resolve
</acceptance_criteria>
</task>

<task id="09-01a-02" title="Add GeneralComputeConfig and wire into RouterConfig">
<read_first>
- shared/model_router/src/model_router/config.py (full file — 96 lines: VertexAIConfig, OpenRouterConfig, RouterConfig classes)
</read_first>
<action>
1. Add `GeneralComputeConfig` class after `OpenRouterConfig` (after line 76) with fields:
   - `api_key: str = ""`
   - `base_url: str = "https://api.generalcompute.com/v1"`
   - `from_env()` classmethod reading `GENERALCOMPUTE_API_KEY` (default `""`) and `GENERALCOMPUTE_BASE_URL` (default `"https://api.generalcompute.com/v1"`)

2. In `RouterConfig` (line 79), add field: `general_compute: GeneralComputeConfig = Field(default_factory=GeneralComputeConfig)` after the `openrouter` field (line 84).

3. In `RouterConfig.from_env()` (line 88), add `general_compute=GeneralComputeConfig.from_env(),` after `openrouter=OpenRouterConfig.from_env(),` (line 93).
</action>
<acceptance_criteria>
- `from model_router.config import GeneralComputeConfig` succeeds
- `GeneralComputeConfig().base_url == "https://api.generalcompute.com/v1"`
- `GeneralComputeConfig().api_key == ""`
- With `GENERALCOMPUTE_API_KEY=test123` env var, `GeneralComputeConfig.from_env().api_key == "test123"`
- `RouterConfig.from_env().general_compute` is a `GeneralComputeConfig` instance
- `RouterConfig()` creates without error (default factory for general_compute)
</acceptance_criteria>
</task>

<task id="09-01a-03" title="Implement GeneralComputeProvider">
<read_first>
- shared/model_router/src/model_router/providers/openrouter.py (full file — 698 lines: OpenRouterProvider class structure, _build_messages, _coerce_text_value, _map_openrouter_error, _is_test_mode, _supports_thinking, _TEST_MODELS)
- shared/model_router/src/model_router/providers/base.py (BaseProvider abstract methods: generate, stream, list_models, health_check)
- shared/model_router/src/model_router/types.py (GenerateRequest, GenerateResponse, ModelInfo, StreamChunk, UsageInfo, ProviderType)
- shared/model_router/src/model_router/errors.py (AuthenticationError, RateLimitError, ModelRouterError)
- shared/model_router/src/model_router/config.py (GeneralComputeConfig — from task 09-01a-02)
</read_first>
<action>
Create `shared/model_router/src/model_router/providers/general_compute.py` following the OpenRouter provider pattern. Key elements:

1. **Module-level helpers**: `_is_test_mode()`, `_supports_thinking()` (return True if `"deepseek"` in model name), `_build_messages()` (duplicate from openrouter.py), `_coerce_text_value()` (duplicate from openrouter.py), `_map_gc_error()` (map httpx errors: 401/403→AuthenticationError, 429→RateLimitError, else→ModelRouterError; provider string = `"general_compute"`)

2. **Test models list**: `_GC_TEST_MODELS` with 3 `ModelInfo` entries:
   - `minimax-m2.7` (thinking_supported=False)
   - `deepseek-v3.2` (thinking_supported=True)
   - `deepseek-v3.1` (thinking_supported=True)
   All with `provider=ProviderType.GENERAL_COMPUTE`

3. **`GeneralComputeProvider(BaseProvider)`** class with:
   - `__init__(config: GeneralComputeConfig)` storing `self._config` and `self._test_mode = _is_test_mode()`
   - `generate(request)` — test mode returns canned GenerateResponse; live mode POSTs to `{base_url}/chat/completions` with `Authorization: Bearer {api_key}`, parses `choices[0].message.content` and `usage`, handles reasoning_content for deepseek models
   - `stream(request)` — test mode yields single StreamChunk; live mode POSTs with `stream: true`, parses SSE chunks, yields StreamChunk(type="thinking"|"content")
   - `list_models()` — test mode returns `_GC_TEST_MODELS`; live mode POSTs to `{base_url}/models/list` (NOTE: POST not GET), parses response for model id/name, sets thinking_supported via `_supports_thinking()`
   - `health_check()` — test mode returns True; live mode POSTs to `/models/list`, returns True on 200, False on error

4. **`__all__`**: `["GeneralComputeProvider", "_map_gc_error"]`

5. **File header**: Standard Python docstring header with FILE, LOCATION, PURPOSE, ROLE, KEY COMPONENTS, DEPENDENCIES, USAGE sections.

Key differences from OpenRouter:
- No `OpenRouterEmbeddingProvider` equivalent (GC doesn't support embeddings)
- No `get_credit_balance()` method
- `list_models()` uses `POST` not `GET`
- No `X-Title`/`HTTP-Referer` headers — only `Authorization: Bearer`
- Simpler `_supports_thinking()` — just check for "deepseek"
</action>
<acceptance_criteria>
- `from model_router.providers.general_compute import GeneralComputeProvider` succeeds
- With `AURA_TEST_MODE=true`:
  - `provider.generate(request)` returns a `GenerateResponse` with `provider=ProviderType.GENERAL_COMPUTE`
  - `provider.stream(request)` yields at least one `StreamChunk`
  - `provider.list_models()` returns 3 `ModelInfo` objects with names `minimax-m2.7`, `deepseek-v3.2`, `deepseek-v3.1`
  - `provider.health_check()` returns `True`
- `_map_gc_error` maps `httpx.HTTPStatusError` with status 401 to `AuthenticationError`
- `_map_gc_error` maps `httpx.HTTPStatusError` with status 429 to `RateLimitError`
</acceptance_criteria>
</task>

<task id="09-01a-04" title="Register General Compute in ModelRouter">
<read_first>
- shared/model_router/src/model_router/router.py (full file — 528 lines: __init__ lines 60-98, _should_auto_register_openrouter lines 101-103, _maybe_lazy_register_openrouter lines 105-145, _resolve_provider lines 196-235, list_models lines 270-320)
- shared/model_router/src/model_router/config.py (GeneralComputeConfig — from task 09-01a-02)
</read_first>
<action>
Edit `router.py` to add General Compute registration following the OpenRouter pattern:

1. **Import**: Add `GeneralComputeConfig` to the import from `model_router.config` on line 18: `from model_router.config import GeneralComputeConfig, OpenRouterConfig, RouterConfig`

2. **Auto-registration in `__init__()`**: After the OpenRouter block (after line 95), add:
   ```
   if self._should_auto_register_generalcompute():
       from model_router.providers.general_compute import GeneralComputeProvider
       gc_provider = GeneralComputeProvider(self._config.general_compute)
       self.register_provider(ProviderType.GENERAL_COMPUTE, gc_provider)
   ```

3. **`_should_auto_register_generalcompute()`**: Add method after `_should_auto_register_openrouter()` (after line 103):
   Returns `self._config.test_mode or bool(self._config.general_compute.api_key)`

4. **`_maybe_lazy_register_generalcompute()`**: Add method after `_maybe_lazy_register_openrouter()` (after line 145):
   - Guard: return if `ProviderType.GENERAL_COMPUTE in self._providers` or `self._key_manager is None`
   - Try: `api_key = await self._key_manager.get_key("general_compute")`
   - If key exists: `from model_router.providers.general_compute import GeneralComputeProvider`, create `GeneralComputeConfig(api_key=api_key)`, register provider
   - Log info on success, warning on failure

5. **`_resolve_provider()`**: After the OpenRouter lazy registration block (after line 225), add:
   ```
   if provider is None and resolved_type is ProviderType.GENERAL_COMPUTE:
       await self._maybe_lazy_register_generalcompute()
       provider = self._providers.get(resolved_type)
   ```

6. **`list_models()`**: After the OpenRouter lazy registration block in `list_models()` (after line 294), add:
   ```
   if (
       resolved_type not in self._providers
       and resolved_type is ProviderType.GENERAL_COMPUTE
   ):
       await self._maybe_lazy_register_generalcompute()
   ```
</action>
<acceptance_criteria>
- With `AURA_TEST_MODE=true`, `ModelRouter(RouterConfig(test_mode=True))` auto-registers `ProviderType.GENERAL_COMPUTE`
- `router.get_provider(ProviderType.GENERAL_COMPUTE)` returns a `GeneralComputeProvider` instance
- `router.list_models(provider_type=ProviderType.GENERAL_COMPUTE)` returns 3 models in test mode
- `_should_auto_register_generalcompute()` returns True when `test_mode=True` or `general_compute.api_key` is non-empty
- `_should_auto_register_generalcompute()` returns False when `test_mode=False` and `api_key=""`
</acceptance_criteria>
</task>

## Verification

```bash
# Check enum and config
python -c "from model_router.types import ProviderType; from model_router.config import GeneralComputeConfig; print('OK')"

# Test provider in test mode
AURA_TEST_MODE=true python -c "
from model_router.config import RouterConfig
from model_router.router import ModelRouter
from model_router.types import ProviderType
r = ModelRouter(RouterConfig(test_mode=True))
p = r.get_provider(ProviderType.GENERAL_COMPUTE)
print(p.health_check(), len(p.list_models()))
"
```
