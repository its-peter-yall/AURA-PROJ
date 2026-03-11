# Roadmap: AURA v1.1 -- Multi-Provider LLM Architecture

**Created:** 2026-03-10
**Phases:** 6 (Phase 8-13)
**Requirements:** 16/16 mapped

## Overview

AURA v1.1 transforms both applications from single-provider (Vertex AI) to a shared, provider-agnostic Model Router supporting Vertex AI, OpenRouter (200+ models), and an Ollama stub. The work progresses from shared types and Vertex AI migration (Phase 8) through new providers and streaming normalization (Phase 9), cross-app wiring with backend configuration (Phase 10), frontend UI for model selection (Phase 11), usage tracking with cost dashboard (Phase 12), and integration polish (Phase 13). Phase numbering continues from v1.0 which ended at Phase 7.

## Milestones

- [x] **v1.0 M2KG Transformation** -- Phases 1-7 (shipped 2026-03-08)
- [ ] **v1.1 Multi-Provider LLM Architecture** -- Phases 8-13 (in progress)

---

## Completed Milestone

<details>
<summary>v1.0 M2KG Transformation (Phases 1-7) -- SHIPPED 2026-03-08</summary>

### Overview
Module-centric learning platform with knowledge graphs, persistent study sessions, and full testing infrastructure.

### Phases Completed

| Phase | Name | Plans | Summary |
|-------|------|-------|---------|
| 1 | Database Schema Extension | 4 | Neo4j schema with HNSW indices, StudySession nodes |
| 2 | Knowledge Graph Processor | 5 | Celery async pipeline, entity extraction, embeddings |
| 3 | Module Management | 3 | CRUD API, 4-level hierarchy, Redis caching |
| 4 | AURA-CHAT Integration | 3 | Module filtering, session-based chat |
| 5 | Study Session System | 3 | Session CRUD, message history, context preservation |
| 6 | Frontend Implementation | 4 | KG UI, module selector, study session sidebar |
| 7 | Testing & Optimization | 6 | 210+ tests, 65+ E2E, Docker Compose |

**Total:** 7 phases, 28 plans, 67 summaries, 121K LOC

### Archive
- [v1.0-ROADMAP.md](./milestones/v1.0-ROADMAP.md) - Full archived roadmap
- [MILESTONES.md](./MILESTONES.md) - Milestone summary

</details>

---

## Phases

**Milestone v1.1: Multi-Provider LLM Architecture**

- [x] **Phase 8: Shared Package Foundation + Vertex AI Migration** - Installable shared router package with types, error hierarchy, and Vertex AI provider wrapping existing code
- [x] **Phase 9: OpenRouter Provider + Streaming Normalization** - OpenRouter integration with 200+ models, normalized SSE streaming, and thinking mode abstraction across providers
- [x] **Phase 10: Cross-App Migration + Backend Integration** - Both apps migrated to shared router with admin configuration endpoints and API key management (completed 2026-03-10)
- [x] **Phase 11: Frontend Provider Settings + Model Selection UI** - Hierarchical model selector, inline chat model picker, per-session model persistence (completed 2026-03-11)
- [x] **Phase 12: Usage Tracking + Cost Dashboard** - Token/cost tracking per request with aggregated dashboard and date range filters (completed 2026-03-11)
- [ ] **Phase 13: Polish + Integration Testing** - Cross-provider edge cases, thinking mode UI validation, full regression, performance verification

## Phase Details

### Phase 8: Shared Package Foundation + Vertex AI Migration

**Goal:** Both AURA applications can route LLM calls through a shared model router with the existing Vertex AI provider, with zero regression in functionality or tests

**Depends on:** Nothing (first phase of v1.1; v1.0 complete)

**Requirements:** ROUTER-01, ROUTER-02, ROUTER-04, PROV-01

**Success Criteria** (what must be TRUE):
  1. A call to `router.generate(model="gemini-2.0-flash", ...)` returns a response identical in shape to the existing Vertex AI direct calls
  2. A call to `router.embed(text, ...)` produces 768-dimension vectors matching existing Gemini embedding output, and rejects any request to switch embedding provider at runtime
  3. All 210+ existing unit tests pass without modification when running through the router interface via compatibility shims
  4. Provider errors (auth failure, rate limit, timeout, content policy, model unavailable) surface as typed exceptions from a unified error hierarchy with the original error preserved
  5. Both AURA-CHAT and AURA-NOTES-MANAGER can `from model_router import ModelRouter` from the shared package installed via `pip install -e`

