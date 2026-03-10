# Project Research Summary

**Project:** AURA Multi-Provider LLM Support (v1.1)
**Domain:** Multi-provider LLM abstraction layer for dual-app academic RAG monorepo
**Researched:** 2026-03-10
**Confidence:** HIGH

## Executive Summary

AURA v1.1 adds multi-provider LLM support to an existing dual-app monorepo (AURA-CHAT for students, AURA-NOTES-MANAGER for staff) that is currently tightly coupled to Google Vertex AI. The proven approach for this type of integration is a thin, in-process routing abstraction -- not a heavyweight framework like LiteLLM or LangChain -- that normalizes generation requests, streaming responses, and error handling across providers. The recommended architecture is a shared Python package (`shared/model_router/`) using Protocol/ABC-based provider contracts, installed in the existing root venv via `pip install -e`. This package is consumed by both FastAPI backends through constructor injection. For the frontend, components should be built in AURA-CHAT (React 19) first and copied to AURA-NOTES-MANAGER (React 18) rather than creating a shared npm package, because the React version gap makes shared packages fragile.

The three providers are: Vertex AI (refactored from existing code, remains the default and only embedding provider), OpenRouter (200+ models via the `openai` SDK with custom `base_url`), and Ollama (local models, stub-only in v1.1). The critical user-facing value is per-session model switching in AURA-CHAT -- students pick any available model for their study session. Supporting this requires 8 table-stakes backend capabilities (unified generate/embed interfaces, streaming, configuration, error normalization, model discovery, API key management) and 4 high-value differentiators (hierarchical model selector UI, inline chat model picker, usage tracking with cost dashboard, and thinking mode standardization across providers).

The dominant risk is Phase 1: refactoring the existing Vertex AI integration into the shared router without breaking either app. AURA-CHAT and AURA-NOTES-MANAGER use different Vertex AI SDKs (`google-genai` vs `vertexai.generative_models`), different env var names for the same concepts (`VERTEX_REGION` vs `VERTEX_LOCATION`), and different streaming/thinking patterns. Three of four critical pitfalls converge in Phase 1. The mitigation is a Strangler Fig pattern -- wrap existing code first, verify all 210+ tests pass through the new interface, then gradually move logic inside. Budget 2-3x estimated time for Phase 1. The second major risk is embedding dimension lock-in: AURA's Neo4j HNSW indices are hardcoded to 768 dimensions (Vertex AI's `text-embedding-004`), and switching embedding providers silently corrupts vector search. The embed() interface must enforce a single provider per deployment from day one.

## Key Findings

### Recommended Stack

The new dependency surface is intentionally minimal: two Python libraries (`openai>=2.26.0` for OpenRouter, `ollama>=0.6.1` for local models) and one frontend library (`recharts@^3.8.0` for the cost dashboard). The existing stack (FastAPI, React, Neo4j, TanStack Query, Zustand, TailwindCSS, Pydantic, Redis) covers all other needs. LiteLLM, LangChain, and the official `openrouter` SDK were evaluated and explicitly rejected for good reasons (dependency bloat, scope mismatch, beta instability respectively).

**Core technologies:**
- `openai` SDK (>=2.26.0): OpenRouter client -- OpenAI-compatible API via custom `base_url`, mature, async-first, streaming SSE. OpenRouter officially recommends this approach over their own beta SDK.
- `ollama` SDK (>=0.6.1): Local model client -- official package, `AsyncClient`, methods map directly to REST API (`chat`, `generate`, `embed`, `list`). Stub-only for v1.1.
- `pydantic-settings` (>=2.13.0): Hierarchical configuration -- upgrade from existing >=2.1.0, supports nested models for global + per-session provider configs.
- `recharts` (^3.8.0): Cost/usage dashboard charts -- React-native, SVG-based, works with both React 18 and 19, lightweight.
- Shared Python package (`shared/model_router/`): Custom Protocol-based provider abstraction -- zero external framework dependencies, full control over routing, error normalization, and cost tracking hooks.

**Critical version requirement:** `openai>=2.26.0` specifically, because earlier versions lack `base_url` configuration stability. Both `openai` and `ollama` use `httpx` internally, which is already in the dependency tree -- no conflicts expected.

See [STACK.md](STACK.md) for full rationale, alternatives considered, and version compatibility matrix.

### Expected Features

All 8 table stakes features are genuinely required -- they form the backbone of the abstraction. Skipping any one makes the system feel broken or incomplete. Among differentiators, usage tracking (D-3) must be wired in from the start because retrofitting instrumentation is significantly harder than building alongside the router.

