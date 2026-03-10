# Technology Stack: Multi-Provider LLM Architecture (v1.1)

**Project:** AURA Multi-Provider LLM Support
**Researched:** 2026-03-10
**Scope:** NEW dependencies only -- existing stack (FastAPI, React, Neo4j, TanStack Query, etc.) is validated and excluded

---

## Recommended Stack

### Core Provider Libraries (Python Backend)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `openai` | >=2.26.0 | OpenRouter provider client | Mature (v2.26.0), OpenAI-compatible API used by OpenRouter via `base_url`. Typed responses, async (`AsyncOpenAI`), streaming SSE, automatic retries. OpenRouter officially documents this approach. Avoids the beta-quality official `openrouter` SDK (v0.7.11) which has breaking changes between versions. |
| `ollama` | >=0.6.1 | Ollama provider client (local models) | Official Python client (MIT, 9.5k stars). Has `chat()`, `generate()`, `embed()`, `list()` methods that map directly to our router interface. Built on httpx. AsyncClient for async operations. |

### Configuration & Validation (Python Backend)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `pydantic-settings` | >=2.13.0 | Hierarchical configuration system | Already in requirements (>=2.1.0), upgrade to >=2.13.0 for latest .env nesting support. `BaseSettings` classes with env var loading for provider configs, API keys, defaults. Supports nested models for global + per-session overrides. |
| `pydantic` | >=2.6.0 | Provider response/request schemas | Already in requirements. Use for typed provider configs, usage tracking models, and normalized response schemas. |

### Shared Package Infrastructure (Python)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `pyproject.toml` | (build config) | Shared package definition | Standard Python packaging for `shared/model_router/`. Both apps install via `pip install -e ../shared/model_router` for development. No external dependency needed -- uses Python's native packaging. |

### Cost Dashboard (Frontend)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `recharts` | ^3.8.0 | Usage/cost dashboard charts | Composable React chart library built on SVG + D3 submodules. Supports area, bar, line, pie charts. Lightweight, works with both React 18 (NOTES) and React 19 (CHAT). MIT licensed. Install in whichever app(s) render the dashboard. |

---

## What NOT to Add

These were considered and explicitly rejected:

| Library | Why NOT |
|---------|---------|
| `openrouter` (official SDK) | Beta (v0.7.11), breaking changes between versions, less battle-tested than `openai` SDK. OpenRouter itself supports the OpenAI SDK approach. Pin to `openai` for stability. |
| `litellm` | Large dependency surface (~100+ transitive deps). Abstracts 100+ providers but we only need 3 (Vertex AI, OpenRouter, Ollama). Our custom Protocol-based abstraction is thinner and tailored to our exact needs. |
| `langchain` / `langchain-core` | Massive framework dependency. We are building a routing layer, not an orchestration chain. LangChain's model abstraction is buried deep in its framework. |
| `instructor` | Structured output library. Not needed -- we use Pydantic directly with Gemini's native JSON mode. |
| New state management lib | Zustand (client state) + TanStack Query (server state) already handle settings/dashboard needs. No new frontend state library required. |
| New UI component library | Existing TailwindCSS + lucide-react + framer-motion + clsx/tailwind-merge cover all settings/dashboard UI needs. No Radix or shadcn needed for AURA-CHAT (AURA-NOTES already has @radix-ui/react-slot). |
| `d3` (direct) | recharts wraps D3 submodules already. No need to add D3 directly. |
| Additional charting libs (Chart.js, Nivo, Victory) | recharts is sufficient, lightweight, and React-native. No reason to use heavier alternatives. |

---

## Detailed Rationale

### Why `openai` SDK for OpenRouter (not the official `openrouter` SDK)

OpenRouter's API is OpenAI-compatible at `https://openrouter.ai/api/v1`. The `openai` Python SDK (v2.26.0) supports custom `base_url` configuration:

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_api_key,
)

