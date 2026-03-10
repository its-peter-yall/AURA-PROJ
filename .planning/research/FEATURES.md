# Feature Landscape: Multi-Provider LLM Architecture

**Domain:** Multi-provider LLM abstraction layer for academic RAG platform
**Researched:** 2026-03-10
**Confidence:** HIGH (OpenRouter/Ollama APIs verified via official docs, LiteLLM patterns verified, existing codebase analyzed)

---

## Table Stakes

Features users expect from a multi-provider LLM system. Missing any of these makes the feature feel broken or incomplete.

### TS-1: Unified generate() Interface

| Aspect | Detail |
|--------|--------|
| **What** | Single `generate(prompt, config)` function that routes to the correct provider, hiding provider-specific SDKs |
| **Why Expected** | This IS the core abstraction. Without it, callers must write provider-specific code and the entire milestone is pointless |
| **Complexity** | Medium |
| **AURA Dependency** | Replaces direct calls to `vertex_ai_client.get_model()` + `generate_content()` in both apps. AURA-CHAT's `rag_engine.py` and AURA-NOTES-MANAGER's `summarizer.py` are the primary consumers |
| **Notes** | Must support both sync and async. Current AURA-CHAT uses `async` throughout (`generate_content_stream` is an `AsyncGenerator`). The interface should accept a model identifier string (e.g., `vertex_ai/gemini-2.5-flash`, `openrouter/anthropic/claude-sonnet-4`) and route accordingly. LiteLLM's prefix-based routing pattern is the proven approach here |

### TS-2: Unified embed() Interface

| Aspect | Detail |
|--------|--------|
| **What** | Single `embed(text_or_texts, config)` function that produces embedding vectors regardless of provider |
| **Why Expected** | AURA has TWO separate EmbeddingService implementations (AURA-CHAT and AURA-NOTES-MANAGER) both tightly coupled to Vertex AI. Embeddings are foundational to the RAG pipeline |
| **Complexity** | High |
| **AURA Dependency** | AURA uses 768-dimensional vectors from `text-embedding-004` stored in Neo4j HNSW indices. Changing embedding providers changes vector dimensions, which means ALL existing embeddings in Neo4j become incompatible. This is the single hardest migration constraint |
| **Notes** | Embedding provider switching is NOT the same as chat model switching. Embeddings must remain consistent within a deployment. The `embed()` interface should exist for future flexibility, but the actual provider should be locked per-deployment (not per-session). OpenRouter supports embeddings via a dedicated endpoint. Ollama supports embeddings via `/api/embed`. Vertex AI uses `TextEmbeddingModel`. Dimension differences: OpenAI ada-002=1536, text-embedding-3-small=1536 (configurable), Vertex text-embedding-004=768, Cohere embed-v3=1024. Changing dimensions requires re-indexing |

### TS-3: Streaming Response Support

| Aspect | Detail |
|--------|--------|
| **What** | All providers stream responses through a normalized SSE format to the frontend |
| **Why Expected** | AURA-CHAT already streams via `generate_content_stream()` using SSE. Users see tokens appear in real-time. Removing streaming for non-Vertex providers would be a visible regression |
| **Complexity** | Medium-High |
| **AURA Dependency** | `AURA-CHAT/server/routers/chat.py` uses `StreamingResponse` with `AsyncGenerator`. The current `_normalize_stream_chunk()` in `vertex_ai_client.py` normalizes Vertex-specific chunks. Each provider has different streaming formats that must converge into AURA's existing `{type: "thinking"|"content", text: "..."}` chunk shape |
| **Notes** | Vertex AI streams via google-genai SDK (sync iterator wrapped in `asyncio.to_thread`). OpenRouter streams SSE with `delta` chunks (OpenAI-compatible format). Ollama streams newline-delimited JSON objects. All three must normalize into the same downstream format. The key challenge is that streaming complicates cost tracking since token counts arrive incrementally (or only at stream end) |

### TS-4: Provider Configuration (Global Defaults)

