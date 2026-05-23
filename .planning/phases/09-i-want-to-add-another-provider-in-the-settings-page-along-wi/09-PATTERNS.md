# Phase 09: Add General Compute Provider - Pattern Map

**Mapped:** 2026-05-23
**Files analyzed:** 16 (2 new, 14 edits)
**Analogs found:** 16 / 16

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `shared/model_router/src/model_router/providers/general_compute.py` | provider | request-response, streaming | `shared/model_router/src/model_router/providers/openrouter.py` | exact (role+flow) |
| `shared/model_router/src/model_router/types.py` | model (enum) | config | (current file itself) | exact (edit in place) |
| `shared/model_router/src/model_router/config.py` | model (config) | config | `shared/model_router/src/model_router/config.py` (OpenRouterConfig) | exact (edit in place) |
| `shared/model_router/src/model_router/router.py` | service (router) | CRUD, request-response | `shared/model_router/src/model_router/router.py` (OpenRouter registration) | exact (edit in place) |
| `shared/model_router/src/model_router/cost_calculator.py` | service (calculator) | CRUD | `shared/model_router/src/model_router/cost_calculator.py` (Vertex AI pricing) | exact (edit in place) |
| `shared/model_router/src/model_router/__init__.py` | config (exports) | config | `shared/model_router/src/model_router/__init__.py` (current file) | exact (edit in place) |
| `shared/model_router/tests/test_general_compute_provider.py` | test | test | `shared/model_router/tests/test_openrouter_provider.py` | exact (role+flow) |
| `shared/model_router/tests/test_import_contexts.py` | test | test | (current file itself) | exact (edit in place) |
| `AURA-CHAT/server/routers/settings.py` | controller (router) | CRUD, request-response | (current file itself — OpenRouter validation) | exact (edit in place) |
| `AURA-CHAT/client/src/types/settings.ts` | model (type) | config | (current file itself — ProviderType union) | exact (edit in place) |
| `AURA-CHAT/client/src/features/settings/components/ProviderSettingsSection.tsx` | component | config | (current file itself — PROVIDERS array) | exact (edit in place) |
| `AURA-CHAT/client/src/features/settings/components/ApiKeyManager.tsx` | component | config | (current file itself — PROVIDERS array) | exact (edit in place) |
| `AURA-NOTES-MANAGER/api/routers/settings.py` | controller (router) | CRUD, request-response | (current file itself — OpenRouter validation) | exact (edit in place) |
| `AURA-NOTES-MANAGER/frontend/src/types/settings.ts` | model (type) | config | (current file itself — ProviderType union) | exact (edit in place) |
| `AURA-NOTES-MANAGER/frontend/src/features/settings/components/ProviderSettingsSection.tsx` | component | config | (current file itself — PROVIDERS array) | exact (edit in place) |
| `AURA-NOTES-MANAGER/frontend/src/features/settings/components/ApiKeyManager.tsx` | component | config | (current file itself — PROVIDERS array) | exact (edit in place) |

## Pattern Assignments

### `shared/model_router/src/model_router/providers/general_compute.py` (provider, request-response/streaming)

**Analog:** `shared/model_router/src/model_router/providers/openrouter.py` (698 lines)

**Imports pattern** (lines 13-43):
```python
from __future__ import annotations

import hashlib
import os
from typing import Any, AsyncGenerator

import httpx

from model_router.config import OpenRouterConfig  # → GeneralComputeConfig
from model_router.errors import (
    AuthenticationError,
    ContentPolicyError,
    ModelRouterError,
    ModelUnavailableError,
    ProviderTimeoutError,
    RateLimitError,
)
from model_router.providers.base import (
    AURA_EMBEDDING_DIMENSIONS,
    BaseProvider,
)
from model_router.types import (
    GenerateRequest,
    GenerateResponse,
    ModelInfo,
    ProviderType,
    StreamChunk,
    UsageInfo,
)
```

