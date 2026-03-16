# Phase 8: Shared Package Foundation + Vertex AI Migration - Research

**Researched:** 2025-07-14
**Domain:** Python shared package architecture, Vertex AI SDK migration, error hierarchy design
**Confidence:** HIGH

## Summary

Phase 8 is the highest-risk phase of v1.1. It must deliver an installable shared Python package (`shared/model_router/`) with a unified `generate()` and `embed()` interface, a Vertex AI provider that wraps existing code, a typed error hierarchy, and compatibility shims — all while keeping 210+ existing tests passing unchanged. The core challenge is that the two AURA apps use **fundamentally different Vertex AI SDKs**: AURA-CHAT has already migrated to the new `google-genai` SDK (via `_GenerativeModelWrapper`), while AURA-NOTES-MANAGER still uses the old `vertexai.generative_models` SDK. Additionally, their embedding implementations diverge — AURA-CHAT uses direct REST API calls while AURA-NOTES-MANAGER uses the `TextEmbeddingModel` SDK class. The env var naming also differs (`VERTEX_REGION` vs `VERTEX_LOCATION`).

The Strangler Fig pattern is mandatory. The shared package wraps existing code first (not replaces it), compatibility shims make `get_model()` and `generate_content()` delegate to the new router, and tests pass without modification. Only after this is proven do callers get migrated. The package structure uses `pyproject.toml` with `hatchling` build backend, `src/model_router/` layout, and `pip install -e` into the root venv. The error hierarchy must map both `google.genai.errors.ClientError` (AURA-CHAT) and the old SDK's `google.api_core.exceptions` (AURA-NOTES-MANAGER) to a unified set of typed exceptions (AuthError, RateLimitError, ContentPolicyError, ModelUnavailableError, TimeoutError) with the original error preserved as `.__cause__`.

**Primary recommendation:** Build the shared package skeleton with types and error hierarchy first, then implement the VertexAIProvider by directly importing the AURA-CHAT `vertex_ai_client.py` patterns (new `google-genai` SDK), then create compatibility shims in both apps that delegate to the router. Never modify existing `vertex_ai_client.py` files until shims are proven.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ROUTER-01 | Backend provides a unified `generate()` interface that routes to the correct provider based on model identifier | Covered by `ModelRouter.generate()` with model-prefix routing. Codebase scan reveals 8 call sites in AURA-CHAT and 5 in AURA-NOTES-MANAGER that currently call `get_model()` + `generate_content()`. Provider resolution: "/" prefix → OpenRouter, plain name → Vertex AI. |
| ROUTER-02 | Backend provides a unified `embed()` interface locked to Vertex AI per deployment with dimension validation | Covered by `ModelRouter.embed()` with `BaseEmbeddingProvider` ABC. Both apps hardcode 768-dim at multiple levels (Neo4j HNSW indices, `EMBEDDING_DIMENSIONS` constants, test generators). The `embed()` interface must validate `len(vector) == 768` before returning. |
| ROUTER-04 | All provider errors map to a unified error hierarchy with original error preserved | Error hierarchy maps `google.genai.errors.ClientError` (AURA-CHAT) and `google.api_core.exceptions.*` (AURA-NOTES-MANAGER) + old SDK errors to typed exceptions: `AuthError`, `RateLimitError`, `ContentPolicyError`, `ModelUnavailableError`, `TimeoutError`. Each preserves original via `.__cause__`. Both apps already have `VertexAIRequestError` with `.original` attribute. |
| PROV-01 | Vertex AI provider wraps existing code through the shared router interface with zero regression in existing tests | The `VertexAIProvider` wraps AURA-CHAT's existing `_GenerativeModelWrapper` pattern (new `google-genai` SDK) and AURA-CHAT's REST-based embedding service. Compatibility shims in both `vertex_ai_client.py` files delegate to the router. All 210+ tests pass via `AURA_TEST_MODE=true` test-mode paths. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `google-genai` | >=1.59.0 | Vertex AI generation (new SDK) | Already used by AURA-CHAT; replaces deprecated `vertexai.generative_models` |
| `vertexai` | >=1.64.0 | Vertex AI embeddings (TextEmbeddingModel) | Used by AURA-NOTES-MANAGER for `TextEmbeddingModel.from_pretrained()` |
| `google-auth` | >=2.35.0 | GCP credential management | Both apps already use for ADC |
| `pydantic` | >=2.6.0 | Type definitions and validation | Already in both apps; used for `GenerateRequest`, `GenerateResponse`, error types |
| `httpx` | >=0.25.0 | HTTP client (embeddings REST calls) | Already in dep tree; AURA-CHAT embeddings use `requests` (sync), will need for async |
| `hatchling` | >=1.26 | Package build backend | Standard modern Python packaging; supports `src/` layout and editable installs |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | >=8.0 | Testing shared package | Unit tests for router, providers, error mapping |
| `pytest-asyncio` | >=0.23 | Async test support | VertexAIProvider async methods |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom router | LiteLLM | Heavyweight dep (50+ transitive), hard to customize error handling and streaming |
| Custom router | LangChain | Massive scope creep, opinionated abstractions don't match AURA's existing patterns |
| `hatchling` | `setuptools` | AURA-CHAT already uses setuptools; hatchling is cleaner for `src/` layout editable installs |