**Must have (table stakes):**
- **TS-1: Unified generate() interface** -- single function routing to correct provider. The entire point of the milestone.
- **TS-2: Unified embed() interface** -- future-proofs embeddings, but locked to Vertex AI per deployment. Switching requires full re-indexing.
- **TS-3: Streaming response support** -- AURA-CHAT already streams via SSE. Removing streaming for non-Vertex providers is a visible regression.
- **TS-4: Global provider configuration** -- system needs defaults to function. Hierarchy: env vars > admin settings > per-session override.
- **TS-5: Per-session model override** -- primary user-facing value. Students pick models for their study session.
- **TS-6: Error handling normalization** -- unified error hierarchy (auth, rate limit, content policy, model unavailable, timeout).
- **TS-7: Model discovery/listing** -- dynamic model lists from each provider, cached with 5-60 min TTL.
- **TS-8: API key management** -- secure storage, validation, masked display. Ollama needs no key.

**Should have (differentiators):**
- **D-1: Hierarchical provider selection UI** -- 2-level (Vertex/Ollama) or 3-level (OpenRouter: vendor > model) selector. Makes 200+ models manageable.
- **D-2: Inline contextual model selector** -- compact picker in chat interface for quick mid-session model switching.
- **D-3: Usage tracking with cost dashboard** -- token/cost tracking per request, aggregated by session/user/model. Wire in from Phase 1.
- **D-5: Thinking mode standardization** -- extend existing Gemini thinking mode to other providers. Pedagogically valuable.

**Defer to v1.2:**
- **D-4: Budget controls with alerts** -- valuable but depends on usage tracking being proven first.
- **D-6: Provider fallback** -- automatic failover is complex (especially mid-stream). Manual model switching is acceptable for v1.1.

**Anti-features (explicitly do NOT build):**
- User-facing embedding provider switching (corrupts vector search)
- Real-time price comparison engine (latency, complexity, marginal value)
- Self-hosted LLM proxy/gateway (scope creep)
- Fine-tuning/custom model training UI (out of scope)
- Per-user BYOK API key management (security nightmare in academic setting)
- Provider-specific advanced parameter exposure (overwhelming UI)

See [FEATURES.md](FEATURES.md) for detailed feature cards, dependency graph, and migration code map.

### Architecture Approach

The architecture centers on a shared Python package (`shared/model_router/`) that defines provider-agnostic types (`GenerateRequest`, `GenerateResponse`, `StreamChunk`) and routes requests to the appropriate provider via model name prefix routing (slash = OpenRouter, plain name = Vertex AI). Generation and embedding are separated into distinct ABCs because they are fundamentally different concerns -- AURA already treats them separately, and forcing them together creates leaky abstractions. Both FastAPI apps register providers at startup via dependency injection and expose new REST endpoints for model discovery, health checks, and usage data. The frontend uses copy-with-convention (build in AURA-CHAT, copy to AURA-NOTES-MANAGER) rather than a shared npm package.

**Major components:**
1. **`shared/model_router/`** -- Provider abstraction, request routing, type definitions, error hierarchy, usage tracking. Installed in root venv via `pip install -e`.
2. **Provider implementations** (VertexAIProvider, OpenRouterProvider, OllamaProvider) -- Each normalizes its native SDK into the shared types. Vertex AI wraps existing code; OpenRouter uses `httpx` directly; Ollama is a stub with health-check/model-listing only.
3. **App-level DI registration** (`server/dependencies.py` in AURA-CHAT, `api/dependencies.py` in AURA-NOTES-MANAGER) -- Singleton ModelRouter with lazy initialization, injected into services via constructors.
4. **Compatibility shims** -- Existing `vertex_ai_client.py` files kept during migration, delegating to ModelRouter. Removed only after all callers are migrated and tests pass.
5. **REST API layer** (`routers/providers.py` in both apps) -- New endpoints for model listing, health status, usage data, provider config.
6. **Frontend provider features** (`features/providers/` in both apps) -- Provider selector, model selector, settings page, usage dashboard. Zustand for selection state, TanStack Query for server data.

**Key patterns to follow:**
- Provider-agnostic request/response types everywhere outside provider implementations
- Constructor injection over import-time coupling (testability)
- Strangler Fig migration with compatibility shims
- Model name prefix routing convention (slash = OpenRouter)
- Fail-safe to default provider on errors
- Hierarchical config: per-request > per-session > user default > system default

