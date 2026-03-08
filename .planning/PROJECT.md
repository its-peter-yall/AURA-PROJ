# AURA Project

## What This Is

AURA is a **module-centric learning platform** with interconnected knowledge graphs, consisting of two integrated applications:

1. **AURA-NOTES-MANAGER** - Staff portal for document management, module organization, and knowledge graph processing
2. **AURA-CHAT** - Student-facing academic RAG chat with module-aware study sessions

## Core Value

Transform from document-centric to module-centric learning, enabling contextual study sessions with persistent history and cross-module concept discovery.

## Current State (v1.0 Shipped)

**Shipped:** March 8, 2026
**Status:** MVP Complete

### What's Built

| Component | Status | Details |
|-----------|--------|---------|
| Neo4j Schema | ✓ | Module nodes, vector indices, StudySession/Message nodes |
| KG Processor | ✓ | Celery async processing, entity extraction, embeddings |
| Module Management | ✓ | Full CRUD, hierarchical organization, document assignment |
| Session-Based Chat | ✓ | Persistent sessions, message history, module-aware RAG |
| Frontend UI | ✓ | KG processing UI, module selector, study session sidebar |
| Testing | ✓ | 210+ unit tests, 65+ E2E tests, performance benchmarks |
| Docker Deploy | ✓ | 8-service Docker Compose stack |

### Technology Stack

- **Backend:** Python 3.11+, FastAPI 0.109, Celery 5.3.6, Neo4j 5.15, Redis 7
- **Frontend:** React 18/19, TypeScript 5.3, TanStack Query, Zustand, TailwindCSS
- **AI/ML:** Gemini (embeddings), Vertex AI (chat)
- **Testing:** Pytest, Vitest, Playwright, Locust

### Performance Achieved

| Metric | Target | Achieved |
|--------|--------|----------|
| Module list load | < 100ms | ✓ |
| KG processing | < 60s/doc | ✓ |
| RAG query (single) | < 2s | ✓ |
| Frontend TTI | < 1.5s | ✓ |

## Validated Requirements (v1.0)

- ✓ Module-centric architecture (Neo4j schema, module hierarchy)
- ✓ Knowledge graph processing (async pipeline, entity extraction)
- ✓ Session-based chat (persistent sessions, message history)
- ✓ Module-aware RAG (filtering, cross-module discovery)
- ✓ Staff portal UI (document management, KG processing)
- ✓ Student chat UI (module selection, study sessions)
- ✓ Testing infrastructure (unit, E2E, performance)
- ✓ Docker deployment (8-service Compose stack)

## Active Requirements (v1.1)

None defined yet.

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

## Context

- **Total LOC:** ~121,035 (Python + TypeScript)
- **Timeline:** 46 days (Jan 19 → Mar 8, 2026)
- **Commits:** 200+
- **Test Coverage:** >85% backend, >80% frontend

## Next Milestone Goals (v1.1)

TBD — define via `/gsd:new-milestone`

---
*Last updated: 2026-03-08 after v1.0 milestone*