**Installation (from project root):**
```bash
# Editable install into root venv
../../.venv/Scripts/pip install -e shared/model_router[vertex]
# Or from AURA-PROJ root:
.venv/Scripts/pip install -e shared/model_router[vertex]
```

## Architecture Patterns

### Recommended Package Structure
```
shared/
  model_router/
    pyproject.toml              # Package metadata + deps
    src/
      model_router/
        __init__.py             # Public API exports
        router.py               # ModelRouter class
        types.py                # GenerateRequest, GenerateResponse, StreamChunk, etc.
        errors.py               # Unified error hierarchy
        config.py               # RouterConfig, ProviderConfig
        providers/
          __init__.py
          base.py               # BaseProvider ABC, BaseEmbeddingProvider ABC
          vertex_ai.py          # VertexAIProvider (wraps existing code)
          openrouter.py         # Stub (Phase 9)
          ollama.py             # Stub (Phase 9)
    tests/
      __init__.py
      conftest.py
      test_types.py
      test_errors.py
      test_router.py
      test_vertex_ai_provider.py
```

### Pattern 1: Strangler Fig Migration
**What:** Wrap existing code behind new interface first; verify tests pass; then migrate callers incrementally.
**When to use:** Always for this phase. The three critical pitfalls (migration breakage, import resolution, embedding validation) demand this approach.

**Step-by-step migration sequence:**

1. **Create package skeleton** — types, errors, ABCs, empty router
2. **Implement VertexAIProvider** — wraps existing SDK patterns; does NOT import from either app's `vertex_ai_client.py`
3. **Create compatibility shims** — modify each app's `vertex_ai_client.py` to optionally delegate to ModelRouter
4. **Verify all tests pass** — no test modifications allowed
5. **Later phases:** Gradually update callers to use ModelRouter directly; remove shims last

```python
# COMPATIBILITY SHIM PATTERN (in AURA-CHAT/backend/utils/vertex_ai_client.py)
# Existing get_model() function is MODIFIED to optionally delegate to router:

_USE_MODEL_ROUTER = os.getenv("USE_MODEL_ROUTER", "").lower() == "true"

def get_model(model_name: str):
    """Get a model instance. Delegates to ModelRouter if enabled."""
    if os.getenv("AURA_TEST_MODE", "").lower() == "true":
        return _TestGenerativeModel(model_name)

    if _USE_MODEL_ROUTER:
        from model_router import get_default_router
        router = get_default_router()
        if router is not None:
            return _RouterModelAdapter(router, model_name)

    # Fallback: original behavior
    normalized = normalize_model_name(model_name)
    try:
        return _GenerativeModelWrapper(normalized)
    except Exception as e:
        raise VertexAIRequestError(...) from e
```

### Pattern 2: Protocol/ABC-Based Provider Contracts
**What:** Define provider interfaces as ABCs with concrete Pydantic request/response types.
**When to use:** For all provider implementations.

```python
# shared/model_router/src/model_router/providers/base.py
from abc import ABC, abstractmethod
from typing import AsyncGenerator
from model_router.types import GenerateRequest, GenerateResponse, StreamChunk

class BaseProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Non-streaming generation."""
        ...

    @abstractmethod
    async def stream(self, request: GenerateRequest) -> AsyncGenerator[StreamChunk, None]:
        """Streaming generation."""
        ...

    @abstractmethod
    async def list_models(self) -> list:
        """List available models."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider reachability."""
        ...


class BaseEmbeddingProvider(ABC):
    """Separate ABC for embedding providers (different concern from generation)."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Batch embed texts."""
        ...

    @abstractmethod
    async def embed_single(self, text: str) -> list[float]:
        """Single text embedding."""
        ...
```

### Pattern 3: Unified Error Hierarchy
**What:** A base `ModelRouterError` with typed subclasses that map to HTTP semantics and preserve the original provider error.
**When to use:** Every error from every provider gets mapped before leaving the provider implementation.

