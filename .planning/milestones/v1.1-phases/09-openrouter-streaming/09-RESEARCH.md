# Phase 9: OpenRouter Provider + Streaming Normalization - Research

**Researched:** 2025-07-15
**Domain:** OpenRouter API integration, OpenAI SDK, streaming normalization, cross-provider thinking/reasoning
**Confidence:** HIGH (standard stack), MEDIUM (streaming/thinking normalization)

## Summary

Phase 9 adds the OpenRouter provider to the shared `model_router` package, enabling access to 200+ models through the same `generate()` and `stream()` interface built in Phase 8. The core challenge is not the OpenRouter API itself — it's OpenAI-compatible and well-served by the `openai` Python SDK — but rather **normalizing streaming output and thinking/reasoning content** from fundamentally different provider APIs into the single `StreamChunk(type='thinking'|'content', text=...)` shape that the frontend already consumes.

Three technical domains converge: (1) OpenRouter provider implementation using the `openai` AsyncOpenAI client with base_url override, (2) streaming normalization where OpenAI-format `delta.content` chunks must be converted to AURA's existing SSE `{type, text}` contract, and (3) a unified thinking/reasoning interface where Gemini's `thinking_config` (budget/level), Claude's extended thinking via OpenRouter (`reasoning.effort`), and DeepSeek's always-on reasoning (`reasoning_content` delta field) all map to a single `thinking_config: dict` on `GenerateRequest` with graceful degradation for non-thinking models.

The existing codebase is well-prepared: Phase 8 already defined `ProviderType.OPENROUTER`, the router resolves `'/' in model` → OPENROUTER, `StreamChunk` and `BaseProvider` ABCs exist, the Vertex AI provider already normalizes its chunks, and the frontend already handles `{type: 'thinking'|'content', text}` events. The primary implementation work is: (a) new `OpenRouterProvider` class in `providers/openrouter.py`, (b) `OpenRouterConfig` in `config.py`, (c) auto-registration in `ModelRouter.__init__`, and (d) comprehensive tests.

**Primary recommendation:** Implement `OpenRouterProvider` using `openai.AsyncOpenAI` with `base_url="https://openrouter.ai/api/v1"`, normalize streaming via a `_normalize_openrouter_stream()` adapter that converts `ChatCompletionChunk.delta.content` and `delta.reasoning_content` to `StreamChunk`, and translate `thinking_config` to provider-specific parameters (Claude: `reasoning.effort`, DeepSeek: pass-through, unsupported: silently ignore).

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PROV-02 | OpenRouter provider supports completions, streaming, model listing, and credit checking via the `openai` SDK | Implement `OpenRouterProvider(BaseProvider)` with `AsyncOpenAI(base_url="https://openrouter.ai/api/v1")`. Chat completions use `client.chat.completions.create()`, streaming adds `stream=True`. Model listing via `GET /api/v1/models`. Credit checking via `GET /api/v1/auth/key` (requires separate httpx call — not in openai SDK). |
| ROUTER-03 | All providers stream responses through a normalized SSE format matching AURA's existing `{type: "thinking"\|"content", text}` chunk shape | Vertex AI already normalizes via `_normalize_stream_chunk()` in Phase 8. OpenRouter normalization converts `delta.content` → `StreamChunk(type='content')` and `delta.reasoning_content` → `StreamChunk(type='thinking')`. Both yield the same type through `BaseProvider.stream()`. |
| PROV-03 | Thinking/reasoning mode works across Vertex AI (Gemini thinking), OpenRouter (Claude extended thinking, DeepSeek reasoning) with a unified enable/budget interface | Translate `GenerateRequest.thinking_config` per provider: Vertex AI passes through to google-genai SDK (already works), Claude via OpenRouter uses `extra_body={"reasoning": {"effort": "high"}}`, DeepSeek R1 reasoning is always-on (ignore thinking_config). Graceful degradation: if model doesn't support thinking, omit the parameter silently. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `openai` | >=1.51.0 | OpenRouter API client (OpenAI-compatible) | Official Python SDK; OpenRouter recommends it; supports async, streaming, typed responses |
| `httpx` | >=0.25.0 | Credit balance & model listing REST calls | Already in openai's dependency tree; needed for OpenRouter-specific endpoints not in openai SDK |
| `pydantic` | >=2.0 | Type definitions (already in use) | Already core dependency of model_router package |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | >=8.0 | Unit tests | Testing OpenRouter provider |
| `pytest-asyncio` | >=0.23 | Async test support | All provider methods are async |
| `respx` | >=0.21 | HTTP mocking for httpx | Mocking OpenRouter REST endpoints in tests (optional; can use unittest.mock) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `openai` SDK | Raw `httpx` calls | More control but loses typed responses, streaming helpers, automatic retries |
| `openai` SDK | `litellm` | Heavyweight (50+ deps), abstracts away provider differences we need to control |
| `httpx` for credit/models | `aiohttp` | Not already in dep tree; httpx comes free with openai SDK |