**Test-mode model list pattern** (lines 47-90):
```python
_GC_TEST_MODELS = [
    ModelInfo(
        name="minimax-m2.7",
        provider=ProviderType.GENERAL_COMPUTE,
        display_name="MiniMax M2.7",
        thinking_supported=False,
    ),
    ModelInfo(
        name="deepseek-v3.2",
        provider=ProviderType.GENERAL_COMPUTE,
        display_name="DeepSeek V3.2",
        thinking_supported=True,
    ),
    ModelInfo(
        name="deepseek-v3.1",
        provider=ProviderType.GENERAL_COMPUTE,
        display_name="DeepSeek V3.1",
        thinking_supported=True,
    ),
]
```

**`_is_test_mode()` helper** (lines 148-150):
```python
def _is_test_mode() -> bool:
    return os.getenv("AURA_TEST_MODE", "").strip().lower() == "true"
```

**`_supports_thinking()` helper pattern** (lines 118-145 from openrouter.py, simplified for GC):
```python
def _supports_thinking(model_name: str) -> bool:
    normalized = model_name.lower()
    if "deepseek" in normalized:
        return True
    return False
```

**`_build_messages()` - reusable OpenAI-compatible message builder** (lines 177-219 from openrouter.py):
```python
def _build_messages(request: GenerateRequest) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    if request.system_instruction:
        messages.append({"role": "system", "content": request.system_instruction})
    if isinstance(request.contents, str):
        messages.append({"role": "user", "content": request.contents})
        return messages
    for item in request.contents:
        if isinstance(item, str):
            messages.append({"role": "user", "content": item})
            continue
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "user"))
        if role == "model":
            role = "assistant"
        parts = item.get("parts", [])
        content_parts: list[str] = []
        for part in parts:
            if isinstance(part, str):
                content_parts.append(part)
            elif isinstance(part, dict):
                text = part.get("text")
                if isinstance(text, str):
                    content_parts.append(text)
        content = "".join(content_parts)
        if content:
            messages.append({"role": role, "content": content})
    return messages
```

**`_coerce_text_value()` - reusable content normalizer** (lines 153-174 from openrouter.py):
```python
def _coerce_text_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                continue
            text = getattr(item, "text", None)
            if isinstance(text, str):
                parts.append(text)
        return "".join(parts)
    return str(value)
```

**Error mapping pattern** (lines 261-345 from openrouter.py, simplified for httpx-only):
```python
def _map_gc_error(error: BaseException, *, model: str = "") -> ModelRouterError:
    if isinstance(error, httpx.HTTPStatusError):
        status_code = error.response.status_code
        if status_code in (401, 403):
            return AuthenticationError(str(error), provider="general_compute", model=model, original=error)
        if status_code == 429:
            return RateLimitError(str(error), provider="general_compute", model=model, original=error)
    return ModelRouterError(str(error), provider="general_compute", model=model, original=error)
```

**Provider class pattern** (lines 348-601 from openrouter.py):
```python
class GeneralComputeProvider(BaseProvider):
    def __init__(self, config: GeneralComputeConfig) -> None:
        self._config = config
        self._test_mode = _is_test_mode()

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """POST /v1/chat/completions — normalized response."""
        if self._test_mode:
            return GenerateResponse(
                text="Test-mode output.",
                model_used=request.model,
                provider=ProviderType.GENERAL_COMPUTE,
                usage=UsageInfo(),
            )
        # httpx POST to /v1/chat/completions
        # Parse response for choices[0].message.content + usage
        # Return GenerateResponse with text, model_used, provider, usage, thinking_text

    async def stream(self, request: GenerateRequest) -> AsyncGenerator[StreamChunk, None]:
        """Stream with SSE from POST /v1/chat/completions with stream: true."""
        if self._test_mode:
            yield StreamChunk(type="content", text="Test-mode stream output.")
            return
        # httpx POST with stream=True
        # Parse SSE, yield StreamChunk for thinking/content types

    async def list_models(self) -> list[ModelInfo]:
        """POST /v1/models/list — returns available models."""
        if self._test_mode:
            return list(_GC_TEST_MODELS)
        # httpx POST to /v1/models/list
        # Parse response, build ModelInfo list with thinking_supported

    async def health_check(self) -> bool:
        """Return True when the API key is valid."""
        if self._test_mode:
            return True
        # httpx POST to /v1/models/list
        # Return True if 200, False on error
```