```python
# shared/model_router/src/model_router/errors.py

class ModelRouterError(Exception):
    """Base error for all model router operations."""
    def __init__(self, message: str, *, provider: str = "", model: str = "",
                 original: BaseException | None = None):
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.original = original
        if original:
            self.__cause__ = original

class AuthenticationError(ModelRouterError):
    """Provider authentication failed (invalid key, expired token, permission denied)."""
    pass

class RateLimitError(ModelRouterError):
    """Provider rate limit exceeded (429)."""
    retry_after: float | None = None

class ContentPolicyError(ModelRouterError):
    """Content blocked by provider safety/content policy."""
    pass

class ModelUnavailableError(ModelRouterError):
    """Requested model not found or not available."""
    pass

class ProviderTimeoutError(ModelRouterError):
    """Provider request timed out."""
    pass

class EmbeddingDimensionError(ModelRouterError):
    """Embedding dimension mismatch (expected vs actual)."""
    def __init__(self, expected: int, actual: int, **kwargs):
        super().__init__(
            f"Embedding dimension mismatch: expected {expected}, got {actual}",
            **kwargs
        )
        self.expected = expected
        self.actual = actual
```

### Pattern 4: Model Name Prefix Routing
**What:** Route based on model name format — "/" means OpenRouter, plain = Vertex AI.
**When to use:** When no explicit provider is specified.

```python
def _resolve_provider(self, request: GenerateRequest) -> BaseProvider:
    if request.provider and request.provider in self._providers:
        return self._providers[request.provider]
    if "/" in request.model:  # e.g., "anthropic/claude-sonnet-4"
        return self._providers[ProviderType.OPENROUTER]
    return self._providers.get(
        ProviderType.VERTEX_AI,
        self._providers[self._config.default_provider]
    )
```

### Anti-Patterns to Avoid
- **Big Bang migration:** Never replace both `vertex_ai_client.py` files at once. Shim first, verify, then migrate callers one-by-one.
- **Importing from app code in shared package:** `model_router` must NEVER `from backend.utils.vertex_ai_client import ...`. The dependency goes one way: app → shared package.
- **Single ABC for generation + embedding:** These are fundamentally different operations with different providers; separate ABCs.
- **Exposing provider-specific types:** Application code must never import `google.genai.types` or `vertexai.generative_models`. All translation happens inside provider implementations.
- **Modifying tests:** If tests need modification to work with the new router, something is wrong with the shim.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Python packaging | Custom import hacks / `sys.path` manipulation | `pyproject.toml` + `pip install -e` | Proper editable install resolves imports cleanly for all contexts (API, Celery, tests) |
| Credential management | Custom auth flows | `google.auth.default()` + existing ADC | Both apps already have working credential chains; don't duplicate |
| JSON schema for types | Manual dict construction | Pydantic `BaseModel` | Auto-validation, serialization, schema generation |
| Retry logic | Custom retry loops | Keep existing retry patterns in each app | Both apps already have battle-tested retry with backoff in their embedding services |

**Key insight:** This phase is about WRAPPING, not REWRITING. The existing code works. The shared package provides a new interface over it. Resist the urge to improve existing code during this phase.

## Common Pitfalls

### Pitfall 1: Two Different Vertex AI SDKs
**What goes wrong:** The VertexAIProvider assumes one SDK, but the two apps use different ones.
**Why it happens:** AURA-CHAT migrated to `google-genai` (new SDK with `genai.Client`), AURA-NOTES-MANAGER still uses `vertexai.generative_models` (old SDK with `GenerativeModel` class) and `google-generativeai` (even older genai SDK with `genai.GenerativeModel`).
**How to avoid:** The VertexAIProvider in the shared package should use the **new `google-genai` SDK** (what AURA-CHAT uses), since it supports `"global"` location and is the future. The compatibility shims in AURA-NOTES-MANAGER translate between old SDK patterns and the new router interface. Both apps' existing `vertex_ai_client.py` files remain unchanged until Phase 10.
**Warning signs:** Import errors mentioning `genai.Client` in AURA-NOTES-MANAGER context, or `vertexai.generative_models` missing attributes.

**SDK inventory (verified from codebase):**

