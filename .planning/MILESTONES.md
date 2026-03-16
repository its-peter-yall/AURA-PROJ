# Milestones

## v1.0 M2KG Transformation (Shipped: 2026-03-08)

**Phases completed:** 7 phases, 28 plans, 67 task summaries

**Timeline:** January 19, 2026 → March 8, 2026 (46 days)

**Code:** 121,035 LOC, 310 files changed, 144,066 insertions

### Key Accomplishments

1. **Database Schema Extension** (Phase 1) - Neo4j module-centric schema with HNSW vector indices, StudySession and Message nodes for persistent chat history

2. **Knowledge Graph Processor** (Phase 2) - Celery-based async processing pipeline with entity/relationship extraction, Gemini embeddings, and Neo4j storage

3. **Module Management** (Phase 3) - Full CRUD API for modules with hierarchical organization (Department → Semester → Subject → Module), document assignment, and Redis caching

4. **AURA-CHAT Integration** (Phase 4) - Module filtering for RAG queries, session-based chat architecture, cross-module concept discovery

5. **Study Session System** (Phase 5) - Session CRUD operations, message history with pagination, session-aware RAG queries with context preservation

6. **Frontend Implementation** (Phase 6) - KG processing UI with status badges and processing queue (AURA-NOTES-MANAGER), module selector with hierarchical drill-down, study session sidebar with MessageBubble and CitationPanel components (AURA-CHAT)

7. **Testing & Optimization** (Phase 7) - 210+ unit tests (85% backend coverage), 65+ E2E tests with Playwright, performance benchmarks (pytest-benchmark), load testing (Locust), Docker Compose deployment (8 services)

### Architecture Delivered

```
AURA-NOTES-MANAGER (Staff Portal)
├── Document Management (hierarchical system)
├── Module Organization (4-level hierarchy)
├── KG Processing (async pipeline with status tracking)
└── Module Publishing (review → publish workflow)

AURA-CHAT (Student Portal)
├── Module Selection UI (hierarchical drill-down)
├── Study Sessions (persistent chat with history)
└── Module-Aware RAG (filtered queries, cross-module discovery)

Shared Infrastructure
├── Neo4j (knowledge graph + vector search)
├── Redis (caching, Celery broker)
└── Docker Compose (8-service deployment)
```

### Performance Targets Met

| Metric | Target | Status |
|--------|--------|--------|
| Module list load | < 100ms | ✓ Met |
| Module create | < 100ms | ✓ Met |
| Document assignment | < 50ms | ✓ Met |
| KG processing | < 60s/doc | ✓ Met |
| RAG query (single) | < 2s | ✓ Met |
| RAG query (multi) | < 3s | ✓ Met |
| Vector search | < 100ms | ✓ Met |
| Frontend TTI | < 1.5s | ✓ Met |

### Files

- [v1.0-ROADMAP.md](./milestones/v1.0-ROADMAP.md) - Full archived roadmap

---

## v1.1 Multi-Provider LLM Architecture (Shipped: 2026-03-16)

**Phases completed:** 6 phases, 23 plans

**Timeline:** March 10, 2026 → March 16, 2026 (6 days)

### Key Accomplishments

1. **Shared Package Foundation** (Phase 8) - Built `aura-model-router` package with Vertex AI provider, unified error hierarchy, 768-dim embedding validation, and compatibility shims for both apps

2. **OpenRouter + Streaming** (Phase 9) - Added OpenRouter provider (200+ models), normalized SSE streaming across providers, thinking-mode abstraction for Gemini/Claude/DeepSeek

3. **Cross-App Migration** (Phase 10) - Migrated both apps to router via façade pattern, Redis-backed admin settings, Fernet key management, AST import-compliance audit

4. **Frontend Settings UI** (Phase 11) - Delivered admin settings pages, hierarchical model picker (3-level for OpenRouter), session model persistence, inline chat picker

5. **Usage & Cost Tracking** (Phase 12) - Implemented UsageTracker/CostCalculator with Redis persistence, REST/SSE endpoints, Recharts dashboard with per-session cost badge

6. **Integration & Polish** (Phase 13) - Cross-provider integration tests, thinking parity validation, router overhead benchmark (<10ms), 1100+ tests passing

### Architecture Delivered

```
shared/model_router/
├── types.py         # Pydantic contracts (GenerateRequest, EmbedRequest)
├── errors.py        # Unified error hierarchy (AuthError, RateLimitError, etc.)
├── config.py        # Settings, KeyManager (Fernet), ModelCache (TTL)
├── providers/
│   ├── base.py      # Provider ABC (generate, embed, stream, list_models)
│   ├── vertexai.py  # VertexAI provider (generation + embeddings)
│   └── openrouter.py # OpenRouter provider (200+ models via OpenAI SDK)
└── router.py        # ModelRouter (routing, delegation, usage hooks)

AURA-CHAT & AURA-NOTES-MANAGER
├── Backend: ModelRouter facade, SettingsStore, UsageTracker
├── Frontend: ProviderSettings, DefaultModel, ApiKey, UsageDashboard
└── API: /settings, /usage/summary, /usage/provider, etc.
```

### Performance Targets Met

| Metric | Target | Achieved |
|--------|--------|----------|
| Router overhead | < 10ms | ✓ ~5ms verified |
| Provider switch | Seamless | ✓ No context loss |
| Streaming | Normalized | ✓ Identical SSE format |
| Tests passing | 100% | ✓ 1100+ tests |

### Files

- [v1.1-ROADMAP.md](./milestones/v1.1-ROADMAP.md) - Full archived roadmap
- [v1.1-REQUIREMENTS.md](./milestones/v1.1-REQUIREMENTS.md) - Requirements with outcomes

---