**Key risks:** Highest-risk phase. Three critical pitfalls converge: migration breakage across 35+ files with two different Vertex AI SDKs (`google-genai` and `vertexai.generative_models`), shared package import resolution in a monorepo with nested git repos and Celery workers, and embedding dimension validation for 768-dim HNSW indices. Strangler Fig pattern mandatory -- wrap existing code first, verify tests, then migrate callers incrementally. Budget 2-3x normal estimation.

**Plans:** 3 plans

Plans:
- [x] 08-01-PLAN.md — Package foundation: types, errors, config, provider ABCs + unit tests ([summary](./phases/08-shared-package-vertex-ai/08-01-SUMMARY.md))
- [x] 08-02-PLAN.md — VertexAI provider + ModelRouter core with routing and delegation ([summary](./phases/08-shared-package-vertex-ai/08-02-SUMMARY.md))
- [x] 08-03-PLAN.md — Compatibility shims in both apps + zero-regression test verification

---

### Phase 9: OpenRouter Provider + Streaming Normalization

**Goal:** Users can access 200+ models via OpenRouter alongside Vertex AI, with all providers streaming responses through a single normalized SSE format and thinking mode working across providers

**Depends on:** Phase 8

**Requirements:** PROV-02, ROUTER-03, PROV-03

**Success Criteria** (what must be TRUE):
  1. A generate request to an OpenRouter model (e.g., `anthropic/claude-sonnet-4`) returns a valid response through the router interface with a valid API key
  2. Streaming responses from both Vertex AI and OpenRouter arrive as identical `{type: "thinking"|"content", text}` SSE chunks in the browser
  3. Thinking/reasoning content from Gemini thinking mode, Claude extended thinking, and DeepSeek reasoning is accessible through a unified enable/budget interface, with graceful degradation for models that do not support thinking
  4. OpenRouter credit balance and available model listing are retrievable via the router API

**Key risks:** Streaming API differences between providers (chunking behavior, thinking content separation, termination signals). Each provider adapter must normalize its own stream format. Curated model allowlist needed to prevent exposing non-functional models.

**Plans:** 3 plans

Plans:
- [x] 09-01-PLAN.md — OpenRouter provider core: config, OpenRouterProvider (generate, stream, list_models, health_check, credit balance), error mapping, auto-registration, TDD tests ([summary](./phases/09-openrouter-streaming/09-01-SUMMARY.md))
- [x] 09-02-PLAN.md — Cross-provider streaming normalization verification + thinking config translation tests + router delegation for OpenRouter ([summary](./phases/09-openrouter-streaming/09-02-SUMMARY.md))
- [x] 09-03-PLAN.md — Gap closure: router-level metadata surface (list_models, health_check, get_provider) + Vertex AI thinking regression tests ([summary](./phases/09-openrouter-streaming/09-03-SUMMARY.md))

---

### Phase 10: Cross-App Migration + Backend Integration

**Goal:** Both applications use the model router exclusively for every LLM call, with admin-configurable defaults, dynamic model discovery, and secure API key management

**Depends on:** Phase 9

**Requirements:** UI-03, CONFIG-01, CONFIG-03, CONFIG-04

**Success Criteria** (what must be TRUE):
  1. Neither AURA-CHAT nor AURA-NOTES-MANAGER contains any direct import of `vertexai`, `google.generativeai`, or `openai` SDK outside the shared model_router package
  2. Admin can set the default provider and model for each use case (chat, embeddings, entity extraction) via REST settings endpoints
  3. The system returns a list of available models from each configured provider, refreshed from a cache with configurable TTL (5-60 minutes)
  4. Admin can store, validate, and manage API keys per provider through backend APIs, with keys masked in all responses (e.g., `sk-...abc`)
  5. Celery workers in both apps successfully import and use the shared model router for background KG processing tasks

**Key risks:** Configuration drift between the two apps. Provider settings, API keys, and defaults can diverge. Shared config source needed with clear separation of generation config (user-facing) from processing config (operational).

**Plans:** 6 plans (4 complete, 2 gap closure)

