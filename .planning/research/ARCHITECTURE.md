# Architecture Patterns: Multi-Provider LLM Integration

**Domain:** Multi-provider LLM abstraction layer for dual-app monorepo
**Researched:** 2026-03-10
**Overall Confidence:** HIGH (based on direct codebase analysis + official documentation)

---

## 1. Current Architecture (Baseline)

### How LLM Calls Work Today

Both applications have **independent, tightly-coupled Vertex AI integrations** with no shared code.

**AURA-CHAT** has two distinct LLM pathways:

| Pathway | Location | SDK | Used By |
|---------|----------|-----|---------|
| Modern wrapper | `backend/utils/vertex_ai_client.py` | `google-genai` (new SDK) via `_GenerativeModelWrapper` | RAG engine, chat router, LLM gatekeeper, entity extractor |
| Legacy shim | (deprecated Streamlit path) | `vertexai.generative_models` | Being migrated away |

Key functions: `get_model(model_name)` returns a `_GenerativeModelWrapper` that provides `generate_content()` and `generate_content_async()`. Also has `generate_content_stream()` for SSE streaming.

**AURA-NOTES-MANAGER** has a separate but structurally similar setup:

| Pathway | Location | SDK | Used By |
|---------|----------|-----|---------|
| Primary | `services/vertex_ai_client.py` | `vertexai.generative_models` (old SDK) | KG processor, summarizer, CoC, entity extractor |
| Shim | `services/genai_client.py` | `google.generativeai` or `google.genai` | Summarizer (thinking mode) |
| Embeddings | `services/embeddings.py` | `vertexai.language_models.TextEmbeddingModel` | KG processor |

### Current Call Sites (What Must Be Migrated)

**AURA-CHAT (8 direct callers of `get_model`):**
1. `backend/rag_engine.py` -- Chat generation (streaming + non-streaming)
2. `backend/llm_entity_extractor.py` -- Entity extraction during document processing
3. `backend/llm_gatekeeper.py` -- Intent re-classification (uses `gemini-2.5-flash-lite`)
4. `server/routers/chat.py` -- Chitchat streaming (inline `get_model` call)
5. `backend/routers/sessions.py` -- Session title generation
6. `backend/utils/vertex_ai_client.py` -- `generate_content_stream()` for SSE

**AURA-NOTES-MANAGER (5 direct callers):**
1. `services/summarizer.py` -- Note summarization (uses both `vertex_ai_client` and `genai_client`)
2. `services/summary_service.py` -- Summary generation
3. `services/coc.py` -- Transcript cleaning/auditing
4. `services/llm_entity_extractor.py` -- Entity extraction for KG
5. `api/kg_processor.py` -- KG processing pipeline (uses `vertex_ai_client` + `embeddings`)

**Embeddings (separate concern):**
- AURA-CHAT: `backend/utils/embeddings.py` (separate embedding client)
- AURA-NOTES-MANAGER: `services/embeddings.py` (`EmbeddingService` class with batching/rate-limiting)

### Current Dependency Injection Pattern

AURA-CHAT's `server/dependencies.py` uses module-level singletons with lazy initialization:

```python
_rag_engine: RAGEngine | None = None

def get_rag_engine() -> RAGEngine:
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine(graph_manager=get_graph_manager())
    return _rag_engine
```

The `RAGEngine` internally calls `get_model()` to get a Vertex AI model. Model selection happens at two levels:
1. **Config-level default:** `config.RAG_MODEL_DEFAULT` (currently `gemini-2.5-flash-lite`)
2. **Per-request override:** `request.model` field in `ChatRequest` schema

AURA-NOTES-MANAGER does NOT use FastAPI DI for AI services -- they are imported directly in service modules.

### Current Frontend Model Selection

AURA-CHAT already has an inline model selector in `InputArea.tsx`:
- Dropdown populated from `GET /chat/config` which returns `allowed_models` list
- Selected model passed in `ChatRequest.model` field
- Config includes thinking mode settings per model

AURA-NOTES-MANAGER has NO model selection UI -- models are hardcoded in config.

---

## 2. Recommended Architecture

### 2.1 Shared Model Router Package

**Location:** `shared/model_router/` at the project root (sibling to `AURA-CHAT/` and `AURA-NOTES-MANAGER/`)

**Why a shared package:** Both apps need the exact same provider abstraction. Duplicating means drift. A shared package installed via `pip install -e` keeps one source of truth while respecting the existing root `.venv` strategy.

