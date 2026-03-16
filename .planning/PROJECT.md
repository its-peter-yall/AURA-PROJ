# AURA Project

## What This Is

AURA is a **module-centric learning platform** with interconnected knowledge graphs, consisting of two integrated applications:

1. **AURA-NOTES-MANAGER** - Staff portal for document management, module organization, and knowledge graph processing
2. **AURA-CHAT** - Student-facing academic RAG chat with module-aware study sessions

## Core Value

Transform from document-centric to module-centric learning, enabling contextual study sessions with persistent history and cross-module concept discovery.

## Current State (v1.1 Shipped)

**Shipped:** March 16, 2026
**Status:** Multi-Provider LLM Architecture Complete

### What's Built (v1.1)

| Component | Status | Details |
|-----------|--------|---------|
| Model Router | ✓ | Shared `shared/model_router/` package with ABC providers |
| Vertex AI Provider | ✓ | Wrapped existing code, full compatibility |
| OpenRouter Provider | ✓ | 200+ models, normalized SSE streaming |
| Thinking Mode | ✓ | Unified enable/budget across providers |
| Cross-App Migration | ✓ | Both apps use router exclusively |
| Admin Settings API | ✓ | Provider config, model cache, key management |
| Provider Settings UI | ✓ | Hierarchical model picker, inline chat picker |
| Usage Tracking | ✓ | Token/cost per request, Redis persistence |
| Cost Dashboard | ✓ | Provider/model breakdown, date filters |
| Integration Tests | ✓ | 1100+ tests passing |

### Technology Stack (v1.1 additions)

- **Model Router:** `shared/model_router/` (Python package)
- **LLM Providers:** Vertex AI, OpenRouter (200+ models), Ollama (stub)
- **Usage:** Recharts for dashboard visualization

### Performance Achieved (v1.1)

| Metric | Target | Achieved |
|--------|--------|----------|
| Router overhead | < 10ms | ✓ Verified |
| Provider switch | Seamless | ✓ No context loss |
| Streaming | Normalized | ✓ Identical SSE format |

---

## Validated Requirements (v1.0)

- ✓ Module-centric architecture (Neo4j schema, module hierarchy) — v1.0
- ✓ Knowledge graph processing (async pipeline, entity extraction) — v1.0
- ✓ Session-based chat (persistent sessions, message history) — v1.0
- ✓ Module-aware RAG (filtering, cross-module discovery) — v1.0
- ✓ Staff portal UI (document management, KG processing) — v1.0
- ✓ Student chat UI (module selection, study sessions) — v1.0
- ✓ Testing infrastructure (unit, E2E, performance) — v1.0

### Validated Requirements (v1.1)

- ✓ ROUTER-01: Router interface (`generate()`, `embed()`) — v1.1
- ✓ ROUTER-02: Provider ABC and VertexAI implementation — v1.1
- ✓ ROUTER-03: Provider routing and delegation — v1.1
- ✓ ROUTER-04: Error hierarchy and typed exceptions — v1.1
- ✓ PROV-01: Vertex AI provider full feature parity — v1.1
- ✓ PROV-02: OpenRouter provider (200+ models) — v1.1
- ✓ PROV-03: Normalized SSE streaming across providers — v1.1
- ✓ UI-01: Hierarchical model selector — v1.1
- ✓ UI-02: Inline chat model picker — v1.1
- ✓ UI-03: Per-session model persistence — v1.1
- ✓ CONFIG-01: Admin settings REST endpoints — v1.1
- ✓ CONFIG-02: Default provider/model configuration — v1.1
- ✓ CONFIG-03: Dynamic model discovery with caching — v1.1
- ✓ CONFIG-04: API key management with masking — v1.1
- ✓ USAGE-01: Token/cost tracking per request — v1.1
- ✓ USAGE-02: Cost dashboard with filters — v1.1

## Active Requirements (v1.2)

*Coming soon — start with `/gsd-new-milestone`*

## Out of Scope

- Mobile native apps (web-first, PWA consideration)
- Video chat (use external tools)
- Real-time collaboration (async focus)
- Third-party LMS integration (future consideration)

| Decision | Outcome | Status |
|----------|---------|--------|
| Neo4j for knowledge graph | Graph + vector search in one DB | ✓ Good |
| Module hierarchy (4-level) | Clean academic organization | ✓ Good |
| Session-based chat | Persistent context achieved | ✓ Good |
| Celery for KG processing | Async pipeline works well | ✓ Good |
| Feature-based frontend | Reusable, maintainable | ✓ Good |
| Separate frontend versions | React 18 vs 19 for gradual migration | ⚠ Revisit |
| Shared Model Router package | Single source of truth for both apps | ✓ Good |
| OpenRouter as primary multi-model provider | 200+ models via single API key | ✓ Good |
| Hybrid UI for provider selection | Settings page + inline selectors | ✓ Good |
| Late-bind UsageTracker into ModelRouter | Redis-safe startup | ✓ Good |
| Workspace-local test runners | Avoid monorepo discovery conflicts | ✓ Good |

## Context

- **Total LOC:** ~135,000 (Python + TypeScript)
- **Timeline v1.0:** 46 days (Jan 19 → Mar 8, 2026)
- **Timeline v1.1:** 5 days (Mar 10 → Mar 16, 2026)
- **Commits:** 250+
- **Test Coverage:** >85% backend, >80% frontend

## Constraints

- **Code Sharing**: Shared package at project root (`shared/model_router/`) — both apps import from it
- **Backward Compatibility**: Existing Vertex AI code must continue working during migration
- **Provider Isolation**: Provider-specific code stays in provider modules only
- **Performance**: Abstraction layer overhead < 10ms per request

---
*Last updated: 2026-03-16 after v1.1 milestone completion*
