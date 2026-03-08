# AURA M2KG Implementation Roadmap

> **Version:** 2.4 (Phase 7 - Testing & Optimization)
> **Created:** January 19, 2026
> **Updated:** January 21, 2026
> **Source:** Module-2-KG.md + Final-Module-2-KG.md
> **Reference:** `.planning/RESEARCH.md`

---

## Project Vision

Transform AURA from document-centric to **module-centric learning platform** with interconnected knowledge graphs enabling:
- Contextual learning (module-scoped study sessions)
- Cross-module discovery (concept bridges)
- Progressive mastery tracking
- Semantic navigation through graph relationships

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

## Phase Structure

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                            12-WEEK IMPLEMENTATION                              │
├─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬──────────────────┤
│ Phase 1 │ Phase 2 │ Phase 3 │ Phase 4 │ Phase 5 │ Phase 6 │ Phase 7          │
│ Schema  │ KG      │ Module  │ AURA-   │ Study   │ Frontend│ Testing &        │
│ & Core  │ Process │ Mgmt    │ CHAT    │ Sessions│ UI      │ Optimization     │
│ 2 weeks │ 2 weeks │ 2 weeks │ 1 week  │ 1.5 wks │ 2 weeks │ 1 week           │
└─────────┴─────────┴─────────┴─────────┴─────────┴─────────┴──────────────────┘

Phase 7 Plans: .planning/phases/07-testing/
├── 07-00-PLAN.md - Phase overview
├── 07-01-PLAN.md - AURA-CHAT Backend Unit Tests (50+ tests, 85% coverage)
├── 07-02-PLAN.md - AURA-CHAT Frontend Unit Tests (40+ tests, 80% coverage)
├── 07-03-PLAN.md - AURA-NOTES-MANAGER Unit Tests (55+ tests, 75% coverage)
├── 07-04-PLAN.md - Integration & E2E Tests (65+ tests, Playwright)
└── 07-05-PLAN.md - Performance & Docker (Benchmarks, Docker Compose)

Project Mapping:
├── AURA-NOTES-MANAGER/ (Phases 1-4, 7: Staff portal, testing)
└── AURA-CHAT/          (Phases 4-7: Student chat, testing)
```

---

## Phase 1: Database Schema Extension

**Status:** COMPLETED ✓
**Duration:** Week 1-2
**Project:** AURA-NOTES-MANAGER
**Source:** Module-2-KG.md Section 3

### Objectives
1. Add Module node type with constraints
2. Extend Document/Chunk with `module_id`
3. Create StudySession and Message nodes (for AURA-CHAT)
4. Set up HNSW vector indices

### Node Types

**Module Node:**
```cypher
(:Module {
  id: String!,                    -- UUID format, e.g., "mod_cs_001"
  code: String!,                  -- Module code (e.g., "CS201")
  name: String!,                  -- Display name
  description: String,
  subject_id: String,
  semester: Integer,
  department: String,
  kg_status: String,              -- "draft", "processing", "published", "archived"
  kg_processed_at: DateTime,
  created_by: String,
  published_at: DateTime,
  created_at: DateTime!,
  updated_at: DateTime!
})
```

**StudySession Node:**
```cypher
(:StudySession {
  id: String!,                    -- UUID
  title: String!,
  module_ids: [String]!,          -- Selected modules
  user_id: String!,
  status: String!,                -- "active", "paused", "completed", "archived"
  message_count: Integer,
  settings: String,
  created_at: DateTime!,
  updated_at: DateTime!,
  is_active: Boolean!
})
```

**Message Node:**
```cypher
(:Message {
  id: String!,
  session_id: String!,
  role: String!,                  -- "user" or "assistant"
  content: String!,
  created_at: DateTime!,
  model_used: String,
  sources: [String],
  thinking_content: String,
  token_count: Integer
})
```

### Vector Index Configuration

```cypher
-- Chunk vector index (HNSW)
CREATE VECTOR INDEX chunk_vector_index IF NOT EXISTS
FOR (c:Chunk) ON (c.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine',
    `vector.hnsw.m`: 16,
    `vector.hnsw.ef_construction`: 200
  }
}
```

### Relationships

| Source | Target | Type | Properties |
|--------|--------|------|------------|
| Module | Document | `:BELONGS_TO_MODULE` | `assigned_at` |
| Document | Chunk | `:HAS_CHUNK` | `index` |
| Chunk | Entity | `:CONTAINS_ENTITY` | `relevance_score`, `mention_count` |
| Entity | Entity | `:RELATES_TO` | `relationship_type` |
| StudySession | Message | `:HAS_MESSAGE` | `message_order` |
| StudySession | Module | `:STUDIES` | `added_at` |
| Document | Entity | `:ADDRESSES_TOPIC` | - |

### Deliverables
- [ ] `AURA-NOTES-MANAGER/api/migrations/001_add_module_schema.py`
- [ ] Module, Document, Chunk, StudySession, Message node types
- [ ] HNSW vector indices for chunks
- [ ] Constraints and indexes on module_id

### Checkpoints
- [ ] Migration script tested against Neo4j 5.15+
- [ ] Vector indices created with `SHOW VECTOR INDEXES`
- [ ] All constraints verified

---

## Phase 2: Knowledge Graph Processor

**Status:** COMPLETED ✓
**Duration:** Week 3-4
**Project:** AURA-NOTES-MANAGER
**Source:** Module-2-KG.md Section 5

### Objectives
1. Module-aware document processor
2. Entity extraction with Gemini LLM
3. Relationship building
4. LLM-based semantic chunking
5. Async batch processing with Celery

### Document Processor Flow

```
Document Upload
       │
       ▼
