# Domain Pitfalls: Multi-Provider LLM Architecture for AURA

**Domain:** Adding multi-provider LLM support to an existing monorepo (Vertex AI to provider-agnostic router)
**Researched:** 2026-03-10
**Confidence:** HIGH (based on codebase analysis of 35+ Vertex AI integration files, 62+ embedding references, and 45+ streaming references across both AURA apps)

---

## Critical Pitfalls

Mistakes that cause data corruption, production outages, or require full re-indexing of the knowledge graph.

---

### Pitfall 1: Embedding Dimension Mismatch Corrupts Vector Search Silently

**What goes wrong:** A new provider's embedding model produces vectors with different dimensions than the 768-dim vectors already stored in Neo4j. The HNSW index silently rejects or mishandles mismatched vectors, returning zero results or garbage similarity scores without throwing errors.

**Why it happens:** AURA has 768-dimensional embeddings hardcoded at multiple levels:
- Neo4j HNSW indices created with `vector.dimensions: 768` (see `graph_manager.py` lines 204-237, `001_add_module_schema.py`)
- `AURA-CHAT/backend/utils/embeddings.py` uses `config.EMBEDDING_DIMENSIONS` (768)
- `AURA-NOTES-MANAGER/services/embeddings.py` hardcodes `EMBEDDING_DIMENSIONS = 768`
- Test mode generators produce 768-dim vectors (`[((seed + i) % 101) / 100.0 for i in range(768)]`)
- Neo4j has 6+ vector indices: `document_vector_index`, `chunk_vector_index`, plus entity-type indices (`topic_vector_index`, `concept_vector_index`, etc.)

Different providers use different dimensions:
- Gemini `text-embedding-004`: 768 dimensions (current)
- OpenAI `text-embedding-3-small`: 1536 dimensions
- OpenAI `text-embedding-3-large`: 3072 dimensions (supports truncation to 256/1024)
- Cohere `embed-v3`: 1024 dimensions
- Mistral `mistral-embed`: 1024 dimensions
- Ollama models vary wildly (384-4096)

**Consequences:**
- Neo4j HNSW index will throw errors or silently return empty results if you store a 1536-dim vector in a 768-dim index
- Mixed-dimension vectors in the same index corrupt similarity calculations
- RAG queries return irrelevant or no results -- the system *looks* functional but produces bad answers
- **All existing embeddings (~121K LOC worth of processed documents) become useless** if you switch embedding providers without re-indexing
- Cross-module concept discovery breaks because entity embeddings are also dimension-locked

**Warning signs:**
- RAG responses suddenly lose quality without code changes
- `semantic_search` returns empty results or suspiciously low scores
- `db.index.vector.queryNodes` calls return 0 results where they previously returned many
- New documents process successfully but never appear in search results

**Prevention:**
1. **Lock embedding provider separately from generation provider.** The Model Router's `embed()` interface must enforce a single embedding model per Neo4j index. Never allow per-session embedding model overrides.
2. **Add dimension validation at the embedding service boundary.** Before storing any embedding, assert `len(embedding) == expected_dimensions`. Fail loudly.
3. **Store embedding model metadata on each vector.** Add `embedding_model: str` property to Chunk and Entity nodes so you can detect mixed-model contamination.
4. **Build a re-indexing migration tool** for the day you do switch embedding providers. This means: drop old HNSW index, re-embed all chunks and entities, recreate index. Estimate: for 1000 documents at 60s/doc, that is ~17 hours of processing.
5. **Phase 1 of the migration must hardcode the embedding provider** to `text-embedding-004` in the shared router's `embed()` method, regardless of which generation provider is selected.