**`list_models()` with live httpx call pattern** (lines 523-563 from openrouter.py, adapted for POST):
```python
async def list_models(self) -> list[ModelInfo]:
    if self._test_mode:
        return list(_GC_TEST_MODELS)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self._config.base_url.rstrip('/')}/models/list",
                headers={"Authorization": f"Bearer {self._config.api_key}"},
            )
            response.raise_for_status()
    except Exception as error:
        raise _map_gc_error(error) from error
    data = response.json()
    models: list[ModelInfo] = []
    for item in data if isinstance(data, list) else data.get("data", []):
        name = item.get("id", "")
        if not isinstance(name, str):
            continue
        models.append(ModelInfo(
            name=name,
            provider=ProviderType.GENERAL_COMPUTE,
            display_name=item.get("name") if isinstance(item.get("name"), str) else None,
            thinking_supported=_supports_thinking(name),
        ))
    return models
```

**`health_check()` pattern** (lines 565-574 from openrouter.py):
```python
async def health_check(self) -> bool:
    if self._test_mode:
        return True
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self._config.base_url.rstrip('/')}/models/list",
                headers={"Authorization": f"Bearer {self._config.api_key}"},
            )
            response.raise_for_status()
        return True
    except Exception:
        return False
```

**`__all__` exports** (lines 694-698 from openrouter.py):
```python
__all__ = [
    "GeneralComputeProvider",
    "_map_gc_error",
]
```

---

### `shared/model_router/src/model_router/types.py` (model/enum, config) — EDIT

**Analog:** `shared/model_router/src/model_router/types.py` (current file, lines 20-26)

**Add to ProviderType enum** (line 25):
```python
class ProviderType(str, Enum):
    VERTEX_AI = "vertex_ai"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    GENERAL_COMPUTE = "general_compute"  # ★ NEW
```

---

### `shared/model_router/src/model_router/config.py` (model/config, config) — EDIT

**Analog:** `shared/model_router/src/model_router/config.py` (current file — OpenRouterConfig pattern, lines 57-76)

**New GeneralComputeConfig** (insert after OpenRouterConfig, ~line 77):
```python
class GeneralComputeConfig(BaseModel):
    """Configuration for the General Compute provider."""

    api_key: str = ""
    base_url: str = "https://api.generalcompute.com/v1"

    @classmethod
    def from_env(cls) -> "GeneralComputeConfig":
        return cls(
            api_key=os.getenv("GENERALCOMPUTE_API_KEY", ""),
            base_url=os.getenv(
                "GENERALCOMPUTE_BASE_URL",
                "https://api.generalcompute.com/v1",
            ),
        )
```

**Add to RouterConfig** (lines 79-95, insert general_compute field and from_env entry):
```python
class RouterConfig(BaseModel):
    default_provider: ProviderType = ProviderType.VERTEX_AI
    vertex_ai: VertexAIConfig = Field(default_factory=VertexAIConfig)
    openrouter: OpenRouterConfig = Field(default_factory=OpenRouterConfig)
    general_compute: GeneralComputeConfig = Field(default_factory=GeneralComputeConfig)  # ★ NEW

    @classmethod
    def from_env(cls) -> "RouterConfig":
        return cls(
            default_provider=ProviderType.VERTEX_AI,
            vertex_ai=VertexAIConfig.from_env(),
            openrouter=OpenRouterConfig.from_env(),
            general_compute=GeneralComputeConfig.from_env(),  # ★ NEW
            test_mode=_env_flag("AURA_TEST_MODE"),
        )
```

---

### `shared/model_router/src/model_router/router.py` (service/router, CRUD+request-response) — EDIT

**Analog:** `shared/model_router/src/model_router/router.py` (current file — OpenRouter registration pattern)

**Import in header** (line 18):
```python
from model_router.config import GeneralComputeConfig, OpenRouterConfig, RouterConfig
```

**Auto-registration in `__init__()`** (insert after OpenRouter block ~line 95):
```python
        if self._should_auto_register_generalcompute():
            from model_router.providers.general_compute import GeneralComputeProvider

            gc_provider = GeneralComputeProvider(self._config.general_compute)
            self.register_provider(ProviderType.GENERAL_COMPUTE, gc_provider)
```