```
AURA-PROJ/
  shared/
    model_router/
      pyproject.toml           # Package metadata
      src/
        model_router/
          __init__.py           # Public API: generate(), embed(), get_router()
          router.py             # ModelRouter class -- routes requests to providers
          config.py             # ProviderConfig, ModelConfig, RouterConfig
          types.py              # Shared types: GenerateRequest, GenerateResponse, etc.
          errors.py             # Unified error hierarchy
          usage.py              # Usage tracking types and accumulator
          providers/
            __init__.py
            base.py             # BaseProvider ABC
            vertex_ai.py        # VertexAIProvider (refactored from existing code)
            openrouter.py        # OpenRouterProvider (new)
            ollama.py           # OllamaProvider (stub)
          embeddings/
            __init__.py
            base.py             # BaseEmbeddingProvider ABC
            vertex_ai.py        # Vertex AI embeddings (refactored)
```

**Package `pyproject.toml`:**

```toml
[build-system]
requires = ["hatchling >= 1.26"]
build-backend = "hatchling.build"

[project]
name = "aura-model-router"
version = "0.1.0"
requires-python = ">=3.10"
description = "Multi-provider LLM routing for AURA"
dependencies = [
    "httpx>=0.25.0",          # For OpenRouter HTTP calls
    "pydantic>=2.0",          # Config and type validation
]

[project.optional-dependencies]
vertex = [
    "google-genai>=1.0.0",
    "vertexai>=1.0.0",
    "google-auth>=2.0.0",
]
openrouter = []               # Uses httpx (already in core deps)
ollama = [
    "ollama>=0.4.0",
]
all = [
    "aura-model-router[vertex,ollama]",
]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]

[tool.hatch.build.targets.wheel]
packages = ["src/model_router"]
```

**Installation into root venv:**

```bash
# From AURA-PROJ root, using root venv
.venv/Scripts/pip install -e shared/model_router[all]
```

This means both `AURA-CHAT` and `AURA-NOTES-MANAGER` can `from model_router import ...` because the package is installed in the shared root venv.

### 2.2 Core Abstractions

**BaseProvider ABC:**

```python
# shared/model_router/src/model_router/providers/base.py
from abc import ABC, abstractmethod
from model_router.types import (
    GenerateRequest, GenerateResponse,
    StreamChunk, ProviderCapabilities,
)
from typing import AsyncGenerator

class BaseProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Generate a completion (non-streaming)."""
        ...

    @abstractmethod
    async def stream(self, request: GenerateRequest) -> AsyncGenerator[StreamChunk, None]:
        """Generate a streaming completion."""
        ...

    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Return what this provider supports (models, streaming, thinking, etc.)."""
        ...

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """List available models for this provider."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is reachable."""
        ...
```

**BaseEmbeddingProvider ABC (separate from generation):**

```python
class BaseEmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        ...

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a search query (may apply normalization)."""
        ...
```

**Why separate generation and embedding providers:** Embedding models are fundamentally different from chat models. The AURA codebase already treats them separately (separate files, separate classes). Forcing them into one interface creates leaky abstractions. Embeddings are also unlikely to need multi-provider routing in v1.1 -- Vertex AI text-embedding-004 is deeply integrated into Neo4j's HNSW indices and switching would require re-indexing.

**Unified Types:**

```python
# shared/model_router/src/model_router/types.py
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class ProviderType(str, Enum):
    VERTEX_AI = "vertex_ai"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"

class GenerateRequest(BaseModel):
    """Provider-agnostic generation request."""
    prompt: str | None = None
    messages: list[dict] | None = None     # OpenAI-style messages
    model: str                              # e.g., "gemini-2.5-flash" or "openai/gpt-4o"
    provider: ProviderType | None = None    # Explicit provider; None = auto-route
    temperature: float = 0.7
    max_tokens: int = 4096
    system_instruction: str | None = None
    thinking_budget: int | None = None      # For models that support thinking
    response_format: str | None = None      # "json" for structured output
    stream: bool = False

class GenerateResponse(BaseModel):
    """Provider-agnostic generation response."""
    text: str
    model_used: str
    provider: ProviderType
    usage: UsageInfo
    thought_summary: str | None = None
    finish_reason: str | None = None

class UsageInfo(BaseModel):
    """Token usage and cost tracking."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float | None = None          # Estimated cost (from OpenRouter pricing)
    cached_tokens: int = 0

class StreamChunk(BaseModel):
    """Single chunk from streaming response."""
    type: str                               # "content", "thinking", "error", "complete"
    text: str = ""
    usage: UsageInfo | None = None          # Present on "complete" chunk

class ModelInfo(BaseModel):
    """Model metadata for discovery UI."""
    id: str                                 # e.g., "gemini-2.5-flash" or "anthropic/claude-3.5-sonnet"
    name: str                               # Human-readable name
    provider: ProviderType
    context_length: int
    supports_streaming: bool = True
    supports_thinking: bool = False
    pricing: ModelPricing | None = None

class ModelPricing(BaseModel):
    """Per-token pricing info (primarily from OpenRouter)."""
    prompt_per_million: float               # USD per 1M prompt tokens
    completion_per_million: float           # USD per 1M completion tokens
```