See [ARCHITECTURE.md](ARCHITECTURE.md) for full component diagrams, data flows, code examples, and anti-patterns.

### Critical Pitfalls

Research identified 4 critical, 5 moderate, and 3 minor pitfalls. The critical ones all converge in Phase 1, making it the highest-risk phase.

1. **Embedding dimension mismatch corrupts vector search silently** -- Neo4j HNSW indices are hardcoded to 768 dimensions across 6+ indices. Switching embedding providers produces vectors of different dimensions, causing zero or garbage search results with no errors. **Avoid by:** locking embedding provider at deployment level, adding dimension validation at the service boundary, never allowing per-session embedding overrides.

2. **Streaming API differences cause silent failures** -- AURA's streaming pipeline is deeply coupled to Gemini's chunking behavior. OpenRouter, Ollama, and Anthropic all have different streaming formats, thinking content separation, and termination signals. **Avoid by:** defining a canonical stream chunk protocol, making each provider adapter responsible for its own normalization, and adding sentinel "complete" chunks at the adapter level.

3. **Migration breaks existing Vertex AI functionality** -- 35+ files across both apps import Vertex AI code, using two different SDKs with different auth patterns, location routing, and safety settings. A naive refactor breaks production. **Avoid by:** Strangler Fig pattern -- wrap existing code first, verify all 210+ tests pass unchanged, then gradually move logic inside. Budget 2-3x time for Phase 1.

4. **Shared package dependency hell** -- The monorepo has nested git repos, independent dependency trees, and Celery workers with separate `sys.path`. A poorly structured shared package causes import failures. **Avoid by:** proper `pyproject.toml` packaging, minimal core dependencies (only `httpx` + `pydantic`), provider SDKs as optional extras, and explicit Celery import path testing.

5. **Configuration sync across two apps** -- Provider settings, API keys, and defaults can drift between AURA-CHAT and AURA-NOTES-MANAGER. **Avoid by:** shared config source for API keys, separate "generation" config (user-facing) from "processing" config (operational), clear UI distinction of setting scope.

See [PITFALLS.md](PITFALLS.md) for all 12 pitfalls with detailed warning signs, prevention strategies, and detection approaches.

## Implications for Roadmap

Based on combined research across all four files, here is the recommended phase structure. The ordering is driven by technical dependencies (types before providers, providers before UI), risk concentration (Phase 1 gets the most attention because 3 critical pitfalls converge there), and user value delivery (per-session model switching is the earliest visible feature).

### Phase 1: Shared Package Foundation + Vertex AI Refactor
**Rationale:** Everything depends on the shared types and router skeleton. The Vertex AI provider must work through the new interface before adding new providers, because existing functionality must not regress. This is the highest-risk phase -- three critical pitfalls (migration breakage, shared package imports, embedding dimension validation) all land here.
**Delivers:** Installable `shared/model_router/` package with types, error hierarchy, base ABCs, `ModelRouter` class, `VertexAIProvider` wrapping existing code, compatibility shims in both apps, and all 210+ existing tests passing unchanged.
**Addresses features:** TS-1 (generate interface), TS-2 (embed interface), TS-6 (error normalization foundation)
**Avoids pitfalls:** P3 (Strangler Fig, not Big Bang), P4 (proper pyproject.toml packaging), P1 (embed dimension validation from day one), P10 (response normalization), P12 (test mode compatibility)
**Stack:** `pydantic-settings>=2.13.0`, shared package `pyproject.toml`
**Time estimate:** Budget 2-3x normal estimation due to critical risk concentration.

### Phase 2: OpenRouter Provider + Streaming Normalization
**Rationale:** New functionality only after existing functionality is proven through the new interface. OpenRouter is the highest-value new provider (200+ models). Streaming normalization must be solved here because it is the second critical pitfall.
**Delivers:** `OpenRouterProvider` with completions, streaming, model listing, credit check. Canonical stream chunk protocol tested against Vertex AI and OpenRouter. Ollama stub with health check and model listing only.
**Addresses features:** TS-3 (streaming), TS-7 (model discovery), TS-8 (API key management), D-5 (thinking mode foundation -- capability flags)
**Avoids pitfalls:** P2 (per-provider stream normalization, not universal normalizer), P7 (curated model allowlist, response validation, OpenRouter-specific timeouts), P9 (capability flags for thinking mode), P6 (no mid-stream fallback -- pre-flight + client retry only)
**Stack:** `openai>=2.26.0`, `ollama>=0.6.1`

