# AURA Roadmap

> **Current:** v1.0 M2KG Transformation (Shipped 2026-03-08)
> **Next:** Planning v1.1

---

## Project Vision

Transform AURA from document-centric to **module-centric learning platform** with interconnected knowledge graphs enabling:
- Contextual learning (module-scoped study sessions)
- Cross-module discovery (concept bridges)
- Progressive mastery tracking
- Semantic navigation through graph relationships

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              AURA-NOTES-MANAGER (Staff Portal)              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. Document Management                               │    │
│  │ 2. Module Organization                               │    │
│  │ 3. KG Processing                                     │    │
│  │ 4. Module Publishing                                 │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   Neo4j KG      │
                   │   (Shared)      │
                   └─────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 AURA-CHAT (Student Chat)                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. Module Selection UI                              │    │
│  │ 2. Study Sessions                                   │    │
│  │ 3. Module-Aware RAG                                 │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Milestones

- ✅ **v1.0 M2KG Transformation** — Phases 1-7 (shipped 2026-03-08)
- 📋 **v1.1** — TBD (planning)

---

## Completed Milestone

<details>
<summary>✅ v1.0 M2KG Transformation (Phases 1-7) — SHIPPED 2026-03-08</summary>

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

## Next Milestone (v1.1)

**Status:** Not started

To begin planning v1.1:

```
/gsd:new-milestone
```

---

## Technology Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.11+ | Backend runtime |
| **FastAPI** | 0.109.0 | API framework |
| **Celery** | 5.3.6 | Async task queue |
| **Neo4j** | 5.15+ | Graph database with vector search |
| **Redis** | 7+ | Caching and broker |
| **React** | 18.2.0/19 | Frontend UI |
| **TypeScript** | 5.3.3 | Type safety |
| **TanStack Query** | 5.17.0 | Server state management |
| **Zustand** | 4.4.7 | Client state management |
| **Gemini** | text-embedding-004 | Embeddings (768-dim) |

---

## References

- [PROJECT.md](./PROJECT.md) - Current project state
- [MILESTONES.md](./MILESTONES.md) - Milestone history
- [RETROSPECTIVE.md](./RETROSPECTIVE.md) - Lessons learned

---

*Last updated: 2026-03-08 after v1.0 milestone completion*