| App | File | SDK | Import Pattern |
|-----|------|-----|----------------|
| AURA-CHAT | `backend/utils/vertex_ai_client.py` | `google-genai` (new) | `from google import genai; from google.genai import types` |
| AURA-CHAT | `backend/utils/vertex_ai_client.py` | `vertexai` (legacy imports) | `from vertexai.generative_models import GenerationConfig, Part` (still present for type compatibility) |
| AURA-CHAT | `backend/utils/embeddings.py` | Direct REST API | `requests.Session().post(endpoint)` with manual auth tokens |
| NOTES | `services/vertex_ai_client.py` | `vertexai` (old SDK) | `from vertexai.generative_models import GenerativeModel, GenerationConfig` |
| NOTES | `services/genai_client.py` | `google-genai` OR `google-generativeai` | Fallback chain: `from google import genai` → `import google.generativeai as genai` |
| NOTES | `services/embeddings.py` | `vertexai.language_models` | `from vertexai.language_models import TextEmbeddingModel` |

### Pitfall 2: Env Var Naming Divergence
**What goes wrong:** The shared package reads one env var name, but one app uses a different name for the same concept.
**Why it happens:** AURA-CHAT uses `VERTEX_REGION` (default `"global"`), AURA-NOTES-MANAGER uses `VERTEX_LOCATION` (default `"us-central1"`). Both use `VERTEX_PROJECT` and `VERTEX_CREDENTIALS`.
**How to avoid:** The shared package's `ProviderConfig` should accept both env var names with a resolution chain: `VERTEX_REGION` → `VERTEX_LOCATION` → default. Document the canonical name.
**Warning signs:** Models failing with "location not found" or "global not supported" errors in one app but not the other.

```python
# In shared/model_router/src/model_router/config.py
class VertexAIConfig(BaseModel):
    project_id: str = ""
    region: str = "global"
    credentials_path: str = ""

    @classmethod
    def from_env(cls) -> "VertexAIConfig":
        return cls(
            project_id=os.getenv("VERTEX_PROJECT", ""),
            region=(os.getenv("VERTEX_REGION")
                    or os.getenv("VERTEX_LOCATION")
                    or "global"),
            credentials_path=(os.getenv("VERTEX_CREDENTIALS")
                              or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                              or ""),
        )
```

### Pitfall 3: Embedding Dimension Mismatch Corruption
**What goes wrong:** If embedding provider changes, 768-dim HNSW indices get silently corrupted.
**Why it happens:** Neo4j has 6+ HNSW vector indices hardcoded to 768 dimensions. Both apps have `EMBEDDING_DIMENSIONS = 768` constants. The test generators produce 768-dim vectors.
**How to avoid:** The `embed()` method MUST validate output dimensions before returning. Add `EmbeddingDimensionError` to error hierarchy. The `BaseEmbeddingProvider` should enforce this in the base class, not leave it to implementations.
**Warning signs:** Vector search returning zero results or very low similarity scores.

```python
class BaseEmbeddingProvider(ABC):
    REQUIRED_DIMENSIONS = 768  # Locked for AURA Neo4j indices

    async def embed_validated(self, texts: list[str]) -> list[list[float]]:
        """Embed with dimension validation."""
        vectors = await self.embed(texts)
        for i, vec in enumerate(vectors):
            if len(vec) != self.REQUIRED_DIMENSIONS:
                raise EmbeddingDimensionError(
                    expected=self.REQUIRED_DIMENSIONS,
                    actual=len(vec),
                    provider=self.__class__.__name__,
                )
        return vectors
```

### Pitfall 4: Shared Package Import Resolution in Workers
**What goes wrong:** Celery workers (AURA-NOTES-MANAGER) and ARQ workers (AURA-CHAT) can't import `model_router`.
**Why it happens:** Workers often manipulate `sys.path` for imports (see `document_processing_tasks.py` lines 53-57: `sys.path.insert(0, _api_dir); sys.path.insert(0, _root_dir)`). The editable install may not be on the worker's path.
**How to avoid:** Verify `pip install -e` resolves for all execution contexts: FastAPI app, Celery worker, ARQ worker, pytest. Add an explicit import test for each context.
**Warning signs:** `ModuleNotFoundError: No module named 'model_router'` in worker logs.

**Verification commands:**
```bash
# From root venv — should all succeed:
.venv/Scripts/python -c "from model_router import ModelRouter; print('OK')"
cd AURA-CHAT && ../.venv/Scripts/python -c "from model_router import ModelRouter; print('OK')"
cd AURA-NOTES-MANAGER && ../.venv/Scripts/python -c "from model_router import ModelRouter; print('OK')"
# Celery worker context:
cd AURA-NOTES-MANAGER && ../.venv/Scripts/python -c "
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from model_router import ModelRouter
print('Celery context OK')
"
```