### Phase 3: Cross-App Migration + Backend Integration
**Rationale:** Once both Vertex AI and OpenRouter work through the router, wire both apps to use it for all LLM calls. This is the "swap the plumbing" phase -- zero behavior change from the user perspective, but the new architecture is in place.
**Delivers:** Both `AURA-CHAT` and `AURA-NOTES-MANAGER` using `ModelRouter` for all LLM calls. Updated `dependencies.py` in both apps. Compatibility shims still present but all direct `get_model()` calls removed. New REST endpoints for `/providers/models`, `/providers/health`.
**Addresses features:** TS-4 (global configuration -- config hierarchy implemented), TS-5 (per-session override backend -- session `model_id` field)
**Avoids pitfalls:** P3 (regression testing after each migration step), P8 (shared config source, separate generation vs processing config), P10 (Celery tasks verified)

### Phase 4: Frontend -- Provider Settings + Model Selection UI
**Rationale:** Backend API must exist before frontend can consume it. This phase delivers the primary user-visible feature: model selection in the chat UI.
**Delivers:** Provider settings page (both apps), updated inline model selector in AURA-CHAT with provider grouping, provider health status display, per-session model override UI. Built in AURA-CHAT first, copied to AURA-NOTES-MANAGER.
**Addresses features:** D-1 (hierarchical provider selection UI), D-2 (inline contextual model selector), TS-5 (per-session override UI)
**Avoids pitfalls:** P11 (Zustand single source of truth, TanStack Query invalidation on provider change), P8 (clear UI distinction of setting scope -- chat vs processing)
**Stack:** Existing TailwindCSS + lucide-react + framer-motion. No new frontend dependencies needed for this phase.

### Phase 5: Usage Tracking + Cost Dashboard
**Rationale:** Usage tracking hooks should have been wired into the router from Phase 1, but the dashboard and aggregation UI come last because they are additive polish. The data model must be proven before building budget controls.
**Delivers:** `UsageTracker` accumulator recording tokens/cost per request. Usage REST endpoints with date range filters. Cost dashboard with line/bar/pie charts showing cost by provider, model, and time period. Per-session cost display in chat UI.
**Addresses features:** D-3 (usage tracking with cost dashboard)
**Avoids pitfalls:** P5 (provider-reported tokens, cached pricing data, estimated flag for missing data)
**Stack:** `recharts@^3.8.0` (install in app(s) rendering the dashboard)

### Phase 6: Polish, Thinking Mode, and Integration Testing
**Rationale:** Final phase for cross-cutting concerns that depend on everything else being in place. Thinking mode standardization requires both backend providers and frontend UI to be complete. Full integration testing catches regressions.
**Delivers:** Thinking mode working across Vertex AI and applicable OpenRouter models (Claude, DeepSeek). Full regression suite. Performance validation. Documentation.
**Addresses features:** D-5 (thinking mode standardization), quality gates
**Avoids pitfalls:** P9 (graceful degradation for non-thinking models, thinking panel hidden when unsupported)

### Phase Ordering Rationale

- **Phases 1-2 are sequential and non-negotiable in order.** Types must exist before providers, and existing Vertex AI must work before adding new providers. The dependency chain is strict.
- **Phase 3 depends on Phases 1-2** but is a low-risk "plumbing swap" if the providers are well-tested.
- **Phase 4 depends on Phase 3** (backend endpoints must exist for frontend to consume), but UI design work can begin in parallel during Phase 3.
- **Phase 5 can partially overlap with Phase 4** (usage tracking hooks are backend work; dashboard is frontend work), but the dashboard depends on accumulated data.
- **Phase 6 is a cleanup/polish phase** that catches any cross-cutting issues. Thinking mode standardization could start as early as Phase 2 (backend) but the full UI integration requires Phase 4.
- **Phase 1 gets the most time budget** because it has the highest risk concentration (3 critical pitfalls) and the most integration surface area (35+ files across both apps).

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** Needs `/gsd:research-phase` -- the Strangler Fig migration across 35+ files with two different Vertex AI SDKs is complex. Need to map every call site and design adapter tests.
- **Phase 2:** Needs `/gsd:research-phase` -- OpenRouter streaming normalization, especially for thinking content across providers (Anthropic thinking blocks, DeepSeek reasoning_content, Gemini thought parts). Also need to validate the curated model allowlist against AURA's specific needs.
- **Phase 5:** Needs `/gsd:research-phase` -- cost calculation logic varies by provider (Gemini prices per character, OpenRouter per token, Ollama is free). Need to design the cost estimation model carefully.