**Installation (add to pyproject.toml):**
```toml
[project.optional-dependencies]
openrouter = [
  'openai>=1.51.0',
]
all = [
  'google-genai>=1.59.0',
  'google-auth>=2.35.0',
  'google-cloud-aiplatform>=1.51.0',
  'requests>=2.31.0',
  'openai>=1.51.0',
]
```

```bash
pip install -e shared/model_router[openrouter]
# Or for everything:
pip install -e shared/model_router[all,dev]
```

## Architecture Patterns

### Recommended File Structure
```
shared/model_router/
  src/model_router/
    providers/
      openrouter.py          # NEW: OpenRouterProvider + stream normalization
    config.py                 # MODIFIED: add OpenRouterConfig
    router.py                 # MODIFIED: auto-register OpenRouter when key present
    __init__.py               # MODIFIED: export new types
  tests/
    test_openrouter_provider.py  # NEW: provider unit tests
    test_streaming.py            # NEW: cross-provider stream normalization tests
    test_thinking.py             # NEW: thinking config translation tests
```

### Pattern 1: OpenAI SDK with Base URL Override
**What:** Use the standard `openai` Python SDK but point it at OpenRouter's API.
**When to use:** All OpenRouter API interactions for completions and streaming.

```python
# Source: OpenRouter docs + openai SDK pattern
from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url='https://openrouter.ai/api/v1',
    api_key=config.api_key,
    default_headers={
        'HTTP-Referer': config.site_url,    # OpenRouter attribution
        'X-Title': config.site_name,        # OpenRouter attribution
    },
)
```

### Pattern 2: Streaming Normalization Adapter
**What:** Convert OpenAI `ChatCompletionChunk` objects to AURA's `StreamChunk` type.
**When to use:** In `OpenRouterProvider.stream()` method.

```python
from model_router.types import StreamChunk

async def _normalize_openrouter_stream(
    stream,  # AsyncStream[ChatCompletionChunk]
) -> AsyncGenerator[StreamChunk, None]:
    """Convert OpenAI streaming chunks to normalized StreamChunk."""
    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta

        # Reasoning/thinking content (Claude extended thinking,
        # DeepSeek reasoning)
        reasoning = getattr(delta, 'reasoning_content', None)
        if reasoning:
            yield StreamChunk(type='thinking', text=reasoning)

        # Regular content
        if delta.content:
            yield StreamChunk(type='content', text=delta.content)
```

### Pattern 3: Thinking Config Translation
**What:** Map AURA's unified `thinking_config` dict to provider-specific parameters.
**When to use:** When building OpenRouter API requests.

```python
# Thinking config translation for OpenRouter models
def _build_thinking_params(
    model: str,
    thinking_config: dict | None,
) -> dict:
    """Translate thinking_config to OpenRouter extra_body params."""
    if not thinking_config:
        return {}

    # Claude models: use reasoning.effort
    if 'claude' in model.lower() or 'anthropic' in model.lower():
        budget = thinking_config.get('thinking_budget', 0)
        if budget <= 0:
            return {}
        # Map budget to effort level
        if budget <= 1024:
            effort = 'low'
        elif budget <= 4096:
            effort = 'medium'
        else:
            effort = 'high'
        return {'reasoning': {'effort': effort}}

    # DeepSeek R1: reasoning is always-on, no config needed
    if 'deepseek' in model.lower() and 'r1' in model.lower():
        return {}  # reasoning_content comes automatically

    # Model doesn't support thinking: silently ignore
    return {}
```