| Aspect | Detail |
|--------|--------|
| **What** | A settings page where staff/admin sets default provider and model for each use case (chat generation, embeddings, entity extraction, summarization) |
| **Why Expected** | Without global defaults, every session starts unconfigured. Users need a "set it and forget it" experience for the common case |
| **Complexity** | Medium |
| **AURA Dependency** | Currently hardcoded: `RAG_MODEL_DEFAULT = "gemini-2.5-flash-lite"` in `rag_engine.py`, `EMBEDDING_MODEL` in config files. These become configurable values stored in a config store (Redis, Firestore, or a dedicated config table) |
| **Notes** | Configuration hierarchy: Environment variables (deployment) -> Global settings (admin UI) -> Per-session override (user). Each level overrides the one above it. Store in Redis for fast reads since every request needs the current config |

### TS-5: Per-Session Model Override

| Aspect | Detail |
|--------|--------|
| **What** | Students can select a different chat model for their study session, overriding the global default |
| **Why Expected** | This is the primary user-facing value of multi-provider support. "Try Claude for this topic" or "Use a cheaper model for quick questions" |
| **Complexity** | Low-Medium |
| **AURA Dependency** | AURA-CHAT already has `StudySession` nodes in Neo4j with configurable properties. Add `model_id` field to session. The `ChatRequest` schema already accepts a `model` parameter. The override persists for the session duration |
| **Notes** | Session model override should NOT change embedding provider (embeddings must stay consistent for vector search). Only the generation model changes. The model selector in the chat UI should show which model is active and allow mid-session switching |

### TS-6: Error Handling Normalization

| Aspect | Detail |
|--------|--------|
| **What** | All provider errors map to a unified error hierarchy (auth errors, rate limits, content policy, model unavailable, timeout) |
| **Why Expected** | Without this, the frontend must handle N different error shapes. Users see cryptic provider-specific errors instead of actionable messages |
| **Complexity** | Medium |
| **AURA Dependency** | AURA already has `VertexAIRequestError` with `model`, `location`, `operation`, `original` fields. Generalize this to `ProviderError` with the same shape plus a `provider` field. Both apps' error handlers in `main.py` need updating |
| **Notes** | LiteLLM's approach of mapping all exceptions to OpenAI-compatible types is proven. Key error categories: `AuthenticationError` (bad API key), `RateLimitError` (429), `ContentPolicyError` (safety filters), `ModelNotFoundError` (invalid model), `ProviderUnavailableError` (503/timeout), `InsufficientCreditsError` (OpenRouter-specific). Each should carry the original error for logging |

### TS-7: Model Discovery / Listing

| Aspect | Detail |
|--------|--------|
| **What** | The system knows what models are available from each configured provider and exposes this to the UI |
| **Why Expected** | The model selector needs to show real, available models -- not a hardcoded list that goes stale. Users need to see model names, capabilities, and pricing |
| **Complexity** | Medium |
| **AURA Dependency** | Currently `RAG_ALLOWED_MODELS` is a hardcoded list in `rag_engine.py`. Replace with dynamic discovery: Vertex AI models from config, OpenRouter models from `GET /api/v1/models`, Ollama models from `GET /api/tags` |
| **Notes** | Cache model lists (refresh every 15-60 minutes for cloud providers, every 5 minutes for local Ollama). OpenRouter returns model metadata including pricing, context length, and capabilities. Ollama returns locally installed models with family/parameter info. Vertex AI models are known at configuration time (no discovery API needed -- use a curated list of supported Gemini models) |

### TS-8: API Key Management

| Aspect | Detail |
|--------|--------|
| **What** | Secure storage and validation of API keys for each provider (OpenRouter API key, Vertex AI credentials, Ollama needs no key) |
| **Why Expected** | Multi-provider means multi-credential. Users need to enter and validate keys without exposing them |
| **Complexity** | Low-Medium |
| **AURA Dependency** | Vertex AI already uses environment variables (`VERTEX_PROJECT`, `VERTEX_CREDENTIALS`, `GOOGLE_APPLICATION_CREDENTIALS`). Add `OPENROUTER_API_KEY` for OpenRouter. Ollama requires no authentication (dummy key accepted). Store encrypted in environment or secrets manager -- NOT in database |
| **Notes** | Validation: call a lightweight endpoint to verify key validity (OpenRouter: `GET /api/v1/auth/key` returns remaining credits; Ollama: `GET /api/version` confirms reachability; Vertex AI: existing ADC check). Show validation status in settings UI. Never expose full keys in UI -- show masked versions |

---

## Differentiators

Features that set the product apart. Not expected by all users, but significantly increase value.

### D-1: Hierarchical Provider Selection UI