┌─────────────────┐
│ Parse Document  │  → Extract text from PDF/TXT
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Semantic Chunk  │  → LLM-based splitting (500-1000 tokens)
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Generate Embed  │  → Gemini text-embedding-004 (768-dim)
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Extract Entities│  → Gemini LLM extracts Topic, Concept, Methodology
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Build Relations │  → Entity relationships (DEFINES, DEPENDS_ON, USES)
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Store in Neo4j  │  → All nodes tagged with module_id
└─────────────────┘
```

### LLM Chunking Strategy

```python
CHUNK_BY_SEMANTIC_SPLIT = """
You are a text segmentation expert. Given the following document content,
identify logical breaks where the topic changes significantly.

Document:
{content}

Instructions:
1. Split into chunks at natural topic boundaries
2. Keep related concepts together
3. Aim for chunks of 500-1000 tokens
4. Return JSON array of chunks with brief descriptions
"""
```

### Celery Task Configuration

```python
@app.task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
    reject_on_worker_lost=True,
    time_limit=1800,
    soft_time_limit=1500
)
def process_document_to_kg(self, document_id, module_id, user_id, options):
    """Process document into knowledge graph with progress tracking."""
```

### Deliverables
- [ ] `AURA-NOTES-MANAGER/api/kg_processor.py`
- [ ] `AURA-NOTES-MANAGER/api/tasks/document_processing_tasks.py`
- [ ] Semantic chunking with LLM
- [ ] Entity extraction and relationship building
- [ ] Progress tracking via task state

### Checkpoints
- [ ] KG processing throughput: 10 docs/min
- [ ] All nodes tagged with module_id
- [ ] Task idempotency verified

---

## Phase 3: Module Management

**Status:** COMPLETED ✓
**Duration:** Week 5-6
**Project:** AURA-NOTES-MANAGER
**Source:** Module-2-KG.md Section 4
**Plans:** `.planning/phases/03-module-management/`

### Objectives
1. Module CRUD API endpoints
2. Document-to-module assignment
3. Module publishing workflow
4. Redis caching layer

### API Endpoints (Staff)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/modules` | Create module |
| GET | `/api/modules` | List all modules |
| GET | `/api/modules/{id}` | Get module details |
| PATCH | `/api/modules/{id}` | Update module |
| DELETE | `/api/modules/{id}` | Delete module |
| GET | `/api/modules/{id}/documents` | Get documents in module |
| POST | `/api/modules/{id}/documents` | Assign documents |
| POST | `/api/modules/{id}/process` | Trigger KG processing |
| POST | `/api/modules/{id}/publish` | Publish to students |
| POST | `/api/modules/{id}/unpublish` | Unpublish |
| GET | `/api/modules/{id}/kg-status` | Get KG status |