### Pattern 4: Provider Auto-Registration
**What:** Router automatically registers OpenRouter provider when API key is configured.
**When to use:** In `ModelRouter.__init__()`.

```python
# In router.py — extend __init__
def __init__(self, config: RouterConfig | None = None) -> None:
    self._config = config or RouterConfig()
    self._providers: dict[ProviderType, BaseProvider] = {}
    self._embedding_provider: BaseEmbeddingProvider | None = None

    if self._should_auto_register_vertex():
        # ... existing Vertex AI registration ...

    if self._should_auto_register_openrouter():
        from model_router.providers.openrouter import OpenRouterProvider
        openrouter_provider = OpenRouterProvider(self._config.openrouter)
        self.register_provider(ProviderType.OPENROUTER, openrouter_provider)

def _should_auto_register_openrouter(self) -> bool:
    return self._config.test_mode or bool(self._config.openrouter.api_key)
```

### Pattern 5: Curated Model Allowlist
**What:** Only expose models known to work well with the AURA interface.
**When to use:** In `OpenRouterProvider.list_models()` — filter the full OpenRouter model list.

```python
# Curated categories for list_models()
_OPENROUTER_CURATED_PREFIXES = [
    'anthropic/',       # Claude models
    'google/',          # Gemini via OpenRouter
    'openai/',          # GPT models
    'deepseek/',        # DeepSeek models
    'meta-llama/',      # Llama models
    'mistralai/',       # Mistral models
    'qwen/',            # Qwen models
]

# Optional: specific model blocklist for known-broken models
_OPENROUTER_BLOCKED_MODELS: set[str] = set()
```

### Anti-Patterns to Avoid
- **Importing `openai` at module level in openrouter.py:** Use lazy imports inside methods (matching `vertex_ai.py` pattern). The openai SDK should only be required when OpenRouter is actually used.
- **Building a custom HTTP client for OpenRouter:** Use the `openai` SDK — it handles retries, streaming parsing, error types, and connection management.
- **Exposing `ChatCompletionChunk` to callers:** All OpenAI types must be converted to `StreamChunk` before leaving the provider. Application code never sees `openai.*` types.
- **Hardcoding thinking params for all models:** Use model-name sniffing to determine thinking capability. Unknown models get no thinking params (graceful degradation).
- **Using `openai` SDK for model listing/credits:** These are OpenRouter-specific REST endpoints, not standard OpenAI API. Use `httpx` directly for these.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OpenAI-compatible HTTP client | Custom httpx wrapper with SSE parsing | `openai.AsyncOpenAI` SDK | Handles streaming, retries, connection pooling, typed responses, error classes |
| SSE stream parsing | Manual `text/event-stream` parser | `openai` SDK's streaming iterator | SDK handles reconnection, partial chunks, `[DONE]` sentinel |
| Error type mapping | String-matching on HTTP responses | `openai` SDK's exception hierarchy | SDK raises typed exceptions: `AuthenticationError`, `RateLimitError`, etc. |
| Model metadata parsing | Custom JSON schema for 200+ models | OpenRouter's `/api/v1/models` endpoint | Returns structured JSON with pricing, context length, capabilities |

**Key insight:** The `openai` SDK does 90% of the heavy lifting. The provider implementation is primarily a translation layer between `openai` types and `model_router` types, plus thinking config translation.

## Common Pitfalls