| Aspect | Detail |
|--------|--------|
| **What** | A 2-level selector for Vertex AI/Ollama (Provider -> Model) and 3-level selector for OpenRouter (Provider -> Vendor -> Model) that makes browsing 200+ models manageable |
| **Why Expected** | N/A (differentiator) |
| **Value Proposition** | OpenRouter exposes 200+ models from dozens of vendors. A flat list is unusable. Grouping by vendor (OpenAI, Anthropic, Meta, Google, Mistral, etc.) makes selection fast. TypingMind proves search+filter+sort is the pattern users love |
| **Complexity** | Medium |
| **AURA Dependency** | OpenRouter model IDs already use `vendor/model` format (e.g., `anthropic/claude-sonnet-4`, `openai/gpt-4o`). Parse the vendor prefix for grouping. Vertex AI and Ollama are simpler (no vendor level needed) |
| **Notes** | UI pattern: Provider tabs (Vertex AI / OpenRouter / Ollama) -> within OpenRouter, collapsible vendor groups -> model cards within each group showing name, context length, price per token. Include search/filter within the selector. Show a "Recently Used" section at the top for quick access |

### D-2: Inline Contextual Model Selector

| Aspect | Detail |
|--------|--------|
| **What** | A compact model picker embedded directly in the chat interface (next to the send button or in the session header) allowing quick model switches without navigating to settings |
| **Why Expected** | N/A (differentiator) |
| **Value Proposition** | Reduces friction from "open settings -> change model -> go back to chat" to a single click. ChatGPT, Claude, and TypingMind all use this pattern (model selector at top of chat). Mid-chat model switching is a power-user feature that dramatically improves exploration |
| **Complexity** | Low-Medium |
| **AURA Dependency** | AURA-CHAT's study session sidebar already shows session metadata. Add a compact model indicator (e.g., pill showing "Gemini 2.5 Flash") that expands into a dropdown. Changes propagate to the session's `model_id` |
| **Notes** | Show only recently used + favorited models in the inline selector for speed. Full model browser available via "Browse all models" link that opens the hierarchical selector. Display current model's cost-per-token as a subtle indicator |

### D-3: Usage Tracking with Cost Dashboard

| Aspect | Detail |
|--------|--------|
| **What** | Track token usage and cost per request, aggregate by session/user/model/provider, display in a dashboard with charts |
| **Why Expected** | N/A (differentiator) |
| **Value Proposition** | Academic platforms have tight budgets. Seeing "this session cost $0.12" or "Claude costs 5x more than Gemini Flash for similar quality" enables informed model selection. No competitor in the academic RAG space does this well |
| **Complexity** | High |
| **AURA Dependency** | Create a `UsageRecord` model stored in Firestore or a dedicated table. Each AI call logs: `provider`, `model`, `input_tokens`, `output_tokens`, `cost`, `session_id`, `user_id`, `timestamp`, `operation` (chat/embed/extract). OpenRouter returns `cost` directly in the usage response. Vertex AI pricing must be calculated from token counts + known rates. Ollama is free (local) |
| **Notes** | Dashboard views: daily/weekly/monthly cost charts, cost breakdown by provider, cost per session, top models by usage, cost trend over time. For OpenRouter, cost data comes from the response `usage.cost` field. For Vertex AI, calculate from published pricing tables (store as config). Real-time cost display: show running session cost in the chat UI |

### D-4: Budget Controls with Alerts

| Aspect | Detail |
|--------|--------|
| **What** | Set spending limits (daily, weekly, monthly) per provider or globally. Alert when approaching limit. Block requests when exceeded |
| **Why Expected** | N/A (differentiator) |
| **Value Proposition** | Prevents runaway costs in an academic setting. A student accidentally running expensive queries in a loop could burn through a department's budget. This is a safety net |
| **Complexity** | Medium-High |
| **AURA Dependency** | Requires the usage tracking system (D-3) as a foundation. Budget state stored in Redis for fast check on every request. Budget enforcement happens in the model router before dispatching to provider |
| **Notes** | Budget hierarchy: Global budget -> Per-provider budget -> Per-user budget (optional). When budget is hit: block new requests with a clear error message, optionally auto-downgrade to a cheaper model instead of blocking. Alert at 80% and 95% thresholds via UI notification. OpenRouter has its own credit system; integrate with `GET /api/v1/auth/key` to show remaining OpenRouter credits alongside internal budget tracking |

