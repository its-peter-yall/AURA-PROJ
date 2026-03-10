# Requirements: AURA Multi-Provider LLM Architecture

**Defined:** 2026-03-10
**Core Value:** Enable both AURA applications to work with multiple LLM providers through a shared, provider-agnostic interface

## v1.1 Requirements

Requirements for multi-provider LLM support. Each maps to roadmap phases.

### Router Abstraction

- [ ] **ROUTER-01**: Backend provides a unified `generate()` interface that routes to the correct provider based on model identifier
- [ ] **ROUTER-02**: Backend provides a unified `embed()` interface locked to Vertex AI per deployment with dimension validation
- [ ] **ROUTER-03**: All providers stream responses through a normalized SSE format matching AURA's existing `{type: "thinking"|"content", text}` chunk shape
- [ ] **ROUTER-04**: All provider errors map to a unified error hierarchy (auth, rate limit, content policy, model unavailable, timeout) with original error preserved

### Provider Implementations

- [ ] **PROV-01**: Vertex AI provider wraps existing code through the shared router interface with zero regression in existing tests
- [x] **PROV-02**: OpenRouter provider supports completions, streaming, model listing, and credit checking via the `openai` SDK
- [ ] **PROV-03**: Thinking/reasoning mode works across Vertex AI (Gemini thinking), OpenRouter (Claude extended thinking, DeepSeek reasoning) with a unified enable/budget interface

### Configuration

- [ ] **CONFIG-01**: Admin can set default provider and model for each use case (chat, embeddings, entity extraction) via a settings page
- [ ] **CONFIG-02**: Student can select a different chat model for their study session that persists for the session duration
- [ ] **CONFIG-03**: System dynamically discovers available models from each configured provider with cached model lists
- [ ] **CONFIG-04**: Admin can securely store, validate, and manage API keys for each provider with masked display

### Frontend UI

- [ ] **UI-01**: Provider selection uses a hierarchical UI: 2-level for Vertex AI, 3-level for OpenRouter (provider > vendor > model) with search/filter
- [ ] **UI-02**: Chat interface includes an inline compact model picker for quick mid-session model switching
- [ ] **UI-03**: Both AURA-CHAT and AURA-NOTES-MANAGER use the shared model router for all LLM calls with no direct provider imports

### Usage Tracking

- [ ] **USAGE-01**: System tracks token usage and cost per request, aggregated by session, user, model, and provider
- [ ] **USAGE-02**: Dashboard displays cost charts by provider, model, time period with date range filters

## v1.2 Requirements

Deferred to next milestone. Tracked but not in current roadmap.

### Budget & Fallback

- **BUDGET-01**: Admin can set spending limits (daily, weekly, monthly) per provider with alerts at 80% and 95% thresholds
- **BUDGET-02**: System blocks requests when budget is exceeded with option to auto-downgrade to cheaper model
- **FALLBACK-01**: Automatic provider fallback on failure (rate limit, timeout, unavailable) with transparent model switching
- **FALLBACK-02**: Provider health tracking with cooldown periods for failing providers

### Local Models

- **LOCAL-01**: Ollama provider supports local model inference with auto-detection of running Ollama instance
- **LOCAL-02**: Ollama model listing shows locally installed models with parameter count and family info

## Out of Scope

| Feature | Reason |
|---------|--------|
| User-facing embedding provider switching | Corrupts Neo4j 768-dim HNSW indices silently -- embeddings locked per deployment |
| Per-user BYOK API key management | Security nightmare in academic setting -- admin manages all keys |
| Real-time provider price comparison | Adds latency, complexity for marginal value -- use cached pricing |
| Self-hosted LLM proxy/gateway | Scope creep -- in-process router is simpler and faster |
| Fine-tuning / custom model training UI | Out of scope -- orders of magnitude more complex |
| Provider-specific advanced parameter exposure | Overwhelming UI -- expose only universal params (temperature, max_tokens, top_p) |
| Mobile native experience | Web-first -- existing PWA patterns sufficient |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ROUTER-01 | Phase 8 | Pending |
| ROUTER-02 | Phase 8 | Pending |
| ROUTER-03 | Phase 9 | Pending |
| ROUTER-04 | Phase 8 | Pending |
| PROV-01 | Phase 8 | Pending |
| PROV-02 | Phase 9 | Complete |
| PROV-03 | Phase 9 | Pending |
| CONFIG-01 | Phase 10 | Pending |
| CONFIG-02 | Phase 11 | Pending |
| CONFIG-03 | Phase 10 | Pending |
| CONFIG-04 | Phase 10 | Pending |
| UI-01 | Phase 11 | Pending |
| UI-02 | Phase 11 | Pending |
| UI-03 | Phase 10 | Pending |
| USAGE-01 | Phase 12 | Pending |
| USAGE-02 | Phase 12 | Pending |

**Coverage:**
- v1.1 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0

---
*Requirements defined: 2026-03-10*
*Last updated: 2026-03-10 after roadmap creation (phases 8-13)*