### Pitfall 1: Reasoning Content Field Name Varies
**What goes wrong:** Thinking/reasoning content from Claude and DeepSeek arrives in a field that doesn't exist on the standard `ChatCompletionChunkChoice.Delta` type.
**Why it happens:** The `reasoning_content` field is a provider-specific extension. OpenRouter passes it through, but the openai SDK may not have it as a typed attribute. It may appear as `reasoning_content` on the delta, or in some cases as `reasoning` in the message object.
**How to avoid:** Use `getattr(delta, 'reasoning_content', None)` defensively. Also check `getattr(delta, 'reasoning', None)` as a fallback. Write tests that mock both field locations. Verify against live OpenRouter responses during integration testing.
**Warning signs:** Thinking content is silently dropped — the frontend shows no thinking toggle for Claude/DeepSeek responses.
**Confidence:** MEDIUM — field name needs validation against current OpenRouter API.

### Pitfall 2: OpenRouter Streaming Termination Differs from Vertex AI
**What goes wrong:** Stream appears to hang or misses the final chunk.
**Why it happens:** OpenAI-format streaming ends with a `data: [DONE]` sentinel, while Vertex AI streaming ends when the iterator is exhausted. The openai SDK handles `[DONE]` internally, but error handling and cleanup differ.
**How to avoid:** Let the openai SDK handle stream lifecycle. Use `async for chunk in stream:` — the SDK's `AsyncStream` handles termination. Ensure the stream is properly closed in `finally` blocks (the SDK's context manager handles this).
**Warning signs:** Streaming works for Vertex AI but hangs indefinitely for OpenRouter.

### Pitfall 3: OpenRouter Rate Limits and Error Shapes
**What goes wrong:** OpenRouter rate limit errors don't map to the shared `RateLimitError` because the error format differs from direct OpenAI.
**Why it happens:** OpenRouter proxies responses from many providers. Some error responses include OpenRouter-specific metadata (e.g., `error.metadata.provider_name`). The `openai` SDK may wrap these differently.
**How to avoid:** Map errors using the `openai` SDK's typed exception classes (`openai.RateLimitError`, `openai.AuthenticationError`, etc.) rather than parsing HTTP status codes manually. The SDK already normalizes these.
**Warning signs:** Generic `ModelRouterError` instead of specific subtypes for OpenRouter failures.

### Pitfall 4: Model Name Format Mismatch
**What goes wrong:** User passes `claude-sonnet-4` (no provider prefix) and it routes to Vertex AI instead of OpenRouter.
**Why it happens:** The router uses `'/' in model` to detect OpenRouter models. If the frontend sends model names without the `vendor/` prefix, routing fails silently.
**How to avoid:** OpenRouter model IDs always include a vendor prefix (e.g., `anthropic/claude-sonnet-4`, `deepseek/deepseek-r1`). Document this requirement. The model picker UI (Phase 11) must send the full model ID.
**Warning signs:** `ModelUnavailableError` when selecting OpenRouter models.

### Pitfall 5: Thinking Budget Mapping Is Approximate
**What goes wrong:** User requests specific thinking budget (e.g., 2048 tokens) but Claude's `reasoning.effort` only has 3 levels (low/medium/high), so the mapping is lossy.
**Why it happens:** Different providers expose thinking control at different granularities. Gemini has token-level budgets, Claude has effort levels, DeepSeek has no control.
**How to avoid:** Document the mapping clearly. The `thinking_config` dict is an intent, not a guarantee. Accept that provider A's "2048 tokens" and provider B's "medium effort" are approximate equivalents. Log the actual parameters sent to each provider.
**Warning signs:** Users expecting identical thinking behavior across providers.

### Pitfall 6: Test Mode Must Not Import openai SDK
**What goes wrong:** Tests fail with `ModuleNotFoundError: No module named 'openai'` when the openrouter optional dependency isn't installed.
**Why it happens:** If `openrouter.py` imports `openai` at module level, it breaks when only `pip install -e .[vertex]` is used.
**How to avoid:** Follow the Vertex AI provider pattern: lazy imports inside methods, check `_is_test_mode()` before touching the SDK. Test mode returns canned responses without importing `openai`.
**Warning signs:** Import errors in CI pipelines that only install the `vertex` extras.