response = await client.chat.completions.create(
    model="anthropic/claude-4.5-sonnet",
    messages=[{"role": "user", "content": "Hello"}],
    extra_headers={
        "HTTP-Referer": "https://aura.edu",
        "X-OpenRouter-Title": "AURA Learning Platform",
    },
)
```

The `openai` SDK advantages over the official `openrouter` package:
- **Stable API**: v2.26.0 with semantic versioning. The openrouter SDK (v0.7.11) warns of breaking changes without major bumps.
- **Battle-tested**: Used by millions of developers; excellent typing, error handling, retry logic.
- **Async-first**: `AsyncOpenAI` with native `asyncio` support, matching our FastAPI async patterns.
- **Streaming**: Built-in SSE streaming that matches our existing `generate_content_stream` patterns.
- **Community**: Extensive documentation, Stack Overflow answers, and examples.

**Confidence: HIGH** -- Verified via OpenRouter official docs and PyPI.

### Why `ollama` for Local Models

The official `ollama` Python package (v0.6.1) is the only maintained client:

```python
from ollama import AsyncClient

client = AsyncClient(host="http://127.0.0.1:11434")

# Chat
response = await client.chat(
    model="gemma3",
    messages=[{"role": "user", "content": "Hello"}],
)

# Embeddings
embeddings = await client.embed(
    model="gemma3",
    input="The sky is blue",
)

# List available models
models = await client.list()
```

Key advantages:
- **Official**: Maintained by Ollama team (MIT licensed, 9.5k GitHub stars).
- **API parity**: Methods mirror the Ollama REST API exactly (`chat`, `generate`, `embed`, `list`).
- **AsyncClient**: Native async support for FastAPI integration.
- **Detection**: `client.list()` can check if Ollama is running and what models are available, enabling the "local detection" feature in the stub.
- **httpx-based**: Same HTTP library already in our stack.

**Confidence: HIGH** -- Verified via official GitHub README and PyPI.

### Why Custom Protocol Abstraction (not LiteLLM)

The model router needs a thin abstraction with two core methods: `generate()` and `embed()`. A Python Protocol-based approach is ideal:

```python
from typing import Protocol, AsyncIterator

class LLMProvider(Protocol):
    async def generate(
        self, messages: list[Message], config: GenerationConfig
    ) -> GenerationResult: ...

    async def generate_stream(
        self, messages: list[Message], config: GenerationConfig
    ) -> AsyncIterator[StreamChunk]: ...

    async def embed(
        self, texts: list[str], model: str
    ) -> list[list[float]]: ...

    async def list_models(self) -> list[ModelInfo]: ...
```

Why not LiteLLM:
- LiteLLM pulls in ~100 transitive dependencies (including its own httpx, aiohttp, tokenizers, etc.)
- We only need 3 providers (Vertex AI, OpenRouter, Ollama). LiteLLM supports 100+.
- LiteLLM's abstraction would fight with our existing Vertex AI wrapper patterns.
- Our Protocol approach adds zero dependencies and gives us full control over error normalization, cost tracking hooks, and configuration.

**Confidence: HIGH** -- Architecture decision based on codebase analysis.

### Why `recharts` for Dashboard

The cost/usage dashboard needs line charts (usage over time), bar charts (cost by provider/model), and pie charts (distribution). recharts v3.8.0 is the right choice:

- **React-native**: Composable components (`<LineChart>`, `<BarChart>`, `<PieChart>`, `<AreaChart>`).
- **Lightweight**: SVG-based with D3 submodule dependencies (not full D3).
- **React 18 + 19 compatible**: Works with both AURA-CHAT and AURA-NOTES-MANAGER.
- **Well-maintained**: v3.8.0 (MIT, widely adopted in React ecosystem).
- **TailwindCSS friendly**: SVG output can be styled alongside existing Tailwind patterns.

Only install in the app(s) that render the dashboard (likely AURA-NOTES-MANAGER for staff cost tracking, possibly AURA-CHAT for per-session usage display).

**Confidence: MEDIUM** -- recharts v3 verified via official site; version confirmed. Exact component API not independently verified via Context7.

---

## Shared Package Structure

The `shared/model_router/` package at project root, importable by both apps:

```
AURA-PROJ/
  shared/
    model_router/
      pyproject.toml          # Package definition
      src/
        model_router/
          __init__.py          # Public API: ModelRouter, generate, embed
          protocols.py         # LLMProvider Protocol definition
          router.py            # ModelRouter class (provider registry, routing)
          config.py            # ProviderConfig, RouterConfig (pydantic-settings)
          schemas.py           # Message, GenerationResult, StreamChunk, ModelInfo, Usage
          exceptions.py        # Normalized exceptions (ProviderError, RateLimitError, etc.)
          tracking.py          # UsageTracker, CostCalculator
          providers/
            __init__.py
            base.py            # Base provider with common patterns
            vertex_ai.py       # Vertex AI provider (wraps existing vertex_ai_client.py)
            openrouter.py      # OpenRouter provider (uses openai SDK)
            ollama.py          # Ollama provider stub (uses ollama SDK)