Plans:
- [x] 10-01-PLAN.md — Shared config modules: settings store, key manager, model cache + TDD unit tests ([summary](./phases/10-cross-app-migration-backend-integration/10-01-SUMMARY.md))
- [x] 10-02-PLAN.md — Admin settings REST endpoints for both AURA-CHAT and AURA-NOTES-MANAGER ([summary](./phases/10-cross-app-migration-backend-integration/10-02-SUMMARY.md))
- [x] 10-03-PLAN.md — AURA-CHAT full migration: vertex_ai_client.py + embeddings.py rewritten as model_router façades ([summary](./phases/10-cross-app-migration-backend-integration/10-03-SUMMARY.md))
- [x] 10-04-PLAN.md — AURA-NOTES-MANAGER full migration + Celery verification + no-direct-imports audit test ([summary](./phases/10-cross-app-migration-backend-integration/10-04-SUMMARY.md))
- [x] 10-05-PLAN.md — Gap closure: test file SDK import cleanup + ARQ worker import verification ([summary](./phases/10-cross-app-migration-backend-integration/10-05-SUMMARY.md))
- [x] 10-06-PLAN.md — Gap closure: configurable model cache TTL (5-60 min) + provider-aware key validation ([summary](./phases/10-cross-app-migration-backend-integration/10-06-SUMMARY.md))

---

### Phase 11: Frontend Provider Settings + Model Selection UI

**Goal:** Students can pick any available model for their study session through an intuitive hierarchical selector, and admins can manage provider configuration through a settings page

**Depends on:** Phase 10

**Requirements:** UI-01, UI-02, CONFIG-02

**Success Criteria** (what must be TRUE):
  1. Provider selection UI displays a 2-level hierarchy for Vertex AI/Ollama (provider then model) and a 3-level hierarchy for OpenRouter (provider then vendor then model), with search and filter capabilities
  2. Chat interface includes a compact inline model picker that lets the student switch models mid-session without leaving the conversation
  3. A student's model selection persists for the duration of their study session and restores when they resume the session later
  4. Both AURA-CHAT and AURA-NOTES-MANAGER render the provider settings page; AURA-CHAT additionally includes the inline chat model picker

**Key risks:** State synchronization between Zustand (client selection) and TanStack Query (server model lists). Provider change must invalidate cached model lists. Clear UI distinction between chat model settings and processing model settings.

**Build note:** Components built in AURA-CHAT (React 19) first, then copied to AURA-NOTES-MANAGER (React 18). React version gap prevents a shared npm package.

**Plans:** 4/4 plans complete

Plans:
- [x] 11-01-PLAN.md — Data layer foundation: settings types, model grouping function, Zustand model store, TanStack Query settings hooks (TDD)
- [x] 11-02-PLAN.md — Settings page UI: HierarchicalModelPicker + admin components (ProviderSettings, DefaultModel, ApiKey) + SettingsPage wiring
- [x] 11-03-PLAN.md — Inline chat model picker + ChatPage integration + session model persistence
- [x] 11-04-PLAN.md — AURA-NOTES-MANAGER adaptation: copy + adapt all settings components, create SettingsPage + routing

---

### Phase 12: Usage Tracking + Cost Dashboard

**Goal:** Administrators can monitor LLM usage costs across providers, models, and time periods to make informed spending decisions

**Depends on:** Phase 10 (usage tracking hooks wired from Phase 8; dashboard depends on accumulated data and frontend from Phase 11)

**Requirements:** USAGE-01, USAGE-02

**Success Criteria** (what must be TRUE):
  1. Every LLM request records token usage (input, output, thinking tokens) and estimated cost, attributed to session, user, model, and provider
  2. A dashboard displays cost charts broken down by provider, model, and time period with selectable date range filters
  3. Per-session cost is visible in the chat UI so students can see the cost impact of their model choices

**Key risks:** Cost calculation varies by provider (Gemini per character, OpenRouter per token, Ollama free). Cached pricing data needed with an "estimated" flag for approximations. Usage tracking hooks should be wired into the router from Phase 8 to avoid costly retrofit.

**Plans:** 4/4 plans complete