**Detection:**
- Add a health check that embeds a known test string and queries the vector index, asserting top-1 result matches
- Log embedding dimensions on every `embed()` call
- Add a Neo4j constraint or trigger that rejects embeddings with wrong dimensions (application-level, since Neo4j doesn't have column constraints on arrays)

**Phase to address:** Phase 1 (Model Router core). The `embed()` interface must validate dimensions from day one. This is not a "nice to have" -- it prevents silent data corruption.

---

### Pitfall 2: Streaming API Differences Cause Silent Failures and Lost Tokens

**What goes wrong:** The provider-agnostic streaming interface masks fundamental differences in how providers emit stream chunks, leading to dropped tokens, garbled thinking content, and incomplete responses that appear to work in demos but fail in production.

**Why it happens:** AURA's streaming pipeline is deeply coupled to Vertex AI/Gemini's specific chunking behavior:
- `generate_content_stream()` in `vertex_ai_client.py` (lines 548-602) yields `{"type": "thinking"|"content", "text": str}` chunks
- `_normalize_stream_chunk()` (lines 519-545) parses `chunk.candidates[].content.parts[]` with Gemini-specific attributes (`part.thought`, `part.thought_summary`)
- `stream_response()` in `rag_engine.py` (lines 756-773) expects exactly `{"type": "thinking|content", "text": str}` format
- SSE encoding in `chat.py` (lines 603, 638, 673) wraps chunks in `data: {json}\n\n` format
- `stream_with_timeout()` uses `asyncio.wait_for()` on `stream.__anext__()` -- provider-specific timeout behavior varies

Key streaming differences across providers:
- **Vertex AI/Gemini:** Yields multi-part chunks; thinking and content in separate parts; sync iterator wrapped with `asyncio.to_thread()` (line 591)
- **OpenRouter:** OpenAI-compatible SSE; `delta.content` field; no native thinking separation; some models return `delta.reasoning_content` (non-standard)
- **OpenAI direct:** `chunk.choices[0].delta.content`; streaming tool calls are interleaved; `finish_reason` signals completion
- **Ollama:** Newline-delimited JSON; `response` field for chat; `done: true` terminator; no thinking separation
- **Anthropic (via OpenRouter):** `content_block_delta` events; thinking in separate content blocks with `type: "thinking"`

**Consequences:**
- Thinking content mixed into answer text (user sees raw reasoning)
- Tokens dropped between chunks (incomplete sentences)
- Stream hangs indefinitely on provider timeout differences
- `persist_stream_completion()` in chat.py saves partial answers to conversation history
- SSE `type: "complete"` event never fires if provider stream terminates differently, leaving frontend in loading state
- `stream_with_timeout()` may not detect provider-side timeouts (provider just stops sending)

**Warning signs:**
- Streaming works for Gemini but hangs or garbles text for OpenRouter models
- "complete" SSE event missing for certain providers
- Thinking content appears in the answer text for non-Gemini models
- Frontend loading spinner never stops
- Conversation history contains truncated or duplicate messages

**Prevention:**
1. **Define a canonical stream chunk protocol** in the shared router: `{type: "thinking"|"content"|"error"|"complete", text: str, metadata: dict}`. Every provider adapter must normalize to this format.
2. **Each provider adapter handles its own streaming normalization.** Do NOT try to build a "universal stream normalizer" -- instead, each provider module converts its native format to the canonical format.
3. **Add a sentinel "complete" chunk** at the adapter level, not the consumer level. The RAG engine should never need to detect end-of-stream by exception; the adapter always yields a final `{type: "done"}` chunk.
4. **Test streaming with a "slow provider" mock** that introduces random delays between chunks, partial UTF-8 sequences, and premature disconnections. Test this against the existing SSE pipeline.
5. **Handle the `asyncio.to_thread()` pattern generically.** AURA's Vertex AI adapter wraps a sync iterator with `asyncio.to_thread(next(...))`. OpenAI/OpenRouter SDKs have native async iterators. The adapter must abstract this.
6. **Thinking content normalization per provider:** Gemini has `part.thought=True`, Anthropic has `content_block.type="thinking"`, OpenAI has no native thinking. Map these consistently in each adapter.

**Detection:**
- Integration test that streams from each provider and asserts: chunk count > 0, all chunks match canonical schema, final chunk is "done" type
- Frontend should implement a 60-second stream timeout with user-visible "response timed out" fallback
- Log `stream_chunk_count` and `stream_duration_ms` per request for monitoring

**Phase to address:** Phase 2 (Provider implementations). Each provider adapter must include streaming tests. The Vertex AI refactor (Phase 1) must extract the canonical chunk format first.

---

### Pitfall 3: Migration Breaks Existing Vertex AI Functionality

**What goes wrong:** Refactoring the tightly-coupled Vertex AI code into the shared Model Router breaks production functionality because the existing code is called from dozens of locations with subtle behavioral dependencies.

**Why it happens:** Vertex AI code is deeply scattered across both apps:
- **AURA-CHAT** (20+ files): `backend/utils/vertex_ai_client.py`, `backend/rag_engine.py`, `backend/llm_entity_extractor.py`, `backend/llm_gatekeeper.py`, `backend/semantic_router.py`, `server/routers/chat.py`, plus 15+ test files
- **AURA-NOTES-MANAGER** (15+ files): `services/vertex_ai_client.py`, `services/genai_client.py`, `services/summarizer.py`, `services/summary_service.py`, `services/coc.py`, `services/llm_entity_extractor.py`, `services/embeddings.py`, `api/kg_processor.py`, `api/tasks/document_processing_tasks.py`

Critical behavioral dependencies:
- **Two different Vertex AI clients:** AURA-CHAT uses `google-genai` SDK (new) via `_GenerativeModelWrapper`; AURA-NOTES-MANAGER uses the old `vertexai.generative_models.GenerativeModel` directly. They have different APIs, auth patterns, and error types.
- **Location routing:** AURA-CHAT has `resolve_model_location()` that routes Gemini 3 to "global" and Gemini 2.5 to fallback regions. AURA-NOTES-MANAGER has `_normalize_location()` with different logic.
- **Safety settings:** AURA-NOTES-MANAGER has `block_none_safety_settings()` for academic content; AURA-CHAT does not use safety settings.
- **Thinking mode:** AURA-CHAT has `_build_stream_thinking_config()` that handles both `thinking_budget` (Gemini 2.5) and `thinking_level` (Gemini 3). AURA-NOTES-MANAGER has no thinking mode at all.
- **Test mode:** Both apps use `AURA_TEST_MODE` but with different mock implementations (`_TestGenerativeModel` has different return shapes).
- **Auth chain:** AURA-CHAT uses `VERTEX_PROJECT` + `VERTEX_REGION`; AURA-NOTES-MANAGER uses `VERTEX_PROJECT` + `VERTEX_LOCATION`. Different env var names for the same concept.

**Consequences:**
- Changing the Vertex AI client interface breaks one app while fixing the other
- KG processing pipeline (Celery tasks) silently fails because it expects specific response shapes from `generate_content()`
- Summarization pipeline produces empty notes because the response `.text` attribute path changes
- Entity extraction returns malformed JSON because the generation config is slightly different
- Auth works in AURA-CHAT but fails in AURA-NOTES-MANAGER (or vice versa) because of env var naming differences
- 210+ existing tests start failing due to mock interface changes

**Warning signs:**
- "Works in AURA-CHAT, broken in AURA-NOTES-MANAGER" (or vice versa)
- Celery tasks fail with `AttributeError` on response objects
- Entity extraction returns unparseable JSON
- Test suite passes for one app but fails for the other
- Auth errors appear after migration despite no credential changes

**Prevention:**
1. **Strangler Fig pattern, not Big Bang.** The shared Model Router wraps the existing code first, then gradually replaces internals. Never remove the old `vertex_ai_client.py` files until the router is proven.
2. **Phase 1 deliverable: Vertex AI provider that passes ALL existing tests unchanged.** The first provider implementation must be a thin wrapper around the existing code, not a rewrite. If existing tests fail, the migration is wrong.
3. **Normalize env vars immediately.** Create a shared config that maps both `VERTEX_REGION` and `VERTEX_LOCATION` to a single canonical `PROVIDER_REGION` in the shared package. Both apps read from the same source.
4. **Create adapter tests for EACH call site.** For every file that imports from `vertex_ai_client`, create an integration test that verifies the Model Router produces identical output. There are 35+ files importing Vertex AI.
5. **Keep safety settings configurable per-app.** AURA-NOTES-MANAGER needs `BLOCK_NONE` for academic content; AURA-CHAT may want different defaults. The Model Router should accept safety settings as a parameter, not hardcode them.
6. **Keep thinking mode as an AURA-CHAT-only feature initially.** Do not try to unify thinking mode handling in Phase 1.

**Detection:**
- Run the full test suite (210+ unit tests, 65+ E2E tests) after each migration step
- Add a "canary" test that makes a real API call through the Model Router and compares output shape with the old direct call
- Monitor Celery task success rate before and after migration

**Phase to address:** Phase 1 (Vertex AI refactor into shared router). This is the highest-risk phase. Budget extra time for regression testing. Expect 2-3x the estimated time.

---

### Pitfall 4: Shared Package Dependency Hell in the Monorepo

**What goes wrong:** The shared `model_router` package at `shared/model_router/` creates import nightmares, version conflicts, and circular dependencies between the two FastAPI apps that have different Python dependency versions.

**Why it happens:** AURA's monorepo has nested git repos and independent dependency trees:
- `AURA-CHAT/` and `AURA-NOTES-MANAGER/` each have their own `.git/`, `requirements.txt`, and virtual environments
- The project uses a single root venv (`../.venv`), but both apps have different transitive dependencies
- AURA-CHAT already migrated to `google-genai` SDK; AURA-NOTES-MANAGER still uses `vertexai.generative_models` directly
- Different Python path manipulation (`sys.path.insert(0, ...)`) is used extensively in both apps
- AURA-NOTES-MANAGER's `embeddings.py` does `from services.vertex_ai_client import init_vertex_ai` -- relative imports that break if the package structure changes

Specific dependency conflicts:
- `google-genai` SDK (AURA-CHAT) vs `vertexai.generative_models` (AURA-NOTES-MANAGER): different import paths, different response types
- Both apps import `google.auth` but may expect different versions
- Celery workers in AURA-NOTES-MANAGER run in a separate process with their own `sys.path`
- The shared package needs to be importable from both `AURA-CHAT/backend/` and `AURA-NOTES-MANAGER/api/` contexts

**Consequences:**
- `ImportError: No module named 'shared.model_router'` in one app but not the other
- Celery workers cannot import the shared package because their `sys.path` is different from the API process
- Version conflict: upgrading a dependency for the shared package breaks one app's existing code
- Circular imports: shared package needs provider configs, provider configs need app-specific settings
- Test isolation breaks: running AURA-CHAT tests imports AURA-NOTES-MANAGER code via the shared package

**Warning signs:**
- Import errors that only appear in Celery workers, not in the API
- Tests pass locally but fail in CI because of different working directories
- One app works, the other gets `ModuleNotFoundError`
- `pip install -e .` for the shared package causes dependency conflicts

**Prevention:**
1. **Use a proper Python package with `pyproject.toml`.** The shared package at `shared/model_router/` should be installable with `pip install -e ./shared/model_router` from the root venv. No `sys.path` hacking.
2. **Minimal dependencies in the shared package.** The shared package should depend only on: `httpx` (for OpenRouter), `pydantic` (for schemas). Provider-specific SDKs (`google-genai`, `vertexai`, `ollama`) should be optional extras.
3. **Provider registration pattern.** The shared package defines interfaces; each app registers its providers at startup. The shared package never imports from `AURA-CHAT` or `AURA-NOTES-MANAGER` directly.
4. **Test the Celery import path explicitly.** Add a test that simulates the Celery worker's `sys.path` and verifies the shared package is importable.
5. **Pin shared package dependencies in the root `requirements.txt`.** Both apps install the same shared package version from the same venv.
6. **Avoid `from shared.model_router import *`** -- use explicit imports to prevent namespace pollution.

**Detection:**
- CI pipeline that runs both apps' test suites after any change to the shared package
- `python -c "from shared.model_router import ModelRouter"` as a build step for both apps
- Celery worker startup health check that verifies shared package imports

**Phase to address:** Phase 1 (shared package setup). Get the package structure right before writing any provider code. Wrong package structure cascades into every subsequent phase.

---

## Moderate Pitfalls

---

### Pitfall 5: Cost Tracking Inaccuracies Across Different Pricing Models

**What goes wrong:** The usage tracking and cost dashboard reports incorrect costs because different providers have wildly different pricing models, token counting methods, and billing granularity.

**Why it happens:**
- Gemini prices per character, not per token (for some models)
- OpenRouter charges per token with model-specific rates that change frequently; some models have different input/output rates
- Ollama is free but has compute cost implications
- Token counting differs: Gemini uses its own tokenizer; OpenAI uses tiktoken; OpenRouter uses the underlying model's tokenizer
- Streaming responses may not include token counts in every chunk (Gemini returns usage metadata only in the final chunk; OpenRouter may include `usage` only if requested)
- Thinking tokens: Gemini 2.5 charges for thinking tokens at reduced rates; Gemini 3 uses thinking levels (no explicit token count); most providers do not charge for thinking separately

**Consequences:**
- Cost dashboard shows estimates that are 2-5x off from actual billing
- Budget alerts trigger too early or too late
- Users cannot compare cost across providers meaningfully
- Usage data is incomplete for streaming responses if the final chunk is lost (client disconnect)

**Prevention:**
1. **Track tokens at the provider adapter level, not the application level.** Each provider adapter extracts token counts from its native response format.
2. **Distinguish input tokens, output tokens, and thinking tokens** in the usage schema. Store all three separately.
3. **Use provider-reported token counts, not local estimates.** Never count tokens yourself unless the provider does not report them.
4. **Cache OpenRouter pricing data** and refresh it periodically (their `/api/v1/models` endpoint includes pricing). Do not hardcode prices.
5. **Handle the "final chunk lost" case.** If a streaming response completes but the usage metadata is missing, estimate based on text length and flag it as estimated.
6. **Store raw provider usage metadata** alongside normalized counts for auditing.

**Phase to address:** Phase 3 (Usage tracking). Must be built into the provider adapters from Phase 2, but the dashboard and aggregation come in Phase 3.

---

### Pitfall 6: Provider Fallback Loses Streaming State and Context

**What goes wrong:** When the primary provider fails mid-stream, the fallback mechanism either restarts from scratch (losing already-streamed content) or tries to resume with a different model (producing incoherent output).

**Why it happens:**
- AURA's current streaming pipeline in `chat.py` uses SSE events. Once chunks are sent to the client, they cannot be recalled.
- Provider failures can happen at any point: before first chunk, mid-stream, or right before completion
- Different providers have different context window sizes, so a fallback model may not accept the same prompt length
- The RAG context (`context_str` in `rag_engine.py`) is assembled before streaming starts, but the generation config may need to change for the fallback model
- Thinking mode may not be available on the fallback provider

**Consequences:**
- User sees partial answer followed by error, then a completely different answer from the fallback
- Conversation history gets corrupted with partial responses
- Thinking content from the primary model is lost; fallback model produces different reasoning
- Frontend state becomes inconsistent (loading indicator off, but answer incomplete)

**Prevention:**
1. **Do NOT implement mid-stream fallback for v1.1.** It is not worth the complexity. If a stream fails, send an error event and let the client retry with the fallback provider.
2. **Pre-flight health checks** before starting a stream. Ping the provider (or check recent success rate) before committing to a streaming response.
3. **Buffer the first N chunks** (e.g., first 3 chunks or 500ms) before sending to the client. If the provider fails in this window, switch to fallback transparently.
4. **Store which provider was used** in the conversation history alongside the message, so re-tries know to use a different provider.
5. **Client-side retry logic.** The frontend should detect SSE error events and automatically retry with the next provider in the fallback chain, displaying a brief notification.

**Phase to address:** Phase 2 (Provider implementations). Fallback logic should be simple (pre-flight + retry) in v1.1. Mid-stream fallback is a v1.2+ feature.

---

### Pitfall 7: OpenRouter API Quirks and Rate Limiting

**What goes wrong:** OpenRouter is treated as a simple OpenAI-compatible API, but it has significant behavioral differences that cause silent failures, unexpected costs, and intermittent errors.

**Why it happens:**
- OpenRouter routes to 200+ models from different providers. Each underlying model has different capabilities, rate limits, and response formats.
- OpenRouter's rate limiting is per-user, per-model, and includes soft limits that return 200 OK with truncated responses instead of 429 errors.
- Some models behind OpenRouter do not support streaming, system messages, or function calling -- but OpenRouter does not always return clear errors.
- Model availability changes without notice (models go offline, pricing changes, new versions replace old ones).
- OpenRouter adds latency (50-200ms) as a routing layer on top of the underlying provider's latency.

Specific quirks relevant to AURA:
- `reasoning_content` field in streaming responses is non-standard and only supported by some models (DeepSeek R1, etc.)
- Token limits reported by OpenRouter's model list may not match actual limits
- Some models return empty responses instead of errors when they cannot process a request
- Rate limit headers use non-standard names (`X-RateLimit-Limit`, not standard OpenAI format)

**Consequences:**
- Requests silently return empty or truncated responses
- Rate limiting causes intermittent failures that are hard to reproduce
- Cost tracking is inaccurate because some models report tokens differently
- Model list in the UI shows models that are temporarily unavailable
- Streaming appears to work but produces garbage for models that do not truly support it

**Prevention:**
1. **Maintain a curated allowlist of tested models**, not just "all 200+ models." Test each model against AURA's specific needs (academic RAG, streaming, context window).
2. **Implement model capability detection.** Query OpenRouter's model metadata to check for streaming support, context window size, and pricing before offering a model to users.
3. **Add response validation.** After every generation, check that the response is non-empty and meets minimum quality criteria. Log and retry if validation fails.
4. **Handle OpenRouter-specific rate limit headers.** Parse `X-RateLimit-*` headers and implement client-side throttling.
5. **Cache the model list** and refresh periodically (every 5 minutes). Do not query `/api/v1/models` on every request.
6. **Add timeouts specific to OpenRouter** (longer than direct API calls due to routing overhead). AURA's current 30s timeout for simple_lookup may be too tight for OpenRouter.

**Phase to address:** Phase 2 (OpenRouter provider implementation). The model allowlist curation is a Phase 3 concern (UI/settings).

---

### Pitfall 8: Configuration Synchronization Across Two Apps

**What goes wrong:** Provider settings (model selection, API keys, default provider) get out of sync between AURA-CHAT and AURA-NOTES-MANAGER, leading to one app using a model that the other does not support, or one app running with stale configuration.

**Why it happens:**
- AURA already has configuration scattered across:
  - `AURA-CHAT/backend/utils/config.py`: `RAG_MODEL_DEFAULT`, `RAG_ALLOWED_MODELS`, `CHAT_MODELS_WITH_THINKING`
  - `AURA-NOTES-MANAGER/api/config.py`: `LLM_ENTITY_EXTRACTION_MODEL`, `LLM_SUMMARIZATION_MODEL`, `EMBEDDING_MODEL`
  - Environment variables: `VERTEX_PROJECT`, `VERTEX_REGION` (CHAT) vs `VERTEX_LOCATION` (NOTES)
- The v1.1 milestone adds: global defaults, per-session overrides, provider selection, API keys for multiple providers
- Both apps run as separate processes; changes to config in one do not propagate to the other
- Celery workers have their own config loading path

**Consequences:**
- User sets default model to "gpt-4o" via AURA-CHAT settings, but AURA-NOTES-MANAGER's KG processing still uses Gemini (expected behavior, but confusing if not clearly communicated)
- API keys stored in one app's config but not available in the other
- Provider goes down; one app falls back to alternative, the other does not
- Celery worker uses stale model configuration because it does not re-read config

**Prevention:**
1. **Separate "generation" config from "processing" config.** AURA-CHAT's interactive chat model selection is user-facing. AURA-NOTES-MANAGER's KG processing model is an operational setting. Do not conflate them.
2. **Shared config source for API keys and provider availability.** Store provider API keys in a shared location (e.g., shared `.env` at project root, or a shared config service). Both apps read from the same source.
3. **Immutable config for Celery workers.** Celery workers should read config at startup and not change mid-task. Provide a "reload config" task for updates.
4. **Configuration schema validation on startup.** Both apps validate that all required provider configs are present and consistent at boot time.
5. **Clear UI distinction.** The settings UI should make it obvious which settings affect chat (AURA-CHAT only) vs which affect document processing (AURA-NOTES-MANAGER only) vs which are global.

**Phase to address:** Phase 1 (shared package config), Phase 4 (UI clarity). Config schema design is Phase 1; UI distinction is Phase 4.

---

### Pitfall 9: Thinking Mode / Reasoning Differences Across Providers

**What goes wrong:** AURA's thinking mode implementation, deeply tied to Gemini's specific thinking API, produces broken or missing reasoning content when used with other providers.

**Why it happens:** AURA-CHAT has a sophisticated thinking mode pipeline:
- `_build_stream_thinking_config()` in `vertex_ai_client.py` handles Gemini 2.5 (`thinking_budget`) and Gemini 3 (`thinking_level`)
- `_normalize_stream_chunk()` detects thinking parts via `part.thought == True` and `part.thought_summary`
- `BUDGET_TO_THINKING_LEVEL` mapping converts token budgets to Gemini 3's enum levels
- `INTENT_THINKING_BUDGETS` in config maps query intents to thinking budgets (chitchat: 512, simple_lookup: 1024, deep_research: 4096)
- Frontend UI streams thinking content separately from answer content
- Conversation history stores `thinking_content` in Message nodes

Different providers handle reasoning differently:
- **Gemini 2.5:** `thinking_budget` parameter, `thought=True` on stream parts
- **Gemini 3:** `thinking_level` enum (LOW/MEDIUM/HIGH), `thought=True` on stream parts
- **DeepSeek R1 (via OpenRouter):** `reasoning_content` in non-streaming; `delta.reasoning_content` in streaming
- **Claude (via OpenRouter):** `content_block_delta` with `type: "thinking"` blocks (requires extended thinking beta header)
- **OpenAI o1/o3:** No exposed thinking content; reasoning is internal-only
- **Most other models:** No thinking/reasoning support at all

**Consequences:**
- Thinking UI shows nothing for models that do not support it (confusing UX)
- Thinking UI shows raw JSON or garbled text for models with non-standard thinking formats
- Intent-based thinking budget (deep_research: 4096 tokens) is meaningless for non-Gemini models
- Frontend crashes or shows errors when thinking content structure is unexpected

**Prevention:**
1. **Model capability flags.** The Model Router's model metadata must include `supports_thinking: bool` and `thinking_format: "gemini"|"deepseek"|"anthropic"|"none"`. The UI and backend use these flags.
2. **Graceful degradation.** If a model does not support thinking, skip thinking entirely -- do not send an error. The UI should hide the thinking panel for non-thinking models.
3. **Normalize thinking output per provider.** Each provider adapter converts its native thinking format to `{"type": "thinking", "text": str}` chunks. If the model has no thinking, it simply never yields thinking chunks.
4. **Do not expose thinking budget controls for non-Gemini models.** The intent-based budget mapping only applies to Gemini. For other models, either use their native reasoning control (if any) or omit it.
5. **Store `thinking_model` alongside `thinking_content` in Message nodes** so the UI knows how to render it.

**Phase to address:** Phase 2 (provider adapters must declare capabilities), Phase 4 (UI must respect capability flags).

---

## Minor Pitfalls

---

### Pitfall 10: Celery Task Pipeline Expects Specific Response Formats

**What goes wrong:** KG processing tasks in `document_processing_tasks.py` parse LLM responses for entity extraction using Gemini-specific response parsing that breaks with other providers.

**Why it happens:** The KG processor (`kg_processor.py`) calls `generate_content()` and parses the `response.text` attribute for JSON entity extraction results. Different providers return responses with different attributes and JSON formatting.

**Prevention:**
1. The Model Router's `generate()` method must return a normalized response object with a `.text` property, regardless of provider.
2. Add response format validation in the entity extraction pipeline -- verify JSON parsability before processing.
3. For v1.1, KG processing should remain on Vertex AI. Multi-provider for KG processing is a v1.2+ feature.

**Phase to address:** Phase 1 (response normalization in the Model Router interface).

---

### Pitfall 11: UI State Management for Hierarchical Provider Selection

**What goes wrong:** The provider selection UI (2-level for Vertex/Ollama, 3-level for OpenRouter) creates complex state management that conflicts with AURA's existing Zustand stores and TanStack Query caching.

**Why it happens:**
- AURA-CHAT already has model selection in the chat config (`/chat/config` endpoint)
- Adding provider > model > variant hierarchy means the settings state needs to cascade: changing provider resets model list, changing model resets variant
- Session-level overrides conflict with global defaults
- TanStack Query may cache the old model list after provider change

**Prevention:**
1. **Single source of truth for active model config.** Use a Zustand store with `{provider, model, variant}` that the chat hooks read from. TanStack Query fetches available options; Zustand holds the selection.
2. **Invalidate model list queries when provider changes.** Use TanStack Query's `queryClient.invalidateQueries()` on provider change.
3. **Optimistic UI updates** for model selection -- do not wait for server confirmation to show the new selection.

**Phase to address:** Phase 4 (Frontend UI). Design the state management pattern before implementing UI components.

---

### Pitfall 12: Test Mode Divergence Between Apps

**What goes wrong:** The `AURA_TEST_MODE` mock implementations diverge between the shared router's test mode and each app's existing test mode, causing test failures.

**Why it happens:** Both apps have `_TestGenerativeModel` classes that return hardcoded responses. The shared Model Router needs its own test mode that is compatible with both apps' test expectations.

**Prevention:**
1. The shared Model Router's test mode must produce responses that satisfy both apps' test assertions.
2. Keep existing `_TestGenerativeModel` classes during migration. Only remove them after all tests pass through the Model Router's test mode.
3. Add a `ModelRouter.test_mode()` factory that returns a pre-configured test router matching the existing mock behavior.

**Phase to address:** Phase 1 (shared package). Test mode compatibility is a Phase 1 requirement.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Phase 1: Model Router Core + Vertex AI Refactor | Pitfall 3 (migration breaks existing), Pitfall 4 (shared package imports), Pitfall 1 (embedding dimension validation) | Strangler Fig pattern; installable package; dimension assertions |
| Phase 2: OpenRouter + Ollama Providers | Pitfall 2 (streaming differences), Pitfall 7 (OpenRouter quirks), Pitfall 9 (thinking mode) | Canonical stream protocol; curated model allowlist; capability flags |
| Phase 3: Usage Tracking + Cost Dashboard | Pitfall 5 (cost inaccuracies) | Provider-reported tokens; cached pricing; estimated flag |
| Phase 4: Frontend UI | Pitfall 11 (UI state), Pitfall 8 (config sync) | Zustand single source; clear settings scope distinction |
| Phase 5: Migration + Integration Testing | Pitfall 3 (regression), Pitfall 6 (fallback behavior) | Full test suite regression; no mid-stream fallback in v1.1 |

---

## Summary of Severity by Phase

| Pitfall | Severity | Silent? | Data Loss? | Phase |
|---------|----------|---------|------------|-------|
| 1. Embedding dimension mismatch | CRITICAL | Yes | Yes (corrupted index) | 1 |
| 2. Streaming API differences | CRITICAL | Yes | No | 2 |
| 3. Migration breaks existing code | CRITICAL | No | No | 1 |
| 4. Shared package dependency hell | CRITICAL | No | No | 1 |
| 5. Cost tracking inaccuracies | MODERATE | Yes | No | 3 |
| 6. Provider fallback state loss | MODERATE | Partially | Partially | 2 |
| 7. OpenRouter quirks | MODERATE | Yes | No | 2 |
| 8. Config sync across apps | MODERATE | Partially | No | 1, 4 |
| 9. Thinking mode differences | MODERATE | Partially | No | 2, 4 |
| 10. Celery response format | MINOR | No | No | 1 |
| 11. UI state management | MINOR | No | No | 4 |
| 12. Test mode divergence | MINOR | No | No | 1 |

---

## Sources

- Codebase analysis: `AURA-CHAT/backend/utils/vertex_ai_client.py` (652 lines, dual SDK approach)
- Codebase analysis: `AURA-CHAT/backend/utils/embeddings.py` (372 lines, 768-dim hardcoded)
- Codebase analysis: `AURA-NOTES-MANAGER/services/embeddings.py` (645 lines, 768-dim hardcoded)
- Codebase analysis: `AURA-NOTES-MANAGER/services/vertex_ai_client.py` (313 lines, old SDK)
- Codebase analysis: `AURA-CHAT/server/routers/chat.py` (791 lines, SSE streaming)
- Codebase analysis: `AURA-CHAT/backend/rag_engine.py` (streaming pipeline, thinking mode)
- Codebase analysis: `AURA-CHAT/backend/graph_manager.py` (6+ HNSW indices at 768 dims)
- Codebase analysis: `AURA-NOTES-MANAGER/api/migrations/001_add_module_schema.py` (768-dim HNSW)
- Codebase analysis: `AURA-NOTES-MANAGER/api/tasks/document_processing_tasks.py` (Celery pipeline)
- Codebase analysis: `.planning/PROJECT.md` (v1.1 milestone context)
- Training data (HIGH confidence): OpenAI, Cohere, Mistral embedding dimensions
- Training data (MEDIUM confidence): OpenRouter API behavior, rate limiting patterns
- Training data (MEDIUM confidence): Streaming format differences across providers