## Code Examples

Verified patterns from the existing codebase and SDK documentation:

### OpenRouterProvider Skeleton
```python
# shared/model_router/src/model_router/providers/openrouter.py
"""OpenRouter provider for the shared model router."""

from __future__ import annotations

import os
from typing import Any, AsyncGenerator

from model_router.config import OpenRouterConfig
from model_router.errors import (
    AuthenticationError,
    ContentPolicyError,
    ModelRouterError,
    ModelUnavailableError,
    ProviderTimeoutError,
    RateLimitError,
)
from model_router.providers.base import BaseProvider
from model_router.types import (
    GenerateRequest,
    GenerateResponse,
    ModelInfo,
    ProviderType,
    StreamChunk,
    UsageInfo,
)


def _is_test_mode() -> bool:
    return os.getenv('AURA_TEST_MODE', '').strip().lower() == 'true'


def _map_openrouter_error(
    error: BaseException,
    *,
    model: str = '',
) -> ModelRouterError:
    """Map openai SDK exceptions to the shared error hierarchy."""
    # Lazy import to avoid requiring openai at module level
    try:
        import openai as openai_mod
    except ImportError:
        return ModelRouterError(
            str(error),
            provider=ProviderType.OPENROUTER.value,
            model=model,
            original=error,
        )

    if isinstance(error, openai_mod.AuthenticationError):
        return AuthenticationError(
            str(error),
            provider=ProviderType.OPENROUTER.value,
            model=model,
            original=error,
        )
    if isinstance(error, openai_mod.RateLimitError):
        return RateLimitError(
            str(error),
            provider=ProviderType.OPENROUTER.value,
            model=model,
            original=error,
        )
    if isinstance(error, openai_mod.NotFoundError):
        return ModelUnavailableError(
            str(error),
            provider=ProviderType.OPENROUTER.value,
            model=model,
            original=error,
        )
    # openai.BadRequestError can be content policy
    if isinstance(error, openai_mod.BadRequestError):
        error_str = str(error).lower()
        if 'safety' in error_str or 'content' in error_str:
            return ContentPolicyError(
                str(error),
                provider=ProviderType.OPENROUTER.value,
                model=model,
                original=error,
            )
    if isinstance(error, openai_mod.APITimeoutError):
        return ProviderTimeoutError(
            str(error),
            provider=ProviderType.OPENROUTER.value,
            model=model,
            original=error,
        )
    return ModelRouterError(
        str(error),
        provider=ProviderType.OPENROUTER.value,
        model=model,
        original=error,
    )


class OpenRouterProvider(BaseProvider):
    """Generation provider backed by OpenRouter (OpenAI-compatible)."""

    def __init__(self, config: OpenRouterConfig) -> None:
        self._config = config
        self._test_mode = _is_test_mode()
        self._client: Any | None = None

    def _get_client(self) -> Any:
        """Create and cache an AsyncOpenAI client."""
        if self._test_mode:
            return None
        if self._client is not None:
            return self._client

        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(
            base_url=self._config.base_url,
            api_key=self._config.api_key,
            default_headers={
                'HTTP-Referer': self._config.site_url,
                'X-Title': self._config.site_name,
            },
        )
        return self._client

    async def generate(
        self, request: GenerateRequest,
    ) -> GenerateResponse:
        """Generate a response via OpenRouter."""
        if self._test_mode:
            return GenerateResponse(
                text='Test-mode output.',
                model_used=request.model,
                provider=ProviderType.OPENROUTER,
                usage=UsageInfo(),
            )

        client = self._get_client()
        try:
            messages = _build_messages(request)
            extra_body = _build_thinking_params(
                request.model, request.thinking_config,
            )
            kwargs: dict[str, Any] = {
                'model': request.model,
                'messages': messages,
            }
            if request.temperature is not None:
                kwargs['temperature'] = request.temperature
            if request.max_output_tokens is not None:
                kwargs['max_tokens'] = request.max_output_tokens
            if extra_body:
                kwargs['extra_body'] = extra_body

            response = await client.chat.completions.create(**kwargs)
        except ModelRouterError:
            raise
        except Exception as error:
            raise _map_openrouter_error(
                error, model=request.model,
            ) from error

        choice = response.choices[0]
        thinking_text = getattr(
            choice.message, 'reasoning_content', None,
        )
        return GenerateResponse(
            text=choice.message.content or '',
            model_used=response.model or request.model,
            provider=ProviderType.OPENROUTER,
            usage=UsageInfo(
                input_tokens=response.usage.prompt_tokens
                if response.usage else 0,
                output_tokens=response.usage.completion_tokens
                if response.usage else 0,
            ),
            thinking_text=thinking_text,
        )

    async def stream(
        self, request: GenerateRequest,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream normalized chunks from OpenRouter."""
        if self._test_mode:
            yield StreamChunk(type='content', text='Test-mode stream output.')
            return

        client = self._get_client()
        try:
            messages = _build_messages(request)
            extra_body = _build_thinking_params(
                request.model, request.thinking_config,
            )
            kwargs: dict[str, Any] = {
                'model': request.model,
                'messages': messages,
                'stream': True,
            }
            if request.temperature is not None:
                kwargs['temperature'] = request.temperature
            if request.max_output_tokens is not None:
                kwargs['max_tokens'] = request.max_output_tokens
            if extra_body:
                kwargs['extra_body'] = extra_body

            stream = await client.chat.completions.create(**kwargs)
        except ModelRouterError:
            raise
        except Exception as error:
            raise _map_openrouter_error(
                error, model=request.model,
            ) from error

        try:
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                # Reasoning/thinking content
                reasoning = getattr(
                    delta, 'reasoning_content', None,
                )
                if reasoning:
                    yield StreamChunk(type='thinking', text=reasoning)
                # Regular content
                if delta.content:
                    yield StreamChunk(type='content', text=delta.content)
        except Exception as error:
            raise _map_openrouter_error(
                error, model=request.model,
            ) from error

    async def list_models(self) -> list[ModelInfo]:
        """List curated models from OpenRouter."""
        if self._test_mode:
            return _TEST_MODELS
        # Use httpx to call OpenRouter models endpoint
        # (not part of openai SDK)
        # ... implementation fetches /api/v1/models ...

    async def health_check(self) -> bool:
        """Check if OpenRouter is reachable."""
        if self._test_mode:
            return True
        # ... implementation checks /api/v1/auth/key ...
```