**`_should_auto_register_generalcompute()`** (insert after openrouter check ~line 103):
```python
    def _should_auto_register_generalcompute(self) -> bool:
        return self._config.test_mode or bool(self._config.general_compute.api_key)
```

**Lazy registration** (insert after OpenRouter lazy ~line 147):
```python
    async def _maybe_lazy_register_generalcompute(self) -> None:
        if ProviderType.GENERAL_COMPUTE in self._providers:
            return
        if self._key_manager is None:
            return
        try:
            api_key = await self._key_manager.get_key("general_compute")
            if api_key:
                from model_router.providers.general_compute import GeneralComputeProvider

                gc_config = GeneralComputeConfig(api_key=api_key)
                provider = GeneralComputeProvider(gc_config)
                self.register_provider(ProviderType.GENERAL_COMPUTE, provider)
                logger.info("Lazy registered General Compute provider from KeyManager")
        except Exception:
            logger.warning("Failed to lazy register General Compute provider", exc_info=True)
```

**Update `_resolve_provider()` for lazy registration** (lines 217-234, add GC branch):
```python
        # Attempt lazy registration if needed
        if provider is None and resolved_type is ProviderType.GENERAL_COMPUTE:
            await self._maybe_lazy_register_generalcompute()
            provider = self._providers.get(resolved_type)
```

**Update `list_models()` for lazy GC registration** (lines 281-317, add GC branch):
```python
            if (
                resolved_type not in self._providers
                and resolved_type is ProviderType.GENERAL_COMPUTE
            ):
                await self._maybe_lazy_register_generalcompute()
```

---

### `shared/model_router/src/model_router/cost_calculator.py` (service/calculator, CRUD) — EDIT

**Analog:** `shared/model_router/src/model_router/cost_calculator.py` (current file — Vertex AI pricing pattern)

**Add GC pricing dictionary** (after `_VERTEX_PRICING` ~line 43):
```python
    _GC_PRICING: dict[str, dict[str, float]] = {
        "minimax-m2.7": {"input": 0.40, "output": 2.34},
        "deepseek-v3.2": {"input": 3.00, "output": 4.50},
        "deepseek-v3.1": {"input": 3.00, "output": 4.50},
    }
```

**Add GC branch in `estimate()`** (lines 66-72):
```python
        if provider == ProviderType.GENERAL_COMPUTE:
            return self._estimate_general_compute(usage, model)
```

**Add `_estimate_general_compute()`** (insert after `_estimate_openrouter()` ~line 120):
```python
    def _estimate_general_compute(self, usage: UsageInfo, model: str) -> float:
        pricing = self._GC_PRICING.get(model)
        if pricing is None:
            return 0.0
        input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
        total_output = usage.output_tokens + usage.thinking_tokens
        output_cost = (total_output / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 6)
```

---

### `shared/model_router/src/model_router/__init__.py` (config/exports, config) — EDIT

**Analog:** `shared/model_router/src/model_router/__init__.py` (current file)

**Add imports** (insert after line 14):
```python
from model_router.config import GeneralComputeConfig  # ★ NEW (after OpenRouterConfig)
from model_router.providers.general_compute import GeneralComputeProvider  # ★ NEW (after OpenRouterProvider)
```

**Add to `__all__`** (insert ~lines 47-79):
```python
    "GeneralComputeConfig",  # ★ NEW
    "GeneralComputeProvider",  # ★ NEW
```

---

### `AURA-CHAT/server/routers/settings.py` (controller/router, CRUD+request-response) — EDIT

**Analog:** Current file itself (lines 158-162, 165-191, 194-202 — OpenRouter validation pattern)

**Update imports** (lines 40-51):
```python
from model_router.config import GeneralComputeConfig, OpenRouterConfig  # ★ ADD GeneralComputeConfig
```

**Add GC validation constant** (~line 69):
```python
GENERAL_COMPUTE_VALIDATION_METHOD = "health_check"
```

