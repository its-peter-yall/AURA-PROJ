# AURA M2KG Project Brief

> **Version:** 1.1 (Dual-Project Architecture)
> **Created:** January 19, 2026
> **Updated:** January 19, 2026
> **Project:** Module-to-Knowledge Graph (M2KG)

---

## Vision

Transform AURA from a **document-centric** to a **module-centric** learning platform where users can organize documents into thematic modules and study within focused, context-aware sessions with interconnected knowledge graphs.

---

## Dual-Project Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              AURA-NOTES-MANAGER (Staff Portal)              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. Document Management                               │    │
│  │    • Create/Edit notes in hierarchical system        │    │
│  │    • Upload PDFs, text files                         │    │
│  │                                                        │    │
│  │ 2. Module Organization                               │    │
│  │    • Assign documents to modules                     │    │
│  │    • Create module hierarchy (dept → semester)       │    │
│  │                                                        │    │
│  │ 3. KG Processing                                     │    │
│  │    • Chunk documents                                 │    │
│  │    • Extract entities/relationships                  │    │
│  │    • Generate embeddings (Gemini)                    │    │
│  │    • Store in Neo4j with module_id tagging           │    │
│  │                                                        │    │
│  │ 4. Module Publishing                                 │    │
│  │    • Review KG before publishing                     │    │
│  │    • Publish to students                             │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│                   ┌─────────────────┐                        │
│                   │   Neo4j KG      │                        │
│                   │   (Shared)      │                        │
│                   └─────────────────┘                        │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 5. Module Selection (for students)                  │    │
│  │    • Browse available modules                       │    │
│  │    • Select modules for study                       │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 AURA-CHAT (Student Chat)                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. Module Selection UI                              │    │
│  │    • Dropdown to select published modules           │    │
│  │    • Multi-select support                           │    │
│  │    • Cross-module discovery                         │    │
│  │                                                        │    │
│  │ 2. Study Sessions                                   │    │
│  │    • Persistent chat sessions                       │    │
│  │    • Message history with context                   │    │
│  │    • Session analytics                              │    │
│  │                                                        │    │
│  │ 3. Module-Aware RAG                                 │    │
│  │    • Filter queries by module_id                    │    │
│  │    • Cross-module concept discovery                 │    │
│  │    • Citations pointing to module content           │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Problem Statement

Current AURA architecture treats documents as isolated units:
- No grouping mechanism for related documents
- Cross-document concept discovery is manual
- Study sessions lack module context
- Knowledge graph lacks organizational hierarchy

---

## Solution

A module-centric architecture with:
1. **Module System** - Thematic containers for documents (e.g., "Machine Learning Fundamentals")
2. **Knowledge Graph Enhancement** - Entities linked to modules, cross-module concept bridges
3. **Study Sessions** - Persistent chat sessions scoped to selected modules
4. **Module-Aware RAG** - Retrieval filtered by module boundaries

---

## Key Features

| Feature | Project | Description |
|---------|---------|-------------|
| Module CRUD | AURA-NOTES-MANAGER | Create, read, update, delete modules |
| Document Assignment | AURA-NOTES-MANAGER | Assign documents to modules |
| KG Processing | AURA-NOTES-MANAGER | Chunk, embed, extract entities |
| Module Publishing | AURA-NOTES-MANAGER | Publish to students |
| Module Selector | AURA-CHAT | Dropdown for module selection |
| Study Sessions | AURA-CHAT | Persistent chat with module context |
| Cross-Module Discovery | AURA-CHAT | Find concepts across modules |
| Module-Aware RAG | AURA-CHAT | Filtered semantic search |

---

## Technology Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.11+ | Backend runtime |
| **FastAPI** | 0.109.0 | API framework |
| **Celery** | 5.3.6 | Async task queue |
| **Neo4j** | 5.15+ | Graph database with vector search |
| **Redis** | 7+ | Caching and broker |
| **React** | 18.2.0 | Frontend UI |
| **TypeScript** | 5.3.3 | Type safety |
| **TanStack Query** | 5.17.0 | Server state management |
| **Zustand** | 4.4.7 | Client state management |
| **Gemini** | text-embedding-004 | Embeddings (768-dim) |

---

## Success Metrics

| Metric | Target | Project |
|--------|--------|---------|
| Module creation latency | < 100ms | AURA-NOTES-MANAGER |
| Document assignment | < 50ms | AURA-NOTES-MANAGER |
| KG processing | < 60s/doc | AURA-NOTES-MANAGER |
| RAG query (single module) | < 2s | AURA-CHAT |
| RAG query (multi-module) | < 3s | AURA-CHAT |
| Test coverage | > 90% | Both |

---

## Current State

- **Git Repository:** Initialized in AURA-PROJ
- **Brief:** This document (v1.1)
- **Roadmap:** `.planning/ROADMAP.md` (v2.1, 7 phases, 12 weeks)
- **Research:** `.planning/RESEARCH.md` (technology validation)
- **Phase Planning:** Phase 1 ready (4 atomic plans)

---

## Roadmap Overview

| Week | Phase | Project | Focus |
|------|-------|---------|-------|
| 1-2 | Phase 1 | AURA-NOTES-MANAGER | Database Schema Extension |
| 3-4 | Phase 2 | AURA-NOTES-MANAGER | KG Processor (chunk, embed, extract) |
| 5-6 | Phase 3 | AURA-NOTES-MANAGER | Module Management & Publishing |
| 7 | Phase 4 | AURA-CHAT | Module-Aware RAG Integration |
| 8-9 | Phase 5 | AURA-CHAT | Study Session System |
| 10-11 | Phase 6 | Both | Frontend Implementation |
| 12 | Phase 7 | Both | Testing & Optimization |

---

## Project Mapping

### AURA-NOTES-MANAGER (Staff Portal)
- `api/migrations/` - Database migrations
- `api/kg_processor.py` - Knowledge graph processing
- `api/tasks/` - Celery tasks for async processing
- `api/module_manager.py` - Module CRUD
- `api/routers/modules.py` - Module API endpoints
- `api/cache/module_cache.py` - Redis caching
- `frontend/src/features/modules/` - Module UI components

### AURA-CHAT (Student Chat)
- `backend/graph_manager.py` - Neo4j operations
- `backend/rag_engine.py` - Module-aware RAG queries
- `backend/session_manager.py` - Study sessions
- `backend/routers/student_modules.py` - Student module APIs
- `backend/routers/sessions.py` - Session APIs
- `frontend/src/features/modules/` - Module selector UI
- `frontend/src/features/study-sessions/` - Chat UI

---

## Next Action

**Phase 1: Database Schema Extension (AURA-NOTES-MANAGER)**

Execute atomic plans:
```
1. Create migration script + Module constraints
2. Add StudySession + Message nodes
3. Add HNSW vector index
4. Add module_id to Document/Chunk + verify
```

Files to create:
- `AURA-NOTES-MANAGER/api/migrations/__init__.py`
- `AURA-NOTES-MANAGER/api/migrations/001_add_module_schema.py`
- `AURA-NOTES-MANAGER/api/migrations/verify_migration.py`