### D-5: Thinking Mode Standardization

| Aspect | Detail |
|--------|--------|
| **What** | Normalize thinking/reasoning mode across providers so users get a consistent "show me the reasoning" experience regardless of model |
| **Why Expected** | N/A (differentiator, but close to table stakes given AURA already has thinking mode for Vertex AI) |
| **Value Proposition** | AURA-CHAT already supports Gemini thinking mode with `ThinkingConfig`. Extending this to Claude's extended thinking, DeepSeek R1, and OpenAI o-series reasoning provides a unified educational experience. Seeing the model's reasoning process is pedagogically valuable |
| **Complexity** | High |
| **AURA Dependency** | Current implementation in `vertex_ai_client.py` uses `types.ThinkingConfig` with `thinking_level` or `thinking_budget`. The `_normalize_stream_chunk()` function already separates thinking vs content parts. This normalization must extend to all providers |
| **Notes** | Provider differences are significant: Gemini uses `thinking_config` with levels/budgets and returns `thought` parts. Anthropic uses `thinking` param with `budget_tokens` and returns `thinking_blocks` with `signature` (stateless -- client must resend blocks). OpenAI o-series uses `reasoning_effort` (stateful -- server stores reasoning). DeepSeek returns `reasoning_content`. OpenRouter normalizes some of this with `reasoning` output items that include a `format` field identifying the upstream provider format (`google-gemini-v1`, `anthropic-claude-v1`, etc.). The unified interface should: (a) accept a boolean `enable_thinking` + optional `thinking_budget`, (b) return thinking content in a standardized format, (c) handle the stateful vs stateless difference transparently |

### D-6: Provider Fallback

| Aspect | Detail |
|--------|--------|
| **What** | Automatic failover to an alternate provider/model when the primary is unavailable (rate limited, down, or erroring) |
| **Why Expected** | N/A (differentiator) |
| **Value Proposition** | Academic use peaks around exams. If Vertex AI rate-limits, automatically falling back to OpenRouter keeps students studying. Zero downtime from provider outages |
| **Complexity** | Medium-High |
| **AURA Dependency** | The model router needs a fallback chain configuration: e.g., `gemini-2.5-flash` -> `openrouter/google/gemini-2.5-flash` -> `openrouter/anthropic/claude-3.5-haiku`. Fallback triggers: HTTP 429 (rate limit), 503 (unavailable), timeout (>30s), authentication failure |
| **Notes** | LiteLLM's cooldown pattern is proven: on failure, cool down the failing deployment for N seconds, route to next in chain. Track health per-provider. Key design decision: fallback should be transparent to the user (they see the response, with a subtle indicator showing which model actually responded) OR explicit (ask user "Primary model unavailable, try X instead?"). Transparent is better UX for academic context. Log which fallback was used for cost attribution |

---

## Anti-Features

Features to explicitly NOT build. Tempting but counterproductive.

### AF-1: User-Facing Embedding Provider Switching

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Letting users change the embedding model/provider per session | Changing embedding models invalidates all existing vectors in Neo4j. A session using OpenAI embeddings cannot search against Gemini-embedded content -- cosine similarity across different embedding spaces is meaningless | Lock embedding provider at deployment level. Only changeable by admin, requires full re-indexing. The `embed()` interface exists for future flexibility and for supporting multiple deployment configurations, not for per-user switching |

### AF-2: Real-Time Provider Price Comparison

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Building a live price comparison engine that fetches and compares pricing across all providers before each request | Adds latency to every request, pricing APIs are not real-time, and the complexity is enormous for marginal value | Cache pricing data from OpenRouter's model listing (includes `pricing` field). Update daily. Show static price indicators in the model selector. Good enough for decision-making without the complexity |

### AF-3: Build Your Own LLM Proxy/Gateway

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Building a full proxy server that sits between AURA and providers (like a self-hosted LiteLLM proxy) | Massive scope creep. AURA is a learning platform, not an LLM infrastructure product. A proxy adds deployment complexity, another service to monitor, and network latency | Use a library-level router (shared Python package) that runs in-process. No extra network hop. OpenRouter already IS a proxy for 200+ models -- use it as intended rather than rebuilding it |