**Add `_validate_generalcompute_key()`** (insert after `_validate_openrouter_key` ~line 162):
```python
async def _validate_generalcompute_key(api_key: str) -> bool:
    config = GeneralComputeConfig(api_key=api_key)
    provider = GeneralComputeProvider(config)
    return await provider.health_check()
```

**Add GC import at top of settings.py** (alongside other provider imports):
```python
from model_router.providers.general_compute import GeneralComputeProvider  # ★ NEW
```

**Add GC branch in `_validate_provider_key()`** (lines 176-186):
```python
    elif provider == ProviderType.GENERAL_COMPUTE.value:
        validator = _validate_generalcompute_key
```

**Add GC branch in `_get_validation_method()`** (lines 194-202):
```python
    if provider == ProviderType.GENERAL_COMPUTE.value:
        return GENERAL_COMPUTE_VALIDATION_METHOD
```

---

### `AURA-CHAT/client/src/types/settings.ts` (model/type, config) — EDIT

**Analog:** Current file itself (line 31)

**Old:**
```typescript
export type ProviderType = 'vertex_ai' | 'openrouter' | 'ollama';
```
**New:**
```typescript
export type ProviderType = 'vertex_ai' | 'openrouter' | 'general_compute' | 'ollama';
```

---

### `AURA-CHAT/client/src/features/settings/components/ProviderSettingsSection.tsx` (component, config) — EDIT

**Analog:** Current file itself (lines 35-44)

**Update icon import** (line 35):
```typescript
import { Cpu, Globe, Cloud, Server, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
```

**Add to PROVIDERS array** (lines 40-44):
```typescript
const PROVIDERS = [
    { id: 'vertex_ai', label: 'Vertex AI', icon: Cpu, needsKey: true },
    { id: 'openrouter', label: 'OpenRouter', icon: Globe, needsKey: true },
    { id: 'general_compute', label: 'General Compute', icon: Cloud, needsKey: true },  // ★ NEW
    { id: 'ollama', label: 'Ollama', icon: Server, needsKey: false },
];
```

**Update grid columns** (line 50):
```typescript
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
```

---

### `AURA-CHAT/client/src/features/settings/components/ApiKeyManager.tsx` (component, config) — EDIT

**Analog:** Current file itself (lines 49-52)

**Add to PROVIDERS array** (lines 49-52):
```typescript
const PROVIDERS = [
    { id: 'vertex_ai', label: 'Vertex AI' },
    { id: 'openrouter', label: 'OpenRouter' },
    { id: 'general_compute', label: 'General Compute' },  // ★ NEW
];
```

**Update grid columns** (line 56):
```typescript
<div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
```

---

### `AURA-NOTES-MANAGER/api/routers/settings.py` (controller/router, CRUD+request-response) — EDIT

**Analog:** Current file itself (lines 149-153, 156-182, 185-193 — OpenRouter validation pattern)

**Identical changes as AURA-CHAT counterpart:**

**Update imports** (lines 40-49):
```python
from model_router.config import GeneralComputeConfig, OpenRouterConfig  # ★ ADD
from model_router.providers.general_compute import GeneralComputeProvider  # ★ NEW
```

**Add constant** (~line 69):
```python
GENERAL_COMPUTE_VALIDATION_METHOD = "health_check"
```

**Add validation function** (after `_validate_openrouter_key` ~line 153):
```python
async def _validate_generalcompute_key(api_key: str) -> bool:
    config = GeneralComputeConfig(api_key=api_key)
    provider = GeneralComputeProvider(config)
    return await provider.health_check()
```

**Add GC branch in `_validate_provider_key()`** (lines 167-177):
```python
    elif provider == ProviderType.GENERAL_COMPUTE.value:
        validator = _validate_generalcompute_key
```

**Add GC branch in `_get_validation_method()`** (lines 185-193):
```python
    if provider == ProviderType.GENERAL_COMPUTE.value:
        return GENERAL_COMPUTE_VALIDATION_METHOD
```

---

### `AURA-NOTES-MANAGER/frontend/src/types/settings.ts` (model/type, config) — EDIT

**Analog:** Current file itself (line 31)