### Module Publishing Workflow

```
┌─────────────────────────────────────────────────────────┐
│              Module Publishing Flow                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐             │
│  │  Draft  │ ──►│Processing│ ──►│  Ready  │             │
│  └─────────┘    └─────────┘    └─────────┘             │
│       │                              │                  │
│       │                              ▼                  │
│       │                        ┌─────────┐              │
│       │                        │ Review  │              │
│       │                        └─────────┘              │
│       │                              │                  │
│       │                              ▼                  │
│       │                        ┌─────────┐              │
│       └───────────────────────►│Published│              │
│                                └─────────┘              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Deliverables
- [ ] `AURA-NOTES-MANAGER/api/module_manager.py`
- [ ] `AURA-NOTES-MANAGER/api/routers/modules.py`
- [ ] `AURA-NOTES-MANAGER/api/cache/module_cache.py`
- [ ] Module publishing workflow

### Checkpoints
- [ ] Module creation < 100ms
- [ ] Redis cache hit rate > 80%
- [ ] Document assignment < 50ms

---

## Phase 4: AURA-CHAT Module Integration

**Status:** COMPLETED ✓
**Duration:** Week 7
**Project:** AURA-CHAT
**Source:** Module-2-KG.md Section 4.3
**Plans:**
- `@.planning/phases/04-aura-chat-integration/04-01-PLAN.md`
- `@.planning/phases/04-aura-chat-integration/04-02-PLAN.md`
- `@.planning/phases/04-aura-chat-integration/04-03-PLAN.md`

### Objectives
1. Module-aware RAG engine
2. Module selection endpoints for students
3. Cross-module query support

### API Endpoints (Student)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/student/modules/available` | Get available modules |
| GET | `/api/student/modules/selected` | Get currently selected modules |
| POST | `/api/student/modules/select` | Select modules for study |
| POST | `/api/student/modules/deselect` | Deselect modules |
| GET | `/api/kg/search` | Search KG with module filter |
| GET | `/api/kg/cross-module` | Query across modules |

### Module-Filtered RAG

```python
async def query_with_modules(
    self,
    user_query: str,
    module_ids: List[str],
    session_id: Optional[str] = None,
    enable_cross_module: bool = True
) -> QueryResult:
    """Query with module_id filtering."""

    # 1. Vector search filtered by module_ids
    query_embedding = await self.embed(user_query)
    chunks = await self.vector_search(
        embedding=query_embedding,
        filter_clause="WHERE chunk.module_id IN $module_ids",
        top_k=20
    )

    # 2. Cross-module concept discovery
    if enable_cross_module:
        cross_concepts = await self.find_cross_module_concepts(
            query=user_query,
            module_ids=module_ids
        )

    # 3. Generate response with citations
    return await self.generate_answer(
        query=user_query,
        context=chunks,
        sources=module_ids
    )
```

### Cross-Module Discovery Query

```cypher
// Find concepts appearing in multiple selected modules
MATCH (e:Entity)
WHERE e.module_id IN $module_ids

MATCH (e2:Entity)
WHERE e2.name = e.name
AND e2.module_id IN $module_ids
AND e2.module_id <> e.module_id

WITH e.name as concept_name,
     collect(DISTINCT e.module_id) as modules,
     e.definition as definition

WHERE size(modules) >= 2

RETURN {
    name: concept_name,
    definition: definition,
    appears_in_modules: modules
} as cross_concept
ORDER BY size(modules) DESC
LIMIT 5
```