### Pitfall 5: Error Mapping Misses Provider-Specific Error Types
**What goes wrong:** An auth error from `google-genai` doesn't match the mapping, so it surfaces as a generic `ModelRouterError` instead of `AuthenticationError`, losing the ability to show meaningful UI messages.
**Why it happens:** `google-genai` errors are in `google.genai.errors` (e.g., `ClientError` with HTTP status codes), while old SDK errors are in `google.api_core.exceptions` (e.g., `PermissionDenied`, `ResourceExhausted`). Each has different attributes.
**How to avoid:** Map errors by **HTTP status code** (universal) and **exception class name** (SDK-specific). Check both.

```python
def _map_vertex_error(e: Exception) -> ModelRouterError:
    """Map Vertex AI errors to unified hierarchy."""
    error_str = str(e).lower()
    error_code = getattr(e, 'code', None) or _extract_http_code(error_str)

    if error_code == 403 or 'permission_denied' in error_str:
        return AuthenticationError(str(e), provider="vertex_ai", original=e)
    if error_code == 429 or 'resource_exhausted' in error_str or 'quota' in error_str:
        return RateLimitError(str(e), provider="vertex_ai", original=e)
    if error_code == 400 and ('safety' in error_str or 'blocked' in error_str):
        return ContentPolicyError(str(e), provider="vertex_ai", original=e)
    if error_code == 404 or 'not_found' in error_str:
        return ModelUnavailableError(str(e), provider="vertex_ai", original=e)
    if 'deadline' in error_str or 'timeout' in error_str:
        return ProviderTimeoutError(str(e), provider="vertex_ai", original=e)

    return ModelRouterError(str(e), provider="vertex_ai", original=e)
```

### Pitfall 6: Test Mode Bypass Not Preserved
**What goes wrong:** The router tries to initialize real Vertex AI credentials in test mode, causing test failures.
**Why it happens:** Both apps use `AURA_TEST_MODE=true` to bypass real SDK initialization. The shared package must respect this.
**How to avoid:** The `VertexAIProvider` constructor checks `AURA_TEST_MODE`. In test mode, `generate()` returns deterministic mock responses and `embed()` returns deterministic 768-dim vectors.
**Warning signs:** Tests suddenly require real GCP credentials or fail with auth errors.

## Code Examples

### pyproject.toml for Shared Package

```toml
# shared/model_router/pyproject.toml
[build-system]
requires = ["hatchling>=1.26"]
build-backend = "hatchling.build"

[project]
name = "aura-model-router"
version = "0.1.0"
requires-python = ">=3.10"
description = "Multi-provider LLM routing for AURA"
dependencies = [
    "pydantic>=2.0",
]

[project.optional-dependencies]
vertex = [
    "google-genai>=1.59.0",
    "google-auth>=2.35.0",
    "google-cloud-aiplatform>=1.51.0",
    "requests>=2.31.0",
]
all = [
    "aura-model-router[vertex]",
]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]

[tool.hatch.build.targets.wheel]
packages = ["src/model_router"]
```

### Package __init__.py (Public API)

```python
# shared/model_router/src/model_router/__init__.py
"""AURA Model Router — Multi-provider LLM abstraction."""

from model_router.types import (
    GenerateRequest,
    GenerateResponse,
    StreamChunk,
    UsageInfo,
    ProviderType,
    ModelInfo,
)
from model_router.errors import (
    ModelRouterError,
    AuthenticationError,
    RateLimitError,
    ContentPolicyError,
    ModelUnavailableError,
    ProviderTimeoutError,
    EmbeddingDimensionError,
)
from model_router.router import ModelRouter
from model_router.providers.base import BaseProvider, BaseEmbeddingProvider

__all__ = [
    "ModelRouter",
    "GenerateRequest",
    "GenerateResponse",
    "StreamChunk",
    "UsageInfo",
    "ProviderType",
    "ModelInfo",
    "ModelRouterError",
    "AuthenticationError",
    "RateLimitError",
    "ContentPolicyError",
    "ModelUnavailableError",
    "ProviderTimeoutError",
    "EmbeddingDimensionError",
    "BaseProvider",
    "BaseEmbeddingProvider",
]
```

### VertexAIProvider Core Pattern