**Old:**
```typescript
export type ProviderType = 'vertex_ai' | 'openrouter' | 'ollama';
```
**New:**
```typescript
export type ProviderType = 'vertex_ai' | 'openrouter' | 'general_compute' | 'ollama';
```

---

### `AURA-NOTES-MANAGER/frontend/src/features/settings/components/ProviderSettingsSection.tsx` (component, config) — EDIT

**Analog:** Current file itself (lines 35-44)

**Update icon import** (line 35):
```typescript
import { Cpu, Globe, Cloud, Server, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
```

**Add to PROVIDERS array** (lines 40-44):
```typescript
const PROVIDERS = [
    { id: 'vertex_ai', label: 'Vertex AI', icon: Cpu, needsKey: true },
    { id: 'openrouter', label: 'OpenRouter', icon: Globe, needsKey: true },
    { id: 'general_compute', label: 'General Compute', icon: Cloud, needsKey: true },  // ★ NEW
    { id: 'ollama', label: 'Ollama', icon: Server, needsKey: false },
];
```

**Update grid columns** (~line 50):
```typescript
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
```

---

### `AURA-NOTES-MANAGER/frontend/src/features/settings/components/ApiKeyManager.tsx` (component, config) — EDIT

**Analog:** Current file itself (lines 49-52)

**Add to PROVIDERS array** (lines 49-52):
```typescript
const PROVIDERS = [
    { id: 'vertex_ai', label: 'Vertex AI' },
    { id: 'openrouter', label: 'OpenRouter' },
    { id: 'general_compute', label: 'General Compute' },  // ★ NEW
];
```

**Update grid columns** (~line 56):
```typescript
<div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
```

---

### `shared/model_router/tests/test_general_compute_provider.py` (test, test) — NEW FILE

**Analog:** `shared/model_router/tests/test_openrouter_provider.py` (435 lines)

**Test structure to copy:**
- Lines 21-41: Imports pattern (ModelRouter, configs, errors, types)
- Lines 43-51: Safe import pattern (`try/except ImportError`)
- Lines 56-67: `FakeAsyncClient` stub class
- Lines 73-76: `make_config()` helper
- Lines 78-86: `make_router()` helper
- Lines 116-127: `make_http_status_error()` helper
- Lines 130-145: `test_generate_returns_correct_shape()` — test-mode generate
- Lines 148-158: `test_generate_uses_request_model()` — model_used verification
- Lines 161-173: `test_stream_yields_chunks()` — test-mode stream
- Lines 176-189: `test_list_models_returns_curated_models()` — test-mode list_models
- Lines 254-258: `test_health_check_passes()` — test-mode health_check
- Lines 273-283: `test_router_auto_registers_*_in_test_mode()` — registration test
- Lines 285-291: `test_public_exports_include_*_symbols()` — export test
- Lines 362-396: Parametrized auth failure tests (using `FakeAsyncClient`)
- Lines 398-435: Parametrized rate limit tests