### 2.3 ModelRouter (Central Orchestrator)

```python
# shared/model_router/src/model_router/router.py

class ModelRouter:
    """Routes generation requests to the appropriate provider.

    Resolution order:
    1. Explicit provider in request
    2. Model prefix routing (e.g., "openai/..." -> OpenRouter)
    3. Configured default provider
    4. First healthy provider
    """

    def __init__(self, config: RouterConfig):
        self._providers: dict[ProviderType, BaseProvider] = {}
        self._embedding_providers: dict[ProviderType, BaseEmbeddingProvider] = {}
        self._config = config
        self._usage_tracker = UsageTracker()

    def register_provider(self, provider_type: ProviderType, provider: BaseProvider):
        self._providers[provider_type] = provider

    def register_embedding_provider(self, ptype: ProviderType, provider: BaseEmbeddingProvider):
        self._embedding_providers[ptype] = provider

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        provider = self._resolve_provider(request)
        response = await provider.generate(request)
        self._usage_tracker.record(response.usage, response.provider, response.model_used)
        return response

    async def stream(self, request: GenerateRequest) -> AsyncGenerator[StreamChunk, None]:
        provider = self._resolve_provider(request)
        async for chunk in provider.stream(request):
            if chunk.type == "complete" and chunk.usage:
                self._usage_tracker.record(chunk.usage, request.provider, request.model)
            yield chunk

    async def embed(self, texts: list[str], provider: ProviderType | None = None) -> list[list[float]]:
        ptype = provider or self._config.default_embedding_provider
        return await self._embedding_providers[ptype].embed(texts)

    async def list_all_models(self) -> list[ModelInfo]:
        models = []
        for provider in self._providers.values():
            models.extend(await provider.list_models())
        return models

    def _resolve_provider(self, request: GenerateRequest) -> BaseProvider:
        # 1. Explicit provider
        if request.provider and request.provider in self._providers:
            return self._providers[request.provider]
        # 2. Model prefix routing
        if "/" in request.model:
            # OpenRouter uses "org/model" format
            return self._providers[ProviderType.OPENROUTER]
        # 3. Model name matching against known provider models
        for ptype, provider in self._providers.items():
            if self._model_belongs_to(request.model, ptype):
                return self._providers[ptype]
        # 4. Default
        return self._providers[self._config.default_provider]
```

### 2.4 Provider Implementations

#### VertexAIProvider (Refactored from Existing Code)

This is NOT a rewrite -- it wraps the existing `_GenerativeModelWrapper` pattern from `backend/utils/vertex_ai_client.py`:

```python
class VertexAIProvider(BaseProvider):
    """Wraps existing Vertex AI integration into provider interface.

    Reuses existing authentication, location routing, and model wrapper logic.
    """

    def __init__(self, project_id: str, region: str = "global", credentials_path: str | None = None):
        self._project_id = project_id
        self._region = region
        self._credentials_path = credentials_path
        self._client: genai.Client | None = None

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        # Translate GenerateRequest -> google-genai call
        # Reuse existing location routing logic (resolve_model_location)
        # Reuse existing thinking config building (_build_stream_thinking_config)
        ...

    async def stream(self, request: GenerateRequest) -> AsyncGenerator[StreamChunk, None]:
        # Reuse existing generate_content_stream() logic
        # Normalize chunks via _normalize_stream_chunk pattern
        ...

    async def list_models(self) -> list[ModelInfo]:
        # Return static list from config (Vertex doesn't have model discovery API)
        # Match existing RAG_ALLOWED_MODELS + CHAT_MODELS_WITH_THINKING
        ...
```