```

**pyproject.toml** for the shared package:

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "model-router"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.6.0",
    "pydantic-settings>=2.13.0",
    "openai>=2.26.0",
    "ollama>=0.6.1",
    # Vertex AI deps already installed in root venv
    "google-genai>=1.59.0",
    "google-cloud-aiplatform>=1.71.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
]
```

**Installation** (both apps use root venv):

```bash
# From project root, install shared package in editable mode
.venv/Scripts/pip install -e shared/model_router/
```

This means changes to `shared/model_router/` are immediately available to both apps without reinstallation.

---

## Integration Points with Existing Stack

### Backend (FastAPI)

| Existing Component | Integration Approach |
|-------------------|---------------------|
| `AURA-CHAT/backend/utils/vertex_ai_client.py` | **Refactor into** `shared/model_router/providers/vertex_ai.py`. Keep existing public API (`get_model`, `generate_content`, `generate_content_stream`) as thin wrappers calling the new provider. |
| `AURA-NOTES-MANAGER/services/vertex_ai_client.py` | Same pattern -- delegate to shared provider. Existing `get_model()` and `generate_content()` become pass-throughs. |
| `AURA-CHAT/backend/rag_engine.py` | Inject `ModelRouter` via constructor/dependency. Replace direct `get_model()` calls with `router.generate()`. Phase migration -- old path works during transition. |
| FastAPI `Depends()` | Register `ModelRouter` as a FastAPI dependency. Inject into routers that need LLM access. |
| Pydantic schemas | Extend existing Pydantic patterns for provider config, usage tracking models. |
| Redis (caching) | Use existing Redis for caching model lists, provider health status. No new infrastructure. |

### Frontend (React/TypeScript)

| Existing Component | Integration Approach |
|-------------------|---------------------|
| TanStack Query | Use for fetching provider configs, model lists, usage data. Standard `useQuery`/`useMutation` patterns. |
| Zustand stores | Add `providerSettingsStore` for client-side settings state (selected provider, model preferences). |
| Axios | Existing HTTP client for new API endpoints (`/api/settings/providers`, `/api/usage`). |
| TailwindCSS | All settings/dashboard UI uses existing Tailwind classes + Cyber Yellow theme. |
| lucide-react | Icons for provider logos, settings toggles, chart decorations. |
| framer-motion | Animate settings panels, dashboard transitions. |

### New API Endpoints Needed

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/providers` | GET | List configured providers with status |
| `/api/v1/providers/models` | GET | List available models across providers |
| `/api/v1/settings/provider` | GET/PUT | Global provider settings |
| `/api/v1/sessions/{id}/provider` | GET/PUT | Per-session provider override |
| `/api/v1/usage` | GET | Usage/cost data (with date range filters) |
| `/api/v1/usage/summary` | GET | Aggregated cost summary for dashboard |

---

## New Environment Variables

| Variable | Description | Required By | Example |
|----------|-------------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | Model Router | `sk-or-v1-abc123...` |
| `OLLAMA_HOST` | Ollama server address | Model Router (optional) | `http://127.0.0.1:11434` |
| `DEFAULT_PROVIDER` | Default LLM provider | Model Router | `vertex_ai` |
| `DEFAULT_CHAT_MODEL` | Default model for chat | Model Router | `gemini-2.5-flash` |
| `DEFAULT_EMBED_MODEL` | Default model for embeddings | Model Router | `text-embedding-004` |
| `USAGE_TRACKING_ENABLED` | Enable cost/usage tracking | Model Router | `true` |
| `MONTHLY_BUDGET_LIMIT` | Monthly spend cap (USD) | Model Router (optional) | `50.00` |

Note: Existing `VERTEX_PROJECT`, `VERTEX_REGION`, `VERTEX_CREDENTIALS`, and `GOOGLE_APPLICATION_CREDENTIALS` remain unchanged for the Vertex AI provider.

---

## Installation Summary

### Python (Backend) -- New Dependencies