### Deliverables
- [ ] `AURA-CHAT/backend/rag_engine.py` (module-aware)
- [ ] `AURA-CHAT/backend/graph_manager.py` (add module methods)
- [ ] `AURA-CHAT/backend/routers/student_modules.py`

### Checkpoints
- [ ] RAG query latency (single module) < 2s
- [ ] RAG query latency (multi-module) < 3s
- [ ] Cross-module concepts discovered correctly

---

## Phase 5: Study Session System

**Duration:** Week 8-9
**Project:** AURA-CHAT
**Source:** Final-Module-2-KG.md Section 7
**Plans:**
- `@.planning/phases/05-study-session/05-01-PLAN.md`
- `@.planning/phases/05-study-session/05-02-PLAN.md`
- `@.planning/phases/05-study-session/05-03-PLAN.md`

### Status: COMPLETED ✓

### Objectives
1. Persistent chat sessions
2. Message history with module context
3. Session resume functionality
4. Session analytics

### Architecture

```
StudySession
  ├── HAS_MESSAGE → Message (ordered)
  └── STUDIES → Module (selected modules)
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions` | List user's sessions |
| POST | `/api/sessions` | Create new session |
| GET | `/api/sessions/{id}` | Get session details |
| PATCH | `/api/sessions/{id}` | Update session |
| DELETE | `/api/sessions/{id}` | Delete session |
| GET | `/api/sessions/{id}/messages` | Get message history |
| POST | `/api/sessions/{id}/messages` | Add message |
| POST | `/api/sessions/{id}/query` | Execute RAG query |
| GET | `/api/sessions/{id}/stats` | Get session analytics |

### Deliverables
- [ ] `AURA-CHAT/backend/session_manager.py`
- [ ] `AURA-CHAT/backend/routers/sessions.py`
- [ ] Message history with ordering
- [ ] Session analytics

### Checkpoints
- [ ] Session creation < 100ms
- [ ] Message history retrieval < 200ms
- [ ] History preserved across sessions

---

## Phase 6: Frontend Implementation

**Duration:** Week 10-11
**Projects:** AURA-NOTES-MANAGER + AURA-CHAT
**Plans:**
- `@.planning/phases/06-frontend/06-01-PLAN.md`
- `@.planning/phases/06-frontend/06-02-PLAN.md`
- `@.planning/phases/06-frontend/06-03-PLAN.md`

### Status: PLANNED ✓ (January 20, 2026)

### AURA-NOTES-MANAGER Frontend (Staff) - Extend Existing Explorer

```
AURA-NOTES-MANAGER/frontend/src/
├── pages/
│   └── ExplorerPage.tsx           # Main page (reuse as-is)
├── components/
│   ├── SidebarTree.tsx            # Tree navigation (reuse as-is)
│   ├── GridView.tsx               # Grid display (extend with KG badges)
│   └── ui/
│       └── ConfirmDialog.tsx      # Reuse existing dialog
├── stores/
│   └── useExplorerStore.ts        # Extend with KG state
├── types/
│   └── FileSystemNode.ts          # Add KG fields
├── api/
│   └── explorerApi.ts             # Use as-is
└── features/kg/                   # NEW: KG Processing UI
    ├── types/
    │   └── kg.types.ts
    ├── hooks/
    │   └── useKGProcessing.ts
    └── components/
        ├── KGStatusBadge.tsx
        ├── PublishDialog.tsx
        └── ProcessingQueue.tsx
```

**Reuse Strategy:** Extend existing ExplorerPage with KG status badges, don't recreate.

### AURA-CHAT Frontend (Student) - Feature-Based with Reuse

