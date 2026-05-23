# Phase 9: Add General Compute Provider Support - Research

**Researched:** 2026-05-23
**Domain:** Multi-Provider LLM Architecture — Adding a new OpenAI-compatible API provider
**Confidence:** HIGH

## Summary

General Compute (https://docs.generalcompute.com/quickstart) is an OpenAI-compatible LLM inference API. This phase adds it as a new provider alongside Vertex AI, OpenRouter, and Ollama in the AURA project's shared `model_router` package and settings UI.

The implementation follows the **exact same pattern** as the existing OpenRouter provider — because General Compute speaks the OpenAI wire format, the provider implementation will be very similar to `openrouter.py`. Key differences:
- **Model listing endpoint**: `POST /v1/models/list` (not `GET /models` like OpenRouter)
- **Auth**: Standard Bearer token (no `X-Title` or `HTTP-Referer` headers)
- **Pricing**: Simple per-model published pricing (static table like Vertex AI)
- **Available models**: `minimax-m2.7`, `deepseek-v3.2`, `deepseek-v3.1` (with reasoning support on DeepSeek)

**Primary recommendation:** Create `providers/general_compute.py` following the OpenRouter pattern, use `httpx` for HTTP calls (avoid requiring the General Compute SDK), add `GENERAL_COMPUTE` to `ProviderType` enum, wire config/env vars, add static cost calculation, and update both frontends (AURA-CHAT and AURA-NOTES-MANAGER) to display the new provider.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| P9-01 | Add General Compute as a new `ProviderType` enum value | `types.py` — add `GENERAL_COMPUTE = "general_compute"` |
| P9-02 | Implement `GeneralComputeProvider` following OpenRouter pattern | Full OpenAI-compatible — use `httpx`, same request/response format |
| P9-03 | Add `GeneralComputeConfig` with env var support | `config.py` — `GENERALCOMPUTE_API_KEY`, `GENERALCOMPUTE_BASE_URL` |
| P9-04 | Register General Compute in `ModelRouter` auto-registration + lazy registration | `router.py` — add `_should_auto_register_generalcompute()`, `_maybe_lazy_register_generalcompute()` |
| P9-05 | Add General Compute cost estimation to `CostCalculator` | Static pricing table: minimax-m2.7 ($0.40/$2.34 per 1M), deepseek-v3.2 ($3.00/$4.50 per 1M) |
| P9-06 | Add General Compute key validation to settings routers | Both `AURA-CHAT/server/routers/settings.py` and `AURA-NOTES-MANAGER/api/routers/settings.py` |
| P9-07 | Expose General Compute in AURA-CHAT settings UI | `types/settings.ts`, `ProviderSettingsSection.tsx`, `ApiKeyManager.tsx` |
| P9-08 | Expose General Compute in AURA-NOTES-MANAGER settings UI | Same pattern — `types/settings.ts`, `ProviderSettingsSection.tsx`, `ApiKeyManager.tsx` |
| P9-09 | Tests: unit tests for provider, integration tests for registration, import contexts | Follow `test_openrouter_provider.py` pattern |
</phase_requirements>

## User Constraints (from CONTEXT.md)

*No CONTEXT.md exists for this phase — this is a new phase added to the roadmap. The user's request is the constraint.*

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Provider implementation (generate, stream, list_models) | Backend (model_router) | — | Pure business logic, no HTTP/UI concerns |
| Provider registration and routing | Backend (model_router) | — | Responsibility of `ModelRouter` in shared package |
| Provider config / env vars | Backend (model_router) | — | Config models live in shared package |
| Cost estimation | Backend (model_router) | — | `CostCalculator` in shared package |
| API key CRUD + validation | Backend (API server settings router) | — | `settings.py` routers in AURA-CHAT and AURA-NOTES-MANAGER |
| Provider card display + model listing | Frontend (settings UI) | — | `ProviderSettingsSection.tsx` and `ApiKeyManager.tsx` |
| Model selection dropdown | Frontend (settings UI) | — | `DefaultModelSection.tsx` uses generic provider grouping |
| Chat/embedding consumers | Both apps' backend | — | Already generic — uses `resolve_use_case_config()` which just reads provider string |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `httpx` | >=0.27.0 | HTTP client for GC API calls | Already used by OpenRouter provider — no new dependency needed |
| `pydantic` | >=2.0 | Config models, request/response types | Already in shared package core dependencies |
| `cryptography` | — | API key encryption at rest | Already used by `KeyManager` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `openai` | >=1.51.0 | Alternative SDK for GC API | *Not needed* — httpx suffices; only use if streaming/complex features require SDK |
| `@generalcompute/sdk` | 0.2.1 | GC official SDK | *Not needed* — the SDK just wraps OpenAI format; httpx gives more control |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct httpx calls | `@generalcompute/sdk` npm package | SDK adds dependency with minimal value — GC is 100% OpenAI-compatible, so `httpx` + same patterns as OpenRouter is simpler |
| Direct httpx calls | OpenAI Python SDK with custom base URL | Would work but adds openai dependency to the "general_compute" path unnecessarily |

**Installation (no new packages required):**
```bash
# No new packages — httpx and pydantic are already in dependencies.
# pyproject.toml already has httpx in the openrouter and all extras.
```

**Version verification:**
```bash
npm view httpx version          # Not applicable (Python package)
pip index versions httpx        # httpx is already in dependencies
npm view @generalcompute/sdk version  # 0.2.1 — exists but NOT used
```

## General Compute API Reference

| Property | Value |
|----------|-------|
| **Base URL** | `https://api.generalcompute.com/v1` |
| **Auth** | Bearer token via `Authorization: Bearer <key>` (standard) |
| **Env variable** | `GENERALCOMPUTE_API_KEY` |
| **Chat endpoint** | `POST /v1/chat/completions` — same body as OpenAI |
| **Streaming** | `stream: true` — standard OpenAI `text/event-stream` chunks |
| **Model list (auth'd)** | `POST /v1/models/list` — returns org-specific models |
| **Model list (public)** | `GET /v1/public/models` — no auth needed, returns public catalog |
| **Health check** | `GET /v1/models/list` or check any model call succeeds |
| **SDK** | `@generalcompute/sdk` (npm v0.2.1) or `generalcompute` (PyPI) |

### Available Models [VERIFIED: docs.generalcompute.com/models]
| Model ID | Context | Input Price (per 1M tokens) | Output Price (per 1M tokens) | Reasoning |
|----------|---------|----------------------------|-----------------------------|-----------|
| `minimax-m2.7` | 160k | $0.40 | $2.34 | No |
| `deepseek-v3.2` | 32k | $3.00 | $4.50 | Yes |
| `deepseek-v3.1` | 128k | $3.00 | $4.50 | Yes |

### Key Differences from OpenRouter
| Aspect | OpenRouter | General Compute | Impact |
|--------|-----------|-----------------|--------|
| Model listing | `GET /models` | `POST /v1/models/list` | Different HTTP method and path in `list_models()` |
| Auth headers | `X-Title`, `HTTP-Referer` headers needed | Only `Authorization: Bearer` | Simpler — no special headers |
| Extra headers | User-agent metadata | None | Less boilerplate in request building |
| Public model list | Not available | `GET /v1/public/models` | Can fetch models without API key for listing |
| Embedding support | Yes (via `/embeddings` endpoint) | Not documented | Skip embedding support initially |
| Pricing data | From API response | Static published prices | Use static pricing table like Vertex AI |

## Package Legitimacy Audit

**No new external packages are required for this phase.** The existing `httpx` dependency (already in `pyproject.toml` under `[project.optional-dependencies] openrouter` and `all`) covers all HTTP needs. The `@generalcompute/sdk` npm package (v0.2.1) exists but is unnecessary — the OpenAI wire protocol is simple enough that `httpx` is the right tool.

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend Settings UI                          │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ ProviderSettingsSection.tsx   ApiKeyManager.tsx               │  │
│  │   [Vertex AI] [OpenRouter] [General Compute] [Ollama]       │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                          │ GET/POST /api/v1/settings/...              │
└──────────────────────────┼──────────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────────┐
│           Backend Settings Router (AURA-CHAT + AURA-NOTES-MANAGER)    │
│  ┌───────────────────────┴─────────────────────────────────────────┐  │
│  │  _validate_generalcompute_key() creates temp provider, checks   │  │
│  │  _validate_provider_key() dispatches by provider string         │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────┼──────────────────────────────────────────┘
                           │ via ModelRouter / get_default_router()
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Shared model_router Package                       │
│                                                                      │
│  ProviderType.GENERAL_COMPUTE                                         │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ providers/general_compute.py                                    │  │
│  │  GeneralComputeProvider(BaseProvider)                           │  │
│  │   ├── generate()   → POST /v1/chat/completions                │  │
│  │   ├── stream()     → POST /v1/chat/completions (stream: true) │  │
│  │   ├── list_models() → POST /v1/models/list (or GET /v1/public/models) │  │
│  │   └── health_check() → verify API key works                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  config.py: GeneralComputeConfig(api_key, base_url)                  │
│  router.py: auto-register + lazy-register                            │
│  cost_calculator.py: static GC pricing table                         │
└─────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │  General Compute API    │
              │  api.generalcompute.com │
              └─────────────────────────┘
```

### Recommended Project Structure (Changes Only)

```
shared/model_router/
├── src/model_router/
│   ├── providers/
│   │   ├── __init__.py              # (no change)
│   │   ├── base.py                  # (no change)
│   │   ├── vertex_ai.py             # (no change)
│   │   ├── openrouter.py            # (no change)
│   │   └── general_compute.py       # ★ NEW — General Compute provider
│   ├── config.py                    # ★ EDIT — add GeneralComputeConfig
│   ├── types.py                     # ★ EDIT — add ProviderType.GENERAL_COMPUTE
│   ├── router.py                    # ★ EDIT — add auto/lazy registration
│   ├── cost_calculator.py           # ★ EDIT — add GC pricing
│   ├── __init__.py                  # ★ EDIT — export GeneralComputeProvider
│   └── compat.py                    # (no change — only for Vertex legacy)
├── tests/
│   ├── test_general_compute_provider.py  # ★ NEW — provider unit tests
│   └── test_import_contexts.py           # ★ EDIT — verify GC exports importable
│
AURA-CHAT/
├── server/routers/settings.py            # ★ EDIT — add GC key validation
├── client/src/
│   ├── types/settings.ts                 # ★ EDIT — add 'general_compute' to ProviderType union
│   ├── features/settings/components/
│   │   ├── ProviderSettingsSection.tsx   # ★ EDIT — add GC card to PROVIDERS array
│   │   └── ApiKeyManager.tsx             # ★ EDIT — add GC to PROVIDERS array
│   └── features/settings/SettingsPage.tsx # (no change — generic component usage)
│
AURA-NOTES-MANAGER/
├── api/routers/settings.py               # ★ EDIT — add GC key validation
├── frontend/src/
│   ├── types/settings.ts                 # ★ EDIT — add 'general_compute' to ProviderType union
│   └── features/settings/components/
│       ├── ProviderSettingsSection.tsx   # ★ EDIT — add GC card to PROVIDERS array
│       └── ApiKeyManager.tsx             # ★ EDIT — add GC to PROVIDERS array
```

### Pattern 1: Provider Implementation (Follow OpenRouter)
**What:** Create a new provider class that implements `BaseProvider` for General Compute's OpenAI-compatible API.
**When to use:** Adding any OpenAI-compatible API provider to the model router.

**General Compute Provider contract:**
```python
class GeneralComputeProvider(BaseProvider):
    """Generation provider backed by General Compute's OpenAI-compatible API."""

    def __init__(self, config: GeneralComputeConfig) -> None:
        self._config = config
        self._test_mode = _is_test_mode()

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """POST /v1/chat/completions — same body as OpenAI."""
        # Uses httpx requests with same _build_messages() helper as OpenRouter
        # Returns normalized GenerateResponse with usage info

    async def stream(self, request: GenerateRequest) -> AsyncGenerator[StreamChunk, None]:
        """Stream with stream=True — same OpenAI chunk format as OpenRouter."""
        # Uses httpx with streaming response
        # Yields StreamChunk(type="thinking"|"content") for reasoning models

    async def list_models(self) -> list[ModelInfo]:
        """POST /v1/models/list — different from OpenRouter's GET /models."""
        # Uses httpx POST to /v1/models/list
        # Returns ModelInfo with thinking_supported for DeepSeek models

    async def health_check(self) -> bool:
        """Verify the API key works (test mode = True)."""
        # Attempt to list models; if 401/403, return False
```

### Pattern 2: Provider Registration in Router
**What:** Follow the existing OpenRouter dual-registration pattern — auto-register at startup when config has API key, plus lazy-register from KeyManager for UI-stored keys.

```python
# In router.py ModelRouter.__init__():
if self._should_auto_register_generalcompute():
    gc_provider = GeneralComputeProvider(self._config.general_compute)
    self.register_provider(ProviderType.GENERAL_COMPUTE, gc_provider)

# Plus lazy registration:
async def _maybe_lazy_register_generalcompute(self) -> None:
    api_key = await self._key_manager.get_key("general_compute")
    if api_key:
        gc_config = GeneralComputeConfig(api_key=api_key)
        self.register_provider(ProviderType.GENERAL_COMPUTE, GeneralComputeProvider(gc_config))
```

### Anti-Patterns to Avoid
- **Using the General Compute SDK**: The `@generalcompute/sdk` npm package exists but is unnecessary. The API is 100% OpenAI-compatible — `httpx` is simpler and already a dependency. This avoids adding another optional dependency for no benefit.
- **Hardcoding model list without fallback**: The model API should return live data, with test-mode fallback to a curated list (same pattern as `_TEST_MODELS` in OpenRouter).
- **Forgetting lazy registration**: UI-stored API keys need the lazy registration path. The existing `_maybe_lazy_register_openrouter()` is the template.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP client for provider API calls | Custom HTTP client | `httpx` (already in deps) | Already battle-tested, async support, timeout control, error handling |
| Request/response models | Custom serialization | `pydantic` (already in deps) | Already used by every other provider, auto-validation |
| Error mapping | Generic exception handling | `ModelRouterError` hierarchy | Already has `AuthenticationError`, `RateLimitError`, `ModelUnavailableError`, etc. |
| API key encryption | Custom encryption | `KeyManager` + `Fernet` | Already implemented, Redis-backed, shared across providers |
| Message building | Custom message format | `_build_messages()` from OpenRouter | GC uses identical OpenAI message format — can reuse the exact same function |

**Key insight:** General Compute uses the exact same OpenAI-compatible wire protocol as OpenRouter. The `_build_messages()`, `_coerce_text_value()`, and streaming chunk parsing functions from `openrouter.py` can be shared. If possible, extract them to a shared utility module — but the simplest approach is to duplicate them (the OpenRouter provider itself was already a copy-paste-and-modify of the OpenAI pattern).

## Common Pitfalls

### Pitfall 1: Model listing endpoint is POST not GET
**What goes wrong:** OpenRouter uses `GET /models` to list models, but General Compute uses `POST /v1/models/list`. Using a GET request will fail.
**Why it happens:** Each provider has its own API conventions. OpenRouter follows the standard `GET /v1/models` from the OpenAI spec, while GC chose `POST /v1/models/list`.
**How to avoid:** Double-check the endpoint method in the provider's `list_models()` implementation. Read the API reference carefully before coding.
**Warning signs:** Test fails with `405 Method Not Allowed` or the model list is empty.

### Pitfall 2: No embedding support documented
**What goes wrong:** OpenRouter has a `/embeddings` endpoint; General Compute does not document one. If the code assumes embedding support exists, it will need to skip or stub it.
**Why it happens:** GC focuses on chat completions. Not all inference providers support embeddings.
**How to avoid:** Skip implementing `BaseEmbeddingProvider` for GC initially. Only implement `BaseProvider` (generation). Set the embedding registration to `None` or skip it.
**Warning signs:** `405` on `/v1/embeddings` endpoints.

### Pitfall 3: Reasoning/thinking support varies by model
**What goes wrong:** The `minimax-m2.7` model doesn't support thinking/reasoning, but `deepseek-v3.2` and `deepseek-v3.1` do. The thinking support detection needs to be model-aware.
**Why it happens:** GC has a mix of models with and without reasoning capabilities.
**How to avoid:** Use the same approach as OpenRouter's `_supports_thinking()` — check for "deepseek" in the model name to set `thinking_supported=True`.

### Pitfall 4: Both settings routers need updates (in two apps)
**What goes wrong:** Adding validation for GC's API key in AURA-CHAT's `settings.py` but forgetting AURA-NOTES-MANAGER's `settings.py`.
**Why it happens:** Two nearly-identical settings routers exist — one per application — both communicating with the same Redis-backed `KeyManager`.
**How to avoid:** Edit both files in the same task, applying identical changes. The two routers have the same validation pattern (see below).

## Code Examples

### General Compute Config (config.py)
```python
class GeneralComputeConfig(BaseModel):
    """Configuration for the General Compute provider."""

    api_key: str = ""
    base_url: str = "https://api.generalcompute.com/v1"

    @classmethod
    def from_env(cls) -> "GeneralComputeConfig":
        return cls(
            api_key=os.getenv("GENERALCOMPUTE_API_KEY", ""),
            base_url=os.getenv("GENERALCOMPUTE_BASE_URL", "https://api.generalcompute.com/v1"),
        )

# In RouterConfig:
class RouterConfig(BaseModel):
    default_provider: ProviderType = ProviderType.VERTEX_AI
    vertex_ai: VertexAIConfig = Field(default_factory=VertexAIConfig)
    openrouter: OpenRouterConfig = Field(default_factory=OpenRouterConfig)
    general_compute: GeneralComputeConfig = Field(default_factory=GeneralComputeConfig)  # ★ NEW
    test_mode: bool = False

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

### General Compute Provider Skeleton (general_compute.py)
```python
"""General Compute provider for the shared model router."""

from __future__ import annotations

import hashlib
import os
from typing import Any, AsyncGenerator

import httpx

from model_router.config import GeneralComputeConfig
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

# Curated test models (same pattern as OpenRouter's _TEST_MODELS)
_GC_TEST_MODELS = [
    ModelInfo(name="minimax-m2.7", provider=ProviderType.GENERAL_COMPUTE,
              display_name="MiniMax M2.7", thinking_supported=False),
    ModelInfo(name="deepseek-v3.2", provider=ProviderType.GENERAL_COMPUTE,
              display_name="DeepSeek V3.2", thinking_supported=True),
    ModelInfo(name="deepseek-v3.1", provider=ProviderType.GENERAL_COMPUTE,
              display_name="DeepSeek V3.1", thinking_supported=True),
]

# Reuse _build_messages() and _coerce_text_value() from openrouter.py
# or implement them identically (same OpenAI format)

def _supports_thinking(model_name: str) -> bool:
    """Return True when a GC model supports reasoning output."""
    normalized = model_name.lower()
    if "deepseek" in normalized:
        return True
    return False

def _map_gc_error(error: BaseException, *, model: str = "") -> ModelRouterError:
    """Map General Compute/httpx failures to shared error hierarchy."""
    if isinstance(error, httpx.HTTPStatusError):
        status_code = error.response.status_code
        if status_code in (401, 403):
            return AuthenticationError(str(error), provider="general_compute", model=model, original=error)
        if status_code == 429:
            return RateLimitError(str(error), provider="general_compute", model=model, original=error)
    return ModelRouterError(str(error), provider="general_compute", model=model, original=error)

class GeneralComputeProvider(BaseProvider):
    """Generation provider backed by General Compute's OpenAI-compatible API."""

    def __init__(self, config: GeneralComputeConfig) -> None:
        self._config = config
        self._test_mode = _is_test_mode()

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """POST /v1/chat/completions — returns normalized response."""
        # Implementation follows same pattern as OpenRouterProvider.generate()
        # Uses httpx.AsyncClient, _build_messages(), same body format
        # Parses response for choices[0].message.content, usage info

    async def stream(self, request: GenerateRequest) -> AsyncGenerator[StreamChunk, None]:
        """Stream with SSE from POST /v1/chat/completions with stream: true."""
        # Same streaming pattern as OpenRouter
        # Yields StreamChunk for thinking and content types

    async def list_models(self) -> list[ModelInfo]:
        """POST /v1/models/list — returns available models."""
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

    async def health_check(self) -> bool:
        """Return True when the API key is valid."""
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

### Key Validation in Settings Router (settings.py)
```python
async def _validate_generalcompute_key(api_key: str) -> bool:
    """Validate a GC key using a temporary provider instance."""
    config = GeneralComputeConfig(api_key=api_key)
    provider = GeneralComputeProvider(config)
    return await provider.health_check()

# In _validate_provider_key():
elif provider == ProviderType.GENERAL_COMPUTE.value:
    validator = _validate_generalcompute_key

# In _get_validation_method():
if provider == ProviderType.GENERAL_COMPUTE.value:
    return "health_check"
```

### Frontend ProviderType Update (both apps' types/settings.ts)
```typescript
export type ProviderType = 'vertex_ai' | 'openrouter' | 'general_compute' | 'ollama';
```

### Frontend Provider Card (Both ProviderSettingsSection.tsx files)
```typescript
import { Cpu, Globe, Server, Cloud } from 'lucide-react';  // ★ Add Cloud icon

const PROVIDERS = [
    { id: 'vertex_ai' as const, label: 'Vertex AI', icon: Cpu, needsKey: true },
    { id: 'openrouter' as const, label: 'OpenRouter', icon: Globe, needsKey: true },
    { id: 'general_compute' as const, label: 'General Compute', icon: Cloud, needsKey: true },  // ★ NEW
    { id: 'ollama' as const, label: 'Ollama', icon: Server, needsKey: false },
];
```

### Cost Calculator Addition
```python
# In CostCalculator class:
_GC_PRICING: dict[str, dict[str, float]] = {
    "minimax-m2.7": {"input": 0.40, "output": 2.34},
    "deepseek-v3.2": {"input": 3.00, "output": 4.50},
    "deepseek-v3.1": {"input": 3.00, "output": 4.50},
}

def estimate(self, usage: UsageInfo, model: str, provider: ProviderType) -> float:
    # ...existing cases...
    if provider == ProviderType.GENERAL_COMPUTE:
        return self._estimate_general_compute(usage, model)
    return 0.0

def _estimate_general_compute(self, usage: UsageInfo, model: str) -> float:
    pricing = self._GC_PRICING.get(model)
    if pricing is None:
        return 0.0
    input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
    total_output = usage.output_tokens + usage.thinking_tokens
    output_cost = (total_output / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| OpenRouter and Vertex AI only | General Compute as 4th provider | This phase | More provider choice, lower-cost inference options |
| OpenRouter-specific model discovery logic | General Compute provider with own model listing | This phase | Provider model listing is now an established pattern |
| Static pricing for Vertex AI, dynamic for OpenRouter | Static pricing for General Compute too (published prices) | This phase | Cost calculation supports another provider easily |

**Deprecated/outdated:**
- Avoid using the OpenRouter SDK's `get_credit_balance()` as the general pattern — not all providers have credit systems. GC doesn't have one.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | General Compute API does not support embeddings | Standard Stack | If they add embeddings later, we'd need to add `GeneralComputeEmbeddingProvider` |
| A2 | General Compute's `POST /v1/models/list` response uses `data` array or direct array | Pattern 1 | If format differs, the `list_models()` parsing will need adjustment — easily debugged with a live test |
| A3 | General Compute streaming uses the exact same OpenAI chunk format as OpenRouter | Pattern 1 | All evidence from docs supports this; same as all OpenAI-compatible APIs |
| A4 | `Cloud` icon from lucide-react is available | Frontend Code | If `Cloud` icon doesn't exist, use `Zap` or `Globe` as fallback |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

## Open Questions

1. **Should `_build_messages()` be shared or duplicated?**
   - What we know: Two providers (OpenRouter and GC) use identical OpenAI message format
   - What's unclear: Whether to extract to a shared `_openai_compat.py` utility or tolerate duplication
   - Recommendation: **Duplicate for now.** The OpenRouter provider itself was already a standalone copy of the OpenAI pattern. Premature extraction adds coupling. If a third OpenAI-compatible provider is added, then extract.

2. **Should we use `GET /v1/public/models` (no auth needed) for model listing?**
   - What we know: GC has both auth'd (`POST /v1/models/list`) and public (`GET /v1/public/models`) endpoints
   - What's unclear: Whether the public endpoint returns all models or just curated ones
   - Recommendation: **Use `POST /v1/models/list`** (auth'd) for the provider's `list_models()` since it returns org-specific models. The public endpoint can be a future optimization.

3. **Should embedding support be added?**
   - What we know: GC does not document an embeddings endpoint
   - What's unclear: Whether they have one undocumented, or plan to add one
   - Recommendation: **Skip embedding support.** Only implement `BaseProvider` (generation). The registration should have `self.register_embedding_provider(..., None)` pattern implicitly skipped (just don't register one).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | Backend (model_router) | ✓ | 3.11+ (project req) | — |
| httpx | HTTP calls to GC API | ✓ | >=0.27.0 (in deps) | — |
| pydantic >=2.0 | Config models | ✓ | Already in deps | — |
| Redis | API key storage, settings | ✓ | 7+ | Test mode bypasses |
| `@generalcompute/sdk` | SDK-based approach | ✓ | 0.2.1 | NOT USED — httpx suffices |

**Missing dependencies with no fallback:** None

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | `shared/model_router/pyproject.toml` (test config) |
| Quick run command | `cd shared/model_router && python -m pytest tests/test_general_compute_provider.py -v` |
| Full suite command | `cd shared/model_router && python -m pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| P9-01 | ProviderType.GENERAL_COMPUTE exists in enum | unit | `test_types.py` — verify member exists | ❌ new |
| P9-02 | GeneralComputeProvider generates in test mode | unit | `test_general_compute_provider.py::test_generate_test_mode` | ❌ new |
| P9-02 | GeneralComputeProvider streams in test mode | unit | `test_general_compute_provider.py::test_stream_test_mode` | ❌ new |
| P9-02 | GeneralComputeProvider lists models in test mode | unit | `test_general_compute_provider.py::test_list_models_test_mode` | ❌ new |
| P9-02 | GeneralComputeProvider health check in test mode | unit | `test_general_compute_provider.py::test_health_check_test_mode` | ❌ new |
| P9-03 | GeneralComputeConfig.from_env() reads env vars | unit | `test_general_compute_provider.py::test_config_from_env` | ❌ new |
| P9-04 | ModelRouter auto-registers GC when config has key | unit | `test_general_compute_provider.py::test_auto_register` | ❌ new |
| P9-05 | CostCalculator estimates GC model pricing | unit | `test_cost_calculator.py::test_general_compute_pricing` | ❌ new |
| P9-07/08 | Frontend types include 'general_compute' | unit | Already tested by TypeScript compilation | ❌ new |
| P9-09 | model_router public exports | import | `test_import_contexts.py::test_import_all_public_api` | ❌ edit |

### Sampling Rate
- **Per task commit:** `python -m pytest shared/model_router/tests/test_general_compute_provider.py -v`
- **Per wave merge:** `python -m pytest shared/model_router/tests/ -v`
- **Phase gate:** Full suite green + both frontends build without type errors

### Wave 0 Gaps
- [ ] `tests/test_general_compute_provider.py` — covers P9-02, P9-03, P9-04
- [ ] `tests/test_cost_calculator.py` — add GC pricing tests (P9-05)
- [ ] `tests/test_import_contexts.py` — add `GeneralComputeProvider` to import test (P9-09)

## Sources

### Primary (HIGH confidence)
- [General Compute Quickstart docs](https://docs.generalcompute.com/quickstart) — [VERIFIED: docs.generalcompute.com]
- [General Compute Models & Pricing](https://docs.generalcompute.com/models) — [VERIFIED: docs.generalcompute.com]
- [General Compute API Reference](https://docs.generalcompute.com/api-reference/introduction) — [VERIFIED: docs.generalcompute.com]
- [General Compute API Keys & Base URLs](https://docs.generalcompute.com/api-keys) — [VERIFIED: docs.generalcompute.com]
- [Existing OpenRouter provider implementation](shared/model_router/src/model_router/providers/openrouter.py) — [VERIFIED: codebase]
- [Existing ModelRouter registration](shared/model_router/src/model_router/router.py) — [VERIFIED: codebase]
- [Existing config models](shared/model_router/src/model_router/config.py) — [VERIFIED: codebase]
- [Existing ProviderType enum](shared/model_router/src/model_router/types.py) — [VERIFIED: codebase]
- [Existing cost calculator](shared/model_router/src/model_router/cost_calculator.py) — [VERIFIED: codebase]
- [AURA-CHAT settings router](AURA-CHAT/server/routers/settings.py) — [VERIFIED: codebase]
- [AURA-NOTES-MANAGER settings router](AURA-NOTES-MANAGER/api/routers/settings.py) — [VERIFIED: codebase]
- [AURA-CHAT frontend types/settings.ts](AURA-CHAT/client/src/types/settings.ts) — [VERIFIED: codebase]
- [AURA-NOTES-MANAGER frontend types/settings.ts](AURA-NOTES-MANAGER/frontend/src/types/settings.ts) — [VERIFIED: codebase]

### Secondary (MEDIUM confidence)
- npm registry: `@generalcompute/sdk` v0.2.1 exists [VERIFIED: npm registry]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all dependencies already in project, no new packages needed
- Architecture: HIGH — follows exact OpenRouter pattern, well-understood
- General Compute API: HIGH — OpenAI-compatible, well-documented, straightforward
- Frontend changes: HIGH — mechanical changes to type unions and PROVIDERS arrays, well-understood pattern
- Pitfalls: HIGH — unambiguous documentation, model listing endpoint difference is the main gotcha

**Research date:** 2026-05-23
**Valid until:** 2026-07-23 (stable API — General Compute is a mature service)
