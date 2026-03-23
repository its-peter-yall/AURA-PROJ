# AURA Project

## What This Is

AURA is a **module-centric learning platform** with interconnected knowledge graphs, consisting of two integrated applications:

1. **AURA-NOTES-MANAGER** - Staff portal for document management, module organization, and knowledge graph processing
2. **AURA-CHAT** - Student-facing academic RAG chat with module-aware study sessions

## Core Value

Transform from document-centric to module-centric learning, enabling contextual study sessions with persistent history and cross-module concept discovery.

## Current State: v1.2 Shipped (2026-03-23)

**All 8 LLM consumers route through ModelRouter with SettingsStore config.** Every AI feature in both applications respects per-use-case model/provider configuration — no more hardcoded env vars or silent provider skips.

### What's Built

| Component | Status | Details |
|-----------|--------|---------|
| Model Router | ✓ | Shared `shared/model_router/` package with ABC providers |
| Vertex AI Provider | ✓ | Full feature parity |
| OpenRouter Provider | ✓ | 200+ models, normalized SSE streaming, JSON mode translation |
| Thinking Mode | ✓ | Unified enable/budget across providers |
| Cross-App Migration | ✓ | Both apps use router exclusively |
| Admin Settings API | ✓ | Provider config, model cache, key management |
| Provider Settings UI | ✓ | Hierarchical model picker, inline chat picker |
| Usage Tracking | ✓ | Token/cost per request, Redis persistence |
| Cost Dashboard | ✓ | Provider/model breakdown, date filters |
| Settings Wiring (v1.2) | ✓ | `resolve_use_case_config()` + all 8 consumers wired |
| Integration Tests | ✓ | 1100+ tests passing |

### Technology Stack

- **Model Router:** `shared/model_router/` (Python package)
- **Config Resolution:** `resolve_use_case_config()` — SettingsStore → env var → hardcoded default
- **LLM Providers:** Vertex AI, OpenRouter (200+ models), Ollama (stub)
- **Settings Store:** Redis (30s error TTL for graceful degradation)
- **Usage:** Recharts for dashboard visualization

### Performance Achieved

| Metric | Target | Achieved |
|--------|--------|----------|
| Router overhead | < 10ms | ✓ ~5ms verified |
| Provider switch | Seamless | ✓ No context loss |
| Streaming | Normalized | ✓ Identical SSE format |
| Config resolution | < 1ms | ✓ In-memory cache + Redis HGET |
| Redis recovery | < 30s | ✓ 30s error TTL |

---

## Requirements

This project tracks requirements in two buckets:

- **Validated Requirements**: completed and verified requirements from shipped milestones
- **Active Requirements**: requirements targeted by the current milestone

See the detailed requirement lists below.

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

### Validated Requirements (v1.2)

- ✓ API-01: Admin can configure gatekeeper model/provider via settings page — v1.2
- ✓ API-02: Admin can configure relationship extraction model/provider via settings page — v1.2
- ✓ PP-01: Entity extractor passes explicit provider from SettingsStore — v1.2
- ✓ PP-02: Gatekeeper routes through ModelRouter with explicit provider — v1.2
- ✓ PP-03: Embeddings passes provider from SettingsStore to router.embed() — v1.2
- ✓ PP-04: Relationship extraction reads from SettingsStore with env var fallback — v1.2
- ✓ PP-05: KG processor reads from SettingsStore at runtime — v1.2
- ✓ PP-06: Entity extractor passes explicit provider from SettingsStore — v1.2
- ✓ PP-07: Embeddings passes provider from SettingsStore to router.embed() — v1.2
- ✓ PP-08: Summarizer routes through ModelRouter — v1.2
- ✓ FB-01: SettingsStore value authoritative over env vars — v1.2
- ✓ FB-02: Graceful degradation on Redis down — v1.2

## Active Requirements

*No active milestone — run `/gsd-new-milestone` to start next cycle*

## Out of Scope

- Mobile native apps (web-first, PWA consideration)
- Video chat (use external tools)
- Real-time collaboration (async focus)
- Third-party LMS integration (future consideration)

## Key Decisions

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
| resolve_use_case_config() for 3-step config | All 8 consumers wired consistently | ✓ Good |
| 30s error TTL for Redis failures | Fast recovery, no zombie-None | ✓ Good |
| Frontend settings outside RoleProtectedRoute | Admin access works despite role guard | ✓ Good |

## Context

- **Total LOC:** ~141,000 (Python + TypeScript)
- **Timeline v1.0:** 46 days (Jan 19 → Mar 8, 2026)
- **Timeline v1.1:** 5 days (Mar 10 → Mar 16, 2026)
- **Timeline v1.2:** 1 day (Mar 23, 2026)
- **Commits:** 280+
- **Test Coverage:** >85% backend, >80% frontend
- **Shipped Milestones:** 3 (v1.0, v1.1, v1.2)

## Constraints

- **Code Sharing**: Shared package at project root (`shared/model_router/`) — both apps import from it
- **Backward Compatibility**: Existing Vertex AI code must continue working during migration
- **Provider Isolation**: Provider-specific code stays in provider modules only
- **Performance**: Abstraction layer overhead < 10ms per request

---
*Last updated: 2026-03-23 after v1.2 milestone (Settings Wiring E2E)*