### OpenRouterConfig Addition
```python
# In config.py — add alongside VertexAIConfig
class OpenRouterConfig(BaseModel):
    """Configuration for the OpenRouter provider."""

    api_key: str = ''
    base_url: str = 'https://openrouter.ai/api/v1'
    site_url: str = ''      # For HTTP-Referer header
    site_name: str = 'AURA'  # For X-Title header

    @classmethod
    def from_env(cls) -> 'OpenRouterConfig':
        return cls(
            api_key=os.getenv('OPENROUTER_API_KEY', ''),
            base_url=os.getenv(
                'OPENROUTER_BASE_URL',
                'https://openrouter.ai/api/v1',
            ),
            site_url=os.getenv('OPENROUTER_SITE_URL', ''),
            site_name=os.getenv('OPENROUTER_SITE_NAME', 'AURA'),
        )


# Extend RouterConfig
class RouterConfig(BaseModel):
    default_provider: ProviderType = ProviderType.VERTEX_AI
    vertex_ai: VertexAIConfig = Field(default_factory=VertexAIConfig)
    openrouter: OpenRouterConfig = Field(default_factory=OpenRouterConfig)
    test_mode: bool = False

    @classmethod
    def from_env(cls) -> 'RouterConfig':
        return cls(
            default_provider=ProviderType.VERTEX_AI,
            vertex_ai=VertexAIConfig.from_env(),
            openrouter=OpenRouterConfig.from_env(),
            test_mode=_env_flag('AURA_TEST_MODE'),
        )
```