**Key differences for GC tests:**
- `list_models` endpoint is `POST /v1/models/list` (not `GET /models`)
- Model names are `minimax-m2.7`, `deepseek-v3.2`, `deepseek-v3.1`
- No embedding support (no `OpenRouterEmbeddingProvider`)
- No `get_credit_balance` tests (GC doesn't have this endpoint)
- Error mapping is simpler (httpx-only, no openai SDK dependency)

---

### `shared/model_router/tests/test_import_contexts.py` (test, test) — EDIT

**Analog:** Current file itself

**Add import test entries:**
```python
# Verify GeneralCompute symbols are importable
from model_router import GeneralComputeConfig as ExportedGcConfig
from model_router import GeneralComputeProvider as ExportedGcProvider

assert ExportedGcConfig is not None
assert ExportedGcProvider is not None
```

---

## Shared Patterns

### Provider Implementation Pattern (OpenRouter → General Compute)
**Source:** `shared/model_router/src/model_router/providers/openrouter.py`
**Apply to:** `shared/model_router/src/model_router/providers/general_compute.py`

The General Compute provider follows the EXACT same class structure as OpenRouter:
1. `BaseProvider` subclass with `generate()`, `stream()`, `list_models()`, `health_check()`
2. Test-mode bypass (return canned data when `_is_test_mode()` is True)
3. httpx-based HTTP calls (instead of OpenAI SDK that OpenRouter uses for chat)
4. Error mapping via a `_map_gc_error()` function (httpx-focused, no openai SDK)

**Key deviations from OpenRouter:**
- `list_models()` uses `POST /v1/models/list` (not `GET /models`)
- No embedding provider implementation (GC doesn't document embeddings)
- No `get_credit_balance()` method (GC doesn't have credits)
- No special auth headers beyond `Authorization: Bearer`
- Simpler `_supports_thinking()` (just check for "deepseek" in model name)

### Error Mapping Pattern
**Source:** `shared/model_router/src/model_router/providers/openrouter.py` lines 261-345
**Apply to:** `general_compute.py`

Map httpx errors to `ModelRouterError` hierarchy:
- `401`/`403` → `AuthenticationError`
- `429` → `RateLimitError`
- All others → `ModelRouterError`

GC's error mapper is simpler than OpenRouter's — no openai SDK dependency to handle.

### Provider Registration Pattern
**Source:** `shared/model_router/src/model_router/router.py` lines 97-147 (OpenRouter)
**Apply to:** `router.py` — add general_compute registration

Dual registration:
1. **Auto-registration** in `__init__()`: Check `_should_auto_register_generalcompute()` (test_mode OR has api_key in config)
2. **Lazy registration** in `_maybe_lazy_register_generalcompute()`: Called during provider resolution when GC is requested but not registered — fetches key from `KeyManager`

### Settings Validation Pattern
**Source:** `AURA-CHAT/server/routers/settings.py` lines 158-202
**Source:** `AURA-NOTES-MANAGER/api/routers/settings.py` lines 149-193
**Apply to:** Both settings routers

Three changes per settings router:
1. Add `_validate_generalcompute_key(api_key)` function — creates temp provider, calls health_check
2. Add GC branch in `_validate_provider_key()` — wires to validation function
3. Add GC branch in `_get_validation_method()` — returns "health_check" string

### Frontend Provider Card Pattern
**Source:** Both apps' `ProviderSettingsSection.tsx` and `ApiKeyManager.tsx`
**Apply to:** All four frontend files

Three changes per app:
1. `types/settings.ts`: Add `'general_compute'` to `ProviderType` union
2. `ProviderSettingsSection.tsx`: Add GC entry to `PROVIDERS` array with `Cloud` icon
3. `ApiKeyManager.tsx`: Add GC entry to `PROVIDERS` array

### Test Mode Pattern
**Source:** `shared/model_router/src/model_router/providers/openrouter.py` lines 148-150
**Apply to:** `general_compute.py`

```python
def _is_test_mode() -> bool:
    return os.getenv("AURA_TEST_MODE", "").strip().lower() == "true"
```

When `_is_test_mode()` is True:
- `generate()` returns a canned `GenerateResponse`
- `stream()` yields a single `StreamChunk`
- `list_models()` returns `_GC_TEST_MODELS`
- `health_check()` returns `True`

### File Header Pattern
**Source:** `AURA-CHAT/server/routers/settings.py` lines 1-27
**Apply to:** All new and edited files

All Python files get a `"""..."""` header with FILE, LOCATION, PURPOSE, ROLE, KEY COMPONENTS, DEPENDENCIES, USAGE sections.
All TypeScript/React files get a `/** ... */` header with same structure.

---

## No Analog Found

All files have exact analogs in the codebase — no new pattern invention needed. Every pattern has a direct existing implementation to copy from.

| File | Role | Data Flow | Reason for No Match |
|------|------|-----------|---------------------|
| (none) | — | — | All 16 files have exact analogs |

---

## Metadata

**Analog search scope:** `shared/model_router/src/model_router/`, `AURA-CHAT/server/routers/`, `AURA-CHAT/client/src/`, `AURA-NOTES-MANAGER/api/routers/`, `AURA-NOTES-MANAGER/frontend/src/`, `shared/model_router/tests/`
**Files scanned:** 16+
**Pattern extraction date:** 2026-05-23