**Migration strategy:** The VertexAIProvider wraps existing functionality. The old `vertex_ai_client.py` files continue to exist during migration. The provider calls through them initially, then we gradually move logic inside.

#### OpenRouterProvider (New)

```python
class OpenRouterProvider(BaseProvider):
    """OpenRouter: 200+ models via OpenAI-compatible API."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str, app_name: str = "AURA", default_model: str = "openai/gpt-4o-mini"):
        self._api_key = api_key
        self._app_name = app_name
        self._default_model = default_model
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://aura-learning.dev",
                "X-OpenRouter-Title": app_name,
            },
            timeout=60.0,
        )

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        # POST /chat/completions with OpenAI-compatible format
        payload = {
            "model": request.model,
            "messages": self._build_messages(request),
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        response = await self._client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
        return self._parse_response(data, request.model)

    async def stream(self, request: GenerateRequest) -> AsyncGenerator[StreamChunk, None]:
        # POST /chat/completions with stream=True, parse SSE
        ...

    async def list_models(self) -> list[ModelInfo]:
        # GET /models returns full model catalog with pricing
        response = await self._client.get("/models")
        data = response.json()
        return [self._parse_model(m) for m in data.get("data", [])]

    async def get_credits(self) -> float:
        # GET /auth/key returns remaining credits
        response = await self._client.get("/auth/key")
        return response.json().get("data", {}).get("limit_remaining", 0.0)
```

**Why `httpx` over `openai` SDK:** OpenRouter's API is OpenAI-compatible, but using the OpenAI SDK adds a heavy transitive dependency and version-coupling. `httpx` is already in the project's requirements. The OpenRouter API surface needed (completions, models, credits) is simple enough for direct HTTP calls. This also avoids confusion between "OpenAI the SDK" and "OpenAI the provider via OpenRouter."

#### OllamaProvider (Stub)

```python
class OllamaProvider(BaseProvider):
    """Local LLM via Ollama. Stub implementation for v1.1."""

    def __init__(self, host: str = "http://localhost:11434"):
        self._host = host
        self._available = False

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        raise NotImplementedError("Ollama provider is a stub in v1.1. Pull models locally and implement in v1.2.")

    async def health_check(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(f"{self._host}/api/tags")
                self._available = r.status_code == 200
                return self._available
        except Exception:
            self._available = False
            return False

    async def list_models(self) -> list[ModelInfo]:
        """List locally available models (if Ollama is running)."""
        if not self._available:
            return []
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{self._host}/api/tags")
            data = r.json()
            return [
                ModelInfo(
                    id=m["name"], name=m["name"],
                    provider=ProviderType.OLLAMA,
                    context_length=m.get("details", {}).get("context_length", 4096),
                )
                for m in data.get("models", [])
            ]
```

**Why a stub, not full implementation:** Ollama requires local GPU, model downloads, and has fundamentally different performance characteristics. The interface and health check are useful for v1.1 (show Ollama status in settings). Full generation deferred to v1.2.

---

## 3. Integration with Existing Architecture

### 3.1 Handling the Dual Backend in AURA-CHAT

AURA-CHAT has `server/` (modern FastAPI) and `backend/` (legacy processing). The Model Router integrates at the `server/` level:

```
server/dependencies.py          <-- NEW: get_model_router() dependency
  |
  v
server/routers/chat.py          <-- Uses ModelRouter instead of direct get_model()
  |
  v
backend/rag_engine.py           <-- Accepts ModelRouter as constructor arg
  |                                  (replaces internal get_model() calls)
  v
backend/llm_gatekeeper.py       <-- Accepts ModelRouter or generate function
backend/llm_entity_extractor.py <-- Same pattern
```

**Key principle:** The `server/` layer owns the ModelRouter singleton. The `backend/` layer receives it via constructor injection, NOT by importing it directly. This preserves the existing test-mode patterns (mock injection) and avoids import cycles.

**Modified `dependencies.py`:**

```python
# In server/dependencies.py
from model_router import ModelRouter, VertexAIProvider, OpenRouterProvider, OllamaProvider

_model_router: ModelRouter | None = None

def get_model_router() -> ModelRouter:
    global _model_router
    if os.getenv("AURA_TEST_MODE", "").lower() == "true":
        return None  # type: ignore
    if _model_router is None:
        router = ModelRouter(config=_load_router_config())
        # Register providers
        router.register_provider(ProviderType.VERTEX_AI, VertexAIProvider(...))
        if os.getenv("OPENROUTER_API_KEY"):
            router.register_provider(ProviderType.OPENROUTER, OpenRouterProvider(...))
        router.register_provider(ProviderType.OLLAMA, OllamaProvider())
        _model_router = router
    return _model_router

def get_rag_engine() -> RAGEngine:
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine(
            graph_manager=get_graph_manager(),
            model_router=get_model_router(),  # NEW: inject router
        )
    return _rag_engine
```