```bash
# Install to root venv (from project root)
.venv/Scripts/pip install "openai>=2.26.0" "ollama>=0.6.1" "pydantic-settings>=2.13.0"

# Install shared package in editable mode
.venv/Scripts/pip install -e shared/model_router/
```

### JavaScript (Frontend) -- New Dependencies

```bash
# Install recharts in the app(s) that need the dashboard
# AURA-NOTES-MANAGER (staff cost dashboard)
cd AURA-NOTES-MANAGER/frontend && npm install recharts@^3.8.0

# AURA-CHAT (optional -- per-session usage display)
cd AURA-CHAT/client && npm install recharts@^3.8.0
```

### Updated Root requirements.txt Additions

```txt
# Multi-Provider LLM Support (v1.1)
openai>=2.26.0
ollama>=0.6.1
pydantic-settings>=2.13.0  # upgrade from >=2.1.0
```

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| OpenRouter client | `openai` SDK (v2.26.0) | `openrouter` SDK (v0.7.11) | Beta quality, breaking changes between minor versions, less mature than openai SDK |
| OpenRouter client | `openai` SDK (v2.26.0) | Raw `httpx` calls | Reinventing typed responses, streaming, retries. openai SDK handles all this. |
| Provider abstraction | Custom Protocol | `litellm` (v1.x) | 100+ transitive deps, supports 100+ providers we do not need, fights existing Vertex AI patterns |
| Provider abstraction | Custom Protocol | `langchain-core` | Heavy framework buy-in for a simple routing need |
| Ollama client | `ollama` (v0.6.1) | Raw HTTP to Ollama REST API | Official client is thin and well-typed. No benefit to raw HTTP. |
| Charts | `recharts` (v3.8.0) | `@nivo/core` | Heavier, more opinionated, not needed for simple cost charts |
| Charts | `recharts` (v3.8.0) | `chart.js` + `react-chartjs-2` | Canvas-based (not SVG), harder to style with Tailwind |
| Charts | `recharts` (v3.8.0) | `visx` (Airbnb) | Lower-level, requires more custom code for basic charts |
| Config management | `pydantic-settings` (v2.13.0) | `python-decouple` | Already using pydantic-settings; no reason to add another config lib |
| Shared package | `pip install -e` | Git submodule | Unnecessary complexity. Editable install is standard Python monorepo pattern. |
| Shared package | `pip install -e` | Copy code to both apps | Violates DRY, maintenance nightmare for shared abstractions |

---

## Version Compatibility Matrix

| New Dependency | Python | Existing Deps | Compatible? |
|----------------|--------|---------------|-------------|
| `openai>=2.26.0` | >=3.9 (our 3.11+) | `httpx>=0.25.0` (openai uses httpx internally) | YES |
| `ollama>=0.6.1` | >=3.8 (our 3.11+) | `httpx>=0.25.0` (ollama uses httpx internally) | YES |
| `pydantic-settings>=2.13.0` | >=3.10 (our 3.11+) | `pydantic>=2.6.0` (already installed) | YES |
| `recharts@^3.8.0` | N/A | React 18.3+ and React 19.2+ | YES (both) |

No known conflicts between new and existing dependencies. Both `openai` and `ollama` use `httpx` internally, which is already in our dependency tree.

---

## Sources

| Claim | Source | Confidence |
|-------|--------|------------|
| openai SDK v2.26.0 supports custom base_url | PyPI page (verified 2026-03-10) | HIGH |
| OpenRouter recommends openai SDK approach | OpenRouter quickstart docs (verified 2026-03-10) | HIGH |
| openrouter SDK v0.7.11 is beta with breaking changes | PyPI page description (verified 2026-03-10) | HIGH |
| ollama v0.6.1 has chat/generate/embed/list | GitHub README + PyPI (verified 2026-03-10) | HIGH |
| ollama AsyncClient for async support | GitHub README (verified 2026-03-10) | HIGH |
| pydantic-settings v2.13.1 supports nested models | PyPI page (verified 2026-03-10) | HIGH |
| recharts v3.8.0 works with React 18 and 19 | Official recharts.github.io (verified 2026-03-10) | MEDIUM |
| OpenRouter API at /api/v1 is OpenAI-compatible | OpenRouter docs + OpenAPI spec (verified 2026-03-10) | HIGH |
| httpx v0.28.1 is compatible with both openai and ollama | PyPI pages for all three packages (verified 2026-03-10) | HIGH |