### Message Format Conversion
```python
def _build_messages(
    request: GenerateRequest,
) -> list[dict[str, Any]]:
    """Convert GenerateRequest contents to OpenAI messages format."""
    messages: list[dict[str, Any]] = []

    # System instruction
    if request.system_instruction:
        messages.append({
            'role': 'system',
            'content': request.system_instruction,
        })

    # Contents can be str or list of dicts
    if isinstance(request.contents, str):
        messages.append({
            'role': 'user',
            'content': request.contents,
        })
    elif isinstance(request.contents, list):
        for item in request.contents:
            if isinstance(item, dict):
                role = item.get('role', 'user')
                if role == 'model':
                    role = 'assistant'  # OpenAI uses 'assistant'
                parts = item.get('parts', [])
                text = ''
                for part in parts:
                    if isinstance(part, dict):
                        text += part.get('text', '')
                    elif isinstance(part, str):
                        text += part
                if text:
                    messages.append({'role': role, 'content': text})
            elif isinstance(item, str):
                messages.append({'role': 'user', 'content': item})

    return messages
```

### Credit Balance Check
```python
async def get_credit_balance(
    self,
) -> dict[str, Any]:
    """Retrieve OpenRouter credit balance and usage."""
    if self._test_mode:
        return {
            'usage': 0.0,
            'limit': 100.0,
            'is_free_tier': False,
        }

    import httpx
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            f'{self._config.base_url}/auth/key',
            headers={
                'Authorization': f'Bearer {self._config.api_key}',
            },
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json().get('data', {})
        return {
            'usage': data.get('usage', 0.0),
            'limit': data.get('limit'),
            'is_free_tier': data.get('is_free_tier', True),
            'rate_limit': data.get('rate_limit', {}),
        }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `openai` SDK v0.x (sync-only) | `openai` SDK v1.x+ (async-native, typed) | Nov 2023 | Must use v1.x patterns (`AsyncOpenAI`, `client.chat.completions.create()`) |
| No reasoning content in SDK types | `delta.reasoning_content` field | ~2024 (openai SDK 1.30+) | Reasoning/thinking from Claude/DeepSeek via this field |
| Manual SSE parsing for streaming | SDK handles SSE internally | openai SDK 1.0+ | Never parse SSE manually — use `async for chunk in stream` |
| Direct API key in URL params | Bearer token in Authorization header | Always (OpenRouter) | `Authorization: Bearer <key>` — never in URL |

**Deprecated/outdated:**
- `openai.ChatCompletion.create()` (v0.x API): Replaced by `client.chat.completions.create()` in v1.x
- `openai.api_key = "..."` module-level config: Replaced by client instantiation `AsyncOpenAI(api_key=...)`

## Open Questions

1. **Exact `reasoning_content` field availability in streaming**
   - What we know: OpenRouter passes through reasoning content from providers. The `openai` SDK v1.30+ includes `reasoning_content` on delta objects for models that support it.
   - What's unclear: Whether all OpenRouter models that support reasoning consistently use `reasoning_content` vs some other field name. Some documentation suggests `reasoning` as an alternative.
   - Recommendation: Use `getattr(delta, 'reasoning_content', None)` defensively. Test against live OpenRouter with Claude and DeepSeek during integration testing. Add a fallback check for `getattr(delta, 'reasoning', None)`.

2. **Claude extended thinking budget granularity via OpenRouter**
   - What we know: Anthropic's direct API uses `thinking.budget_tokens`. OpenRouter wraps this and may expose it as `reasoning.effort` (low/medium/high) or pass through the `budget_tokens` parameter.
   - What's unclear: Whether OpenRouter's `reasoning` parameter supports `budget_tokens` directly or only effort levels. The mapping from AURA's `thinking_config.thinking_budget` to OpenRouter's parameter format.
   - Recommendation: Start with `reasoning.effort` level mapping. If OpenRouter supports `budget_tokens` pass-through, add it as an enhancement. Document the approximate mapping.

3. **Model allowlist maintenance strategy**
   - What we know: OpenRouter has 200+ models, many are niche or unstable. Exposing all models in the UI would be overwhelming and some may not work with AURA's message format.
   - What's unclear: Whether to use a static allowlist (curated in code) or dynamic filtering (by provider prefix + capability flags from the API).
   - Recommendation: Use a curated prefix allowlist (anthropic/, google/, openai/, deepseek/, meta-llama/, mistralai/) plus a per-model blocklist for known-broken models. The full model list is cached but filtered before returning to the UI. This is simpler than capability-based filtering and easier to maintain.

4. **OpenRouter usage/cost data format for UsageInfo**
   - What we know: OpenRouter returns standard `usage.prompt_tokens` and `usage.completion_tokens` in non-streaming responses. Streaming responses typically don't include usage in chunks.
   - What's unclear: Whether OpenRouter provides thinking token counts separately, and how to capture usage from streamed responses (the last chunk may include it, or a final metadata event).
   - Recommendation: Capture usage from non-streaming responses directly. For streaming, check the last chunk for usage metadata. If unavailable, log a warning and return zero usage (best-effort tracking, full tracking in Phase 12).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio |
| Config file | `shared/model_router/pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `cd shared/model_router && ../../.venv/Scripts/python -m pytest tests/ -x` |
| Full suite command | `cd shared/model_router && ../../.venv/Scripts/python -m pytest tests/ -v` |