### 3.2 AURA-NOTES-MANAGER Integration

AURA-NOTES-MANAGER does not use FastAPI DI for AI services. The integration pattern differs:

```python
# In AURA-NOTES-MANAGER/api/dependencies.py (new file or extended)
from model_router import ModelRouter

_model_router: ModelRouter | None = None

def get_model_router() -> ModelRouter:
    # Same pattern as AURA-CHAT
    ...

# Services accept router as parameter
class SummaryService:
    def __init__(self, model_router: ModelRouter):
        self._router = model_router

    async def summarize(self, text: str, model: str | None = None) -> str:
        response = await self._router.generate(GenerateRequest(
            prompt=text,
            model=model or "gemini-2.5-flash-lite",
            system_instruction=SUMMARY_PROMPT,
        ))
        return response.text
```

**Migration approach for AURA-NOTES-MANAGER:** Services currently import `from services.vertex_ai_client import get_model, generate_content`. The migration:

1. Keep `services/vertex_ai_client.py` as a thin compatibility shim that delegates to ModelRouter
2. Gradually update services to accept ModelRouter directly
3. Once all services use ModelRouter, remove the shim

### 3.3 FastAPI Dependency Injection for Provider Routing

**New endpoint for provider/model discovery:**

```python
# In both apps: routers/providers.py
from fastapi import APIRouter, Depends
from model_router import ModelRouter
from server.dependencies import get_model_router

router = APIRouter(prefix="/providers", tags=["Providers"])

@router.get("/models")
async def list_models(router: ModelRouter = Depends(get_model_router)):
    """List all available models across all providers."""
    models = await router.list_all_models()
    return {"models": [m.model_dump() for m in models]}

@router.get("/health")
async def provider_health(router: ModelRouter = Depends(get_model_router)):
    """Check health of all registered providers."""
    health = {}
    for ptype, provider in router._providers.items():
        health[ptype.value] = await provider.health_check()
    return {"providers": health}

@router.get("/usage")
async def get_usage(router: ModelRouter = Depends(get_model_router)):
    """Get usage statistics."""
    return router.get_usage_summary()
```

### 3.4 Frontend Component Sharing Between React 18 and 19

**Problem:** AURA-CHAT uses React 19 + Vite 7, AURA-NOTES-MANAGER uses React 18 + Vite 6. Shared UI components must work with both.

**Do NOT create a shared npm package.** The version gap and build tool differences make this fragile. Instead:

**Pattern: Copy-with-convention.** Build provider UI components in AURA-CHAT first (it has the more complex model selection needs), then copy to AURA-NOTES-MANAGER with minimal adaptation.

**Why this works for AURA:**
- Both apps use TailwindCSS with the same Cyber Yellow theme
- Both use TanStack Query for server state
- Both use Zustand for client state
- The UI divergence is small (React 18 vs 19 hooks are compatible)
- React 19 features used in AURA-CHAT (like `use()`) are NOT needed for provider selection UI

**Components to build (in feature-based structure):**

```
# AURA-CHAT
client/src/features/providers/
  components/
    ProviderSelector.tsx      # 2-level (Vertex/Ollama) or 3-level (OpenRouter) selector
    ModelSelector.tsx          # Dropdown with model metadata (context length, pricing)
    ProviderSettings.tsx       # Global defaults settings panel
    UsageDashboard.tsx         # Cost tracking and budget display
    ProviderStatusBadge.tsx    # Health indicator per provider
  hooks/
    useProviders.ts            # TanStack Query hook for GET /providers/models
    useProviderConfig.ts       # Zustand store for provider preferences
    useUsage.ts                # TanStack Query hook for GET /providers/usage
  types/
    index.ts                   # Provider, Model, Usage types

# AURA-NOTES-MANAGER (copy + adapt)
frontend/src/features/providers/
  components/
    ProviderSelector.tsx       # Simplified version (no inline selector needed)
    ProviderSettings.tsx       # Global settings for summarization/extraction models
  hooks/
    useProviders.ts
    useProviderConfig.ts
```

### 3.5 State Management for Provider Configuration