Phases with standard patterns (skip research-phase):
- **Phase 3:** Standard DI wiring and endpoint creation. FastAPI dependency injection is well-documented. Migration is mechanical once providers are tested.
- **Phase 4:** Standard React + TanStack Query + Zustand patterns. Model selector UIs are well-understood (ChatGPT, Claude, TypingMind all use similar patterns).
- **Phase 6:** Standard integration testing and polishing. Thinking mode normalization is the only non-trivial part, and the research for it will have been done in Phase 2.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All libraries verified via PyPI/npm, versions confirmed, compatibility matrix checked. OpenRouter's OpenAI SDK approach verified via official docs. Only recharts v3 component API is MEDIUM (not independently verified via Context7). |
| Features | HIGH | Feature landscape derived from OpenRouter API spec (verified), LiteLLM patterns (verified), TypingMind UI patterns (MEDIUM -- changelog-derived), and direct AURA codebase analysis. Feature dependencies and critical path are solid. |
| Architecture | HIGH | Architecture directly derived from AURA codebase analysis (35+ files inspected). Provider abstraction patterns are well-established in the Python ecosystem. Shared package approach validated against Python packaging standards. |
| Pitfalls | HIGH | All critical pitfalls backed by specific line numbers in the AURA codebase (embedding dimensions in 6+ locations, streaming in 45+ references, Vertex AI in 35+ files). Provider-specific quirks are MEDIUM confidence (training data + partial live verification). |

**Overall confidence:** HIGH

### Gaps to Address

- **OpenRouter model allowlist curation:** Which of the 200+ models actually work well for academic RAG? Need to test a representative set (top 5-10 models across vendors) against AURA's specific query types during Phase 2.
- **recharts v3 component API:** Version and React compatibility verified, but exact component usage patterns (composability, customization API) not independently verified. Low risk -- fallback to v2 or alternative is straightforward.
- **Ollama model quality for academic use:** Ollama is stub-only in v1.1, but when planning v1.2, need to evaluate which local models (Gemma, LLaMA, Phi) produce acceptable quality for academic RAG at acceptable latency.
- **Cost estimation accuracy:** Gemini per-character vs per-token pricing, OpenRouter's dynamic pricing, and thinking token costs need validation against actual billing data during Phase 5.
- **Celery worker shared package imports:** The monorepo's Celery workers run with different `sys.path`. Need to verify the shared package is importable from Celery worker context specifically, not just from the API process.
- **Neo4j re-indexing tooling:** If embedding providers ever need to change, a re-indexing migration tool is required. Not needed for v1.1 (embedding stays on Vertex AI), but should be planned for v1.2+.

## Sources

### Primary (HIGH confidence)
- OpenRouter OpenAPI spec (openrouter.ai/openapi.json) -- endpoint compatibility, streaming format, pricing fields, model metadata
- OpenRouter quickstart docs (openrouter.ai/docs/quickstart) -- base URL, auth headers, SDK compatibility
- Ollama API docs (github.com/ollama/ollama/blob/main/docs/api.md) -- REST API reference, streaming format, embed endpoint
- PyPI pages for `openai` v2.26.0, `ollama` v0.6.1, `pydantic-settings` v2.13.1 -- version verification, dependency trees
- AURA codebase analysis -- direct inspection of 35+ Vertex AI integration files, 62+ embedding references, 45+ streaming references across both apps
- LiteLLM documentation (docs.litellm.ai) -- patterns for unified interface, streaming normalization, error mapping, reasoning content normalization
- Python Packaging User Guide -- pyproject.toml structure, editable installs, hatchling build backend
- FastAPI official docs -- Depends(), dependency_overrides for testing

### Secondary (MEDIUM confidence)
- recharts official site (recharts.github.io) -- React 18/19 compatibility, v3.8.0 availability
- TypingMind documentation (docs.typingmind.com) -- UI patterns for model selection, cost estimation
- OpenRouter rate limiting behavior -- inferred from API docs and community reports
- Streaming format differences across providers -- composite of official docs and training data

### Tertiary (LOW confidence)
- Ollama model quality for academic use -- not tested, inference based on model family characteristics
- Neo4j HNSW behavior with mismatched dimensions -- inferred from vector database principles, not tested against Neo4j specifically

---
*Research completed: 2026-03-10*
*Ready for roadmap: yes*