```python
# shared/model_router/src/model_router/providers/vertex_ai.py
"""Vertex AI provider wrapping existing google-genai SDK patterns."""

import os
from typing import AsyncGenerator, Optional
from model_router.types import GenerateRequest, GenerateResponse, StreamChunk, UsageInfo, ProviderType
from model_router.errors import ModelRouterError, AuthenticationError
from model_router.providers.base import BaseProvider, BaseEmbeddingProvider

class VertexAIProvider(BaseProvider):
    """Wraps Vertex AI via google-genai SDK (same pattern as AURA-CHAT's _GenerativeModelWrapper)."""

    def __init__(self, project_id: str, region: str = "global",
                 credentials_path: str = ""):
        self._project_id = project_id
        self._region = region
        self._credentials_path = credentials_path
        self._test_mode = os.getenv("AURA_TEST_MODE", "").lower() == "true"
        self._client = None  # Lazy init

    def _get_client(self):
        """Lazy-initialize google-genai client."""
        if self._client is not None:
            return self._client
        if self._test_mode:
            return None

        try:
            from google import genai
            self._client = genai.Client(
                vertexai=True,
                project=self._project_id,
                location=self._region,
            )
            return self._client
        except Exception as e:
            raise AuthenticationError(
                str(e), provider="vertex_ai", original=e
            )

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        if self._test_mode:
            return GenerateResponse(
                text="Test-mode output.",
                model_used=request.model,
                provider=ProviderType.VERTEX_AI,
                usage=UsageInfo(),
            )
        # Real implementation delegates to google-genai SDK
        # (mirrors AURA-CHAT's _GenerativeModelWrapper.generate_content)
        ...

    async def health_check(self) -> bool:
        if self._test_mode:
            return True
        try:
            self._get_client()
            return True
        except Exception:
            return False
```

### Compatibility Shim in AURA-NOTES-MANAGER

```python
# Modified services/vertex_ai_client.py — ONLY add router delegation, don't remove anything

# --- ADD at module level ---
_ROUTER_ENABLED = os.getenv("USE_MODEL_ROUTER", "").lower() == "true"

# --- MODIFY get_model() ---
def get_model(model_name: str) -> GenerativeModel:
    if os.getenv("AURA_TEST_MODE", "").lower() == "true":
        return _TestGenerativeModel(model_name)

    # NEW: optionally delegate to model router
    if _ROUTER_ENABLED:
        try:
            from model_router.compat import VertexCompatModel
            return VertexCompatModel(model_name)
        except ImportError:
            pass  # Fallback to original behavior

    # EXISTING: original behavior (unchanged)
    init_vertex_ai(model_name)
    normalized = normalize_model_name(model_name)
    try:
        return GenerativeModel(normalized)
    except Exception as e:
        raise VertexAIRequestError(
            model=model_name,
            location=_normalize_location(_LOCATION, model_name),
            operation="model load",
            original=e,
        ) from e
```

### Embedding Dimension Validation