```
AURA-CHAT/client/src/
├── types/
│   └── api.ts                    # EXTEND with module + session types
├── lib/
│   └── api.ts                    # EXTEND with module + session APIs
├── components/
│   ├── MessageBubble.tsx         # EXTRACT from ChatPage.tsx
│   └── CitationPanel.tsx         # EXTRACT from ChatPage.tsx
├── features/chat/
│   └── ChatPage.tsx              # REUSE Dropdown for ModuleSelector
│
├── features/modules/              # Module Selection (NEW)
│   ├── hooks/
│   │   └── useModule.ts
│   └── components/
│       ├── ModuleCard.tsx
│       ├── ModuleSelector.tsx    # Reuses Dropdown from ChatPage
│       └── CrossModuleConcepts.tsx
│
└── features/study-sessions/      # Study Session Chat (NEW)
    ├── hooks/
    │   ├── useStudySession.ts
    │   └── useSessionQuery.ts
    └── components/
        ├── StudySession.tsx       # Main container
        ├── SessionChat.tsx        # Uses extracted MessageBubble
        └── SessionSidebar.tsx     # Session history
```

### State Management

| Layer | Technology | Purpose |
|-------|------------|---------|
| L1 | React Query | Server state (modules, sessions) |
| L2 | Zustand | UI state (selections, preferences) |

### Deliverables

#### AURA-NOTES-MANAGER (Extend Existing)
- [x] ExplorerPage.tsx (reuse as-is)
- [x] SidebarTree.tsx (reuse as-is)
- [x] GridView.tsx (extend with KG badges)
- [x] useExplorerStore.ts (extend with KG state)
- [x] FileSystemNode.ts (add KG fields)
- [x] explorerApi.ts (use as-is)
- [x] ConfirmDialog.tsx (reuse)
- [ ] `features/kg/types/kg.types.ts` (NEW)
- [ ] `features/kg/hooks/useKGProcessing.ts` (NEW)
- [ ] `features/kg/components/KGStatusBadge.tsx` (NEW)
- [ ] `features/kg/components/PublishDialog.tsx` (NEW)
- [ ] `features/kg/components/ProcessingQueue.tsx` (NEW)

#### AURA-CHAT Module Selector (06-02) - Extend/Reuse
- [x] types/api.ts (extend with module types)
- [x] lib/api.ts (extend with module API functions)
- [x] features/chat/ChatPage.tsx (reuse Dropdown component)
- [ ] `features/modules/hooks/useModule.ts` (NEW)
- [ ] `features/modules/components/ModuleCard.tsx` (NEW)
- [ ] `features/modules/components/ModuleSelector.tsx` (NEW)
- [ ] `features/modules/components/CrossModuleConcepts.tsx` (NEW)

**06-02 Summary: 6 files (3 existing/extended + 4 new)**

#### AURA-CHAT Study Sessions (06-03) - Extract/Reuse
- [x] types/api.ts (extend with session types)
- [x] lib/api.ts (extend with session API functions)
- [ ] `components/MessageBubble.tsx` (EXTRACT from ChatPage.tsx)
- [ ] `components/CitationPanel.tsx` (EXTRACT from ChatPage.tsx)
- [ ] `features/study-sessions/hooks/useStudySession.ts` (NEW)
- [ ] `features/study-sessions/hooks/useSessionQuery.ts` (NEW)
- [ ] `features/study-sessions/components/SessionSidebar.tsx` (NEW)
- [ ] `features/study-sessions/components/SessionChat.tsx` (NEW)
- [ ] `features/study-sessions/components/StudySession.tsx` (NEW)

**06-03 Summary: 9 files (4 existing/extended/extracted + 5 new)**

**Total Phase 6: 26 files (16 existing/extended/extracted + 10 new)**

### Checkpoints
- [ ] UI Module Load Time < 500ms
- [ ] All components responsive
- [ ] Optimistic updates work

---

## Phase 7: Testing & Optimization

**Duration:** Week 12
**Projects:** Both
**Plans:** `.planning/phases/07-testing/`

**Status:** PLANNED (January 21, 2026)

### Phase 7 Sub-Plans

| # | Focus | Deliverables |
|---|-------|--------------|
| 07-01 | AURA-CHAT Backend Unit Tests | 50+ tests, 85% coverage, fixtures |
| 07-02 | AURA-CHAT Frontend Unit Tests | 40+ tests, Vitest, React Testing Library |
| 07-03 | AURA-NOTES-MANAGER Unit Tests | 55+ tests, KG component tests |
| 07-04 | Integration & E2E Tests | 65+ E2E tests, Playwright, all browsers |
| 07-05 | Performance & Docker | Benchmarks, Docker Compose, security |