**Zustand store for provider preferences (client-side):**

```typescript
// features/providers/hooks/useProviderConfig.ts
interface ProviderConfigState {
  // Global defaults (persisted to Firestore via API)
  defaultProvider: ProviderType;
  defaultModel: string;
  defaultEmbeddingModel: string;

  // Per-session overrides (local, transient)
  sessionOverrides: Record<string, { provider?: ProviderType; model?: string }>;

  // Actions
  setDefaultProvider: (provider: ProviderType) => void;
  setDefaultModel: (model: string) => void;
  setSessionOverride: (sessionId: string, override: { provider?: ProviderType; model?: string }) => void;
  clearSessionOverride: (sessionId: string) => void;
}
```

**Configuration hierarchy (backend):**

```
1. Per-request override (ChatRequest.model + ChatRequest.provider)
   |
   v  (fallback if not set)
2. Per-session override (stored in Firestore session doc)
   |
   v  (fallback if not set)
3. User global default (stored in Firestore user preferences)
   |
   v  (fallback if not set)
4. System default (from env vars / config.py)
```

**Firestore schema additions:**

```
# User preferences (new collection or sub-document)
users/{uid}/preferences:
  default_provider: "vertex_ai"
  default_model: "gemini-2.5-flash"
  budget_limit_usd: 10.00

# Session override (added to existing session document)
sessions/{session_id}:
  ... (existing fields)
  provider_override: "openrouter"
  model_override: "anthropic/claude-3.5-sonnet"
```

### 3.6 API Endpoint Design

**New endpoints (both apps):**

| Method | Path | Purpose | Response |
|--------|------|---------|----------|
| `GET` | `/providers/models` | List all models across all providers | `{ models: ModelInfo[] }` |
| `GET` | `/providers/models?provider=openrouter` | Filter by provider | `{ models: ModelInfo[] }` |
| `GET` | `/providers/health` | Provider health status | `{ providers: { vertex_ai: true, openrouter: true, ollama: false } }` |
| `GET` | `/providers/usage` | Usage statistics | `{ total_cost_usd, by_provider: {...}, by_model: {...} }` |
| `GET` | `/providers/credits` | OpenRouter credit balance | `{ balance_usd: 12.50 }` |
| `GET` | `/config/provider` | Get user's provider preferences | `{ default_provider, default_model }` |
| `PUT` | `/config/provider` | Update provider preferences | Same |

**Modified existing endpoints:**

| Method | Path | Change |
|--------|------|--------|
| `POST` | `/chat` | Add optional `provider` field to `ChatRequest` |
| `POST` | `/chat/stream` | Same |
| `GET` | `/chat/config` | Extend to include provider info alongside model info |

---

## 4. Data Flow

### 4.1 Chat Request with Provider Selection

```
[Frontend]
  User selects model in InputArea dropdown
  (model: "anthropic/claude-3.5-sonnet", provider: auto-detected from "/" prefix)
    |
    v
[POST /chat/stream]
  ChatRequest { message, session_id, model: "anthropic/claude-3.5-sonnet" }
    |
    v
[server/routers/chat.py]
  rag_engine = Depends(get_rag_engine)  // has ModelRouter injected
    |
    v
[backend/rag_engine.py]
  self.model_router.stream(GenerateRequest(
      model="anthropic/claude-3.5-sonnet",
      messages=[...],  // conversation history + RAG context
      system_instruction=ACADEMIC_SYSTEM_PROMPT,
  ))
    |
    v
[model_router/router.py]
  _resolve_provider("anthropic/claude-3.5-sonnet")
    -> "/" detected -> OpenRouterProvider
    |
    v
[model_router/providers/openrouter.py]
  POST https://openrouter.ai/api/v1/chat/completions
    { model: "anthropic/claude-3.5-sonnet", messages: [...], stream: true }
    |
    v
[SSE response chunks]
  -> normalized to StreamChunk -> yielded back through chain
  -> usage tracked in UsageTracker
```

### 4.2 Model Discovery Flow

```
[Frontend Settings Page]
  useProviders() hook -> GET /providers/models
    |
    v
[server/routers/providers.py]
  router.list_all_models()
    |
    +-> VertexAIProvider.list_models()   -> [gemini-2.5-flash, gemini-3-flash-preview, ...]
    +-> OpenRouterProvider.list_models() -> [anthropic/claude-3.5-sonnet, openai/gpt-4o, ...]
    +-> OllamaProvider.list_models()     -> [llama3.2:latest, ...] (if running)
    |
    v
  Combined list returned to frontend
  Frontend groups by provider for hierarchical display
```