Plans:
- [x] 12-01-PLAN.md — Shared backend: UsageRecord types, CostCalculator, UsageTracker, router hooks (TDD) ([summary](./phases/12-usage-tracking-cost-dashboard/12-01-SUMMARY.md))
 - [x] 12-02-PLAN.md — Backend API endpoints (both apps) + SSE completion usage data ([summary](./phases/12-usage-tracking-cost-dashboard/12-02-SUMMARY.md))
 - [x] 12-03-PLAN.md — AURA-CHAT frontend: Recharts dashboard + per-session cost badge ([summary](./phases/12-usage-tracking-cost-dashboard/12-03-SUMMARY.md))
 - [x] 12-04-PLAN.md — AURA-NOTES-MANAGER dashboard adaptation (admin-protected) ([summary](./phases/12-usage-tracking-cost-dashboard/12-04-SUMMARY.md))

---

### Phase 13: Polish + Integration Testing

**Goal:** The entire multi-provider system works reliably across both applications with no regressions, edge cases handled, and cross-provider features validated end-to-end

**Depends on:** Phases 8-12

**Requirements:** Cross-cutting quality validation (no new requirements -- validates that phases 8-12 deliver as specified)

**Success Criteria** (what must be TRUE):
  1. Switching providers mid-session via the inline picker produces no errors, no lost context, and the conversation continues seamlessly
  2. Thinking mode UI (thinking panel, toggle, token budget) works identically for Gemini thinking and Claude extended thinking from the student's perspective
  3. Both applications pass their full test suites (unit + E2E) with the multi-provider architecture active
  4. Router abstraction adds less than 10ms overhead per request compared to direct SDK calls

**Key risks:** Low risk if phases 8-12 are individually well-tested. Primary concern is cross-cutting interactions that unit tests miss (e.g., thinking mode + streaming + session persistence + provider switching in one flow).

**Plans:** 3 plans

Plans:
- [x] 13-01-PLAN.md — Cross-provider integration tests + router overhead benchmark ([summary](./phases/13-polish-integration-testing/13-01-SUMMARY.md))
- [x] 13-02-PLAN.md — Full regression sweep across all test suites ([summary](./phases/13-polish-integration-testing/13-02-SUMMARY.md))
- [x] 13-03-PLAN.md — Requirements verification + traceability closure ([summary](./phases/13-polish-integration-testing/13-03-SUMMARY.md))

---

## Progress

**Execution Order:** 8 -> 9 -> 10 -> 11 -> 12 -> 13

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 8. Shared Package + Vertex AI | v1.1 | 3/3 | Complete | 2026-03-10 |
| 9. OpenRouter + Streaming | v1.1 | 3/3 | Complete | 2026-03-10 |
| 10. Cross-App Migration + Config | v1.1 | 6/6 | Complete | 2026-03-10 |
| 11. Frontend Settings + Model UI | 4/4 | Complete    | 2026-03-11 | - |
| 12. Usage Tracking + Dashboard | 4/4 | Complete    | 2026-03-11 | - |
| 13. Polish + Integration Testing | v1.1 | 3/3 | Complete | 2026-03-11 |

---

## Technology Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.11+ | Backend runtime |
| **FastAPI** | 0.109.0 | API framework |
| **Celery** | 5.3.6 | Async task queue |
| **Neo4j** | 5.15+ | Graph database with vector search |
| **Redis** | 7+ | Caching and broker |
| **React** | 18.2.0 / 19 | Frontend UI (NOTES / CHAT) |
| **TypeScript** | 5.3.3 | Type safety |
| **TanStack Query** | 5.17.0 | Server state management |
| **Zustand** | 4.4.7 | Client state management |
| **Gemini** | text-embedding-004 | Embeddings (768-dim, locked) |
| **openai SDK** | >=2.26.0 | OpenRouter client (v1.1) |
| **ollama SDK** | >=0.6.1 | Local model client stub (v1.1) |
| **pydantic-settings** | >=2.13.0 | Hierarchical config (v1.1) |
| **recharts** | ^3.8.0 | Cost dashboard charts (v1.1) |

---

## References

- [PROJECT.md](./PROJECT.md) - Current project state
- [REQUIREMENTS.md](./REQUIREMENTS.md) - v1.1 requirements with traceability
- [MILESTONES.md](./MILESTONES.md) - Milestone history
- [research/SUMMARY.md](./research/SUMMARY.md) - v1.1 research findings

---

*Roadmap created: 2026-03-10*
*Last updated: 2026-03-11*