### Testing Pyramid

```
┌────────────────────────────────────────────────────────────────┐
│                    Testing Pyramid                             │
├────────────────────────────────────────────────────────────────┤
│  Unit Tests          ████████  (210+ tests)                   │
│  Integration Tests   ██████    (50+ tests)                    │
│  E2E Tests           ███       (65+ tests)                    │
│  Load Tests          ██        (5 scenarios)                  │
└────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Python Tests | Pytest | Backend unit tests |
| Python Performance | pytest-benchmark | Performance benchmarks |
| Python Load | Locust | Load testing |
| JS Tests | Vitest | Frontend unit tests |
| JS E2E | Playwright | End-to-end testing |
| JS Coverage | V8 Coverage | Coverage reporting |
| Container | Docker Compose | Full stack deployment |
| Monitoring | Prometheus + Grafana | Metrics and dashboards |

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Module list load | < 100ms | P95 latency |
| Module create | < 100ms | P95 latency |
| Document assignment | < 50ms | P95 latency |
| KG processing | < 60s/doc | Average |
| RAG query (single module) | < 2s | P95 latency |
| RAG query (multi-module) | < 3s | P95 latency |
| Vector search | < 100ms | P99 latency |
| Frontend TTI | < 1.5s | Lighthouse |

### Security Measures

| Component | Security Measure |
|-----------|-----------------|
| API Auth | JWT tokens |
| Module Access | User ownership check |
| Document Access | Module membership |
| Session Access | User ownership |
| Rate Limiting | Redis-based (100 req/min) |
| Input Validation | Pydantic schemas |
| CORS | Configured origins |
| Headers | X-Frame-Options, HSTS, XSS-Protection |

### Deliverables

#### 07-01 AURA-CHAT Backend Unit Tests
- [x] `tests/conftest.py` - Extended fixtures (mock Neo4j, Gemini, Redis)
- [ ] `tests/unit/test_session_crud.py` - Session CRUD tests (13)
- [ ] `tests/unit/test_messages.py` - Message operation tests (13)
- [ ] `tests/unit/test_module_filtering.py` - Module filtering tests (13)
- [ ] `tests/unit/test_rag_engine.py` - RAG engine tests (13)

**Total: 52 tests, 85% coverage target**

#### 07-02 AURA-CHAT Frontend Unit Tests
- [ ] `client/package.json` - Add Vitest dependencies
- [ ] `client/vitest.config.ts` - Vitest configuration
- [ ] `client/src/test/setup.ts` - Test setup
- [ ] `client/src/features/chat/ChatPage.test.tsx` - Chat tests (20)
- [ ] `client/src/features/study-sessions/hooks/useStudySession.test.ts` - Hook tests (9)
- [ ] `client/src/components/MessageBubble.test.tsx` - Component tests (10)
- [ ] `client/src/components/CitationPanel.test.tsx` - Component tests (5)

**Total: 44 tests, 80% coverage target**

#### 07-03 AURA-NOTES-MANAGER Unit Tests
- [ ] `frontend/src/test/setup.ts` - Extended setup
- [ ] `frontend/src/features/kg/components/KGStatusBadge.test.tsx` - Badge tests (10)
- [ ] `frontend/src/features/kg/components/PublishDialog.test.tsx` - Dialog tests (10)
- [ ] `frontend/src/features/kg/components/ProcessingQueue.test.tsx` - Queue tests (10)
- [ ] `frontend/src/pages/ExplorerPage.test.tsx` - Page tests (16)
- [ ] `frontend/src/stores/useExplorerStore.test.ts` - Store tests (12)

**Total: 58 tests, 75% coverage target**

#### 07-04 Integration & E2E Tests
- [ ] `frontend/playwright.config.ts` - Playwright config
- [ ] `AURA-CHAT/client/e2e/chat.spec.ts` - Chat E2E (20)
- [ ] `AURA-CHAT/client/e2e/graph.spec.ts` - Graph E2E (15)
- [ ] `AURA-NOTES-MANAGER/frontend/e2e/explorer.spec.ts` - Explorer E2E (20)
- [ ] `AURA-NOTES-MANAGER/frontend/e2e/kg-processing.spec.ts` - KG E2E (15)
- [ ] `AURA-CHAT/client/e2e/test-utils.ts` - Shared utilities

**Total: 70 E2E tests, all browsers**

#### 07-05 Performance & Docker
- [ ] `tests/performance/test_benchmarks.py` - 10 benchmark tests
- [ ] `tests/load/locustfile.py` - 5 load scenarios
- [ ] `AURA-CHAT/docker-compose.yml` - Full stack deployment
- [ ] `.env.example` - Environment configuration
- [ ] `server/routers/health.py` - Health check endpoints
- [ ] `server/security/middleware.py` - Security middleware

**Total: All performance targets met, Docker works**

### Checkpoints
- [ ] 224+ unit tests pass
- [ ] 70+ E2E tests pass
- [ ] 85% backend coverage
- [ ] 80% frontend coverage
- [ ] All performance targets met
- [ ] Docker deployment works
- [ ] Health checks pass
- [ ] Rate limiting configured

---

## Implementation Timeline Summary

| Week | Phase | Project | Deliverables |
|------|-------|---------|--------------|
| 1-2 | Phase 1: Schema | AURA-NOTES-MANAGER | Migration, constraints, indices |
| 3-4 | Phase 2: KG Processor | AURA-NOTES-MANAGER | Entity extraction, Celery tasks, Chunking |
| 5-6 | Phase 3: Module Mgmt | AURA-NOTES-MANAGER | ModuleManager, API, Publishing |
| 7 | Phase 4: AURA-CHAT Integration | AURA-CHAT | Module-filtered RAG, student APIs |
| 8-9 | Phase 5: Study Sessions | AURA-CHAT | SessionManager, History, Analytics |
| 10-11 | Phase 6: Frontend | Both | React components for both apps |
| 12 | Phase 7: Testing | Both | 224+ unit tests, 70+ E2E tests, Docker |

---

## Key Files Reference

### AURA-NOTES-MANAGER

| File Path | Purpose |
|-----------|---------|
| `api/migrations/001_add_module_schema.py` | Database migration |
| `api/kg_processor.py` | Knowledge graph processing |
| `api/tasks/document_processing_tasks.py` | Celery tasks |
| `api/module_manager.py` | Module CRUD |
| `api/routers/modules.py` | Module API endpoints |
| `api/cache/module_cache.py` | Redis caching |
| `frontend/src/features/kg/*` | KG Processing UI |
| `frontend/src/pages/ExplorerPage.tsx` | Module explorer (extend) |
| `frontend/src/components/GridView.tsx` | Grid view (extend) |

### AURA-CHAT

| File Path | Purpose |
|-----------|---------|
| `backend/graph_manager.py` | Neo4j operations |
| `backend/rag_engine.py` | Module-aware RAG queries |
| `backend/session_manager.py` | Study sessions |
| `backend/routers/student_modules.py` | Student module APIs |
| `backend/routers/sessions.py` | Session APIs |
| `client/src/features/modules/*` | Module selector |
| `client/src/features/study-sessions/*` | Chat UI |

---

## Success Metrics Summary

| Metric | Target | Phase |
|--------|--------|-------|
| Module list load | < 100ms | Phase 3 |
| Module create | < 100ms | Phase 3 |
| KG processing | < 60s/doc | Phase 2 |
| RAG query (single module) | < 2s | Phase 4 |
| RAG query (multi-module) | < 3s | Phase 4 |
| Frontend TTI | < 1.5s | Phase 6 |
| Test coverage | > 90% | Phase 7 |

---

## Roadmap Evolution

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2026-01-19 | Initial aligned roadmap |
| 2.1 | 2026-01-19 | Dual-project architecture (AURA-NOTES-MANAGER + AURA-CHAT) |
| 2.2 | 2026-01-20 | Phase 6 Frontend plans (extend existing, feature-based structure) |
| 2.3 | 2026-01-20 | Phase 6 plans optimized: extend types/api.ts, lib/api.ts, extract MessageBubble/CitationPanel, reuse Dropdown |
| 2.4 | 2026-01-21 | Phase 7 Testing & Optimization plans: 5 sub-plans, 224+ tests, Docker Compose |

---

## How to Create Plans/Prompts

Use this XML-based structure for all phase plans. Each plan is self-contained and executable by Claude.

### Plan Structure Template

```markdown
<objective>
[What and why]
Purpose: [...]
Output: [...]
</objective>

<context>
@.planning/ROADMAP.md - Phase context
@relevant/source/files.py - Existing code to extend
Previous: [what was completed]
Current: [what we're doing now]
</context>

<requirements>
1. Specific requirement one (what the feature must do)
2. Specific requirement two (constraints or behaviors)
3. Data schema expectations (what fields and types, not implementation)
4. API contracts (endpoints, parameters, responses - not code)
5. Integration points (what other systems/modules this connects to)
</requirements>

<tasks>
<task>
<type>create|update</type>
<file>path/to/file.py</file>
<action>
Describe WHAT to implement and WHY, not HOW.

Include:
- Purpose of the file/class/method
- Data structures and their purpose
- Behavior and edge cases to handle
- Pitfalls to avoid
- Integration points with existing code

DO NOT include code - the implementing agent writes the code.
</action>
<verify>
1. Check syntax: `python -m py_compile path/to/file.py`
2. Verify expected behavior
</verify>
<done>
[Measurable completion criteria - what the implementation must achieve]
</done>
</task>
</tasks>

<output>
SUMMARY.md in `.planning/phases/XX-name/XX-SUMMARY.md`
</output>

<success_criteria>
- [ ] Criterion one
- [ ] Criterion two
- [ ] All files pass py_compile check
</success_criteria>

<checkpoint:human-verify>
[Instructions for human verification - visual check, API test, etc.]
</checkpoint:human-verify>
```

### Task Types

| Type | When to Use |
|------|-------------|
| `create` | New file creation |
| `update` | Modify existing file |
| `delete` | Remove file/feature |

### Task Fields

| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | create/update/delete |
| `file` | Yes | Exact file path |
| `action` | Yes | Implementation details with code examples |
| `verify` | Yes | Executable verification commands |
| `done` | Yes | Measurable completion criteria |

### Naming Convention

- Phase folder: `phases/XX-name/`
- Plan file: `XX-YY-PLAN.md` (XX=phase, YY=sub-plan)
- Summary file: `XX-YY-SUMMARY.md`

Example: `phases/05-study-session/05-02-PLAN.md`

### Checkpoint Types

| Type | Description |
|------|-------------|
| `checkpoint:human-verify` | Visual/UI verification needed |
| `checkpoint:decision` | Human must choose between options |

### Best Practices

1. **Web-search first**: Before implementing any feature, search for official documentation and best practices
2. **Atomic tasks**: Each task = 15-60 min of Claude work
3. **Descriptive, not prescriptive**: Describe WHAT and WHY, not HOW
4. **No code in plans**: The implementing agent writes all code
5. **Verification**: Always include `py_compile` check
6. **File headers**: Every new file needs header with description and @see

---

## Next Steps

1. **Approve roadmap** - Confirm dual-project structure
2. **Begin Phase 1** - Start with database schema in AURA-NOTES-MANAGER
3. **Verify checkpoints** - Each phase begins with research verification

---

## Research References

- **Neo4j Vector Index:** https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/
- **GraphRAG Field Guide:** https://neo4j.com/blog/developer/graphrag-field-guide-rag-patterns/
- **Module-2-KG.md:** Full implementation plan reference