---

## 5. Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `model_router` (shared package) | Provider abstraction, request routing, usage tracking | All providers, config store |
| `VertexAIProvider` | Vertex AI SDK wrapper (generation + streaming) | Google Cloud APIs |
| `OpenRouterProvider` | OpenRouter API client | OpenRouter REST API |
| `OllamaProvider` | Local LLM detection and stub | Local Ollama server |
| `server/dependencies.py` (AURA-CHAT) | DI registration, singleton management | ModelRouter, RAGEngine |
| `api/dependencies.py` (AURA-NOTES-MANAGER) | Same for notes app | ModelRouter, services |
| `routers/providers.py` (both apps) | REST API for provider discovery/config | ModelRouter |
| `features/providers/` (frontend) | UI for provider selection, settings, usage | Backend API |
| Firestore | Provider preferences persistence | Both app backends |

---

## 6. Patterns to Follow

### Pattern 1: Provider-Agnostic Request/Response
**What:** All code outside `model_router/providers/` uses only `GenerateRequest`/`GenerateResponse` types. Never import provider-specific SDKs in application code.
**When:** Always -- this is the core abstraction contract.

### Pattern 2: Constructor Injection over Import-Time Coupling
**What:** Services receive `ModelRouter` as a constructor parameter, not by importing a global singleton.
**When:** For all backend services that make LLM calls (RAGEngine, Summarizer, EntityExtractor, etc.).
**Why:** Testability. Existing tests mock `get_model` via `patch()`. With DI, tests pass a mock router directly.

### Pattern 3: Compatibility Shim for Gradual Migration
**What:** Keep existing `vertex_ai_client.py` files during migration. Add a thin shim that delegates to ModelRouter.
**When:** During the migration phase. Remove after all callers are updated.

```python
# TEMPORARY shim in backend/utils/vertex_ai_client.py
def get_model(model_name: str):
    """Legacy compatibility shim. Delegates to ModelRouter."""
    from server.dependencies import get_model_router
    router = get_model_router()
    if router is None:
        # Test mode fallback
        return _TestGenerativeModel(model_name)
    return _RouterModelAdapter(router, model_name)
```

### Pattern 4: Model Name Routing Convention
**What:** Model names with "/" (e.g., "anthropic/claude-3.5-sonnet") route to OpenRouter. Plain names (e.g., "gemini-2.5-flash") route to Vertex AI. Names matching Ollama format route to Ollama.
**When:** When no explicit provider is specified in the request.
**Why:** Intuitive, zero-config routing that matches how users think about models.

### Pattern 5: Fail-Safe to Default Provider
**What:** If the requested provider is unhealthy or the model is unavailable, fall back to the system default (Vertex AI).
**When:** Any provider error.
**Why:** Academic use case demands reliability. A student mid-study-session cannot wait for provider recovery.

---

## 7. Anti-Patterns to Avoid

### Anti-Pattern 1: Shared npm Package for React Components
**What:** Creating a `shared/ui/` npm package consumed by both frontends.
**Why bad:** React 18 vs 19 version mismatch causes hydration/hook issues. Vite 6 vs 7 build differences. Two separate `node_modules` trees with conflicting React versions.
**Instead:** Copy-with-convention. Build in AURA-CHAT first, copy to AURA-NOTES-MANAGER. The provider UI surface is small enough that duplication is cheaper than the abstraction.

### Anti-Pattern 2: Single Provider ABC for Both Generation and Embedding
**What:** One `BaseProvider` with both `generate()` and `embed()` methods.
**Why bad:** Embedding models (text-embedding-004) are not chat models. OpenRouter has separate embedding endpoints. Ollama has separate `/api/embed`. Forcing them together creates unused methods and confusing interfaces.
**Instead:** Separate `BaseProvider` and `BaseEmbeddingProvider` ABCs.

### Anti-Pattern 3: Provider-Specific Types Leaking into Application Code
**What:** Application code importing `google.genai.types.GenerateContentConfig` or `openai.types.ChatCompletion`.
**Why bad:** Provider lock-in at the application layer. Every provider change requires touching application code.
**Instead:** All translation happens inside provider implementations. Application code uses only `model_router.types`.