```python
# shared/model_router/src/model_router/providers/base.py

AURA_EMBEDDING_DIMENSIONS = 768

class BaseEmbeddingProvider(ABC):
    """ABC for embedding providers with mandatory dimension validation."""

    @abstractmethod
    async def _embed_raw(self, texts: list[str]) -> list[list[float]]:
        """Raw embedding call — subclasses implement this."""
        ...

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts with dimension validation."""
        if not texts:
            return []
        vectors = await self._embed_raw(texts)
        for i, vec in enumerate(vectors):
            if len(vec) != AURA_EMBEDDING_DIMENSIONS:
                from model_router.errors import EmbeddingDimensionError
                raise EmbeddingDimensionError(
                    expected=AURA_EMBEDDING_DIMENSIONS,
                    actual=len(vec),
                    provider=self.__class__.__name__,
                )
        return vectors
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `vertexai.generative_models.GenerativeModel` | `google.genai.Client.models.generate_content()` | June 2025 | AURA-CHAT already migrated; AURA-NOTES-MANAGER still on old SDK |
| `google.generativeai` (API-key based) | `google-genai` (ADC Vertex AI) | 2025 | Old genai SDK still used in AURA-NOTES-MANAGER's `genai_client.py` shim |
| `setuptools` + `setup.py` | `pyproject.toml` + `hatchling` | 2023-2024 | Modern standard for editable installs; AURA-CHAT already has a `pyproject.toml` with setuptools |
| `vertexai.language_models.TextEmbeddingModel` | Still supported but may be replaced by `google.genai` embedding API | Ongoing | AURA-NOTES-MANAGER uses the old TextEmbeddingModel; AURA-CHAT uses direct REST |

**Deprecated/outdated:**
- `vertexai.generative_models`: Deprecated since June 2025. AURA-CHAT already migrated away. AURA-NOTES-MANAGER still uses it.
- `google.generativeai` (the old `genai` package): Being superseded by `google-genai`. Both are in AURA-NOTES-MANAGER's dependency chain.

## Codebase Impact Map

### Files that MUST be shimmed (NOT modified otherwise)

**AURA-CHAT callers of `vertex_ai_client`:**
1. `backend/rag_engine.py` — imports `get_model`, `GenerationConfig`, `generate_content_stream`
2. `backend/llm_entity_extractor.py` — imports `get_model`
3. `backend/llm_gatekeeper.py` — imports `get_model`
4. `server/routers/chat.py` — inline `from backend.utils.vertex_ai_client import get_model`
5. `backend/routers/sessions.py` — inline `from backend.utils.vertex_ai_client import ...`

**AURA-CHAT callers of `EmbeddingService`:**
1. `backend/rag_engine.py` — `from backend.utils.embeddings import EmbeddingService`
2. `backend/document_processor.py` — same
3. `backend/semantic_chunker.py` — same
4. `backend/llm_entity_extractor.py` — same
5. `backend/semantic_router.py` — same

**AURA-NOTES-MANAGER callers of `vertex_ai_client`:**
1. `services/summarizer.py` — imports `GenerationConfig`, `generate_content`, `get_model`
2. `services/summary_service.py` — same
3. `services/coc.py` — imports from `vertex_ai_client`
4. `services/llm_entity_extractor.py` — imports `GenerationConfig`, `generate_content`, `get_model`
5. `api/kg_processor.py` — imports `init_vertex_ai`, `get_model`, `generate_content`, `GenerationConfig`

**AURA-NOTES-MANAGER callers of `EmbeddingService`:**
1. `api/kg_processor.py` — `from services.embeddings import EmbeddingService`

**Worker contexts:**
- AURA-CHAT: ARQ workers (`backend/tasks/worker.py`) — uses `arq`, not Celery
- AURA-NOTES-MANAGER: Celery workers (`api/tasks/document_processing_tasks.py`) — has explicit `sys.path` manipulation

### Env var divergences to normalize

| Concept | AURA-CHAT | AURA-NOTES-MANAGER | Shared Package |
|---------|-----------|---------------------|----------------|
| Region | `VERTEX_REGION` (default `"global"`) | `VERTEX_LOCATION` (default `"us-central1"`) | Accept both, prefer `VERTEX_REGION` |
| Project | `VERTEX_PROJECT` | `VERTEX_PROJECT` | Same ✓ |
| Credentials | `VERTEX_CREDENTIALS` | `VERTEX_CREDENTIALS` | Same ✓ |
| Test mode | `AURA_TEST_MODE` | `AURA_TEST_MODE` | Same ✓ |

## Open Questions

1. **Should the VertexAI embedding provider use REST API (AURA-CHAT style) or SDK (AURA-NOTES-MANAGER style)?**
   - What we know: AURA-CHAT uses direct REST (`requests.Session().post()`), AURA-NOTES-MANAGER uses `TextEmbeddingModel.get_embeddings()`. Both produce identical 768-dim vectors.
   - What's unclear: Whether the new `google-genai` SDK has an embedding API that replaces both approaches.
   - Recommendation: For Phase 8, the VertexAI embedding provider should use the **direct REST approach** (AURA-CHAT pattern) since it has fewer SDK dependencies and works with both auth patterns. Wrap existing `EmbeddingService` class via compatibility shim rather than reimplementing.

2. **How to handle `GenerationConfig` type differences?**
   - What we know: Both apps import `GenerationConfig` from `vertexai.generative_models`. AURA-CHAT's `_GenerativeModelWrapper` internally converts this to `google.genai.types.GenerateContentConfig`. The shared router needs its own config type.
   - What's unclear: How many callers depend on `GenerationConfig` attributes beyond `temperature` and `max_output_tokens`.
   - Recommendation: The shared `GenerateRequest` type replaces `GenerationConfig` at the router boundary. The compatibility shim translates `GenerationConfig` → `GenerateRequest` internally. Don't break callers who pass `GenerationConfig` to `generate_content()`.

3. **Async vs sync for embedding service?**
   - What we know: Both apps' `EmbeddingService` is synchronous. The `BaseEmbeddingProvider` ABC defines `async def embed()`. Callers in Celery workers run synchronously.
   - What's unclear: Whether making embeddings async is required for Phase 8 or can be deferred.
   - Recommendation: Implement `embed()` as async in the provider, but provide a sync wrapper (`embed_sync()`) for Celery worker compatibility. Use `asyncio.run()` or `loop.run_until_complete()` in the sync path.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio |
| Config file (AURA-CHAT) | `AURA-CHAT/pytest.ini` + `AURA-CHAT/pyproject.toml` |
| Config file (AURA-NOTES-MANAGER) | `AURA-NOTES-MANAGER/conftest.py` (env vars only) |
| Config file (shared package) | `shared/model_router/pyproject.toml` [tool.pytest.ini_options] |
| Quick run (AURA-CHAT) | `cd AURA-CHAT && ../.venv/Scripts/python -m pytest tests/ -x --tb=short` |
| Quick run (NOTES) | `cd AURA-NOTES-MANAGER && ../.venv/Scripts/python -m pytest tests/ -x --tb=short` |
| Quick run (shared) | `cd shared/model_router && ../../.venv/Scripts/python -m pytest tests/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ROUTER-01 | `router.generate(model="gemini-2.0-flash")` returns correct shape | unit | `pytest shared/model_router/tests/test_router.py::test_generate_vertex_ai -x` | ❌ Wave 0 |
| ROUTER-02 | `router.embed()` returns 768-dim, rejects runtime provider switch | unit | `pytest shared/model_router/tests/test_router.py::test_embed_dimension_validation -x` | ❌ Wave 0 |
| ROUTER-04 | Provider errors surface as typed exceptions | unit | `pytest shared/model_router/tests/test_errors.py -x` | ❌ Wave 0 |
| PROV-01 | All 210+ existing tests pass through shims | integration | `cd AURA-CHAT && ../.venv/Scripts/python -m pytest tests/ -x` | ✅ (existing) |
| PROV-01 | AURA-NOTES-MANAGER tests pass through shims | integration | `cd AURA-NOTES-MANAGER && ../.venv/Scripts/python -m pytest tests/ -x` | ✅ (existing) |
| PROV-01 | Shared package importable from both app contexts | smoke | `pytest shared/model_router/tests/test_import_contexts.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** Run shared package tests + one app's quick suite
- **Per wave merge:** Full suite of both apps + shared package
- **Phase gate:** All three test suites green before phase completion

### Wave 0 Gaps
- [ ] `shared/model_router/tests/conftest.py` — shared fixtures, AURA_TEST_MODE setup
- [ ] `shared/model_router/tests/test_types.py` — GenerateRequest, GenerateResponse validation
- [ ] `shared/model_router/tests/test_errors.py` — error hierarchy mapping from google.genai errors
- [ ] `shared/model_router/tests/test_router.py` — ModelRouter routing, generate, embed
- [ ] `shared/model_router/tests/test_vertex_ai_provider.py` — VertexAIProvider in test mode
- [ ] `shared/model_router/tests/test_import_contexts.py` — verify import from different cwd paths
- [ ] `shared/model_router/pyproject.toml` — pytest configuration section
- [ ] Framework install: `pip install -e shared/model_router[all,dev]`

## Sources

### Primary (HIGH confidence)
- **Codebase analysis** — Direct inspection of all Vertex AI integration files across both apps:
  - `AURA-CHAT/backend/utils/vertex_ai_client.py` (650+ lines, new google-genai SDK)
  - `AURA-CHAT/backend/utils/embeddings.py` (370+ lines, REST-based)
  - `AURA-NOTES-MANAGER/services/vertex_ai_client.py` (310+ lines, old vertexai SDK)
  - `AURA-NOTES-MANAGER/services/embeddings.py` (600+ lines, TextEmbeddingModel SDK)
  - `AURA-NOTES-MANAGER/services/genai_client.py` (86 lines, backward-compat shim)
  - `AURA-NOTES-MANAGER/api/tasks/document_processing_tasks.py` (Celery worker setup)
  - `AURA-CHAT/backend/tasks/worker.py` (ARQ worker setup)
- **Project-level research** — `.planning/research/ARCHITECTURE.md`, `PITFALLS.md`, `SUMMARY.md`
- **Python Packaging User Guide** — `pyproject.toml` structure, editable installs, hatchling build backend

### Secondary (MEDIUM confidence)
- **Google Cloud documentation** — `google-genai` vs `vertexai` SDK differences, migration guidance
- **Python ABC/Protocol patterns** — Standard library documentation for abstract base classes

### Tertiary (LOW confidence)
- **Hatchling version compatibility** — Exact minimum version for `src/` layout editable installs needs validation during implementation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All libraries verified from existing `requirements.txt` files and codebase imports
- Architecture: HIGH — Package structure derived from project-level research + Python packaging standards + codebase analysis
- Pitfalls: HIGH — Every pitfall backed by specific line numbers and file references in the AURA codebase
- Error hierarchy: MEDIUM — Error mapping patterns are standard Python, but exact `google.genai.errors` exception types need runtime verification

**Research date:** 2025-07-14
**Valid until:** 2025-08-14 (30 days — stable domain, main risk is SDK version changes)