### AF-4: Fine-Tuning / Custom Model Training UI

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Building UI for fine-tuning models or managing custom model training | Completely out of scope for v1.1. Requires ML infrastructure, GPU management, dataset curation -- each a project larger than the entire AURA platform | If custom models are needed later, use Ollama (which can load any GGUF model) or OpenRouter (which supports custom fine-tuned models via API). The model router already supports any model these providers expose |

### AF-5: Per-User API Key Management

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Letting individual students enter their own API keys (BYOK) | Security nightmare in academic setting -- students may share keys, keys may be compromised, tracking/billing becomes impossible, support burden explodes | Admin manages all API keys. Budget controls limit per-user spend. If BYOK is needed later, it should be a separate feature with proper key isolation and audit logging |

### AF-6: Provider-Specific Advanced Features

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Exposing every provider-specific parameter (Anthropic's `top_k`, OpenAI's `logprobs`, Gemini's `safety_settings`, etc.) in the UI | Creates an overwhelming UI that most users won't understand. Each parameter requires provider-specific validation. The matrix of features x providers is unmanageable | Expose only universally-supported parameters: `temperature`, `max_tokens`, `top_p`. Provider-specific params can be set in admin config as JSON overrides. Power users get what they need without polluting the student UI |

---

## Feature Dependencies

```
                    TS-1: generate() interface
                    /        |            \
                   /         |             \
    TS-3: Streaming    TS-6: Error      TS-5: Per-Session
                       Normalization     Override
                            |                |
                            v                v
                    D-6: Provider       D-2: Inline
                    Fallback            Selector
                                            |
                                            v
                                    D-1: Hierarchical
                                    Provider UI

    TS-2: embed() interface (independent, but shares provider config)

    TS-7: Model Discovery  -->  D-1: Hierarchical Provider UI
                           -->  D-2: Inline Selector

    TS-4: Global Config  -->  TS-5: Per-Session Override (override needs defaults)
                         -->  TS-8: API Key Management

    D-3: Usage Tracking  -->  D-4: Budget Controls (needs usage data)
                         -->  D-3 depends on TS-1 (hook into every generate/embed call)

    D-5: Thinking Mode  -->  depends on TS-1 + TS-3 (unified generate + streaming)
```

### Critical Path

1. **TS-1** (generate interface) is the foundation -- everything else depends on it
2. **TS-2** (embed interface) is independent but must be designed alongside TS-1
3. **TS-4** (global config) + **TS-8** (API keys) enable providers to be configured
4. **TS-7** (model discovery) feeds the UI components
5. **TS-3** (streaming) + **TS-6** (error normalization) complete the runtime layer
6. UI features (D-1, D-2) can only be built after the backend supports model listing and generation
7. **D-3** (usage tracking) must be wired into TS-1 from the start (retrofitting is painful)
8. **D-4** (budget controls) layers on top of D-3

---

## MVP Recommendation

### Must Ship (Milestone v1.1 Core)

1. **TS-1: Unified generate() interface** -- the entire point of the milestone
2. **TS-2: Unified embed() interface** -- future-proofs embeddings, even if only Vertex AI is used initially
3. **TS-3: Streaming support** -- regression without it
4. **TS-4: Global configuration** -- system needs defaults to function
5. **TS-5: Per-session model override** -- primary user-facing value
6. **TS-6: Error normalization** -- unusable without clear errors
7. **TS-7: Model discovery** -- model selector needs real data
8. **TS-8: API key management** -- providers need credentials

### Should Ship (High Value)

9. **D-1: Hierarchical provider selection UI** -- makes 200+ OpenRouter models usable
10. **D-2: Inline contextual model selector** -- the "wow" UX moment
11. **D-3: Usage tracking** -- wire it in from the start; dashboard can be simple initially
12. **D-5: Thinking mode standardization** -- AURA already has this for Vertex AI; extend it

### Defer to v1.2

13. **D-4: Budget controls** -- valuable but can be added after usage tracking proves the data model
14. **D-6: Provider fallback** -- nice to have, but manual model switching is acceptable for v1.1

### Rationale

All table stakes features are genuinely required -- they form the backbone of the abstraction. Among differentiators, the UI features (D-1, D-2) deliver the most visible user value. Usage tracking (D-3) should be wired in early because retrofitting instrumentation is much harder than building it alongside the router. Thinking mode (D-5) extends existing AURA capability. Budget controls (D-4) and fallback (D-6) are operationally valuable but can follow once the system is proven.

---

## Existing AURA Code to Migrate

Understanding what already exists is critical for scoping. These are the specific integration points that must be refactored.

| Current Code | Location | What It Does | Migration Path |
|-------------|----------|--------------|---------------|
| `vertex_ai_client.py` (CHAT) | `AURA-CHAT/backend/utils/` | Wraps google-genai SDK, handles auth, streaming, thinking | Becomes the Vertex AI provider implementation inside the shared model router |
| `vertex_ai_client.py` (NOTES) | `AURA-NOTES-MANAGER/services/` | Simpler Vertex AI wrapper for summarization | Same -- becomes provider impl |
| `genai_client.py` (NOTES) | `AURA-NOTES-MANAGER/services/` | Legacy shim over Vertex AI | Remove after migration, replaced by model router |
| `embeddings.py` (CHAT) | `AURA-CHAT/backend/utils/` | REST-based embedding via Vertex AI | Refactor into embed() interface; keep Vertex AI as default provider |
| `embeddings.py` (NOTES) | `AURA-NOTES-MANAGER/services/` | SDK-based embedding via Vertex AI | Same refactor path |
| `rag_engine.py` | `AURA-CHAT/backend/` | Calls `get_model()` and `generate_content()` directly | Change to `router.generate()` calls |
| `summarizer.py` | `AURA-NOTES-MANAGER/services/` | Calls Vertex AI for note summarization | Change to `router.generate()` calls |
| `llm_entity_extractor.py` | `AURA-CHAT/backend/` | Calls Vertex AI for entity extraction | Change to `router.generate()` calls |
| `RAG_ALLOWED_MODELS` | `AURA-CHAT/backend/rag_engine.py` | Hardcoded model allowlist | Replace with dynamic model discovery |
| `RAG_MODEL_DEFAULT` | `AURA-CHAT/backend/rag_engine.py` | Hardcoded default model | Replace with configurable default |
| `EMBEDDING_MODEL` | Various config files | Hardcoded `text-embedding-004` | Replace with configurable embedding model |

---

## Sources

- **OpenRouter API** (openrouter.ai/openapi.json) -- OpenAPI 3.1 spec, verified 2026-03-10. Confirms: OpenAI-compatible endpoints, `usage.cost` field in responses, embedding endpoints, model listing, SSE streaming, provider routing via `service_tier`, reasoning output with cross-provider format tracking. **HIGH confidence.**
- **OpenRouter Quickstart** (openrouter.ai/docs/quickstart) -- Confirmed base URL, auth headers, SDK compatibility. **HIGH confidence.**
- **Ollama API** (github.com/ollama/ollama/blob/main/docs/api.md) -- Full REST API reference. Confirmed: `/api/chat`, `/api/embed`, `/api/tags`, streaming format (newline-delimited JSON), `think` parameter for reasoning models, OpenAI-compatible endpoint at `/v1/chat/completions`. **HIGH confidence.**
- **LiteLLM Documentation** (docs.litellm.ai) -- Verified patterns for: unified interface, streaming normalization, error mapping to OpenAI exception types, embedding standardization across providers, router with fallback/cooldown, budget management, thinking/reasoning mode support across providers. **HIGH confidence.**
- **LiteLLM Reasoning Content** (docs.litellm.ai/docs/reasoning_content) -- Confirmed cross-provider thinking mode differences: Anthropic stateless with `thinking_blocks` + `signature`, OpenAI stateful with `previous_response_id`, Gemini with `thinking_config`, DeepSeek with `reasoning_content`. LiteLLM normalizes to `reasoning_content` + optional `thinking_blocks`. **HIGH confidence.**
- **LiteLLM Embeddings** (docs.litellm.ai/docs/embedding/supported_embedding) -- Confirmed dimension differences across providers, `dimensions` parameter only supported by OpenAI text-embedding-3. **HIGH confidence.**
- **TypingMind Documentation** (docs.typingmind.com) -- UI patterns for model selection (search/filter/sort, mid-chat switching, per-model icons), cost estimation before send, hierarchical settings (global -> per-model -> per-agent). **MEDIUM confidence** (changelog-derived, not full feature docs).
- **AURA Codebase Analysis** -- Direct code review of `vertex_ai_client.py` (both apps), `embeddings.py` (both apps), `rag_engine.py`, `genai_client.py`, `chat.py` router. **HIGH confidence.**