### Anti-Pattern 4: Global Config for Per-Session Overrides
**What:** Using environment variables or a global config file for provider preferences that should be per-user or per-session.
**Why bad:** Multiple students using the same deployment should have independent provider choices. Staff vs student may have different model access.
**Instead:** Hierarchical config: per-request > per-session > user default > system default.

### Anti-Pattern 5: Blocking Ollama Detection on Startup
**What:** Checking for Ollama availability during app startup and blocking if not found.
**Why bad:** Ollama is optional. Most deployments will not have it. Blocking startup for an optional dependency is wrong.
**Instead:** Lazy detection. Health check on first access. Show "unavailable" in UI if not running.

---

## 8. Build Order (Dependency-Driven)

This order reflects true technical dependencies -- each step's outputs feed the next step's inputs.

### Phase 1: Shared Package + Core Types
**Build:** `shared/model_router/` with types, errors, base ABCs, router skeleton
**Why first:** Everything else depends on these types and interfaces
**Output:** Installable package with `from model_router import GenerateRequest, GenerateResponse, ModelRouter`

### Phase 2: Vertex AI Provider (Refactored)
**Build:** `VertexAIProvider` wrapping existing code, compatibility shims
**Why second:** Existing functionality must keep working. This is the "make it work through the new interface" step.
**Output:** All existing Vertex AI features accessible via `ModelRouter.generate()`
**Dependency:** Phase 1 (types + base ABC)

### Phase 3: Cross-Project Migration
**Build:** Update `server/dependencies.py` and backend services to use ModelRouter. Update AURA-NOTES-MANAGER services similarly.
**Why third:** Once Vertex AI works through the router, swap the plumbing in both apps.
**Output:** Both apps using ModelRouter for all LLM calls. Zero behavior change from user perspective.
**Dependency:** Phase 2 (working Vertex AI provider)

### Phase 4: OpenRouter Provider
**Build:** `OpenRouterProvider` with completions, streaming, model listing, credit check
**Why fourth:** New functionality added only after existing functionality is stable through the new interface.
**Output:** 200+ models available via the same `ModelRouter.generate()` interface
**Dependency:** Phase 1 (types), Phase 3 (router is wired up)

### Phase 5: Frontend - Settings + Inline Selection
**Build:** Provider settings page, model selector updates, provider health display
**Why fifth:** Backend API must exist before frontend can consume it.
**Output:** Users can select providers/models in both apps
**Dependency:** Phase 3 (API endpoints), Phase 4 (OpenRouter models to display)

### Phase 6: Configuration + Usage Tracking
**Build:** Firestore preferences, per-session overrides, usage accumulator, cost dashboard
**Why last:** This is additive polish. Core functionality works without it.
**Output:** Persistent preferences, usage visibility, budget controls
**Dependency:** Phase 5 (settings UI exists)

---

## 9. Scalability Considerations

| Concern | At 10 users | At 1K users | At 10K users |
|---------|------------|-------------|-------------|
| Provider rate limits | Not an issue | OpenRouter has per-key limits; implement request queuing | Dedicated OpenRouter plan; provider-level circuit breakers |
| Cost tracking | In-memory accumulator sufficient | Firestore writes per request OK | Batch writes, Redis accumulator with periodic Firestore flush |
| Model list caching | Fetch on every page load | Cache in Redis (5-min TTL) | Cache in Redis + CDN |
| Provider failover | Manual (change default) | Automatic fallback chain | Load balancing across providers with health-weighted routing |

---

## 10. Sources

- **Codebase analysis:** Direct inspection of `AURA-CHAT/backend/utils/vertex_ai_client.py`, `AURA-CHAT/server/dependencies.py`, `AURA-CHAT/server/routers/chat.py`, `AURA-NOTES-MANAGER/services/vertex_ai_client.py`, `AURA-NOTES-MANAGER/services/embeddings.py` (HIGH confidence)
- **OpenRouter API:** Official documentation at openrouter.ai/docs -- OpenAI-compatible chat completions, model listing, credit tracking, guardrails (MEDIUM confidence -- fetched live)
- **Ollama Python library:** Official GitHub repo -- `chat()`, `generate()`, `embed()`, `list()` APIs, sync/async clients (MEDIUM confidence -- fetched live)
- **Python packaging:** Official Python Packaging User Guide -- `pyproject.toml` structure, editable installs, hatchling build backend (HIGH confidence -- official docs)
- **FastAPI DI:** Official FastAPI documentation -- `Depends()`, `Annotated` pattern, `dependency_overrides` for testing (HIGH confidence -- official docs)