### Phase Requirements → Test Map
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

### Sampling Rate
- **Per task commit:** `cd shared/model_router && ../../.venv/Scripts/python -m pytest tests/ -x`
- **Per wave merge:** Full shared package suite + both app quick suites
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `shared/model_router/tests/test_openrouter_provider.py` — covers PROV-02 (generate, stream, list_models, credit balance, error mapping, health check)
- [ ] `shared/model_router/tests/test_streaming.py` — covers ROUTER-03 (cross-provider stream normalization)
- [ ] `shared/model_router/tests/test_thinking.py` — covers PROV-03 (thinking config translation, graceful degradation)
- [ ] `openai>=1.51.0` added to `pyproject.toml` optional deps
- [ ] Update `shared/model_router/tests/test_router.py` — add OpenRouter generate/stream delegation tests (currently only tests error path for unregistered provider)

## Sources

### Primary (HIGH confidence)
- Codebase scan: `shared/model_router/` — all existing types, providers, router, config, errors verified from source
- Codebase scan: `AURA-CHAT/client/src/types/api.ts` — existing `StreamChunk` type contract verified
- Codebase scan: `AURA-CHAT/backend/routers/sessions.py` — existing SSE format (`format_sse()`, chunk types) verified
- Codebase scan: `AURA-CHAT/backend/utils/vertex_ai_client.py` — existing streaming normalization pattern verified

### Secondary (MEDIUM confidence)
- OpenAI Python SDK v1.x documentation — `AsyncOpenAI`, `chat.completions.create()`, streaming API, exception hierarchy
- OpenRouter API documentation — base URL, authentication headers, model listing, credit balance endpoints, reasoning parameter
- openai SDK reasoning_content field — available in SDK v1.30+ for models with reasoning capability

### Tertiary (LOW confidence)
- Claude extended thinking via OpenRouter: exact parameter format (`reasoning.effort` vs `budget_tokens` pass-through) — needs live validation
- DeepSeek R1 reasoning_content field consistency — needs live validation
- OpenRouter streaming usage metadata availability — needs live validation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — openai SDK with base_url for OpenRouter is well-documented and widely used
- Architecture: HIGH — follows established Phase 8 patterns (BaseProvider, test mode, lazy imports, error mapping)
- Streaming normalization: MEDIUM — OpenAI chunk format is well-known, but reasoning_content field behavior needs live testing
- Thinking config translation: MEDIUM — approximate mapping between provider-specific thinking interfaces is inherently lossy
- Pitfalls: HIGH — identified from codebase analysis and SDK patterns

**Research date:** 2025-07-15
**Valid until:** 2025-08-15 (openai SDK and OpenRouter API are stable; reasoning features evolving)
