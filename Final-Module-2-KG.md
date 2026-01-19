# AURA Module-to-Knowledge Graph (M2KG) - Comprehensive Implementation Plan

> **Version:** 2.0 (Low-Level Implementation)  
> **Last Updated:** January 19, 2026  
> **Status:** Implementation Ready  
> **Total Duration:** 12 Weeks (84 Working Days)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Deep-Dive](#2-architecture-deep-dive)
3. [Technology Stack & Best Practices](#3-technology-stack--best-practices)
4. [Data Models & Neo4j Schema](#4-data-models--neo4j-schema)
5. [Phase 1: Database Schema Extension](#5-phase-1-database-schema-extension)
6. [Phase 2: Backend Module Management](#6-phase-2-backend-module-management)
7. [Phase 3: Knowledge Graph Processor](#7-phase-3-knowledge-graph-processor)
8. [Phase 4: Module-Aware RAG Engine](#8-phase-4-module-aware-rag-engine)
9. [Phase 5: Study Session System](#9-phase-5-study-session-system)
10. [Phase 6: Frontend Implementation](#10-phase-6-frontend-implementation)
11. [Phase 7: Testing & Optimization](#11-phase-7-testing--optimization)
12. [API Reference](#12-api-reference)
13. [Security & Performance](#13-security--performance)
14. [Deployment Guide](#14-deployment-guide)

---

## 1. Executive Summary

### 1.1 Project Vision

The Module-to-Knowledge Graph (M2KG) feature transforms AURA from a document-centric system to a **module-centric learning platform**. Users will organize documents into thematic modules (e.g., "Machine Learning Fundamentals", "Quantum Computing"), and the system builds interconnected knowledge graphs that enable:

- **Contextual Learning:** Study sessions filtered to specific knowledge domains
- **Cross-Module Discovery:** Find conceptual bridges between different study areas
- **Progressive Mastery:** Track understanding across module hierarchies
- **Semantic Navigation:** Explore concepts through graph relationships

### 1.2 Key Deliverables

| Deliverable | Description | Priority |
|-------------|-------------|----------|
| Module CRUD API | Full lifecycle management for modules | P0 |
| Knowledge Graph Processor | Entity extraction with module-aware relationships | P0 |
| Module-Filtered RAG | Query responses scoped to selected modules | P0 |
| Study Session System | Persistent chat sessions with module context | P0 |
| Module Browser UI | React components for module management | P0 |
| Cross-Module Analytics | Concept overlap and relationship visualization | P1 |
| Batch Processing Pipeline | Celery-based async document processing | P1 |

### 1.3 Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Module Creation Latency | < 100ms | API response time |
| Document-to-Module Assignment | < 50ms | Database operation time |
| KG Processing Throughput | 10 docs/min | Celery task metrics |
| Module-Filtered Query Latency | < 2s | End-to-end RAG timing |
| UI Module Load Time | < 500ms | React performance profiling |
| Vector Search Accuracy | > 85% relevance | User feedback sampling |

---

## 2. Architecture Deep-Dive

### 2.1 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React + TypeScript)                   │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │ModuleBrowser│  │ModuleSelector│  │StudySession │  │ ModuleChat       │   │
│  │  (CRUD UI)  │  │  (Dropdown)  │  │  (Context)  │  │ (RAG Interface)  │   │
│  └──────┬──────┘  └──────┬───────┘  └──────┬──────┘  └────────┬─────────┘   │
│         │                │                 │                   │            │
│  ┌──────┴────────────────┴─────────────────┴───────────────────┴─────────┐  │
│  │                    TanStack Query (Server State)                       │  │
│  │         useModules() | useStudySession() | useModuleChat()            │  │
│  └────────────────────────────────┬──────────────────────────────────────┘  │
│                                   │                                         │
│  ┌────────────────────────────────┴──────────────────────────────────────┐  │
│  │                    Zustand Store (Client State)                        │  │
│  │      selectedModuleIds | activeSessionId | uiPreferences              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FASTAPI SERVER (Python 3.11+)                      │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────────────────┐  │
│  │ /api/modules   │  │ /api/sessions   │  │ /api/chat                    │  │
│  │  - CRUD        │  │  - Create       │  │  - Query (module-filtered)   │  │
│  │  - Documents   │  │  - History      │  │  - Stream response           │  │
│  │  - Stats       │  │  - Resume       │  │  - Citations                 │  │
│  └───────┬────────┘  └────────┬────────┘  └──────────────┬───────────────┘  │
│          │                    │                          │                  │
│  ┌───────┴────────────────────┴──────────────────────────┴───────────────┐  │
│  │                    Dependency Injection Layer                          │  │
│  │   get_graph_manager() | get_rag_engine() | get_module_manager()       │  │
│  └───────────────────────────────┬───────────────────────────────────────┘  │
└──────────────────────────────────┼───────────────────────────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
┌─────────────────┐    ┌───────────────────────┐    ┌─────────────────────┐
│  CELERY WORKER  │    │    BACKEND SERVICES   │    │    REDIS CACHE      │
│  ┌───────────┐  │    │  ┌─────────────────┐  │    │  ┌───────────────┐  │
│  │ kg_tasks  │  │    │  │ ModuleManager   │  │    │  │ module_cache  │  │
│  │  - process│  │    │  │ SessionManager  │  │    │  │ session_cache │  │
│  │  - batch  │  │    │  │ RAGEngine       │  │    │  │ query_cache   │  │
│  │  - retry  │  │    │  │ GraphManager    │  │    │  │ stats_cache   │  │
│  └───────────┘  │    │  └─────────────────┘  │    │  └───────────────┘  │
└────────┬────────┘    └───────────┬───────────┘    └─────────────────────┘
         │                         │
         └────────────┬────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NEO4J KNOWLEDGE GRAPH (5.x+)                         │
│                                                                              │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐        │
│   │ :Module  │─────▶│:Document │─────▶│  :Chunk  │─────▶│ :Entity  │        │
│   │          │      │          │      │          │      │(Topic,   │        │
│   │ id,name  │      │ id,title │      │ id,text  │      │Concept)  │        │
│   │ module_id│◀─────│ module_id│◀─────│ module_id│◀─────│ module_id│        │
│   └──────────┘      └──────────┘      └──────────┘      └──────────┘        │
│                                                                              │
│   Vector Indices:    chunk_vector_index (HNSW, 768-dim, cosine)             │
│                      module_vector_index (for semantic module matching)      │
│   Fulltext Index:    chunk_fulltext_index (Apache Lucene, English)          │
│   Constraints:       module_id_unique, document_module_compound              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Architecture

```
Document Upload Flow:
────────────────────
User Upload → API Validation → File Storage → Celery Task Queue
                                                      │
                    ┌─────────────────────────────────┘
                    ▼
            Text Extraction (PyMuPDF/python-docx)
                    │
                    ▼
            Entity Extraction (Gemini LLM)
                    │
                    ▼
            Semantic Chunking (768-dim embeddings)
                    │
                    ▼
            Module Assignment (module_id propagation)
                    │
                    ▼
            Neo4j Storage (nodes + relationships + vector index)
                    │
                    ▼
            Cache Invalidation (Redis module stats)


Query Flow (Module-Filtered RAG):
─────────────────────────────────
User Query + Module Selection
            │
            ▼
    Query Embedding (Gemini text-embedding-004)
            │
            ▼
    Cache Check (Redis: query + module_ids hash)
            │
    ┌───────┴───────┐
    │ Cache Hit     │ Cache Miss
    ▼               ▼
  Return         Vector Search (HNSW with module_id filter)
  Cached              │
  Response            ▼
                 Graph Expansion (2-hop traversal within modules)
                      │
                      ▼
                 Context Assembly (ranked chunks + entities)
                      │
                      ▼
                 LLM Generation (Gemini with citations)
                      │
                      ▼
                 Cache Store + Response
```

### 2.3 Component Responsibilities

| Component | Location | Responsibilities |
|-----------|----------|------------------|
| `ModuleManager` | `backend/module_manager.py` | Module CRUD, document assignment, validation |
| `KGProcessor` | `backend/kg_processor.py` | Entity extraction, relationship building, module tagging |
| `SessionManager` | `backend/session_manager.py` | Study session lifecycle, message history |
| `RAGEngine` | `backend/rag_engine.py` (modified) | Module-filtered retrieval, context assembly |
| `GraphManager` | `backend/graph_manager.py` (modified) | Neo4j operations, vector search, module queries |
| `ModuleCache` | `backend/cache/module_cache.py` | Redis caching for module data |
| `ModuleTasks` | `backend/tasks/module_processing_tasks.py` | Celery async processing |

---

## 3. Technology Stack & Best Practices

### 3.1 Neo4j Vector Search (Best Practices from Research)

Based on Neo4j 5.x documentation and GraphRAG patterns:

#### 3.1.1 Vector Index Configuration

```cypher
-- HNSW Index for Chunk Embeddings (Optimal Settings)
CREATE VECTOR INDEX chunk_vector_index IF NOT EXISTS
FOR (c:Chunk) ON (c.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,           -- Gemini embedding dimensions
    `vector.similarity_function`: 'cosine',
    `vector.hnsw.m`: 16,                -- Connections per layer (default optimal)
    `vector.hnsw.ef_construction`: 200  -- Build-time quality (higher = better recall)
  }
}

-- Runtime Search Configuration
CALL db.index.vector.queryNodes(
  'chunk_vector_index',
  10,                                    -- top_k results
  $query_embedding
) YIELD node, score
WHERE node.module_id IN $module_ids      -- Module filtering (post-filter)
RETURN node, score
ORDER BY score DESC
```

#### 3.1.2 GraphRAG Pattern (Combining Vector + Graph)

```python
# Best Practice: Two-Phase Retrieval
async def graphrag_retrieve(query: str, module_ids: List[str]) -> Context:
    """
    Phase 1: Vector similarity for initial candidates
    Phase 2: Graph traversal for contextual expansion
    """
    # Phase 1: Semantic search within module scope
    query_embedding = await self.embed(query)
    initial_chunks = await self.graph_manager.vector_search_with_filter(
        embedding=query_embedding,
        top_k=20,
        filter_clause="WHERE node.module_id IN $module_ids",
        params={"module_ids": module_ids}
    )
    
    # Phase 2: Graph expansion for context
    chunk_ids = [c["id"] for c in initial_chunks[:10]]
    expanded_context = await self.graph_manager.expand_graph_context(
        node_ids=chunk_ids,
        max_hops=2,
        relationship_types=["CONTAINS_ENTITY", "RELATES_TO", "DEPENDS_ON"],
        module_filter=module_ids  # Stay within module boundaries
    )
    
    return self._merge_and_rank(initial_chunks, expanded_context)
```

#### 3.1.3 Multi-Tenancy via Module Partitioning

```cypher
-- Property-based partitioning (recommended for module isolation)
-- Each node carries module_id for efficient filtering

-- Compound index for fast module-scoped lookups
CREATE INDEX chunk_module_index IF NOT EXISTS
FOR (c:Chunk) ON (c.module_id, c.created_at)

-- Example: Get all chunks in a module, ordered by creation
MATCH (c:Chunk {module_id: $module_id})
RETURN c ORDER BY c.created_at DESC
LIMIT 100
```

### 3.2 Celery Task Processing (Best Practices from Research)

Based on Celery 5.6.x documentation and production patterns:

#### 3.2.1 Task Definition with Best Practices

```python
# backend/tasks/module_processing_tasks.py
from celery import Celery, Task
from celery.exceptions import MaxRetriesExceededError
from pydantic import BaseModel, ValidationError
import logging

app = Celery('aura_tasks')

class ProcessingInput(BaseModel):
    """Pydantic validation for task inputs"""
    document_id: str
    module_id: str
    user_id: str
    options: dict = {}

class KGProcessingTask(Task):
    """Base task with shared resources and error handling"""
    _graph_manager = None
    _embedding_service = None
    
    @property
    def graph_manager(self):
        if self._graph_manager is None:
            from backend.graph_manager import GraphManager
            self._graph_manager = GraphManager()
        return self._graph_manager
    
    @property
    def embedding_service(self):
        if self._embedding_service is None:
            from backend.utils.embeddings import EmbeddingService
            self._embedding_service = EmbeddingService()
        return self._embedding_service

@app.task(
    bind=True,                           # Access self for retries
    base=KGProcessingTask,               # Inherit shared resources
    autoretry_for=(ConnectionError, TimeoutError),  # Auto-retry these
    retry_backoff=True,                  # Exponential backoff
    retry_backoff_max=600,               # Max 10 min between retries
    retry_jitter=True,                   # Add randomness to prevent thundering herd
    max_retries=5,                       # Maximum retry attempts
    acks_late=True,                      # Acknowledge after completion (safer)
    reject_on_worker_lost=True,          # Re-queue if worker dies
    time_limit=1800,                     # 30 min hard limit
    soft_time_limit=1500                 # 25 min soft limit (raises exception)
)
def process_document_to_kg(
    self,
    document_id: str,
    module_id: str,
    user_id: str,
    options: dict = None
) -> dict:
    """
    Process a document into the knowledge graph.
    
    This task is IDEMPOTENT: running it multiple times with the same
    inputs produces the same result (upsert semantics in Neo4j).
    """
    logger = logging.getLogger(f"kg_task.{self.request.id}")
    
    # Validate inputs with Pydantic
    try:
        validated = ProcessingInput(
            document_id=document_id,
            module_id=module_id,
            user_id=user_id,
            options=options or {}
        )
    except ValidationError as e:
        logger.error(f"Validation failed: {e}")
        raise ValueError(f"Invalid task input: {e}")
    
    logger.info(f"Processing document {document_id} for module {module_id}")
    
    try:
        # Update task state for progress tracking
        self.update_state(
            state='PROCESSING',
            meta={'stage': 'text_extraction', 'progress': 0}
        )
        
        # 1. Extract text
        text = self._extract_document_text(validated.document_id)
        self.update_state(
            state='PROCESSING',
            meta={'stage': 'entity_extraction', 'progress': 25}
        )
        
        # 2. Extract entities
        entities = self._extract_entities(text)
        self.update_state(
            state='PROCESSING',
            meta={'stage': 'chunking', 'progress': 50}
        )
        
        # 3. Create chunks with embeddings
        chunks = self._create_chunks(text, validated.module_id)
        self.update_state(
            state='PROCESSING',
            meta={'stage': 'graph_storage', 'progress': 75}
        )
        
        # 4. Store in Neo4j (idempotent MERGE operations)
        result = self._store_in_graph(
            document_id=validated.document_id,
            module_id=validated.module_id,
            entities=entities,
            chunks=chunks
        )
        
        # 5. Invalidate caches
        self._invalidate_module_cache(validated.module_id)
        
        return {
            'success': True,
            'document_id': validated.document_id,
            'module_id': validated.module_id,
            'entities_count': len(entities),
            'chunks_count': len(chunks),
            'processing_time': result['processing_time']
        }
        
    except self.MaxRetriesExceededError:
        logger.error(f"Max retries exceeded for document {document_id}")
        self._mark_document_failed(document_id, "Max retries exceeded")
        raise
    
    except Exception as e:
        logger.exception(f"Processing failed: {e}")
        # Don't auto-retry unknown errors, but record them
        self._mark_document_failed(document_id, str(e))
        raise
```

#### 3.2.2 Task State Tracking Pattern

```python
# Checking task status from API
from celery.result import AsyncResult

def get_processing_status(task_id: str) -> dict:
    """Get the status of a processing task."""
    result = AsyncResult(task_id)
    
    response = {
        'task_id': task_id,
        'state': result.state,  # PENDING, STARTED, PROCESSING, SUCCESS, FAILURE, RETRY
        'ready': result.ready(),
        'successful': result.successful() if result.ready() else None,
    }
    
    if result.state == 'PROCESSING':
        response['meta'] = result.info  # {'stage': '...', 'progress': N}
    elif result.state == 'SUCCESS':
        response['result'] = result.result
    elif result.state == 'FAILURE':
        response['error'] = str(result.result)
        response['traceback'] = result.traceback
    
    return response
```

### 3.3 FastAPI Patterns (Best Practices from Research)

Based on FastAPI documentation and production patterns:

#### 3.3.1 Dependency Injection Architecture

```python
# server/dependencies.py
from typing import Annotated, Generator
from functools import lru_cache
from fastapi import Depends, Request

from backend.graph_manager import GraphManager
from backend.module_manager import ModuleManager
from backend.rag_engine import RAGEngine
from backend.session_manager import SessionManager
from backend.cache.module_cache import ModuleCache

# Singleton services (created once, reused)
@lru_cache()
def get_graph_manager() -> GraphManager:
    """Singleton GraphManager with connection pooling."""
    return GraphManager()

@lru_cache()
def get_module_cache() -> ModuleCache:
    """Singleton Redis cache client."""
    return ModuleCache()

# Dependent services (depend on other services)
def get_module_manager(
    graph_manager: Annotated[GraphManager, Depends(get_graph_manager)],
    cache: Annotated[ModuleCache, Depends(get_module_cache)]
) -> ModuleManager:
    """ModuleManager with injected dependencies."""
    return ModuleManager(graph_manager=graph_manager, cache=cache)

def get_rag_engine(
    graph_manager: Annotated[GraphManager, Depends(get_graph_manager)]
) -> RAGEngine:
    """RAGEngine with injected GraphManager."""
    return RAGEngine(graph_manager=graph_manager)

def get_session_manager(
    graph_manager: Annotated[GraphManager, Depends(get_graph_manager)],
    rag_engine: Annotated[RAGEngine, Depends(get_rag_engine)]
) -> SessionManager:
    """SessionManager for study session lifecycle."""
    return SessionManager(
        graph_manager=graph_manager,
        rag_engine=rag_engine
    )

# Type aliases for cleaner route signatures
GraphManagerDep = Annotated[GraphManager, Depends(get_graph_manager)]
ModuleManagerDep = Annotated[ModuleManager, Depends(get_module_manager)]
RAGEngineDep = Annotated[RAGEngine, Depends(get_rag_engine)]
SessionManagerDep = Annotated[SessionManager, Depends(get_session_manager)]

# Cleanup on shutdown
def cleanup_services():
    """Called during application shutdown."""
    gm = get_graph_manager()
    if gm:
        gm.close()
    
    cache = get_module_cache()
    if cache:
        cache.close()
```

#### 3.3.2 Background Tasks vs Celery Decision

```python
# Use BackgroundTasks for: quick operations (< 30s), no persistence needed
# Use Celery for: long operations, need retry, need status tracking

from fastapi import BackgroundTasks

# Example: Quick cache invalidation (use BackgroundTasks)
@router.post("/modules/{module_id}/documents/{doc_id}")
async def assign_document(
    module_id: str,
    doc_id: str,
    background_tasks: BackgroundTasks,
    module_manager: ModuleManagerDep
):
    # Synchronous assignment (fast)
    result = await module_manager.assign_document(module_id, doc_id)
    
    # Background cache invalidation (doesn't block response)
    background_tasks.add_task(
        module_manager.invalidate_stats_cache,
        module_id
    )
    
    return result

# Example: Document processing (use Celery)
@router.post("/modules/{module_id}/documents/{doc_id}/process")
async def process_document(
    module_id: str,
    doc_id: str,
    module_manager: ModuleManagerDep
):
    # Queue async task (returns immediately)
    task = process_document_to_kg.delay(
        document_id=doc_id,
        module_id=module_id,
        user_id=get_current_user_id()
    )
    
    return {
        "task_id": task.id,
        "status": "queued",
        "status_url": f"/api/tasks/{task.id}"
    }
```

### 3.4 React + TypeScript Patterns (Best Practices from Research)

Based on React documentation and TanStack Query patterns:

#### 3.4.1 Component Architecture ("Thinking in React")

```
ModuleBrowser/                    # Feature folder
├── index.ts                      # Public exports
├── ModuleBrowser.tsx             # Container (data fetching, state)
├── ModuleList.tsx                # Presentation (receives props)
├── ModuleCard.tsx                # Presentation (single module)
├── ModuleCreateDialog.tsx        # Controlled modal
├── hooks/
│   ├── useModules.ts             # TanStack Query hook
│   ├── useModuleMutations.ts     # Create/Update/Delete mutations
│   └── useModuleSelection.ts     # Local selection state
├── types.ts                      # Module-specific types
└── ModuleBrowser.test.tsx        # Component tests
```

#### 3.4.2 TanStack Query Integration

```typescript
// hooks/useModules.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { modulesApi } from '../api/modulesApi';
import type { Module, CreateModuleInput, UpdateModuleInput } from '../types';

// Query keys factory (prevents typos, enables targeted invalidation)
export const moduleKeys = {
  all: ['modules'] as const,
  lists: () => [...moduleKeys.all, 'list'] as const,
  list: (filters: ModuleFilters) => [...moduleKeys.lists(), filters] as const,
  details: () => [...moduleKeys.all, 'detail'] as const,
  detail: (id: string) => [...moduleKeys.details(), id] as const,
  stats: (id: string) => [...moduleKeys.all, 'stats', id] as const,
};

// Fetch all modules
export function useModules(filters?: ModuleFilters) {
  return useQuery({
    queryKey: moduleKeys.list(filters ?? {}),
    queryFn: () => modulesApi.getModules(filters),
    staleTime: 30_000,           // Consider fresh for 30s
    gcTime: 5 * 60 * 1000,       // Keep in cache 5min (formerly cacheTime)
    refetchOnWindowFocus: true,  // Refresh when user returns
  });
}

// Fetch single module with documents
export function useModule(moduleId: string) {
  return useQuery({
    queryKey: moduleKeys.detail(moduleId),
    queryFn: () => modulesApi.getModule(moduleId),
    enabled: !!moduleId,  // Only fetch if moduleId provided
  });
}

// Create module mutation
export function useCreateModule() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (input: CreateModuleInput) => modulesApi.createModule(input),
    onSuccess: (newModule) => {
      // Add to cache immediately (optimistic update)
      queryClient.setQueryData<Module[]>(
        moduleKeys.lists(),
        (old) => old ? [...old, newModule] : [newModule]
      );
      // Invalidate to refetch fresh data
      queryClient.invalidateQueries({ queryKey: moduleKeys.lists() });
    },
    onError: (error) => {
      console.error('Failed to create module:', error);
      // Toast notification handled by global error boundary
    },
  });
}

// Update module mutation with optimistic update
export function useUpdateModule() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: UpdateModuleInput }) =>
      modulesApi.updateModule(id, input),
    
    onMutate: async ({ id, input }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: moduleKeys.detail(id) });
      
      // Snapshot previous value
      const previousModule = queryClient.getQueryData<Module>(
        moduleKeys.detail(id)
      );
      
      // Optimistically update
      if (previousModule) {
        queryClient.setQueryData<Module>(
          moduleKeys.detail(id),
          { ...previousModule, ...input }
        );
      }
      
      return { previousModule };
    },
    
    onError: (err, { id }, context) => {
      // Rollback on error
      if (context?.previousModule) {
        queryClient.setQueryData(
          moduleKeys.detail(id),
          context.previousModule
        );
      }
    },
    
    onSettled: (_, __, { id }) => {
      // Refetch after mutation settles
      queryClient.invalidateQueries({ queryKey: moduleKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: moduleKeys.lists() });
    },
  });
}
```

#### 3.4.3 State Management Strategy

```typescript
// stores/moduleStore.ts (Zustand for client state)
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ModuleState {
  // UI State (not server data)
  selectedModuleIds: string[];
  activeSessionId: string | null;
  sidebarCollapsed: boolean;
  
  // Actions
  selectModule: (id: string) => void;
  deselectModule: (id: string) => void;
  toggleModule: (id: string) => void;
  setActiveSession: (sessionId: string | null) => void;
  toggleSidebar: () => void;
  clearSelection: () => void;
}

export const useModuleStore = create<ModuleState>()(
  persist(
    (set) => ({
      selectedModuleIds: [],
      activeSessionId: null,
      sidebarCollapsed: false,
      
      selectModule: (id) =>
        set((state) => ({
          selectedModuleIds: state.selectedModuleIds.includes(id)
            ? state.selectedModuleIds
            : [...state.selectedModuleIds, id],
        })),
      
      deselectModule: (id) =>
        set((state) => ({
          selectedModuleIds: state.selectedModuleIds.filter((mid) => mid !== id),
        })),
      
      toggleModule: (id) =>
        set((state) => ({
          selectedModuleIds: state.selectedModuleIds.includes(id)
            ? state.selectedModuleIds.filter((mid) => mid !== id)
            : [...state.selectedModuleIds, id],
        })),
      
      setActiveSession: (sessionId) =>
        set({ activeSessionId: sessionId }),
      
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      
      clearSelection: () =>
        set({ selectedModuleIds: [], activeSessionId: null }),
    }),
    {
      name: 'aura-module-state',
      partialize: (state) => ({
        // Only persist these fields
        selectedModuleIds: state.selectedModuleIds,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
);
```

---

## 4. Data Models & Neo4j Schema

### 4.1 Node Schemas

#### 4.1.1 Module Node

```cypher
-- Module node stores metadata for a study module
(:Module {
  id: String!,                    -- UUID, e.g., "mod_abc123"
  name: String!,                  -- Display name, e.g., "Machine Learning 101"
  description: String,            -- Optional description
  color: String,                  -- Hex color for UI, e.g., "#4A90D9"
  icon: String,                   -- Icon name, e.g., "brain"
  created_at: DateTime!,          -- Creation timestamp
  updated_at: DateTime!,          -- Last modification
  user_id: String!,               -- Owner user ID
  is_archived: Boolean,           -- Soft delete flag
  settings: String                -- JSON string for module-specific settings
})

-- Constraints
CREATE CONSTRAINT module_id_unique IF NOT EXISTS
FOR (m:Module) REQUIRE m.id IS UNIQUE

CREATE INDEX module_user_idx IF NOT EXISTS
FOR (m:Module) ON (m.user_id)
```

#### 4.1.2 Extended Document Node

```cypher
-- Document node with module association
(:Document {
  id: String!,                    -- UUID
  title: String!,                 -- Document title
  original_filename: String!,     -- Original upload filename
  file_type: String!,             -- "pdf", "docx", "txt"
  file_path: String!,             -- Storage path
  content: String,                -- Full text content
  year: Integer,                  -- Publication year
  authors: [String],              -- Author names
  url: String,                    -- Source URL if applicable
  upload_date: DateTime!,         -- When uploaded
  format: String,                 -- Document format details
  
  -- NEW: Module association
  module_id: String,              -- FK to Module.id (nullable for unassigned)
  processing_status: String,      -- "pending", "processing", "completed", "failed"
  processing_error: String,       -- Error message if failed
  chunk_count: Integer,           -- Number of chunks generated
  entity_count: Integer           -- Number of entities extracted
})

-- Compound index for module-scoped queries
CREATE INDEX doc_module_idx IF NOT EXISTS
FOR (d:Document) ON (d.module_id, d.upload_date)
```

#### 4.1.3 Extended Chunk Node

```cypher
-- Chunk node with module inheritance
(:Chunk {
  id: String!,                    -- UUID
  text: String!,                  -- Chunk text content
  embedding: [Float]!,            -- 768-dim embedding vector
  document_id: String!,           -- FK to Document.id
  chunk_index: Integer!,          -- Position in document
  start_char: Integer,            -- Character offset start
  end_char: Integer,              -- Character offset end
  token_count: Integer,           -- Approximate token count
  
  -- NEW: Module propagation (denormalized for query performance)
  module_id: String               -- Inherited from parent Document
})

-- Vector index for module-filtered semantic search
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

-- Compound index for module filtering
CREATE INDEX chunk_module_idx IF NOT EXISTS
FOR (c:Chunk) ON (c.module_id, c.document_id)
```

#### 4.1.4 Study Session Node

```cypher
-- StudySession node for persistent chat sessions
(:StudySession {
  id: String!,                    -- UUID, e.g., "sess_abc123"
  title: String!,                 -- Session title (auto or user-defined)
  module_ids: [String]!,          -- Array of module IDs in scope
  user_id: String!,               -- Session owner
  created_at: DateTime!,          -- Session start time
  updated_at: DateTime!,          -- Last activity
  is_active: Boolean!,            -- Whether session is active
  message_count: Integer,         -- Number of messages
  settings: String                -- JSON: model preferences, mode, etc.
})

CREATE CONSTRAINT session_id_unique IF NOT EXISTS
FOR (s:StudySession) REQUIRE s.id IS UNIQUE

CREATE INDEX session_user_idx IF NOT EXISTS
FOR (s:StudySession) ON (s.user_id, s.is_active)
```

#### 4.1.5 Message Node

```cypher
-- Message node for session history
(:Message {
  id: String!,                    -- UUID
  session_id: String!,            -- FK to StudySession.id
  role: String!,                  -- "user" or "assistant"
  content: String!,               -- Message text
  created_at: DateTime!,          -- Timestamp
  
  -- Response metadata (for assistant messages)
  model_used: String,             -- Which LLM model
  sources: [String],              -- Document IDs cited
  thinking_content: String,       -- Thinking/reasoning (if enabled)
  token_count: Integer            -- Response token count
})

CREATE INDEX message_session_idx IF NOT EXISTS
FOR (m:Message) ON (m.session_id, m.created_at)
```

### 4.2 Relationship Schemas

```cypher
-- Module contains Document
(:Module)-[:CONTAINS_DOCUMENT {
  assigned_at: DateTime!,
  assigned_by: String
}]->(:Document)

-- Document has Chunk
(:Document)-[:HAS_CHUNK {
  chunk_index: Integer!
}]->(:Chunk)

-- Chunk contains Entity (with context)
(:Chunk)-[:CONTAINS_ENTITY {
  relevance_score: Float,         -- 0.0-1.0 how relevant entity is
  mention_count: Integer,         -- Times mentioned in chunk
  context_snippet: String         -- Surrounding text
}]->(:Entity)

-- Entity relationships (cross-module possible)
(:Entity)-[:RELATES_TO {
  relationship_type: String!,     -- "defines", "depends_on", "contradicts", etc.
  strength: Float,                -- 0.0-1.0 relationship strength
  source_module_id: String,       -- Where relationship was discovered
  evidence: String                -- Supporting text snippet
}]->(:Entity)

-- Module to Entity (for module-level concepts)
(:Module)-[:HAS_CORE_CONCEPT {
  importance: Float               -- How central to module
}]->(:Entity)

-- Study Session contains Messages
(:StudySession)-[:HAS_MESSAGE {
  message_order: Integer!
}]->(:Message)

-- Session references Modules
(:StudySession)-[:STUDIES {
  added_at: DateTime
}]->(:Module)
```

### 4.3 Pydantic Schemas (Python)

```python
# server/schemas/module.py
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ModuleCreate(BaseModel):
    """Schema for creating a new module."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    color: Optional[str] = Field("#4A90D9", regex=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field("folder", max_length=50)
    
    @validator('name')
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Module name cannot be empty')
        return v.strip()

class ModuleUpdate(BaseModel):
    """Schema for updating a module."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    color: Optional[str] = Field(None, regex=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)
    is_archived: Optional[bool] = None

class ModuleResponse(BaseModel):
    """Schema for module response."""
    id: str
    name: str
    description: Optional[str]
    color: str
    icon: str
    created_at: datetime
    updated_at: datetime
    document_count: int = 0
    entity_count: int = 0
    is_archived: bool = False
    
    class Config:
        from_attributes = True

class ModuleListResponse(BaseModel):
    """Schema for listing modules."""
    modules: List[ModuleResponse]
    total: int

class ModuleStatsResponse(BaseModel):
    """Schema for module statistics."""
    module_id: str
    document_count: int
    chunk_count: int
    entity_count: int
    concept_count: int
    topic_count: int
    relationship_count: int
    total_tokens: int
    last_updated: datetime

# server/schemas/study_session.py
class StudySessionCreate(BaseModel):
    """Schema for creating a study session."""
    title: Optional[str] = Field(None, max_length=200)
    module_ids: List[str] = Field(..., min_items=1)
    settings: Optional[dict] = None

class StudySessionResponse(BaseModel):
    """Schema for study session response."""
    id: str
    title: str
    module_ids: List[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    message_count: int
    modules: List[ModuleResponse]  # Populated modules
    
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    """Schema for creating a message."""
    content: str = Field(..., min_length=1, max_length=10000)
    
class MessageResponse(BaseModel):
    """Schema for message response."""
    id: str
    role: str
    content: str
    created_at: datetime
    model_used: Optional[str]
    sources: Optional[List[str]]
```

---

## 5. Phase 1: Database Schema Extension

**Duration:** Week 1-2 (10 days)  
**Priority:** P0 (Critical Path)  
**Dependencies:** None

### 5.1 Objectives

1. Add Module node type and constraints to Neo4j
2. Extend existing Document and Chunk nodes with `module_id`
3. Create migration strategy for existing data
4. Set up compound indices for module-scoped queries
5. Create StudySession and Message node types

### 5.2 Detailed Tasks

#### Task 5.2.1: Create Schema Migration Script

**File:** `backend/migrations/001_add_module_schema.py`

```python
"""
Migration 001: Add Module Schema
================================
Adds Module nodes, extends Document/Chunk with module_id,
creates StudySession nodes for persistent chat.

Run with: python -m backend.migrations.001_add_module_schema
"""
import logging
from datetime import datetime
from backend.graph_manager import GraphManager
from backend.utils.logging_config import setup_logging

logger = setup_logging("migration_001")

class ModuleSchemaMigration:
    """Migration to add module-related schema to Neo4j."""
    
    VERSION = "001"
    DESCRIPTION = "Add Module, StudySession nodes and module_id to existing nodes"
    
    def __init__(self, graph_manager: GraphManager = None):
        self.gm = graph_manager or GraphManager()
        self.migration_log = []
    
    def run(self, dry_run: bool = False) -> dict:
        """
        Execute the migration.
        
        Args:
            dry_run: If True, log changes without executing
            
        Returns:
            Migration result summary
        """
        logger.info(f"Starting migration {self.VERSION}: {self.DESCRIPTION}")
        logger.info(f"Dry run: {dry_run}")
        
        results = {
            'version': self.VERSION,
            'dry_run': dry_run,
            'started_at': datetime.utcnow().isoformat(),
            'steps': []
        }
        
        try:
            # Step 1: Create Module constraints and indices
            results['steps'].append(
                self._create_module_schema(dry_run)
            )
            
            # Step 2: Create StudySession schema
            results['steps'].append(
                self._create_session_schema(dry_run)
            )
            
            # Step 3: Add module_id property to existing Documents
            results['steps'].append(
                self._extend_document_schema(dry_run)
            )
            
            # Step 4: Add module_id property to existing Chunks
            results['steps'].append(
                self._extend_chunk_schema(dry_run)
            )
            
            # Step 5: Create compound indices for performance
            results['steps'].append(
                self._create_compound_indices(dry_run)
            )
            
            # Step 6: Create default "Unassigned" module for orphan docs
            results['steps'].append(
                self._create_default_module(dry_run)
            )
            
            results['success'] = True
            results['completed_at'] = datetime.utcnow().isoformat()
            
        except Exception as e:
            logger.exception(f"Migration failed: {e}")
            results['success'] = False
            results['error'] = str(e)
        
        return results
    
    def _create_module_schema(self, dry_run: bool) -> dict:
        """Create Module node constraints and indices."""
        step = {'name': 'create_module_schema', 'queries': []}
        
        queries = [
            # Unique constraint on module ID
            """
            CREATE CONSTRAINT module_id_unique IF NOT EXISTS
            FOR (m:Module) REQUIRE m.id IS UNIQUE
            """,
            # Index on user_id for listing user's modules
            """
            CREATE INDEX module_user_idx IF NOT EXISTS
            FOR (m:Module) ON (m.user_id)
            """,
            # Index on name for searching
            """
            CREATE INDEX module_name_idx IF NOT EXISTS
            FOR (m:Module) ON (m.name)
            """,
        ]
        
        for query in queries:
            step['queries'].append(query.strip())
            if not dry_run:
                try:
                    self.gm.execute_query(query)
                    logger.info(f"Executed: {query[:50]}...")
                except Exception as e:
                    logger.warning(f"Query may already exist: {e}")
        
        step['success'] = True
        return step
    
    def _create_session_schema(self, dry_run: bool) -> dict:
        """Create StudySession and Message node schemas."""
        step = {'name': 'create_session_schema', 'queries': []}
        
        queries = [
            # StudySession constraints
            """
            CREATE CONSTRAINT session_id_unique IF NOT EXISTS
            FOR (s:StudySession) REQUIRE s.id IS UNIQUE
            """,
            # Session user index
            """
            CREATE INDEX session_user_active_idx IF NOT EXISTS
            FOR (s:StudySession) ON (s.user_id, s.is_active)
            """,
            # Message constraints
            """
            CREATE CONSTRAINT message_id_unique IF NOT EXISTS
            FOR (m:Message) REQUIRE m.id IS UNIQUE
            """,
            # Message session index
            """
            CREATE INDEX message_session_idx IF NOT EXISTS
            FOR (m:Message) ON (m.session_id, m.created_at)
            """,
        ]
        
        for query in queries:
            step['queries'].append(query.strip())
            if not dry_run:
                try:
                    self.gm.execute_query(query)
                    logger.info(f"Executed: {query[:50]}...")
                except Exception as e:
                    logger.warning(f"Query may already exist: {e}")
        
        step['success'] = True
        return step
    
    def _extend_document_schema(self, dry_run: bool) -> dict:
        """Add module_id and processing_status to Document nodes."""
        step = {'name': 'extend_document_schema', 'queries': []}
        
        # Add properties with default values
        query = """
        MATCH (d:Document)
        WHERE d.module_id IS NULL
        SET d.module_id = 'unassigned',
            d.processing_status = COALESCE(d.processing_status, 'completed'),
            d.chunk_count = COALESCE(d.chunk_count, 0),
            d.entity_count = COALESCE(d.entity_count, 0)
        RETURN count(d) as updated_count
        """
        
        step['queries'].append(query.strip())
        
        if not dry_run:
            result = self.gm.execute_query(query)
            updated = result[0]['updated_count'] if result else 0
            logger.info(f"Updated {updated} Document nodes with module_id")
            step['updated_count'] = updated
        
        step['success'] = True
        return step
    
    def _extend_chunk_schema(self, dry_run: bool) -> dict:
        """Add module_id to Chunk nodes (inherited from Document)."""
        step = {'name': 'extend_chunk_schema', 'queries': []}
        
        # Propagate module_id from Document to Chunk
        query = """
        MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)
        WHERE c.module_id IS NULL
        SET c.module_id = d.module_id
        RETURN count(c) as updated_count
        """
        
        step['queries'].append(query.strip())
        
        if not dry_run:
            result = self.gm.execute_query(query)
            updated = result[0]['updated_count'] if result else 0
            logger.info(f"Updated {updated} Chunk nodes with module_id")
            step['updated_count'] = updated
        
        step['success'] = True
        return step
    
    def _create_compound_indices(self, dry_run: bool) -> dict:
        """Create compound indices for module-filtered queries."""
        step = {'name': 'create_compound_indices', 'queries': []}
        
        queries = [
            # Document by module and date
            """
            CREATE INDEX doc_module_date_idx IF NOT EXISTS
            FOR (d:Document) ON (d.module_id, d.upload_date)
            """,
            # Chunk by module and document
            """
            CREATE INDEX chunk_module_doc_idx IF NOT EXISTS
            FOR (c:Chunk) ON (c.module_id, c.document_id)
            """,
            # Entity by module (for entities that belong to specific modules)
            """
            CREATE INDEX entity_module_idx IF NOT EXISTS
            FOR (e:Entity) ON (e.module_id)
            """,
        ]
        
        for query in queries:
            step['queries'].append(query.strip())
            if not dry_run:
                try:
                    self.gm.execute_query(query)
                    logger.info(f"Created index: {query[:50]}...")
                except Exception as e:
                    logger.warning(f"Index may already exist: {e}")
        
        step['success'] = True
        return step
    
    def _create_default_module(self, dry_run: bool) -> dict:
        """Create default 'Unassigned' module for orphan documents."""
        step = {'name': 'create_default_module', 'queries': []}
        
        query = """
        MERGE (m:Module {id: 'unassigned'})
        ON CREATE SET
            m.name = 'Unassigned Documents',
            m.description = 'Documents not yet assigned to a module',
            m.color = '#808080',
            m.icon = 'folder-open',
            m.created_at = datetime(),
            m.updated_at = datetime(),
            m.user_id = 'system',
            m.is_archived = false,
            m.is_system = true
        RETURN m.id as module_id
        """
        
        step['queries'].append(query.strip())
        
        if not dry_run:
            result = self.gm.execute_query(query)
            logger.info(f"Created/verified default module: unassigned")
            step['module_id'] = 'unassigned'
        
        step['success'] = True
        return step
    
    def rollback(self) -> dict:
        """
        Rollback the migration (remove added schema elements).
        WARNING: This will lose data. Use only in development.
        """
        logger.warning("Rolling back migration 001 - this will remove module data!")
        
        queries = [
            # Remove module_id from Chunks
            "MATCH (c:Chunk) REMOVE c.module_id",
            # Remove module_id from Documents  
            "MATCH (d:Document) REMOVE d.module_id, d.processing_status",
            # Delete all StudySessions and Messages
            "MATCH (s:StudySession) DETACH DELETE s",
            "MATCH (m:Message) DETACH DELETE m",
            # Delete all Modules
            "MATCH (m:Module) DETACH DELETE m",
            # Drop indices (constraints must be dropped manually)
            "DROP INDEX module_user_idx IF EXISTS",
            "DROP INDEX module_name_idx IF EXISTS",
            "DROP INDEX session_user_active_idx IF EXISTS",
            "DROP INDEX message_session_idx IF EXISTS",
            "DROP INDEX doc_module_date_idx IF EXISTS",
            "DROP INDEX chunk_module_doc_idx IF EXISTS",
        ]
        
        results = []
        for query in queries:
            try:
                self.gm.execute_query(query)
                results.append({'query': query[:50], 'success': True})
            except Exception as e:
                results.append({'query': query[:50], 'success': False, 'error': str(e)})
        
        return {'rollback': True, 'steps': results}


def main():
    """Run the migration from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run module schema migration')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Show what would be done without executing')
    parser.add_argument('--rollback', action='store_true',
                        help='Rollback the migration (WARNING: loses data)')
    
    args = parser.parse_args()
    
    migration = ModuleSchemaMigration()
    
    if args.rollback:
        result = migration.rollback()
    else:
        result = migration.run(dry_run=args.dry_run)
    
    import json
    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
```

#### Task 5.2.2: Update GraphManager with Module Support

**File:** `backend/graph_manager.py` (modifications)

```python
# Add to existing GraphManager class

# === MODULE OPERATIONS ===

def create_module_node(self, module_data: Dict[str, Any]) -> str:
    """
    Create a new module node.
    
    Args:
        module_data: Dict containing id, name, description, color, icon, user_id
        
    Returns:
        The created module ID
    """
    query = """
    CREATE (m:Module {
        id: $id,
        name: $name,
        description: $description,
        color: $color,
        icon: $icon,
        created_at: datetime(),
        updated_at: datetime(),
        user_id: $user_id,
        is_archived: false
    })
    RETURN m.id as id
    """
    
    # Set defaults
    module_data.setdefault('description', '')
    module_data.setdefault('color', '#4A90D9')
    module_data.setdefault('icon', 'folder')
    
    result = self.execute_query(query, module_data)
    logger.info(f"Created module: {module_data['id']}")
    return result[0]['id'] if result else None

def get_module(self, module_id: str) -> Optional[Dict[str, Any]]:
    """Get a module by ID with document count."""
    query = """
    MATCH (m:Module {id: $module_id})
    OPTIONAL MATCH (m)-[:CONTAINS_DOCUMENT]->(d:Document)
    WITH m, count(d) as doc_count
    OPTIONAL MATCH (d)-[:HAS_CHUNK]->(:Chunk)-[:CONTAINS_ENTITY]->(e)
    RETURN m {
        .*,
        document_count: doc_count,
        entity_count: count(DISTINCT e)
    } as module
    """
    result = self.execute_query(query, {'module_id': module_id})
    return result[0]['module'] if result else None

def list_modules(
    self, 
    user_id: str, 
    include_archived: bool = False,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    List all modules for a user.
    
    Args:
        user_id: The user's ID
        include_archived: Whether to include archived modules
        limit: Maximum modules to return
        offset: Pagination offset
        
    Returns:
        List of module dicts with document counts
    """
    archive_filter = "" if include_archived else "AND m.is_archived = false"
    
    query = f"""
    MATCH (m:Module {{user_id: $user_id}})
    WHERE m.is_system IS NULL OR m.is_system = false
    {archive_filter}
    OPTIONAL MATCH (m)-[:CONTAINS_DOCUMENT]->(d:Document)
    WITH m, count(d) as doc_count
    RETURN m {{
        .*,
        document_count: doc_count
    }} as module
    ORDER BY m.updated_at DESC
    SKIP $offset
    LIMIT $limit
    """
    
    result = self.execute_query(query, {
        'user_id': user_id,
        'offset': offset,
        'limit': limit
    })
    return [r['module'] for r in result]

def update_module(self, module_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update module properties.
    
    Args:
        module_id: Module to update
        updates: Dict of properties to update (name, description, color, icon, is_archived)
        
    Returns:
        True if updated, False if not found
    """
    # Build dynamic SET clause
    set_parts = ["m.updated_at = datetime()"]
    params = {'module_id': module_id}
    
    allowed_fields = ['name', 'description', 'color', 'icon', 'is_archived']
    for field in allowed_fields:
        if field in updates:
            set_parts.append(f"m.{field} = ${field}")
            params[field] = updates[field]
    
    set_clause = ", ".join(set_parts)
    
    query = f"""
    MATCH (m:Module {{id: $module_id}})
    SET {set_clause}
    RETURN m.id as id
    """
    
    result = self.execute_query(query, params)
    return len(result) > 0

def delete_module(self, module_id: str, reassign_to: str = 'unassigned') -> dict:
    """
    Delete a module and reassign its documents.
    
    Args:
        module_id: Module to delete
        reassign_to: Module ID to reassign orphaned documents to
        
    Returns:
        Dict with deletion stats
    """
    # First, reassign documents
    reassign_query = """
    MATCH (m:Module {id: $module_id})-[:CONTAINS_DOCUMENT]->(d:Document)
    MATCH (target:Module {id: $reassign_to})
    SET d.module_id = $reassign_to
    WITH d, target
    MERGE (target)-[:CONTAINS_DOCUMENT]->(d)
    RETURN count(d) as reassigned
    """
    
    reassign_result = self.execute_query(reassign_query, {
        'module_id': module_id,
        'reassign_to': reassign_to
    })
    
    # Update chunks to new module
    update_chunks_query = """
    MATCH (c:Chunk {module_id: $module_id})
    SET c.module_id = $reassign_to
    RETURN count(c) as updated
    """
    
    self.execute_query(update_chunks_query, {
        'module_id': module_id,
        'reassign_to': reassign_to
    })
    
    # Delete the module and its relationships
    delete_query = """
    MATCH (m:Module {id: $module_id})
    DETACH DELETE m
    RETURN count(m) as deleted
    """
    
    delete_result = self.execute_query(delete_query, {'module_id': module_id})
    
    return {
        'module_id': module_id,
        'documents_reassigned': reassign_result[0]['reassigned'] if reassign_result else 0,
        'deleted': delete_result[0]['deleted'] > 0 if delete_result else False
    }

def assign_document_to_module(
    self, 
    document_id: str, 
    module_id: str,
    user_id: str = None
) -> bool:
    """
    Assign a document to a module.
    Updates the document's module_id and creates CONTAINS_DOCUMENT relationship.
    Also updates all associated chunks.
    
    Args:
        document_id: Document to assign
        module_id: Target module
        user_id: User performing the assignment (for audit)
        
    Returns:
        True if successful
    """
    query = """
    MATCH (d:Document {id: $document_id})
    MATCH (m:Module {id: $module_id})
    
    // Remove from old module if exists
    OPTIONAL MATCH (old:Module)-[r:CONTAINS_DOCUMENT]->(d)
    DELETE r
    
    // Set new module_id on document
    SET d.module_id = $module_id
    
    // Create new relationship
    MERGE (m)-[:CONTAINS_DOCUMENT {
        assigned_at: datetime(),
        assigned_by: $user_id
    }]->(d)
    
    // Update all chunks
    WITH d
    MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
    SET c.module_id = $module_id
    
    RETURN d.id as id, count(c) as chunks_updated
    """
    
    result = self.execute_query(query, {
        'document_id': document_id,
        'module_id': module_id,
        'user_id': user_id or 'system'
    })
    
    if result:
        logger.info(f"Assigned document {document_id} to module {module_id}, "
                   f"updated {result[0]['chunks_updated']} chunks")
        return True
    return False

def get_module_documents(
    self, 
    module_id: str,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get all documents in a module."""
    query = """
    MATCH (m:Module {id: $module_id})-[:CONTAINS_DOCUMENT]->(d:Document)
    RETURN d {
        .*,
        chunk_count: size((d)-[:HAS_CHUNK]->())
    } as document
    ORDER BY d.upload_date DESC
    SKIP $offset
    LIMIT $limit
    """
    
    result = self.execute_query(query, {
        'module_id': module_id,
        'offset': offset,
        'limit': limit
    })
    return [r['document'] for r in result]

def get_module_stats(self, module_id: str) -> Dict[str, Any]:
    """Get comprehensive statistics for a module."""
    query = """
    MATCH (m:Module {id: $module_id})
    OPTIONAL MATCH (m)-[:CONTAINS_DOCUMENT]->(d:Document)
    OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
    OPTIONAL MATCH (c)-[:CONTAINS_ENTITY]->(e)
    WITH m, 
         count(DISTINCT d) as doc_count,
         count(DISTINCT c) as chunk_count,
         count(DISTINCT e) as entity_count,
         collect(DISTINCT labels(e)) as entity_labels
    
    // Count by entity type
    OPTIONAL MATCH (m)-[:CONTAINS_DOCUMENT]->(d)-[:HAS_CHUNK]->()-[:CONTAINS_ENTITY]->(t:Topic)
    WITH m, doc_count, chunk_count, entity_count, count(DISTINCT t) as topic_count
    
    OPTIONAL MATCH (m)-[:CONTAINS_DOCUMENT]->(d)-[:HAS_CHUNK]->()-[:CONTAINS_ENTITY]->(c:Concept)
    WITH m, doc_count, chunk_count, entity_count, topic_count, count(DISTINCT c) as concept_count
    
    RETURN {
        module_id: m.id,
        module_name: m.name,
        document_count: doc_count,
        chunk_count: chunk_count,
        entity_count: entity_count,
        topic_count: topic_count,
        concept_count: concept_count,
        last_updated: m.updated_at
    } as stats
    """
    
    result = self.execute_query(query, {'module_id': module_id})
    return result[0]['stats'] if result else None
```

### 5.3 Verification Checklist

| Item | Verification Method | Expected Result |
|------|-------------------|-----------------|
| Module constraint exists | `SHOW CONSTRAINTS` | `module_id_unique` listed |
| Session constraint exists | `SHOW CONSTRAINTS` | `session_id_unique` listed |
| Vector index intact | `SHOW INDEXES` | `chunk_vector_index` with 768 dims |
| Compound indices created | `SHOW INDEXES` | `doc_module_date_idx`, `chunk_module_doc_idx` |
| Existing docs have module_id | `MATCH (d:Document) WHERE d.module_id IS NULL RETURN count(d)` | 0 |
| Existing chunks have module_id | `MATCH (c:Chunk) WHERE c.module_id IS NULL RETURN count(c)` | 0 |
| Default module exists | `MATCH (m:Module {id: 'unassigned'}) RETURN m` | 1 result |

---

## 6. Phase 2: Backend Module Management

**Duration:** Week 2-3 (10 days)  
**Priority:** P0 (Critical Path)  
**Dependencies:** Phase 1 complete

### 6.1 Objectives

1. Create `ModuleManager` service class with full CRUD operations
2. Implement `ModuleCache` for Redis caching
3. Create FastAPI routers for module endpoints
4. Add validation and error handling
5. Implement batch document assignment

### 6.2 Detailed Implementation

#### Task 6.2.1: ModuleManager Service

**File:** `backend/module_manager.py`

```python
"""
AURA Module Manager
===================

Service class for managing study modules. Handles CRUD operations,
document assignments, and module statistics with caching.

Usage:
    from backend.module_manager import ModuleManager
    from backend.graph_manager import GraphManager
    from backend.cache.module_cache import ModuleCache
    
    gm = GraphManager()
    cache = ModuleCache()
    mm = ModuleManager(graph_manager=gm, cache=cache)
    
    # Create a module
    module = mm.create_module(
        name="Machine Learning",
        description="ML fundamentals",
        user_id="user_123"
    )
    
    # Assign documents
    mm.assign_documents(module.id, ["doc_1", "doc_2"], user_id="user_123")
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from backend.graph_manager import GraphManager
from backend.cache.module_cache import ModuleCache
from backend.utils.logging_config import setup_logging

logger = setup_logging("module_manager")


@dataclass
class Module:
    """Domain model for a study module."""
    id: str
    name: str
    description: str
    color: str
    icon: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    is_archived: bool = False
    document_count: int = 0
    entity_count: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Module':
        """Create Module from dictionary (Neo4j result)."""
        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            color=data.get('color', '#4A90D9'),
            icon=data.get('icon', 'folder'),
            user_id=data['user_id'],
            created_at=data.get('created_at', datetime.utcnow()),
            updated_at=data.get('updated_at', datetime.utcnow()),
            is_archived=data.get('is_archived', False),
            document_count=data.get('document_count', 0),
            entity_count=data.get('entity_count', 0)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            'is_archived': self.is_archived,
            'document_count': self.document_count,
            'entity_count': self.entity_count
        }


class ModuleManagerError(Exception):
    """Base exception for ModuleManager errors."""
    pass


class ModuleNotFoundError(ModuleManagerError):
    """Raised when a module is not found."""
    pass


class ModuleValidationError(ModuleManagerError):
    """Raised when module validation fails."""
    pass


class DuplicateModuleError(ModuleManagerError):
    """Raised when trying to create a duplicate module."""
    pass


class ModuleManager:
    """
    Service for managing study modules.
    
    Provides CRUD operations, document assignment, and statistics
    with Redis caching for frequently accessed data.
    """
    
    # Cache TTL settings (seconds)
    MODULE_LIST_TTL = 300      # 5 minutes
    MODULE_DETAIL_TTL = 600    # 10 minutes
    MODULE_STATS_TTL = 120     # 2 minutes (stats change more frequently)
    
    def __init__(
        self, 
        graph_manager: GraphManager,
        cache: Optional[ModuleCache] = None
    ):
        """
        Initialize ModuleManager.
        
        Args:
            graph_manager: Neo4j graph manager instance
            cache: Optional Redis cache instance
        """
        self.gm = graph_manager
        self.cache = cache
        self._use_cache = cache is not None
    
    # === CRUD OPERATIONS ===
    
    def create_module(
        self,
        name: str,
        user_id: str,
        description: str = "",
        color: str = "#4A90D9",
        icon: str = "folder"
    ) -> Module:
        """
        Create a new study module.
        
        Args:
            name: Module display name (1-200 chars)
            user_id: Owner's user ID
            description: Optional description (max 2000 chars)
            color: Hex color code (e.g., "#4A90D9")
            icon: Icon name (e.g., "folder", "brain", "book")
            
        Returns:
            Created Module object
            
        Raises:
            ModuleValidationError: If validation fails
            DuplicateModuleError: If module name exists for user
        """
        # Validation
        name = name.strip()
        if not name:
            raise ModuleValidationError("Module name cannot be empty")
        if len(name) > 200:
            raise ModuleValidationError("Module name too long (max 200 chars)")
        if len(description) > 2000:
            raise ModuleValidationError("Description too long (max 2000 chars)")
        
        # Check for duplicate name
        if self._module_name_exists(name, user_id):
            raise DuplicateModuleError(f"Module '{name}' already exists")
        
        # Generate ID
        module_id = f"mod_{uuid.uuid4().hex[:12]}"
        
        # Create in Neo4j
        module_data = {
            'id': module_id,
            'name': name,
            'description': description,
            'color': color,
            'icon': icon,
            'user_id': user_id
        }
        
        created_id = self.gm.create_module_node(module_data)
        
        if not created_id:
            raise ModuleManagerError("Failed to create module in database")
        
        # Invalidate user's module list cache
        self._invalidate_list_cache(user_id)
        
        logger.info(f"Created module: {module_id} ({name}) for user {user_id}")
        
        # Fetch and return the created module
        return self.get_module(module_id)
    
    def get_module(self, module_id: str) -> Module:
        """
        Get a module by ID.
        
        Args:
            module_id: Module ID
            
        Returns:
            Module object
            
        Raises:
            ModuleNotFoundError: If module not found
        """
        # Check cache
        if self._use_cache:
            cached = self.cache.get_module(module_id)
            if cached:
                return Module.from_dict(cached)
        
        # Fetch from Neo4j
        data = self.gm.get_module(module_id)
        
        if not data:
            raise ModuleNotFoundError(f"Module not found: {module_id}")
        
        module = Module.from_dict(data)
        
        # Cache it
        if self._use_cache:
            self.cache.set_module(module_id, module.to_dict(), ttl=self.MODULE_DETAIL_TTL)
        
        return module
    
    def list_modules(
        self,
        user_id: str,
        include_archived: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Module]:
        """
        List all modules for a user.
        
        Args:
            user_id: User's ID
            include_archived: Whether to include archived modules
            limit: Max results (default 100)
            offset: Pagination offset
            
        Returns:
            List of Module objects
        """
        # Build cache key
        cache_key = f"list:{user_id}:arch={include_archived}:l={limit}:o={offset}"
        
        # Check cache
        if self._use_cache:
            cached = self.cache.get_module_list(cache_key)
            if cached:
                return [Module.from_dict(m) for m in cached]
        
        # Fetch from Neo4j
        data = self.gm.list_modules(
            user_id=user_id,
            include_archived=include_archived,
            limit=limit,
            offset=offset
        )
        
        modules = [Module.from_dict(m) for m in data]
        
        # Cache it
        if self._use_cache:
            self.cache.set_module_list(
                cache_key, 
                [m.to_dict() for m in modules],
                ttl=self.MODULE_LIST_TTL
            )
        
        return modules
    
    def update_module(
        self,
        module_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        is_archived: Optional[bool] = None
    ) -> Module:
        """
        Update a module's properties.
        
        Args:
            module_id: Module to update
            name: New name (optional)
            description: New description (optional)
            color: New color (optional)
            icon: New icon (optional)
            is_archived: Archive status (optional)
            
        Returns:
            Updated Module object
            
        Raises:
            ModuleNotFoundError: If module not found
            ModuleValidationError: If validation fails
        """
        # Verify module exists
        existing = self.get_module(module_id)
        
        # Build updates dict
        updates = {}
        
        if name is not None:
            name = name.strip()
            if not name:
                raise ModuleValidationError("Module name cannot be empty")
            if len(name) > 200:
                raise ModuleValidationError("Module name too long")
            # Check for duplicate (excluding self)
            if name != existing.name and self._module_name_exists(name, existing.user_id):
                raise DuplicateModuleError(f"Module '{name}' already exists")
            updates['name'] = name
        
        if description is not None:
            if len(description) > 2000:
                raise ModuleValidationError("Description too long")
            updates['description'] = description
        
        if color is not None:
            updates['color'] = color
        
        if icon is not None:
            updates['icon'] = icon
        
        if is_archived is not None:
            updates['is_archived'] = is_archived
        
        if not updates:
            return existing  # Nothing to update
        
        # Update in Neo4j
        success = self.gm.update_module(module_id, updates)
        
        if not success:
            raise ModuleManagerError("Failed to update module")
        
        # Invalidate caches
        self._invalidate_module_cache(module_id)
        self._invalidate_list_cache(existing.user_id)
        
        logger.info(f"Updated module {module_id}: {list(updates.keys())}")
        
        return self.get_module(module_id)
    
    def delete_module(
        self,
        module_id: str,
        reassign_to: str = 'unassigned'
    ) -> Dict[str, Any]:
        """
        Delete a module and reassign its documents.
        
        Args:
            module_id: Module to delete
            reassign_to: Module ID for orphaned documents (default: 'unassigned')
            
        Returns:
            Deletion result with stats
            
        Raises:
            ModuleNotFoundError: If module not found
            ModuleValidationError: If trying to delete system module
        """
        # Verify module exists
        module = self.get_module(module_id)
        
        # Prevent deletion of system modules
        if module_id == 'unassigned':
            raise ModuleValidationError("Cannot delete system module")
        
        # Delete in Neo4j
        result = self.gm.delete_module(module_id, reassign_to)
        
        # Invalidate caches
        self._invalidate_module_cache(module_id)
        self._invalidate_module_cache(reassign_to)
        self._invalidate_list_cache(module.user_id)
        
        logger.info(f"Deleted module {module_id}, reassigned {result['documents_reassigned']} docs")
        
        return result
    
    # === DOCUMENT ASSIGNMENT ===
    
    def assign_document(
        self,
        module_id: str,
        document_id: str,
        user_id: str = None
    ) -> bool:
        """
        Assign a single document to a module.
        
        Args:
            module_id: Target module
            document_id: Document to assign
            user_id: User performing assignment (for audit)
            
        Returns:
            True if successful
        """
        # Verify module exists
        self.get_module(module_id)
        
        success = self.gm.assign_document_to_module(
            document_id=document_id,
            module_id=module_id,
            user_id=user_id
        )
        
        if success:
            # Invalidate caches
            self._invalidate_module_cache(module_id)
            self._invalidate_stats_cache(module_id)
        
        return success
    
    def assign_documents_batch(
        self,
        module_id: str,
        document_ids: List[str],
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Assign multiple documents to a module in a single transaction.
        
        Args:
            module_id: Target module
            document_ids: List of document IDs
            user_id: User performing assignment
            
        Returns:
            Result with success count and any failures
        """
        # Verify module exists
        self.get_module(module_id)
        
        results = {
            'total': len(document_ids),
            'successful': 0,
            'failed': 0,
            'failures': []
        }
        
        for doc_id in document_ids:
            try:
                success = self.gm.assign_document_to_module(
                    document_id=doc_id,
                    module_id=module_id,
                    user_id=user_id
                )
                if success:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['failures'].append({
                        'document_id': doc_id,
                        'error': 'Assignment returned false'
                    })
            except Exception as e:
                results['failed'] += 1
                results['failures'].append({
                    'document_id': doc_id,
                    'error': str(e)
                })
        
        # Invalidate caches
        self._invalidate_module_cache(module_id)
        self._invalidate_stats_cache(module_id)
        
        logger.info(f"Batch assigned {results['successful']}/{results['total']} "
                   f"docs to module {module_id}")
        
        return results
    
    def remove_document(
        self,
        module_id: str,
        document_id: str,
        reassign_to: str = 'unassigned'
    ) -> bool:
        """
        Remove a document from a module.
        
        Args:
            module_id: Module to remove from
            document_id: Document to remove
            reassign_to: Module to reassign to (default: 'unassigned')
            
        Returns:
            True if successful
        """
        success = self.gm.assign_document_to_module(
            document_id=document_id,
            module_id=reassign_to
        )
        
        if success:
            self._invalidate_module_cache(module_id)
            self._invalidate_module_cache(reassign_to)
            self._invalidate_stats_cache(module_id)
        
        return success
    
    def get_module_documents(
        self,
        module_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all documents in a module.
        
        Args:
            module_id: Module ID
            limit: Max results
            offset: Pagination offset
            
        Returns:
            List of document dicts
        """
        # Verify module exists
        self.get_module(module_id)
        
        return self.gm.get_module_documents(
            module_id=module_id,
            limit=limit,
            offset=offset
        )
    
    # === STATISTICS ===
    
    def get_module_stats(self, module_id: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a module.
        
        Args:
            module_id: Module ID
            
        Returns:
            Stats dict with counts and metadata
        """
        # Check cache
        if self._use_cache:
            cached = self.cache.get_stats(module_id)
            if cached:
                return cached
        
        # Fetch from Neo4j
        stats = self.gm.get_module_stats(module_id)
        
        if not stats:
            raise ModuleNotFoundError(f"Module not found: {module_id}")
        
        # Cache it
        if self._use_cache:
            self.cache.set_stats(module_id, stats, ttl=self.MODULE_STATS_TTL)
        
        return stats
    
    def invalidate_stats_cache(self, module_id: str):
        """
        Invalidate statistics cache for a module.
        Called after document processing or assignment changes.
        """
        self._invalidate_stats_cache(module_id)
    
    # === PRIVATE HELPERS ===
    
    def _module_name_exists(self, name: str, user_id: str) -> bool:
        """Check if module name exists for user."""
        query = """
        MATCH (m:Module {name: $name, user_id: $user_id})
        WHERE m.is_archived = false OR m.is_archived IS NULL
        RETURN count(m) > 0 as exists
        """
        result = self.gm.execute_query(query, {'name': name, 'user_id': user_id})
        return result[0]['exists'] if result else False
    
    def _invalidate_module_cache(self, module_id: str):
        """Invalidate cached module data."""
        if self._use_cache:
            self.cache.delete_module(module_id)
    
    def _invalidate_list_cache(self, user_id: str):
        """Invalidate user's module list cache."""
        if self._use_cache:
            self.cache.delete_module_lists(user_id)
    
    def _invalidate_stats_cache(self, module_id: str):
        """Invalidate module statistics cache."""
        if self._use_cache:
            self.cache.delete_stats(module_id)
```

#### Task 6.2.2: Redis Cache Layer

**File:** `backend/cache/module_cache.py`

```python
"""
AURA Module Cache
=================

Redis caching layer for module data. Provides fast access to
frequently requested module lists, details, and statistics.

Cache Key Patterns:
- module:{module_id} - Single module data
- module:list:{cache_key} - Module list results
- module:stats:{module_id} - Module statistics
- module:user:{user_id}:* - Pattern for user-specific data

Usage:
    from backend.cache.module_cache import ModuleCache
    
    cache = ModuleCache()
    
    # Cache a module
    cache.set_module("mod_123", {"id": "mod_123", "name": "ML"}, ttl=300)
    
    # Get cached module
    data = cache.get_module("mod_123")
    
    # Invalidate
    cache.delete_module("mod_123")
"""
import json
import redis
from typing import Dict, Any, Optional, List
from datetime import timedelta

from backend.utils.config import config
from backend.utils.logging_config import setup_logging

logger = setup_logging("module_cache")


class ModuleCache:
    """
    Redis cache for module data.
    
    Provides caching for:
    - Individual module data
    - Module list queries
    - Module statistics
    """
    
    # Key prefixes
    MODULE_PREFIX = "module:"
    LIST_PREFIX = "module:list:"
    STATS_PREFIX = "module:stats:"
    
    # Default TTLs (seconds)
    DEFAULT_TTL = 300  # 5 minutes
    STATS_TTL = 120    # 2 minutes
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = None,
        password: str = None
    ):
        """
        Initialize Redis connection.
        
        Args:
            host: Redis host (default from config)
            port: Redis port (default from config)
            db: Redis database number
            password: Redis password if required
        """
        self.host = host or config.REDIS_HOST or 'localhost'
        self.port = port or config.REDIS_PORT or 6379
        self.db = db or config.REDIS_DB or 0
        self.password = password or config.REDIS_PASSWORD
        
        self._client: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self):
        """Establish Redis connection with retry."""
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,  # Return strings, not bytes
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self._client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}. Cache disabled.")
            self._client = None
    
    @property
    def is_available(self) -> bool:
        """Check if Redis is available."""
        if not self._client:
            return False
        try:
            self._client.ping()
            return True
        except:
            return False
    
    def close(self):
        """Close Redis connection."""
        if self._client:
            self._client.close()
            self._client = None
    
    # === MODULE CACHING ===
    
    def get_module(self, module_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached module data.
        
        Args:
            module_id: Module ID
            
        Returns:
            Module dict or None if not cached
        """
        if not self._client:
            return None
        
        try:
            key = f"{self.MODULE_PREFIX}{module_id}"
            data = self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache get failed for module {module_id}: {e}")
            return None
    
    def set_module(
        self, 
        module_id: str, 
        data: Dict[str, Any],
        ttl: int = None
    ) -> bool:
        """
        Cache module data.
        
        Args:
            module_id: Module ID
            data: Module data dict
            ttl: Time-to-live in seconds
            
        Returns:
            True if cached successfully
        """
        if not self._client:
            return False
        
        try:
            key = f"{self.MODULE_PREFIX}{module_id}"
            self._client.setex(
                key,
                ttl or self.DEFAULT_TTL,
                json.dumps(data, default=str)
            )
            return True
        except Exception as e:
            logger.warning(f"Cache set failed for module {module_id}: {e}")
            return False
    
    def delete_module(self, module_id: str) -> bool:
        """Delete cached module data."""
        if not self._client:
            return False
        
        try:
            key = f"{self.MODULE_PREFIX}{module_id}"
            self._client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete failed for module {module_id}: {e}")
            return False
    
    # === LIST CACHING ===
    
    def get_module_list(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached module list.
        
        Args:
            cache_key: Unique key for this list query
            
        Returns:
            List of module dicts or None
        """
        if not self._client:
            return None
        
        try:
            key = f"{self.LIST_PREFIX}{cache_key}"
            data = self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache get failed for list {cache_key}: {e}")
            return None
    
    def set_module_list(
        self,
        cache_key: str,
        data: List[Dict[str, Any]],
        ttl: int = None
    ) -> bool:
        """Cache module list results."""
        if not self._client:
            return False
        
        try:
            key = f"{self.LIST_PREFIX}{cache_key}"
            self._client.setex(
                key,
                ttl or self.DEFAULT_TTL,
                json.dumps(data, default=str)
            )
            return True
        except Exception as e:
            logger.warning(f"Cache set failed for list {cache_key}: {e}")
            return False
    
    def delete_module_lists(self, user_id: str) -> int:
        """
        Delete all cached lists for a user.
        
        Args:
            user_id: User ID to clear lists for
            
        Returns:
            Number of keys deleted
        """
        if not self._client:
            return 0
        
        try:
            # Find all list keys for this user
            pattern = f"{self.LIST_PREFIX}list:{user_id}:*"
            keys = list(self._client.scan_iter(match=pattern))
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete failed for user lists {user_id}: {e}")
            return 0
    
    # === STATS CACHING ===
    
    def get_stats(self, module_id: str) -> Optional[Dict[str, Any]]:
        """Get cached module statistics."""
        if not self._client:
            return None
        
        try:
            key = f"{self.STATS_PREFIX}{module_id}"
            data = self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache get failed for stats {module_id}: {e}")
            return None
    
    def set_stats(
        self,
        module_id: str,
        data: Dict[str, Any],
        ttl: int = None
    ) -> bool:
        """Cache module statistics."""
        if not self._client:
            return False
        
        try:
            key = f"{self.STATS_PREFIX}{module_id}"
            self._client.setex(
                key,
                ttl or self.STATS_TTL,
                json.dumps(data, default=str)
            )
            return True
        except Exception as e:
            logger.warning(f"Cache set failed for stats {module_id}: {e}")
            return False
    
    def delete_stats(self, module_id: str) -> bool:
        """Delete cached module statistics."""
        if not self._client:
            return False
        
        try:
            key = f"{self.STATS_PREFIX}{module_id}"
            self._client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete failed for stats {module_id}: {e}")
            return False
    
    # === BULK OPERATIONS ===
    
    def clear_all_module_cache(self) -> int:
        """
        Clear all module-related cache entries.
        WARNING: Use only for testing or maintenance.
        
        Returns:
            Number of keys deleted
        """
        if not self._client:
            return 0
        
        try:
            patterns = [
                f"{self.MODULE_PREFIX}*",
                f"{self.LIST_PREFIX}*",
                f"{self.STATS_PREFIX}*"
            ]
            
            total_deleted = 0
            for pattern in patterns:
                keys = list(self._client.scan_iter(match=pattern))
                if keys:
                    total_deleted += self._client.delete(*keys)
            
            logger.info(f"Cleared {total_deleted} module cache entries")
            return total_deleted
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return 0
```

#### Task 6.2.3: FastAPI Router for Modules

**File:** `server/routers/modules.py`

```python
"""
AURA Module Router
==================

REST API endpoints for module management including CRUD operations,
document assignment, and statistics retrieval.

Endpoints:
----------
GET    /modules              - List user's modules
POST   /modules              - Create a new module
GET    /modules/{id}         - Get module details
PATCH  /modules/{id}         - Update module
DELETE /modules/{id}         - Delete module

GET    /modules/{id}/documents         - List module's documents
POST   /modules/{id}/documents         - Assign documents to module
DELETE /modules/{id}/documents/{doc_id} - Remove document from module

GET    /modules/{id}/stats    - Get module statistics
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks

from server.dependencies import ModuleManagerDep, get_current_user_id
from server.schemas.module import (
    ModuleCreate,
    ModuleUpdate,
    ModuleResponse,
    ModuleListResponse,
    ModuleStatsResponse,
    DocumentAssignRequest,
    DocumentAssignResponse,
)
from backend.module_manager import (
    ModuleManager,
    ModuleNotFoundError,
    ModuleValidationError,
    DuplicateModuleError,
)
from backend.utils.logging_config import setup_logging

logger = setup_logging("modules_router")
router = APIRouter(prefix="/modules", tags=["Modules"])


# === CRUD ENDPOINTS ===

@router.get("", response_model=ModuleListResponse)
async def list_modules(
    module_manager: ModuleManagerDep,
    include_archived: bool = Query(False, description="Include archived modules"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id)
):
    """
    List all modules for the current user.
    
    Returns modules ordered by last updated, with document counts.
    """
    modules = module_manager.list_modules(
        user_id=user_id,
        include_archived=include_archived,
        limit=limit,
        offset=offset
    )
    
    return ModuleListResponse(
        modules=[ModuleResponse(**m.to_dict()) for m in modules],
        total=len(modules)
    )


@router.post("", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
async def create_module(
    request: ModuleCreate,
    module_manager: ModuleManagerDep,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new study module.
    
    Module names must be unique per user.
    """
    try:
        module = module_manager.create_module(
            name=request.name,
            description=request.description or "",
            color=request.color,
            icon=request.icon,
            user_id=user_id
        )
        return ModuleResponse(**module.to_dict())
    
    except DuplicateModuleError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ModuleValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{module_id}", response_model=ModuleResponse)
async def get_module(
    module_id: str,
    module_manager: ModuleManagerDep
):
    """
    Get details for a specific module.
    
    Includes document count and entity count.
    """
    try:
        module = module_manager.get_module(module_id)
        return ModuleResponse(**module.to_dict())
    
    except ModuleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module not found: {module_id}"
        )


@router.patch("/{module_id}", response_model=ModuleResponse)
async def update_module(
    module_id: str,
    request: ModuleUpdate,
    module_manager: ModuleManagerDep
):
    """
    Update a module's properties.
    
    Only provided fields are updated.
    """
    try:
        module = module_manager.update_module(
            module_id=module_id,
            name=request.name,
            description=request.description,
            color=request.color,
            icon=request.icon,
            is_archived=request.is_archived
        )
        return ModuleResponse(**module.to_dict())
    
    except ModuleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module not found: {module_id}"
        )
    except DuplicateModuleError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ModuleValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{module_id}", status_code=status.HTTP_200_OK)
async def delete_module(
    module_id: str,
    module_manager: ModuleManagerDep,
    reassign_to: str = Query("unassigned", description="Module for orphaned documents")
):
    """
    Delete a module and reassign its documents.
    
    Documents are moved to the specified module (default: 'unassigned').
    """
    try:
        result = module_manager.delete_module(
            module_id=module_id,
            reassign_to=reassign_to
        )
        return {
            "success": True,
            "message": f"Module deleted, {result['documents_reassigned']} documents reassigned",
            **result
        }
    
    except ModuleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module not found: {module_id}"
        )
    except ModuleValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# === DOCUMENT ASSIGNMENT ENDPOINTS ===

@router.get("/{module_id}/documents")
async def get_module_documents(
    module_id: str,
    module_manager: ModuleManagerDep,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Get all documents assigned to a module.
    """
    try:
        documents = module_manager.get_module_documents(
            module_id=module_id,
            limit=limit,
            offset=offset
        )
        return {
            "module_id": module_id,
            "documents": documents,
            "total": len(documents)
        }
    
    except ModuleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module not found: {module_id}"
        )


@router.post("/{module_id}/documents", response_model=DocumentAssignResponse)
async def assign_documents(
    module_id: str,
    request: DocumentAssignRequest,
    module_manager: ModuleManagerDep,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id)
):
    """
    Assign one or more documents to a module.
    
    Accepts a list of document IDs. Returns success count and any failures.
    """
    try:
        if len(request.document_ids) == 1:
            # Single document assignment
            success = module_manager.assign_document(
                module_id=module_id,
                document_id=request.document_ids[0],
                user_id=user_id
            )
            return DocumentAssignResponse(
                module_id=module_id,
                total=1,
                successful=1 if success else 0,
                failed=0 if success else 1,
                failures=[] if success else [{"document_id": request.document_ids[0], "error": "Assignment failed"}]
            )
        else:
            # Batch assignment
            result = module_manager.assign_documents_batch(
                module_id=module_id,
                document_ids=request.document_ids,
                user_id=user_id
            )
            
            # Background task to update stats cache
            background_tasks.add_task(
                module_manager.invalidate_stats_cache,
                module_id
            )
            
            return DocumentAssignResponse(
                module_id=module_id,
                **result
            )
    
    except ModuleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module not found: {module_id}"
        )


@router.delete("/{module_id}/documents/{document_id}")
async def remove_document(
    module_id: str,
    document_id: str,
    module_manager: ModuleManagerDep,
    reassign_to: str = Query("unassigned", description="Module to reassign to")
):
    """
    Remove a document from a module.
    
    Document is moved to the specified module (default: 'unassigned').
    """
    try:
        success = module_manager.remove_document(
            module_id=module_id,
            document_id=document_id,
            reassign_to=reassign_to
        )
        return {
            "success": success,
            "document_id": document_id,
            "reassigned_to": reassign_to
        }
    
    except ModuleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module not found: {module_id}"
        )


# === STATISTICS ENDPOINT ===

@router.get("/{module_id}/stats", response_model=ModuleStatsResponse)
async def get_module_stats(
    module_id: str,
    module_manager: ModuleManagerDep
):
    """
    Get comprehensive statistics for a module.
    
    Includes document, chunk, and entity counts broken down by type.
    """
    try:
        stats = module_manager.get_module_stats(module_id)
        return ModuleStatsResponse(**stats)
    
    except ModuleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module not found: {module_id}"
        )
```

### 6.3 Verification Checklist

| Item | Verification Method | Expected Result |
|------|-------------------|-----------------|
| Create module works | `POST /modules` | 201 with module data |
| List modules works | `GET /modules` | Array with document counts |
| Get module works | `GET /modules/{id}` | Module with stats |
| Update module works | `PATCH /modules/{id}` | Updated fields |
| Delete module works | `DELETE /modules/{id}` | Docs reassigned |
| Assign document works | `POST /modules/{id}/documents` | Success response |
| Cache hit works | Check X-Cache header | "HIT" on second request |
| Validation errors | Invalid input | 400 with message |
| Duplicate name | Same name | 409 Conflict |

---

## 7. Phase 3: Knowledge Graph Processor

**Duration:** Week 3-5 (15 days)  
**Priority:** P0 (Critical Path)  
**Dependencies:** Phase 1, Phase 2 complete

### 7.1 Objectives

1. Create `KGProcessor` service for module-aware entity extraction
2. Implement Celery task pipeline for async document processing
3. Build relationship inference engine for entity connections
4. Add module-level concept aggregation
5. Implement progress tracking and error handling

### 7.2 Detailed Implementation

#### Task 7.2.1: KGProcessor Service

**File:** `backend/kg_processor.py`

```python
"""
AURA Knowledge Graph Processor
==============================

Service for processing documents into knowledge graph structures.
Handles entity extraction, relationship building, and module-aware
tagging of all graph elements.

Processing Pipeline:
1. Text extraction from document
2. Semantic chunking with embeddings
3. Entity extraction via LLM
4. Relationship inference between entities
5. Graph storage with module tagging
6. Module-level concept aggregation

Usage:
    from backend.kg_processor import KGProcessor
    
    processor = KGProcessor(graph_manager, embedding_service)
    
    result = await processor.process_document(
        document_id="doc_123",
        module_id="mod_456",
        text="Document content...",
        options={"extract_relationships": True}
    )
"""
import uuid
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from backend.graph_manager import GraphManager
from backend.utils.embeddings import EmbeddingService
from backend.llm_entity_extractor import LLMEntityExtractor
from backend.semantic_chunker import SemanticChunker
from backend.utils.logging_config import setup_logging

logger = setup_logging("kg_processor")


class ProcessingStage(str, Enum):
    """Stages in the processing pipeline."""
    INITIALIZED = "initialized"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    ENTITY_EXTRACTION = "entity_extraction"
    RELATIONSHIP_INFERENCE = "relationship_inference"
    GRAPH_STORAGE = "graph_storage"
    AGGREGATION = "aggregation"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProcessingProgress:
    """Tracks processing progress for status updates."""
    stage: ProcessingStage
    progress_percent: int
    message: str
    entities_found: int = 0
    chunks_created: int = 0
    relationships_inferred: int = 0


@dataclass
class Entity:
    """Extracted entity from document."""
    id: str
    name: str
    entity_type: str  # "Topic", "Concept", "Methodology", "Finding"
    definition: str
    category: str
    confidence: float
    source_chunk_ids: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None


@dataclass
class Relationship:
    """Inferred relationship between entities."""
    source_id: str
    target_id: str
    relationship_type: str  # "DEFINES", "DEPENDS_ON", "USES", etc.
    strength: float
    evidence: str
    source_chunk_id: str


@dataclass 
class ProcessingResult:
    """Result of document processing."""
    document_id: str
    module_id: str
    success: bool
    chunks_created: int
    entities_extracted: int
    relationships_inferred: int
    processing_time_ms: int
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class KGProcessor:
    """
    Knowledge Graph Processor for module-aware document processing.
    
    Orchestrates the full pipeline from raw text to knowledge graph
    with proper module tagging on all nodes and relationships.
    """
    
    # Processing configuration
    CHUNK_SIZE = 512          # Target tokens per chunk
    CHUNK_OVERLAP = 50        # Overlap between chunks
    MAX_ENTITIES_PER_CHUNK = 10
    EMBEDDING_BATCH_SIZE = 20
    RELATIONSHIP_CONFIDENCE_THRESHOLD = 0.6
    
    def __init__(
        self,
        graph_manager: GraphManager,
        embedding_service: EmbeddingService,
        entity_extractor: Optional[LLMEntityExtractor] = None,
        chunker: Optional[SemanticChunker] = None
    ):
        """
        Initialize KGProcessor.
        
        Args:
            graph_manager: Neo4j graph manager
            embedding_service: Embedding generation service
            entity_extractor: LLM-based entity extractor (optional, created if None)
            chunker: Semantic chunker (optional, created if None)
        """
        self.gm = graph_manager
        self.embeddings = embedding_service
        self.entity_extractor = entity_extractor or LLMEntityExtractor()
        self.chunker = chunker or SemanticChunker()
        
        self._progress_callback = None
    
    def set_progress_callback(self, callback):
        """Set callback for progress updates: callback(ProcessingProgress)"""
        self._progress_callback = callback
    
    def _report_progress(self, progress: ProcessingProgress):
        """Report progress via callback if set."""
        if self._progress_callback:
            try:
                self._progress_callback(progress)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
    
    async def process_document(
        self,
        document_id: str,
        module_id: str,
        text: str,
        title: str = "",
        options: Optional[Dict[str, Any]] = None
    ) -> ProcessingResult:
        """
        Process a document into the knowledge graph.
        
        This is the main entry point for document processing. It orchestrates
        the full pipeline and ensures all nodes are properly tagged with module_id.
        
        Args:
            document_id: Unique document identifier
            module_id: Target module for this document
            text: Full document text content
            title: Document title (used for context in extraction)
            options: Processing options:
                - extract_relationships: bool (default True)
                - min_chunk_size: int (default 100)
                - max_entities: int (default 50)
                
        Returns:
            ProcessingResult with statistics and status
        """
        start_time = datetime.utcnow()
        options = options or {}
        
        self._report_progress(ProcessingProgress(
            stage=ProcessingStage.INITIALIZED,
            progress_percent=0,
            message="Starting document processing"
        ))
        
        try:
            # Stage 1: Semantic Chunking
            self._report_progress(ProcessingProgress(
                stage=ProcessingStage.CHUNKING,
                progress_percent=10,
                message="Creating semantic chunks"
            ))
            
            chunks = await self._create_chunks(
                document_id=document_id,
                module_id=module_id,
                text=text,
                min_size=options.get('min_chunk_size', 100)
            )
            
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")
            
            # Stage 2: Generate Embeddings
            self._report_progress(ProcessingProgress(
                stage=ProcessingStage.EMBEDDING,
                progress_percent=25,
                message=f"Generating embeddings for {len(chunks)} chunks",
                chunks_created=len(chunks)
            ))
            
            chunks_with_embeddings = await self._generate_chunk_embeddings(chunks)
            
            # Stage 3: Entity Extraction
            self._report_progress(ProcessingProgress(
                stage=ProcessingStage.ENTITY_EXTRACTION,
                progress_percent=40,
                message="Extracting entities from chunks",
                chunks_created=len(chunks)
            ))
            
            entities = await self._extract_entities(
                chunks=chunks_with_embeddings,
                title=title,
                max_entities=options.get('max_entities', 50)
            )
            
            logger.info(f"Extracted {len(entities)} entities from document {document_id}")
            
            # Stage 4: Relationship Inference
            relationships = []
            if options.get('extract_relationships', True) and len(entities) > 1:
                self._report_progress(ProcessingProgress(
                    stage=ProcessingStage.RELATIONSHIP_INFERENCE,
                    progress_percent=55,
                    message=f"Inferring relationships between {len(entities)} entities",
                    chunks_created=len(chunks),
                    entities_found=len(entities)
                ))
                
                relationships = await self._infer_relationships(
                    entities=entities,
                    chunks=chunks_with_embeddings
                )
                
                logger.info(f"Inferred {len(relationships)} relationships")
            
            # Stage 5: Store in Graph
            self._report_progress(ProcessingProgress(
                stage=ProcessingStage.GRAPH_STORAGE,
                progress_percent=70,
                message="Storing in knowledge graph",
                chunks_created=len(chunks),
                entities_found=len(entities),
                relationships_inferred=len(relationships)
            ))
            
            await self._store_in_graph(
                document_id=document_id,
                module_id=module_id,
                chunks=chunks_with_embeddings,
                entities=entities,
                relationships=relationships
            )
            
            # Stage 6: Module Aggregation
            self._report_progress(ProcessingProgress(
                stage=ProcessingStage.AGGREGATION,
                progress_percent=90,
                message="Updating module aggregates",
                chunks_created=len(chunks),
                entities_found=len(entities),
                relationships_inferred=len(relationships)
            ))
            
            await self._update_module_aggregates(module_id, entities)
            
            # Complete
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            self._report_progress(ProcessingProgress(
                stage=ProcessingStage.COMPLETED,
                progress_percent=100,
                message="Processing completed successfully",
                chunks_created=len(chunks),
                entities_found=len(entities),
                relationships_inferred=len(relationships)
            ))
            
            return ProcessingResult(
                document_id=document_id,
                module_id=module_id,
                success=True,
                chunks_created=len(chunks),
                entities_extracted=len(entities),
                relationships_inferred=len(relationships),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.exception(f"Document processing failed: {e}")
            
            self._report_progress(ProcessingProgress(
                stage=ProcessingStage.FAILED,
                progress_percent=0,
                message=f"Processing failed: {str(e)}"
            ))
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return ProcessingResult(
                document_id=document_id,
                module_id=module_id,
                success=False,
                chunks_created=0,
                entities_extracted=0,
                relationships_inferred=0,
                processing_time_ms=processing_time,
                error=str(e)
            )
    
    async def _create_chunks(
        self,
        document_id: str,
        module_id: str,
        text: str,
        min_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Create semantic chunks from document text.
        
        Uses semantic boundaries (paragraphs, sections) rather than
        fixed-size splitting for better context preservation.
        """
        # Use semantic chunker for intelligent splitting
        raw_chunks = self.chunker.chunk_text(
            text=text,
            chunk_size=self.CHUNK_SIZE,
            overlap=self.CHUNK_OVERLAP,
            min_chunk_size=min_size
        )
        
        chunks = []
        for idx, chunk_text in enumerate(raw_chunks):
            chunk_id = f"chunk_{document_id}_{idx}"
            chunks.append({
                'id': chunk_id,
                'text': chunk_text,
                'document_id': document_id,
                'module_id': module_id,
                'chunk_index': idx,
                'token_count': len(chunk_text.split())  # Approximate
            })
        
        return chunks
    
    async def _generate_chunk_embeddings(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for all chunks in batches.
        
        Uses batched API calls for efficiency.
        """
        # Extract texts for batch embedding
        texts = [c['text'] for c in chunks]
        
        # Generate embeddings in batches
        embeddings = []
        for i in range(0, len(texts), self.EMBEDDING_BATCH_SIZE):
            batch = texts[i:i + self.EMBEDDING_BATCH_SIZE]
            batch_embeddings = await self.embeddings.embed_texts(batch)
            embeddings.extend(batch_embeddings)
        
        # Attach embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding
        
        return chunks
    
    async def _extract_entities(
        self,
        chunks: List[Dict[str, Any]],
        title: str,
        max_entities: int = 50
    ) -> List[Entity]:
        """
        Extract entities from chunks using LLM.
        
        Deduplicates entities across chunks and assigns confidence scores.
        """
        all_entities = []
        entity_name_map = {}  # For deduplication
        
        for chunk in chunks:
            try:
                # Extract entities from this chunk
                chunk_entities = await self.entity_extractor.extract(
                    text=chunk['text'],
                    context=f"Document: {title}",
                    max_entities=self.MAX_ENTITIES_PER_CHUNK
                )
                
                for entity_data in chunk_entities:
                    name_lower = entity_data['name'].lower()
                    
                    if name_lower in entity_name_map:
                        # Update existing entity with new chunk reference
                        existing = entity_name_map[name_lower]
                        existing.source_chunk_ids.append(chunk['id'])
                        existing.confidence = min(1.0, existing.confidence + 0.1)
                    else:
                        # Create new entity
                        entity = Entity(
                            id=f"ent_{uuid.uuid4().hex[:12]}",
                            name=entity_data['name'],
                            entity_type=entity_data.get('type', 'Concept'),
                            definition=entity_data.get('definition', ''),
                            category=entity_data.get('category', 'general'),
                            confidence=entity_data.get('confidence', 0.8),
                            source_chunk_ids=[chunk['id']]
                        )
                        all_entities.append(entity)
                        entity_name_map[name_lower] = entity
                        
            except Exception as e:
                logger.warning(f"Entity extraction failed for chunk {chunk['id']}: {e}")
        
        # Sort by confidence and limit
        all_entities.sort(key=lambda e: e.confidence, reverse=True)
        return all_entities[:max_entities]
    
    async def _infer_relationships(
        self,
        entities: List[Entity],
        chunks: List[Dict[str, Any]]
    ) -> List[Relationship]:
        """
        Infer relationships between entities.
        
        Uses co-occurrence in chunks and LLM-based relationship classification.
        """
        relationships = []
        
        # Build chunk-to-entities map
        chunk_entities = {}
        for entity in entities:
            for chunk_id in entity.source_chunk_ids:
                if chunk_id not in chunk_entities:
                    chunk_entities[chunk_id] = []
                chunk_entities[chunk_id].append(entity)
        
        # Find co-occurring entities
        seen_pairs = set()
        for chunk_id, entities_in_chunk in chunk_entities.items():
            if len(entities_in_chunk) < 2:
                continue
            
            # Get chunk text for evidence
            chunk_text = next(
                (c['text'] for c in chunks if c['id'] == chunk_id),
                ""
            )
            
            # Create relationships for co-occurring entities
            for i, entity1 in enumerate(entities_in_chunk):
                for entity2 in entities_in_chunk[i+1:]:
                    pair_key = tuple(sorted([entity1.id, entity2.id]))
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)
                    
                    # Infer relationship type using simple heuristics
                    # (In production, use LLM for better classification)
                    rel_type, strength = self._classify_relationship(
                        entity1, entity2, chunk_text
                    )
                    
                    if strength >= self.RELATIONSHIP_CONFIDENCE_THRESHOLD:
                        relationships.append(Relationship(
                            source_id=entity1.id,
                            target_id=entity2.id,
                            relationship_type=rel_type,
                            strength=strength,
                            evidence=chunk_text[:200],
                            source_chunk_id=chunk_id
                        ))
        
        return relationships
    
    def _classify_relationship(
        self,
        entity1: Entity,
        entity2: Entity,
        context: str
    ) -> Tuple[str, float]:
        """
        Classify the relationship between two entities.
        
        Returns (relationship_type, confidence).
        """
        # Simple heuristic-based classification
        # In production, use LLM for better accuracy
        
        type1 = entity1.entity_type.lower()
        type2 = entity2.entity_type.lower()
        
        # Type-based relationship inference
        if type1 == 'methodology' and type2 == 'finding':
            return ('PRODUCES', 0.8)
        elif type1 == 'concept' and type2 == 'concept':
            return ('RELATES_TO', 0.7)
        elif type1 == 'topic' and type2 == 'concept':
            return ('CONTAINS', 0.75)
        elif type1 == 'concept' and type2 == 'methodology':
            return ('USES', 0.7)
        else:
            return ('RELATES_TO', 0.6)
    
    async def _store_in_graph(
        self,
        document_id: str,
        module_id: str,
        chunks: List[Dict[str, Any]],
        entities: List[Entity],
        relationships: List[Relationship]
    ):
        """
        Store all processed data in Neo4j.
        
        Uses MERGE for idempotency - safe to reprocess documents.
        """
        # Store chunks with module_id
        for chunk in chunks:
            self.gm.create_chunk_node({
                'id': chunk['id'],
                'text': chunk['text'],
                'embedding': chunk['embedding'],
                'document_id': document_id,
                'module_id': module_id,
                'chunk_index': chunk['chunk_index'],
                'token_count': chunk.get('token_count', 0)
            })
            
            # Create HAS_CHUNK relationship
            self.gm.create_relationship(
                source_type='Document',
                source_id=document_id,
                rel_type='HAS_CHUNK',
                target_type='Chunk',
                target_id=chunk['id'],
                properties={'chunk_index': chunk['chunk_index']}
            )
        
        # Store entities with module_id
        for entity in entities:
            # Generate embedding for entity
            if not entity.embedding:
                entity.embedding = await self.embeddings.embed_text(
                    f"{entity.name}: {entity.definition}"
                )
            
            # Create entity node based on type
            entity_data = {
                'id': entity.id,
                'name': entity.name,
                'definition': entity.definition,
                'category': entity.category,
                'module_id': module_id,
                'embedding': entity.embedding,
                'confidence': entity.confidence
            }
            
            if entity.entity_type == 'Topic':
                self.gm.create_topic_node(entity_data)
            elif entity.entity_type == 'Concept':
                self.gm.create_concept_node(entity_data)
            elif entity.entity_type == 'Methodology':
                self.gm.create_methodology_node(entity_data)
            elif entity.entity_type == 'Finding':
                self.gm.create_finding_node(entity_data)
            
            # Link entity to source chunks
            for chunk_id in entity.source_chunk_ids:
                self.gm.create_relationship(
                    source_type='Chunk',
                    source_id=chunk_id,
                    rel_type='CONTAINS_ENTITY',
                    target_type=entity.entity_type,
                    target_id=entity.id,
                    properties={'confidence': entity.confidence}
                )
        
        # Store relationships
        for rel in relationships:
            # Get entity types for source and target
            source_entity = next((e for e in entities if e.id == rel.source_id), None)
            target_entity = next((e for e in entities if e.id == rel.target_id), None)
            
            if source_entity and target_entity:
                self.gm.create_relationship(
                    source_type=source_entity.entity_type,
                    source_id=rel.source_id,
                    rel_type=rel.relationship_type,
                    target_type=target_entity.entity_type,
                    target_id=rel.target_id,
                    properties={
                        'strength': rel.strength,
                        'evidence': rel.evidence[:500],
                        'module_id': module_id
                    }
                )
        
        # Update document with processing stats
        self.gm.execute_query("""
            MATCH (d:Document {id: $doc_id})
            SET d.chunk_count = $chunk_count,
                d.entity_count = $entity_count,
                d.processing_status = 'completed',
                d.processed_at = datetime()
        """, {
            'doc_id': document_id,
            'chunk_count': len(chunks),
            'entity_count': len(entities)
        })
    
    async def _update_module_aggregates(
        self,
        module_id: str,
        entities: List[Entity]
    ):
        """
        Update module-level concept aggregations.
        
        Links high-confidence entities directly to module for quick access.
        """
        # Find core concepts (high confidence, multiple mentions)
        core_entities = [
            e for e in entities
            if e.confidence >= 0.8 and len(e.source_chunk_ids) >= 2
        ]
        
        for entity in core_entities[:10]:  # Top 10 core concepts
            self.gm.create_relationship(
                source_type='Module',
                source_id=module_id,
                rel_type='HAS_CORE_CONCEPT',
                target_type=entity.entity_type,
                target_id=entity.id,
                properties={'importance': entity.confidence}
            )


# === BATCH PROCESSING ===

class BatchProcessor:
    """
    Handles batch processing of multiple documents.
    
    Optimizes for throughput with parallel processing and
    shared resource pooling.
    """
    
    def __init__(
        self,
        kg_processor: KGProcessor,
        max_concurrent: int = 3
    ):
        self.processor = kg_processor
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch(
        self,
        documents: List[Dict[str, Any]],
        module_id: str
    ) -> List[ProcessingResult]:
        """
        Process multiple documents concurrently.
        
        Args:
            documents: List of {"id": str, "text": str, "title": str}
            module_id: Target module for all documents
            
        Returns:
            List of ProcessingResults
        """
        async def process_one(doc):
            async with self.semaphore:
                return await self.processor.process_document(
                    document_id=doc['id'],
                    module_id=module_id,
                    text=doc['text'],
                    title=doc.get('title', '')
                )
        
        tasks = [process_one(doc) for doc in documents]
        return await asyncio.gather(*tasks)
```

#### Task 7.2.2: Celery Task Pipeline

**File:** `backend/tasks/module_processing_tasks.py`

```python
"""
AURA Module Processing Tasks
============================

Celery tasks for asynchronous document processing into the knowledge graph.
Provides reliable, retryable task execution with progress tracking.

Task Types:
-----------
1. process_document_to_kg: Single document processing
2. process_batch_to_kg: Batch document processing
3. reprocess_module: Reprocess all documents in a module
4. cleanup_failed_processing: Clean up failed processing attempts

Usage:
------
    from backend.tasks.module_processing_tasks import process_document_to_kg
    
    # Queue a document for processing
    task = process_document_to_kg.delay(
        document_id="doc_123",
        module_id="mod_456",
        user_id="user_789"
    )
    
    # Check status
    print(task.state)  # PENDING, PROCESSING, SUCCESS, FAILURE
    print(task.info)   # Progress information
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from celery import Celery, Task, chain, group
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
from pydantic import BaseModel, ValidationError

from backend.utils.config import config
from backend.utils.logging_config import setup_logging

logger = setup_logging("kg_tasks")

# Celery app configuration
app = Celery(
    'aura_kg_tasks',
    broker=config.CELERY_BROKER_URL or 'redis://localhost:6379/0',
    backend=config.CELERY_RESULT_BACKEND or 'redis://localhost:6379/1'
)

# Task configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 min hard limit
    task_soft_time_limit=1500,  # 25 min soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
    task_acks_late=True,  # Acknowledge after completion
    task_reject_on_worker_lost=True,  # Re-queue if worker dies
)


# === PYDANTIC VALIDATION MODELS ===

class ProcessDocumentInput(BaseModel):
    """Validation model for document processing input."""
    document_id: str
    module_id: str
    user_id: str
    options: Dict[str, Any] = {}


class BatchProcessInput(BaseModel):
    """Validation model for batch processing input."""
    document_ids: List[str]
    module_id: str
    user_id: str
    options: Dict[str, Any] = {}


# === BASE TASK CLASS ===

class KGProcessingTask(Task):
    """
    Base task class with shared resources and error handling.
    
    Resources are lazily initialized and cached per worker.
    """
    _graph_manager = None
    _embedding_service = None
    _kg_processor = None
    _document_processor = None
    
    @property
    def graph_manager(self):
        if self._graph_manager is None:
            from backend.graph_manager import GraphManager
            self._graph_manager = GraphManager()
        return self._graph_manager
    
    @property
    def embedding_service(self):
        if self._embedding_service is None:
            from backend.utils.embeddings import EmbeddingService
            self._embedding_service = EmbeddingService()
        return self._embedding_service
    
    @property
    def kg_processor(self):
        if self._kg_processor is None:
            from backend.kg_processor import KGProcessor
            self._kg_processor = KGProcessor(
                graph_manager=self.graph_manager,
                embedding_service=self.embedding_service
            )
        return self._kg_processor
    
    @property
    def document_processor(self):
        if self._document_processor is None:
            from backend.document_processor import DocumentProcessor
            self._document_processor = DocumentProcessor()
        return self._document_processor
    
    def update_processing_state(
        self,
        stage: str,
        progress: int,
        message: str,
        **extra
    ):
        """Update task state with processing progress."""
        self.update_state(
            state='PROCESSING',
            meta={
                'stage': stage,
                'progress': progress,
                'message': message,
                'updated_at': datetime.utcnow().isoformat(),
                **extra
            }
        )
    
    def mark_document_status(
        self,
        document_id: str,
        status: str,
        error: str = None
    ):
        """Update document processing status in database."""
        try:
            query = """
            MATCH (d:Document {id: $doc_id})
            SET d.processing_status = $status,
                d.processing_error = $error,
                d.status_updated_at = datetime()
            """
            self.graph_manager.execute_query(query, {
                'doc_id': document_id,
                'status': status,
                'error': error
            })
        except Exception as e:
            logger.warning(f"Failed to update document status: {e}")


# === PROCESSING TASKS ===

@app.task(
    bind=True,
    base=KGProcessingTask,
    name='aura.process_document_to_kg',
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
    reject_on_worker_lost=True
)
def process_document_to_kg(
    self,
    document_id: str,
    module_id: str,
    user_id: str,
    options: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Process a single document into the knowledge graph.
    
    This task is IDEMPOTENT - safe to retry on failure.
    Uses MERGE operations in Neo4j to avoid duplicates.
    
    Args:
        document_id: Document to process
        module_id: Target module
        user_id: User who initiated processing
        options: Processing options
            - extract_relationships: bool (default True)
            - max_entities: int (default 50)
            
    Returns:
        Processing result with statistics
    """
    task_id = self.request.id
    logger.info(f"Task {task_id}: Processing document {document_id} for module {module_id}")
    
    # Validate input
    try:
        validated = ProcessDocumentInput(
            document_id=document_id,
            module_id=module_id,
            user_id=user_id,
            options=options or {}
        )
    except ValidationError as e:
        logger.error(f"Validation failed: {e}")
        raise ValueError(f"Invalid input: {e}")
    
    try:
        # Mark as processing
        self.mark_document_status(document_id, 'processing')
        
        # Stage 1: Get document content
        self.update_processing_state(
            stage='text_extraction',
            progress=5,
            message='Extracting document text'
        )
        
        doc_data = self._get_document(document_id)
        if not doc_data:
            raise ValueError(f"Document not found: {document_id}")
        
        text = doc_data.get('content', '')
        if not text:
            # Extract text from file if content not stored
            file_path = doc_data.get('file_path')
            if file_path:
                text = self.document_processor.extract_text(file_path)
            
            if not text:
                raise ValueError("Document has no content to process")
        
        # Stage 2: Process through KG pipeline
        self.update_processing_state(
            stage='kg_processing',
            progress=15,
            message='Processing into knowledge graph'
        )
        
        # Set up progress callback
        def progress_callback(progress):
            # Scale progress to 15-95 range
            scaled = 15 + int((progress.progress_percent / 100) * 80)
            self.update_processing_state(
                stage=progress.stage.value,
                progress=scaled,
                message=progress.message,
                chunks=progress.chunks_created,
                entities=progress.entities_found,
                relationships=progress.relationships_inferred
            )
        
        self.kg_processor.set_progress_callback(progress_callback)
        
        # Run async processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                self.kg_processor.process_document(
                    document_id=validated.document_id,
                    module_id=validated.module_id,
                    text=text,
                    title=doc_data.get('title', ''),
                    options=validated.options
                )
            )
        finally:
            loop.close()
        
        if result.success:
            # Mark as completed
            self.mark_document_status(document_id, 'completed')
            
            # Invalidate module cache
            self._invalidate_cache(module_id)
            
            self.update_processing_state(
                stage='completed',
                progress=100,
                message='Processing completed successfully'
            )
            
            logger.info(f"Task {task_id}: Completed - {result.chunks_created} chunks, "
                       f"{result.entities_extracted} entities")
            
            return {
                'success': True,
                'document_id': document_id,
                'module_id': module_id,
                'chunks_created': result.chunks_created,
                'entities_extracted': result.entities_extracted,
                'relationships_inferred': result.relationships_inferred,
                'processing_time_ms': result.processing_time_ms
            }
        else:
            raise Exception(result.error or "Processing failed")
            
    except SoftTimeLimitExceeded:
        logger.error(f"Task {task_id}: Soft time limit exceeded")
        self.mark_document_status(document_id, 'failed', 'Processing timeout')
        raise
        
    except MaxRetriesExceededError:
        logger.error(f"Task {task_id}: Max retries exceeded")
        self.mark_document_status(document_id, 'failed', 'Max retries exceeded')
        raise
        
    except Exception as e:
        logger.exception(f"Task {task_id}: Processing failed - {e}")
        self.mark_document_status(document_id, 'failed', str(e))
        raise
    
    def _get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Fetch document data from graph."""
        query = """
        MATCH (d:Document {id: $doc_id})
        RETURN d {.*} as document
        """
        result = self.graph_manager.execute_query(query, {'doc_id': document_id})
        return result[0]['document'] if result else None
    
    def _invalidate_cache(self, module_id: str):
        """Invalidate module-related caches."""
        try:
            from backend.cache.module_cache import ModuleCache
            cache = ModuleCache()
            cache.delete_module(module_id)
            cache.delete_stats(module_id)
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")


@app.task(
    bind=True,
    base=KGProcessingTask,
    name='aura.process_batch_to_kg',
    time_limit=7200,  # 2 hour limit for batch
    soft_time_limit=6600
)
def process_batch_to_kg(
    self,
    document_ids: List[str],
    module_id: str,
    user_id: str,
    options: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Process multiple documents as a batch.
    
    Creates sub-tasks for each document and aggregates results.
    """
    logger.info(f"Starting batch processing of {len(document_ids)} documents")
    
    # Validate input
    try:
        validated = BatchProcessInput(
            document_ids=document_ids,
            module_id=module_id,
            user_id=user_id,
            options=options or {}
        )
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}")
    
    # Create a group of subtasks
    job = group([
        process_document_to_kg.s(
            document_id=doc_id,
            module_id=validated.module_id,
            user_id=validated.user_id,
            options=validated.options
        )
        for doc_id in validated.document_ids
    ])
    
    # Execute and gather results
    group_result = job.apply_async()
    
    # Wait for all to complete (with timeout)
    results = group_result.get(timeout=6000)  # 100 min timeout
    
    # Aggregate results
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    return {
        'success': len(failed) == 0,
        'module_id': module_id,
        'total': len(document_ids),
        'successful': len(successful),
        'failed': len(failed),
        'results': results
    }


@app.task(
    bind=True,
    base=KGProcessingTask,
    name='aura.reprocess_module'
)
def reprocess_module(
    self,
    module_id: str,
    user_id: str,
    options: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Reprocess all documents in a module.
    
    Useful after algorithm updates or to refresh stale data.
    """
    logger.info(f"Reprocessing all documents in module {module_id}")
    
    # Get all document IDs in module
    query = """
    MATCH (m:Module {id: $module_id})-[:CONTAINS_DOCUMENT]->(d:Document)
    RETURN collect(d.id) as document_ids
    """
    result = self.graph_manager.execute_query(query, {'module_id': module_id})
    
    if not result or not result[0]['document_ids']:
        return {
            'success': True,
            'module_id': module_id,
            'message': 'No documents to reprocess',
            'total': 0
        }
    
    document_ids = result[0]['document_ids']
    
    # Clear existing KG data for this module (chunks, entities)
    self._clear_module_kg_data(module_id)
    
    # Delegate to batch processor
    return process_batch_to_kg(
        document_ids=document_ids,
        module_id=module_id,
        user_id=user_id,
        options=options or {}
    )


@app.task(
    bind=True,
    base=KGProcessingTask,
    name='aura.cleanup_failed_processing'
)
def cleanup_failed_processing(
    self,
    older_than_hours: int = 24
) -> Dict[str, Any]:
    """
    Clean up documents stuck in 'processing' status.
    
    Resets them to 'pending' for retry or marks as 'failed'.
    """
    query = """
    MATCH (d:Document)
    WHERE d.processing_status = 'processing'
    AND d.status_updated_at < datetime() - duration({hours: $hours})
    SET d.processing_status = 'failed',
        d.processing_error = 'Processing timed out'
    RETURN count(d) as cleaned
    """
    
    result = self.graph_manager.execute_query(query, {'hours': older_than_hours})
    cleaned = result[0]['cleaned'] if result else 0
    
    logger.info(f"Cleaned up {cleaned} stuck documents")
    
    return {
        'success': True,
        'documents_cleaned': cleaned
    }
```

### 7.3 Verification Checklist

| Item | Test Method | Expected Result |
|------|-------------|-----------------|
| Document processing works | Process a PDF | Chunks, entities created |
| Entity extraction accurate | Check extracted entities | Match document content |
| Relationships inferred | Check graph relationships | Logical connections |
| Module tagging correct | Query `WHERE module_id = X` | All nodes tagged |
| Retry on failure | Kill worker mid-process | Task retries |
| Progress tracking | Check task state | PROCESSING with % |
| Batch processing | Process 5 docs | All complete |
| Idempotency | Reprocess same doc | No duplicates |

---

## 8. Phase 4: Module-Aware RAG Engine

**Duration:** Week 5-7 (15 days)  
**Priority:** P0 (Critical Path)  
**Dependencies:** Phase 1, Phase 2, Phase 3 complete

### 8.1 Objectives

1. Extend `RAGEngine` with module filtering capabilities
2. Implement module-scoped vector search
3. Add cross-module concept discovery
4. Build module context aggregation for better responses
5. Optimize query performance with caching

### 8.2 Detailed Implementation

#### Task 8.2.1: Extended RAGEngine with Module Support

**File:** `backend/rag_engine.py` (modifications and additions)

```python
"""
Extended RAGEngine with Module-Aware Retrieval
==============================================

Additions to existing rag_engine.py for module-filtered queries.
"""

# Add these imports at top
from typing import Set
from backend.cache.module_cache import ModuleCache

# Add to RAGEngine class:

class RAGEngine:
    """Extended with module-aware retrieval."""
    
    def __init__(
        self,
        graph_manager: GraphManager,
        cache: Optional[ModuleCache] = None
    ):
        self.gm = graph_manager
        self.cache = cache
        self.embeddings = EmbeddingService()
        self.chat_manager = ChatManager(graph_manager)
        
        # Module filtering configuration
        self.enable_cross_module_discovery = True
        self.cross_module_concept_threshold = 0.85
    
    async def query_with_modules(
        self,
        user_query: str,
        module_ids: List[str],
        session_id: Optional[str] = None,
        mode: AnswerMode = "assistant",
        enable_thinking: bool = False,
        top_k: int = 10,
        enable_cross_module: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a RAG query filtered to specific modules.
        
        This is the primary query method for module-scoped learning sessions.
        Retrieves context only from specified modules and generates
        module-contextualized responses.
        
        Args:
            user_query: The user's question
            module_ids: List of module IDs to search within
            session_id: Optional session for context tracking
            mode: Response mode ("assistant" or "tutor")
            enable_thinking: Whether to include reasoning in response
            top_k: Number of chunks to retrieve
            enable_cross_module: Whether to find cross-module connections
            
        Returns:
            {
                "answer": str,
                "sources": List[SourceInfo],
                "model_used": str,
                "modules_searched": List[str],
                "cross_module_concepts": List[CrossModuleConcept] (optional),
                "thought_summary": str (optional)
            }
        """
        logger.info(f"Module-filtered query: '{user_query[:50]}...' in modules {module_ids}")
        
        # Check query cache
        cache_key = self._build_cache_key(user_query, module_ids, mode)
        if self.cache:
            cached = self.cache.get_query_result(cache_key)
            if cached:
                logger.debug("Query cache hit")
                return cached
        
        # Generate query embedding
        query_embedding = await self.embeddings.embed_text(user_query)
        
        # Expand query with synonyms and related terms
        expanded_query = await self._expand_query(user_query)
        
        # Classify query for routing
        query_type = self._classify_query(user_query)
        
        # Retrieve context from modules
        context = await self._retrieve_module_context(
            query=expanded_query,
            query_embedding=query_embedding,
            module_ids=module_ids,
            top_k=top_k,
            query_type=query_type
        )
        
        # Optionally find cross-module concepts
        cross_module_concepts = []
        if enable_cross_module and len(module_ids) > 1:
            cross_module_concepts = await self._find_cross_module_concepts(
                query=user_query,
                module_ids=module_ids,
                context=context
            )
        
        # Get conversation history if session provided
        history = []
        if session_id:
            history = await self.chat_manager.get_session_history(
                session_id=session_id,
                limit=10
            )
        
        # Build prompt with module context
        prompt = self._build_module_prompt(
            query=user_query,
            context=context,
            history=history,
            mode=mode,
            module_ids=module_ids,
            cross_module_concepts=cross_module_concepts
        )
        
        # Generate response
        response = await self._generate_response(
            prompt=prompt,
            mode=mode,
            enable_thinking=enable_thinking
        )
        
        # Build result
        result = {
            "answer": response["text"],
            "sources": self._format_sources(context),
            "model_used": response["model"],
            "modules_searched": module_ids,
        }
        
        if cross_module_concepts:
            result["cross_module_concepts"] = cross_module_concepts
        
        if enable_thinking and response.get("thinking"):
            result["thought_summary"] = response["thinking"]
        
        # Cache result
        if self.cache:
            self.cache.set_query_result(cache_key, result, ttl=300)
        
        # Save to session history if provided
        if session_id:
            await self.chat_manager.add_message(
                session_id=session_id,
                role="user",
                content=user_query
            )
            await self.chat_manager.add_message(
                session_id=session_id,
                role="assistant",
                content=response["text"],
                metadata={
                    "sources": [s["id"] for s in result["sources"]],
                    "model": response["model"]
                }
            )
        
        return result
    
    async def _retrieve_module_context(
        self,
        query: str,
        query_embedding: List[float],
        module_ids: List[str],
        top_k: int,
        query_type: str
    ) -> Dict[str, Any]:
        """
        Retrieve context from specified modules only.
        
        Combines vector search with graph traversal for comprehensive context.
        """
        # Phase 1: Vector search with module filter
        chunks = await self._module_vector_search(
            embedding=query_embedding,
            module_ids=module_ids,
            top_k=top_k * 2  # Retrieve more, filter later
        )
        
        # Phase 2: Fulltext search for exact matches
        fulltext_chunks = await self._module_fulltext_search(
            query=query,
            module_ids=module_ids,
            top_k=top_k
        )
        
        # Merge and deduplicate
        all_chunks = self._merge_chunk_results(chunks, fulltext_chunks)
        
        # Phase 3: Graph expansion (if query warrants it)
        entities = []
        if query_type in ['graph_expansion', 'hybrid']:
            entities = await self._module_entity_search(
                query=query,
                query_embedding=query_embedding,
                module_ids=module_ids,
                top_k=10
            )
            
            # Expand graph for additional context
            if entities:
                entity_ids = [e["id"] for e in entities[:5]]
                graph_context = await self._expand_graph_within_modules(
                    entity_ids=entity_ids,
                    module_ids=module_ids,
                    max_hops=2
                )
                
                # Add graph context to chunks
                for ctx in graph_context:
                    if ctx not in all_chunks:
                        all_chunks.append(ctx)
        
        # Rank and limit
        ranked_chunks = self._rank_chunks(all_chunks, query_embedding)[:top_k]
        
        return {
            "chunks": ranked_chunks,
            "entities": entities,
            "module_ids": module_ids
        }
    
    async def _module_vector_search(
        self,
        embedding: List[float],
        module_ids: List[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Vector similarity search filtered by module_id.
        
        Uses Neo4j's HNSW vector index with post-filtering.
        """
        query = """
        CALL db.index.vector.queryNodes(
            'chunk_vector_index',
            $top_k_expanded,
            $embedding
        ) YIELD node, score
        WHERE node.module_id IN $module_ids
        WITH node, score
        LIMIT $top_k
        
        // Get parent document info
        MATCH (d:Document)-[:HAS_CHUNK]->(node)
        
        RETURN {
            id: node.id,
            text: node.text,
            score: score,
            document_id: d.id,
            document_title: d.title,
            module_id: node.module_id,
            chunk_index: node.chunk_index
        } as chunk
        ORDER BY score DESC
        """
        
        result = self.gm.execute_query(query, {
            'embedding': embedding,
            'module_ids': module_ids,
            'top_k': top_k,
            'top_k_expanded': top_k * 3  # Expand to allow for filtering
        })
        
        return [r['chunk'] for r in result]
    
    async def _module_fulltext_search(
        self,
        query: str,
        module_ids: List[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Fulltext search filtered by module_id.
        
        Uses Apache Lucene index for keyword matching.
        """
        cypher = """
        CALL db.index.fulltext.queryNodes(
            'chunk_fulltext_index',
            $query
        ) YIELD node, score
        WHERE node.module_id IN $module_ids
        WITH node, score
        LIMIT $top_k
        
        MATCH (d:Document)-[:HAS_CHUNK]->(node)
        
        RETURN {
            id: node.id,
            text: node.text,
            score: score * 0.8,  // Weight fulltext slightly lower
            document_id: d.id,
            document_title: d.title,
            module_id: node.module_id,
            chunk_index: node.chunk_index
        } as chunk
        """
        
        result = self.gm.execute_query(cypher, {
            'query': query,
            'module_ids': module_ids,
            'top_k': top_k
        })
        
        return [r['chunk'] for r in result]
    
    async def _module_entity_search(
        self,
        query: str,
        query_embedding: List[float],
        module_ids: List[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant entities within modules.
        
        Searches across all entity types (Topic, Concept, Methodology, Finding).
        """
        # Search each entity type's vector index
        entity_types = ['Topic', 'Concept', 'Methodology', 'Finding']
        all_entities = []
        
        for entity_type in entity_types:
            index_name = f"{entity_type.lower()}_vector_index"
            
            cypher = f"""
            CALL db.index.vector.queryNodes(
                '{index_name}',
                $top_k,
                $embedding
            ) YIELD node, score
            WHERE node.module_id IN $module_ids
            
            RETURN {{
                id: node.id,
                name: node.name,
                type: '{entity_type}',
                definition: node.definition,
                score: score,
                module_id: node.module_id
            }} as entity
            """
            
            try:
                result = self.gm.execute_query(cypher, {
                    'embedding': query_embedding,
                    'module_ids': module_ids,
                    'top_k': top_k
                })
                all_entities.extend([r['entity'] for r in result])
            except Exception as e:
                logger.warning(f"Entity search failed for {entity_type}: {e}")
        
        # Sort by score and deduplicate
        all_entities.sort(key=lambda e: e['score'], reverse=True)
        seen_ids = set()
        unique_entities = []
        for entity in all_entities:
            if entity['id'] not in seen_ids:
                seen_ids.add(entity['id'])
                unique_entities.append(entity)
        
        return unique_entities[:top_k]
    
    async def _expand_graph_within_modules(
        self,
        entity_ids: List[str],
        module_ids: List[str],
        max_hops: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Expand graph context while staying within module boundaries.
        
        Traverses relationships to find additional relevant context.
        """
        cypher = """
        UNWIND $entity_ids AS eid
        MATCH (start)
        WHERE start.id = eid
        
        // Traverse up to max_hops relationships
        CALL {
            WITH start
            MATCH path = (start)-[r*1..$max_hops]-(related)
            WHERE ALL(n IN nodes(path) WHERE n.module_id IN $module_ids OR n.module_id IS NULL)
            RETURN related, length(path) as distance
        }
        
        // Get chunks that mention these related entities
        OPTIONAL MATCH (c:Chunk)-[:CONTAINS_ENTITY]->(related)
        WHERE c.module_id IN $module_ids
        
        WITH DISTINCT c, related, distance
        WHERE c IS NOT NULL
        
        MATCH (d:Document)-[:HAS_CHUNK]->(c)
        
        RETURN {
            id: c.id,
            text: c.text,
            score: 1.0 / (1 + distance),
            document_id: d.id,
            document_title: d.title,
            module_id: c.module_id,
            related_entity: related.name
        } as chunk
        LIMIT 20
        """
        
        result = self.gm.execute_query(cypher, {
            'entity_ids': entity_ids,
            'module_ids': module_ids,
            'max_hops': max_hops
        })
        
        return [r['chunk'] for r in result]
    
    async def _find_cross_module_concepts(
        self,
        query: str,
        module_ids: List[str],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Find concepts that appear across multiple selected modules.
        
        Useful for discovering connections between different study areas.
        """
        cypher = """
        // Find entities that appear in multiple of the selected modules
        MATCH (e:Entity)
        WHERE e.module_id IN $module_ids
        
        // For each entity, count how many modules it appears in
        WITH e, e.module_id as mid
        
        // Find entities with same name across modules
        MATCH (e2:Entity)
        WHERE e2.name = e.name
        AND e2.module_id IN $module_ids
        AND e2.module_id <> e.module_id
        
        WITH e.name as concept_name, 
             collect(DISTINCT e.module_id) + collect(DISTINCT e2.module_id) as modules,
             e.definition as definition
        
        WHERE size(modules) >= 2
        
        RETURN {
            name: concept_name,
            definition: definition,
            appears_in_modules: modules,
            module_count: size(modules)
        } as cross_concept
        ORDER BY size(modules) DESC
        LIMIT 5
        """
        
        result = self.gm.execute_query(cypher, {
            'module_ids': module_ids
        })
        
        return [r['cross_concept'] for r in result]
    
    def _build_module_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        history: List[Dict],
        mode: AnswerMode,
        module_ids: List[str],
        cross_module_concepts: List[Dict] = None
    ) -> str:
        """
        Build the LLM prompt with module context.
        
        Includes module-specific framing and cross-module insights.
        """
        # Get module names for context
        module_names = self._get_module_names(module_ids)
        
        # Base system prompt
        if mode == "assistant":
            system = STRICT_SYSTEM_PROMPT
        else:
            system = TUTOR_SYSTEM_PROMPT
        
        # Add module context
        module_context = f"\n\nYou are answering questions within the context of the following study modules: {', '.join(module_names)}."
        
        # Build context section
        context_section = "### Context from Your Study Materials:\n\n"
        
        for i, chunk in enumerate(context["chunks"], 1):
            context_section += f"**[{i}] From: {chunk['document_title']}**\n"
            context_section += f"{chunk['text']}\n\n"
        
        # Add cross-module insights if present
        if cross_module_concepts:
            context_section += "\n### Cross-Module Connections:\n"
            for concept in cross_module_concepts:
                modules = ", ".join(concept["appears_in_modules"][:3])
                context_section += f"- **{concept['name']}**: Appears in {modules}\n"
            context_section += "\n"
        
        # Add entity information
        if context.get("entities"):
            context_section += "\n### Key Concepts Identified:\n"
            for entity in context["entities"][:5]:
                context_section += f"- **{entity['name']}** ({entity['type']}): {entity.get('definition', 'N/A')[:100]}\n"
        
        # Build conversation history
        history_section = ""
        if history:
            history_section = "\n### Previous Conversation:\n"
            for msg in history[-6:]:  # Last 6 messages
                role = "User" if msg["role"] == "user" else "Assistant"
                history_section += f"**{role}:** {msg['content'][:200]}...\n"
        
        # Combine all sections
        full_prompt = f"{system}{module_context}\n\n{context_section}{history_section}\n### User Question:\n{query}"
        
        return full_prompt
    
    def _get_module_names(self, module_ids: List[str]) -> List[str]:
        """Get human-readable module names."""
        cypher = """
        UNWIND $module_ids as mid
        MATCH (m:Module {id: mid})
        RETURN m.name as name
        """
        result = self.gm.execute_query(cypher, {'module_ids': module_ids})
        return [r['name'] for r in result]
    
    def _build_cache_key(
        self,
        query: str,
        module_ids: List[str],
        mode: str
    ) -> str:
        """Build a cache key for query results."""
        import hashlib
        # Sort module_ids for consistent key
        sorted_modules = sorted(module_ids)
        key_string = f"{query}:{':'.join(sorted_modules)}:{mode}"
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]
    
    def _merge_chunk_results(
        self,
        vector_chunks: List[Dict],
        fulltext_chunks: List[Dict]
    ) -> List[Dict]:
        """Merge and deduplicate chunk results from different sources."""
        seen_ids = set()
        merged = []
        
        # Prefer vector results (higher priority)
        for chunk in vector_chunks:
            if chunk['id'] not in seen_ids:
                seen_ids.add(chunk['id'])
                merged.append(chunk)
        
        # Add fulltext results that aren't duplicates
        for chunk in fulltext_chunks:
            if chunk['id'] not in seen_ids:
                seen_ids.add(chunk['id'])
                merged.append(chunk)
        
        return merged
    
    def _rank_chunks(
        self,
        chunks: List[Dict],
        query_embedding: List[float]
    ) -> List[Dict]:
        """Rank chunks by relevance score."""
        # Already have scores from search, just sort
        return sorted(chunks, key=lambda c: c.get('score', 0), reverse=True)
    
    def _format_sources(self, context: Dict[str, Any]) -> List[Dict]:
        """Format sources for response."""
        sources = []
        seen_docs = set()
        
        for chunk in context.get("chunks", []):
            doc_id = chunk.get("document_id")
            if doc_id and doc_id not in seen_docs:
                seen_docs.add(doc_id)
                sources.append({
                    "id": doc_id,
                    "title": chunk.get("document_title", "Unknown"),
                    "module_id": chunk.get("module_id")
                })
        
        return sources
```

#### Task 8.2.2: Module Query Router

**File:** `server/routers/module_chat.py`

```python
"""
AURA Module Chat Router
=======================

REST API endpoints for module-scoped chat and RAG queries.

Endpoints:
----------
POST /modules/chat           - Query across selected modules
POST /modules/{id}/chat      - Query within a single module
GET  /modules/concepts/cross - Find cross-module concepts
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from server.dependencies import RAGEngineDep, SessionManagerDep, get_current_user_id
from backend.utils.logging_config import setup_logging

logger = setup_logging("module_chat_router")
router = APIRouter(prefix="/modules", tags=["Module Chat"])


class ModuleChatRequest(BaseModel):
    """Request for module-scoped chat."""
    query: str = Field(..., min_length=1, max_length=5000)
    module_ids: List[str] = Field(..., min_items=1, max_items=20)
    session_id: Optional[str] = None
    mode: str = Field("assistant", pattern="^(assistant|tutor)$")
    enable_thinking: bool = False
    enable_cross_module: bool = False
    top_k: int = Field(10, ge=1, le=50)


class ModuleChatResponse(BaseModel):
    """Response from module-scoped chat."""
    answer: str
    sources: List[dict]
    model_used: str
    modules_searched: List[str]
    cross_module_concepts: Optional[List[dict]] = None
    thought_summary: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/chat", response_model=ModuleChatResponse)
async def chat_with_modules(
    request: ModuleChatRequest,
    rag_engine: RAGEngineDep,
    session_manager: SessionManagerDep,
    user_id: str = Depends(get_current_user_id)
):
    """
    Query the knowledge base filtered to specific modules.
    
    Retrieves context only from the selected modules and generates
    a response based on that filtered context.
    
    If session_id is provided, conversation history is included.
    If session_id is None, a new session is created.
    """
    try:
        # Create session if not provided
        session_id = request.session_id
        if not session_id:
            session = await session_manager.create_session(
                module_ids=request.module_ids,
                user_id=user_id
            )
            session_id = session.id
        
        # Execute query
        result = await rag_engine.query_with_modules(
            user_query=request.query,
            module_ids=request.module_ids,
            session_id=session_id,
            mode=request.mode,
            enable_thinking=request.enable_thinking,
            top_k=request.top_k,
            enable_cross_module=request.enable_cross_module
        )
        
        return ModuleChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            model_used=result["model_used"],
            modules_searched=result["modules_searched"],
            cross_module_concepts=result.get("cross_module_concepts"),
            thought_summary=result.get("thought_summary"),
            session_id=session_id
        )
        
    except Exception as e:
        logger.exception(f"Module chat failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/{module_id}/chat", response_model=ModuleChatResponse)
async def chat_with_single_module(
    module_id: str,
    request: ModuleChatRequest,
    rag_engine: RAGEngineDep,
    session_manager: SessionManagerDep,
    user_id: str = Depends(get_current_user_id)
):
    """
    Query within a single module.
    
    Convenience endpoint for single-module queries.
    """
    # Override module_ids with the single module
    request.module_ids = [module_id]
    
    return await chat_with_modules(
        request=request,
        rag_engine=rag_engine,
        session_manager=session_manager,
        user_id=user_id
    )


class CrossModuleConceptRequest(BaseModel):
    """Request for cross-module concept discovery."""
    module_ids: List[str] = Field(..., min_items=2, max_items=20)
    limit: int = Field(10, ge=1, le=50)


@router.post("/concepts/cross")
async def find_cross_module_concepts(
    request: CrossModuleConceptRequest,
    rag_engine: RAGEngineDep
):
    """
    Find concepts that appear across multiple modules.
    
    Useful for discovering connections between different study areas
    and identifying common themes across modules.
    """
    try:
        # Query for cross-module concepts
        cypher = """
        MATCH (e:Entity)
        WHERE e.module_id IN $module_ids
        
        WITH e.name as name, collect(DISTINCT e.module_id) as modules,
             collect(DISTINCT e.definition)[0] as definition,
             collect(DISTINCT labels(e))[0] as entity_type
        
        WHERE size(modules) >= 2
        
        // Get module names
        UNWIND modules as mid
        MATCH (m:Module {id: mid})
        
        WITH name, definition, entity_type, 
             collect({id: m.id, name: m.name}) as module_info
        
        RETURN {
            name: name,
            definition: definition,
            type: entity_type,
            modules: module_info,
            module_count: size(module_info)
        } as concept
        ORDER BY size(module_info) DESC
        LIMIT $limit
        """
        
        result = rag_engine.gm.execute_query(cypher, {
            'module_ids': request.module_ids,
            'limit': request.limit
        })
        
        return {
            "concepts": [r['concept'] for r in result],
            "modules_analyzed": request.module_ids
        }
        
    except Exception as e:
        logger.exception(f"Cross-module concept search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
```

### 8.3 Verification Checklist

| Item | Test Method | Expected Result |
|------|-------------|-----------------|
| Module-filtered search | Query with 1 module | Only module chunks returned |
| Multi-module search | Query with 3 modules | Chunks from all 3 modules |
| Cross-module concepts | Query 2+ modules | Shared concepts found |
| Entity search works | Query about concept | Entities included in context |
| Graph expansion works | Complex query | 2-hop relationships traversed |
| Cache hit | Repeat query | Faster response, cache logged |
| Session history | Multi-turn chat | Context preserved |
| Mode switching | Tutor vs assistant | Different response styles |

---

## 9. Phase 5: Study Session System

**Duration:** Week 7-8 (10 days)  
**Priority:** P0 (Critical Path)  
**Dependencies:** Phase 1, Phase 2, Phase 4 complete

### 9.1 Objectives

1. Create `SessionManager` for study session lifecycle
2. Implement persistent message history in Neo4j
3. Build session resumption and context restoration
4. Add session analytics and progress tracking
5. Create FastAPI endpoints for session management

### 9.2 Detailed Implementation

#### Task 9.2.1: SessionManager Service

**File:** `backend/session_manager.py`

```python
"""
AURA Session Manager
====================

Service for managing study sessions. Handles session lifecycle,
message history, and module context tracking.

A study session represents a focused learning interaction with
one or more modules. Sessions persist conversation history
and can be resumed later.

Usage:
    from backend.session_manager import SessionManager
    
    sm = SessionManager(graph_manager, rag_engine)
    
    # Create a session
    session = await sm.create_session(
        module_ids=["mod_123", "mod_456"],
        user_id="user_789",
        title="ML Study Session"
    )
    
    # Add messages
    await sm.add_message(session.id, "user", "What is backpropagation?")
    response = await sm.query(session.id, "What is backpropagation?")
    await sm.add_message(session.id, "assistant", response["answer"])
    
    # Resume later
    session = await sm.get_session(session.id)
    history = await sm.get_history(session.id)
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from backend.graph_manager import GraphManager
from backend.rag_engine import RAGEngine
from backend.utils.logging_config import setup_logging

logger = setup_logging("session_manager")


class SessionStatus(str, Enum):
    """Session status values."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class Message:
    """A message in a study session."""
    id: str
    session_id: str
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime
    model_used: Optional[str] = None
    sources: List[str] = field(default_factory=list)
    thinking_content: Optional[str] = None
    token_count: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        return cls(
            id=data['id'],
            session_id=data['session_id'],
            role=data['role'],
            content=data['content'],
            created_at=data.get('created_at', datetime.utcnow()),
            model_used=data.get('model_used'),
            sources=data.get('sources', []),
            thinking_content=data.get('thinking_content'),
            token_count=data.get('token_count')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'model_used': self.model_used,
            'sources': self.sources,
            'thinking_content': self.thinking_content,
            'token_count': self.token_count
        }


@dataclass
class StudySession:
    """A study session with module context."""
    id: str
    title: str
    module_ids: List[str]
    user_id: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    settings: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StudySession':
        return cls(
            id=data['id'],
            title=data['title'],
            module_ids=data.get('module_ids', []),
            user_id=data['user_id'],
            status=SessionStatus(data.get('status', 'active')),
            created_at=data.get('created_at', datetime.utcnow()),
            updated_at=data.get('updated_at', datetime.utcnow()),
            message_count=data.get('message_count', 0),
            settings=data.get('settings', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'module_ids': self.module_ids,
            'user_id': self.user_id,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            'message_count': self.message_count,
            'settings': self.settings
        }


class SessionManagerError(Exception):
    """Base exception for SessionManager errors."""
    pass


class SessionNotFoundError(SessionManagerError):
    """Raised when a session is not found."""
    pass


class SessionManager:
    """
    Manager for study sessions.
    
    Handles session creation, message history, and query execution
    with module context.
    """
    
    # Configuration
    MAX_HISTORY_FOR_CONTEXT = 10  # Messages to include in RAG context
    DEFAULT_SESSION_TITLE_LENGTH = 50
    
    def __init__(
        self,
        graph_manager: GraphManager,
        rag_engine: Optional[RAGEngine] = None
    ):
        """
        Initialize SessionManager.
        
        Args:
            graph_manager: Neo4j graph manager
            rag_engine: Optional RAG engine for query execution
        """
        self.gm = graph_manager
        self.rag = rag_engine
    
    # === SESSION LIFECYCLE ===
    
    async def create_session(
        self,
        module_ids: List[str],
        user_id: str,
        title: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> StudySession:
        """
        Create a new study session.
        
        Args:
            module_ids: Modules to include in this session
            user_id: User who owns the session
            title: Optional title (generated from modules if not provided)
            settings: Session settings (mode, model preferences, etc.)
            
        Returns:
            Created StudySession
        """
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        
        # Generate title from module names if not provided
        if not title:
            title = await self._generate_session_title(module_ids)
        
        # Create session node
        query = """
        CREATE (s:StudySession {
            id: $id,
            title: $title,
            module_ids: $module_ids,
            user_id: $user_id,
            status: 'active',
            created_at: datetime(),
            updated_at: datetime(),
            message_count: 0,
            settings: $settings
        })
        
        // Create relationships to modules
        WITH s
        UNWIND $module_ids as mid
        MATCH (m:Module {id: mid})
        MERGE (s)-[:STUDIES {added_at: datetime()}]->(m)
        
        RETURN s {.*, module_count: size($module_ids)} as session
        """
        
        result = self.gm.execute_query(query, {
            'id': session_id,
            'title': title,
            'module_ids': module_ids,
            'user_id': user_id,
            'settings': settings or {}
        })
        
        if not result:
            raise SessionManagerError("Failed to create session")
        
        logger.info(f"Created session {session_id} with {len(module_ids)} modules")
        
        return StudySession.from_dict(result[0]['session'])
    
    async def get_session(self, session_id: str) -> StudySession:
        """
        Get a session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            StudySession
            
        Raises:
            SessionNotFoundError: If session not found
        """
        query = """
        MATCH (s:StudySession {id: $session_id})
        OPTIONAL MATCH (s)-[:HAS_MESSAGE]->(m:Message)
        RETURN s {
            .*,
            message_count: count(m)
        } as session
        """
        
        result = self.gm.execute_query(query, {'session_id': session_id})
        
        if not result:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        return StudySession.from_dict(result[0]['session'])
    
    async def list_sessions(
        self,
        user_id: str,
        status: Optional[SessionStatus] = None,
        module_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[StudySession]:
        """
        List sessions for a user.
        
        Args:
            user_id: User ID
            status: Optional filter by status
            module_id: Optional filter by module
            limit: Max results
            offset: Pagination offset
            
        Returns:
            List of StudySessions
        """
        filters = ["s.user_id = $user_id"]
        params = {'user_id': user_id, 'limit': limit, 'offset': offset}
        
        if status:
            filters.append("s.status = $status")
            params['status'] = status.value
        
        if module_id:
            filters.append("$module_id IN s.module_ids")
            params['module_id'] = module_id
        
        filter_clause = " AND ".join(filters)
        
        query = f"""
        MATCH (s:StudySession)
        WHERE {filter_clause}
        OPTIONAL MATCH (s)-[:HAS_MESSAGE]->(m:Message)
        WITH s, count(m) as msg_count
        RETURN s {{
            .*,
            message_count: msg_count
        }} as session
        ORDER BY s.updated_at DESC
        SKIP $offset
        LIMIT $limit
        """
        
        result = self.gm.execute_query(query, params)
        return [StudySession.from_dict(r['session']) for r in result]
    
    async def update_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> StudySession:
        """
        Update session properties.
        
        Args:
            session_id: Session to update
            title: New title
            status: New status
            settings: Updated settings
            
        Returns:
            Updated StudySession
        """
        # Build SET clause
        set_parts = ["s.updated_at = datetime()"]
        params = {'session_id': session_id}
        
        if title is not None:
            set_parts.append("s.title = $title")
            params['title'] = title
        
        if status is not None:
            set_parts.append("s.status = $status")
            params['status'] = status.value
        
        if settings is not None:
            set_parts.append("s.settings = $settings")
            params['settings'] = settings
        
        set_clause = ", ".join(set_parts)
        
        query = f"""
        MATCH (s:StudySession {{id: $session_id}})
        SET {set_clause}
        RETURN s {{.*}} as session
        """
        
        result = self.gm.execute_query(query, params)
        
        if not result:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        return StudySession.from_dict(result[0]['session'])
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its messages.
        
        Args:
            session_id: Session to delete
            
        Returns:
            True if deleted
        """
        query = """
        MATCH (s:StudySession {id: $session_id})
        OPTIONAL MATCH (s)-[:HAS_MESSAGE]->(m:Message)
        DETACH DELETE s, m
        RETURN count(s) as deleted
        """
        
        result = self.gm.execute_query(query, {'session_id': session_id})
        deleted = result[0]['deleted'] > 0 if result else False
        
        if deleted:
            logger.info(f"Deleted session {session_id}")
        
        return deleted
    
    # === MESSAGE MANAGEMENT ===
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        model_used: Optional[str] = None,
        sources: Optional[List[str]] = None,
        thinking_content: Optional[str] = None
    ) -> Message:
        """
        Add a message to a session.
        
        Args:
            session_id: Session to add to
            role: "user" or "assistant"
            content: Message content
            model_used: Model used (for assistant messages)
            sources: Document sources (for assistant messages)
            thinking_content: Thinking/reasoning content
            
        Returns:
            Created Message
        """
        message_id = f"msg_{uuid.uuid4().hex[:12]}"
        
        # Estimate token count
        token_count = len(content.split()) * 1.3  # Rough estimate
        
        query = """
        MATCH (s:StudySession {id: $session_id})
        
        // Get current message count for ordering
        OPTIONAL MATCH (s)-[:HAS_MESSAGE]->(existing:Message)
        WITH s, count(existing) as msg_count
        
        // Create new message
        CREATE (m:Message {
            id: $msg_id,
            session_id: $session_id,
            role: $role,
            content: $content,
            created_at: datetime(),
            model_used: $model_used,
            sources: $sources,
            thinking_content: $thinking_content,
            token_count: $token_count
        })
        
        // Link to session
        CREATE (s)-[:HAS_MESSAGE {message_order: msg_count + 1}]->(m)
        
        // Update session
        SET s.updated_at = datetime(),
            s.message_count = msg_count + 1
        
        RETURN m {.*} as message
        """
        
        result = self.gm.execute_query(query, {
            'session_id': session_id,
            'msg_id': message_id,
            'role': role,
            'content': content,
            'model_used': model_used,
            'sources': sources or [],
            'thinking_content': thinking_content,
            'token_count': int(token_count)
        })
        
        if not result:
            raise SessionManagerError("Failed to add message")
        
        return Message.from_dict(result[0]['message'])
    
    async def get_history(
        self,
        session_id: str,
        limit: int = 50,
        before_message_id: Optional[str] = None
    ) -> List[Message]:
        """
        Get message history for a session.
        
        Args:
            session_id: Session ID
            limit: Max messages to return
            before_message_id: For pagination, get messages before this one
            
        Returns:
            List of Messages in chronological order
        """
        params = {'session_id': session_id, 'limit': limit}
        
        if before_message_id:
            query = """
            MATCH (s:StudySession {id: $session_id})-[:HAS_MESSAGE]->(m:Message)
            WHERE m.created_at < (
                MATCH (:Message {id: $before_id})
                RETURN m2.created_at
            )[0]
            RETURN m {.*} as message
            ORDER BY m.created_at DESC
            LIMIT $limit
            """
            params['before_id'] = before_message_id
        else:
            query = """
            MATCH (s:StudySession {id: $session_id})-[r:HAS_MESSAGE]->(m:Message)
            RETURN m {.*} as message
            ORDER BY r.message_order ASC
            LIMIT $limit
            """
        
        result = self.gm.execute_query(query, params)
        messages = [Message.from_dict(r['message']) for r in result]
        
        # Ensure chronological order
        messages.sort(key=lambda m: m.created_at)
        
        return messages
    
    async def get_session_history(
        self,
        session_id: str,
        limit: int = None
    ) -> List[Dict[str, str]]:
        """
        Get simplified history for RAG context.
        
        Returns only role and content for LLM context window.
        """
        limit = limit or self.MAX_HISTORY_FOR_CONTEXT
        messages = await self.get_history(session_id, limit=limit)
        
        return [
            {'role': m.role, 'content': m.content}
            for m in messages
        ]
    
    # === QUERY EXECUTION ===
    
    async def query(
        self,
        session_id: str,
        user_query: str,
        mode: str = "assistant",
        enable_thinking: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a query within session context.
        
        Automatically includes conversation history and session modules.
        
        Args:
            session_id: Session for context
            user_query: User's question
            mode: Response mode
            enable_thinking: Whether to include reasoning
            
        Returns:
            RAG response with answer, sources, etc.
        """
        if not self.rag:
            raise SessionManagerError("RAG engine not configured")
        
        # Get session for module context
        session = await self.get_session(session_id)
        
        # Add user message
        await self.add_message(session_id, "user", user_query)
        
        # Execute module-aware query
        result = await self.rag.query_with_modules(
            user_query=user_query,
            module_ids=session.module_ids,
            session_id=session_id,
            mode=mode,
            enable_thinking=enable_thinking
        )
        
        # Add assistant response
        await self.add_message(
            session_id=session_id,
            role="assistant",
            content=result["answer"],
            model_used=result["model_used"],
            sources=[s["id"] for s in result["sources"]],
            thinking_content=result.get("thought_summary")
        )
        
        return result
    
    # === ANALYTICS ===
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get analytics for a session.
        
        Includes message counts, topics discussed, sources used, etc.
        """
        query = """
        MATCH (s:StudySession {id: $session_id})
        OPTIONAL MATCH (s)-[:HAS_MESSAGE]->(m:Message)
        
        WITH s, 
             count(m) as total_messages,
             count(CASE WHEN m.role = 'user' THEN 1 END) as user_messages,
             count(CASE WHEN m.role = 'assistant' THEN 1 END) as assistant_messages,
             sum(m.token_count) as total_tokens,
             collect(m.sources) as all_sources
        
        // Flatten and count unique sources
        UNWIND all_sources as source_list
        UNWIND source_list as source_id
        WITH s, total_messages, user_messages, assistant_messages, total_tokens,
             collect(DISTINCT source_id) as unique_sources
        
        // Get module info
        MATCH (mod:Module)
        WHERE mod.id IN s.module_ids
        
        RETURN {
            session_id: s.id,
            title: s.title,
            status: s.status,
            created_at: s.created_at,
            updated_at: s.updated_at,
            total_messages: total_messages,
            user_messages: user_messages,
            assistant_messages: assistant_messages,
            total_tokens: total_tokens,
            unique_sources_count: size(unique_sources),
            modules: collect({id: mod.id, name: mod.name}),
            duration_minutes: duration.between(s.created_at, s.updated_at).minutes
        } as stats
        """
        
        result = self.gm.execute_query(query, {'session_id': session_id})
        
        if not result:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        return result[0]['stats']
    
    # === HELPERS ===
    
    async def _generate_session_title(self, module_ids: List[str]) -> str:
        """Generate a session title from module names."""
        query = """
        UNWIND $module_ids as mid
        MATCH (m:Module {id: mid})
        RETURN collect(m.name) as names
        """
        
        result = self.gm.execute_query(query, {'module_ids': module_ids})
        
        if result and result[0]['names']:
            names = result[0]['names']
            if len(names) == 1:
                return f"{names[0]} Study Session"
            elif len(names) == 2:
                return f"{names[0]} & {names[1]} Session"
            else:
                return f"{names[0]} + {len(names)-1} more"
        
        return f"Study Session {datetime.utcnow().strftime('%Y-%m-%d')}"
```

#### Task 9.2.2: Study Session Router

**File:** `server/routers/study_sessions.py`

```python
"""
AURA Study Session Router
=========================

REST API endpoints for study session management.

Endpoints:
----------
GET    /sessions              - List user's sessions
POST   /sessions              - Create a new session
GET    /sessions/{id}         - Get session details
PATCH  /sessions/{id}         - Update session
DELETE /sessions/{id}         - Delete session

GET    /sessions/{id}/messages      - Get message history
POST   /sessions/{id}/messages      - Add a message
POST   /sessions/{id}/query         - Execute a query

GET    /sessions/{id}/stats         - Get session analytics
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from server.dependencies import SessionManagerDep, get_current_user_id
from backend.session_manager import (
    SessionManager,
    SessionNotFoundError,
    SessionStatus,
    StudySession,
    Message
)
from backend.utils.logging_config import setup_logging

logger = setup_logging("sessions_router")
router = APIRouter(prefix="/sessions", tags=["Study Sessions"])


# === REQUEST/RESPONSE SCHEMAS ===

class SessionCreateRequest(BaseModel):
    """Request for creating a session."""
    module_ids: List[str] = Field(..., min_items=1)
    title: Optional[str] = Field(None, max_length=200)
    settings: Optional[dict] = None


class SessionUpdateRequest(BaseModel):
    """Request for updating a session."""
    title: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = Field(None, pattern="^(active|paused|completed|archived)$")
    settings: Optional[dict] = None


class SessionResponse(BaseModel):
    """Response for session data."""
    id: str
    title: str
    module_ids: List[str]
    status: str
    created_at: str
    updated_at: str
    message_count: int
    settings: dict = {}


class MessageCreateRequest(BaseModel):
    """Request for adding a message."""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=50000)
    model_used: Optional[str] = None
    sources: Optional[List[str]] = None


class MessageResponse(BaseModel):
    """Response for message data."""
    id: str
    session_id: str
    role: str
    content: str
    created_at: str
    model_used: Optional[str]
    sources: List[str]


class QueryRequest(BaseModel):
    """Request for executing a query in session."""
    query: str = Field(..., min_length=1, max_length=5000)
    mode: str = Field("assistant", pattern="^(assistant|tutor)$")
    enable_thinking: bool = False


class QueryResponse(BaseModel):
    """Response for query execution."""
    answer: str
    sources: List[dict]
    model_used: str
    modules_searched: List[str]
    thought_summary: Optional[str] = None


# === ENDPOINTS ===

@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    session_manager: SessionManagerDep,
    user_id: str = Depends(get_current_user_id),
    status: Optional[str] = Query(None, pattern="^(active|paused|completed|archived)$"),
    module_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    List study sessions for the current user.
    
    Can filter by status or module. Returns most recent first.
    """
    status_enum = SessionStatus(status) if status else None
    
    sessions = await session_manager.list_sessions(
        user_id=user_id,
        status=status_enum,
        module_id=module_id,
        limit=limit,
        offset=offset
    )
    
    return [SessionResponse(**s.to_dict()) for s in sessions]


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreateRequest,
    session_manager: SessionManagerDep,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new study session.
    
    A session provides persistent chat context for the specified modules.
    """
    session = await session_manager.create_session(
        module_ids=request.module_ids,
        user_id=user_id,
        title=request.title,
        settings=request.settings
    )
    
    return SessionResponse(**session.to_dict())


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    session_manager: SessionManagerDep
):
    """Get details for a specific session."""
    try:
        session = await session_manager.get_session(session_id)
        return SessionResponse(**session.to_dict())
    except SessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    session_manager: SessionManagerDep
):
    """Update session properties."""
    try:
        status_enum = SessionStatus(request.status) if request.status else None
        
        session = await session_manager.update_session(
            session_id=session_id,
            title=request.title,
            status=status_enum,
            settings=request.settings
        )
        
        return SessionResponse(**session.to_dict())
    except SessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )


@router.delete("/{session_id}", status_code=status.HTTP_200_OK)
async def delete_session(
    session_id: str,
    session_manager: SessionManagerDep
):
    """Delete a session and all its messages."""
    deleted = await session_manager.delete_session(session_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    
    return {"success": True, "session_id": session_id}


# === MESSAGE ENDPOINTS ===

@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: str,
    session_manager: SessionManagerDep,
    limit: int = Query(50, ge=1, le=500),
    before: Optional[str] = None
):
    """
    Get message history for a session.
    
    Returns messages in chronological order.
    Use 'before' parameter for pagination.
    """
    try:
        messages = await session_manager.get_history(
            session_id=session_id,
            limit=limit,
            before_message_id=before
        )
        
        return [MessageResponse(**m.to_dict()) for m in messages]
    except SessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )


@router.post("/{session_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    session_id: str,
    request: MessageCreateRequest,
    session_manager: SessionManagerDep
):
    """
    Add a message to the session history.
    
    Typically used for manual message insertion or correction.
    For normal chat, use the /query endpoint instead.
    """
    try:
        message = await session_manager.add_message(
            session_id=session_id,
            role=request.role,
            content=request.content,
            model_used=request.model_used,
            sources=request.sources
        )
        
        return MessageResponse(**message.to_dict())
    except SessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )


# === QUERY ENDPOINT ===

@router.post("/{session_id}/query", response_model=QueryResponse)
async def query_session(
    session_id: str,
    request: QueryRequest,
    session_manager: SessionManagerDep
):
    """
    Execute a query within session context.
    
    Automatically includes conversation history and module context.
    Adds both user question and assistant response to history.
    """
    try:
        result = await session_manager.query(
            session_id=session_id,
            user_query=request.query,
            mode=request.mode,
            enable_thinking=request.enable_thinking
        )
        
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            model_used=result["model_used"],
            modules_searched=result["modules_searched"],
            thought_summary=result.get("thought_summary")
        )
        
    except SessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    except Exception as e:
        logger.exception(f"Query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


# === ANALYTICS ENDPOINT ===

@router.get("/{session_id}/stats")
async def get_session_stats(
    session_id: str,
    session_manager: SessionManagerDep
):
    """
    Get analytics for a session.
    
    Includes message counts, duration, sources used, etc.
    """
    try:
        stats = await session_manager.get_session_stats(session_id)
        return stats
    except SessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
```

### 9.3 Verification Checklist

| Item | Test Method | Expected Result |
|------|-------------|-----------------|
| Create session | POST /sessions | 201 with session data |
| Session has modules | GET /sessions/{id} | module_ids populated |
| Add messages | POST /sessions/{id}/messages | Message created |
| Query with context | POST /sessions/{id}/query | History in response |
| Message ordering | GET /sessions/{id}/messages | Chronological order |
| Session stats | GET /sessions/{id}/stats | Analytics returned |
| Resume session | GET then query | Context preserved |
| Delete session | DELETE /sessions/{id} | Session and messages gone |

---

## 10. Phase 6: Frontend Implementation

**Duration:** Week 8-10 (15 days)  
**Priority:** P0 (Critical Path)  
**Dependencies:** Phase 2, Phase 4, Phase 5 complete

### 10.1 Objectives

1. Create module management UI components
2. Build study session interface with module context
3. Implement module-filtered chat with real-time responses
4. Add cross-module concept visualization
5. Integrate with TanStack Query for server state

### 10.2 Component Architecture

```
frontend/src/
├── features/
│   └── modules/
│       ├── components/
│       │   ├── ModuleBrowser.tsx        # Main module list view
│       │   ├── ModuleCard.tsx           # Individual module card
│       │   ├── ModuleCreateDialog.tsx   # Create/edit modal
│       │   ├── ModuleSelector.tsx       # Multi-select dropdown
│       │   ├── ModuleDocuments.tsx      # Documents in module
│       │   └── ModuleStats.tsx          # Statistics display
│       ├── hooks/
│       │   ├── useModules.ts            # TanStack Query hooks
│       │   ├── useModuleMutations.ts    # Create/Update/Delete
│       │   └── useModuleDocuments.ts    # Document assignment
│       ├── api/
│       │   └── modulesApi.ts            # API client functions
│       ├── types/
│       │   └── module.types.ts          # TypeScript interfaces
│       └── index.ts                     # Public exports
│
├── features/
│   └── study-sessions/
│       ├── components/
│       │   ├── StudySession.tsx         # Main session container
│       │   ├── SessionSidebar.tsx       # Session history sidebar
│       │   ├── SessionChat.tsx          # Chat interface
│       │   ├── SessionHeader.tsx        # Module context header
│       │   └── MessageList.tsx          # Message history
│       ├── hooks/
│       │   ├── useStudySession.ts       # Session management
│       │   ├── useSessionMessages.ts    # Message history
│       │   └── useSessionQuery.ts       # Query execution
│       ├── api/
│       │   └── sessionsApi.ts           # API client
│       └── types/
│           └── session.types.ts         # TypeScript interfaces
│
├── stores/
│   ├── moduleStore.ts                   # Zustand: module selection state
│   └── sessionStore.ts                  # Zustand: active session state
│
└── components/
    └── ui/                              # Shared UI components
        ├── Dialog.tsx
        ├── Dropdown.tsx
        ├── Badge.tsx
        └── LoadingSpinner.tsx
```

### 10.3 Detailed Implementation

#### Task 10.3.1: TypeScript Types

**File:** `frontend/src/features/modules/types/module.types.ts`

```typescript
/**
 * Module Types
 * ============
 * Type definitions for module management feature.
 */

export interface Module {
  id: string;
  name: string;
  description: string;
  color: string;
  icon: string;
  createdAt: string;
  updatedAt: string;
  documentCount: number;
  entityCount: number;
  isArchived: boolean;
}

export interface ModuleCreateInput {
  name: string;
  description?: string;
  color?: string;
  icon?: string;
}

export interface ModuleUpdateInput {
  name?: string;
  description?: string;
  color?: string;
  icon?: string;
  isArchived?: boolean;
}

export interface ModuleListResponse {
  modules: Module[];
  total: number;
}

export interface ModuleStats {
  moduleId: string;
  moduleName: string;
  documentCount: number;
  chunkCount: number;
  entityCount: number;
  topicCount: number;
  conceptCount: number;
  relationshipCount: number;
  totalTokens: number;
  lastUpdated: string;
}

export interface ModuleDocument {
  id: string;
  title: string;
  originalFilename: string;
  fileType: string;
  uploadDate: string;
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed';
  chunkCount: number;
  entityCount: number;
}

export interface DocumentAssignRequest {
  documentIds: string[];
}

export interface DocumentAssignResponse {
  moduleId: string;
  total: number;
  successful: number;
  failed: number;
  failures: Array<{ documentId: string; error: string }>;
}

export interface ModuleFilters {
  includeArchived?: boolean;
  search?: string;
}

// Color palette for modules
export const MODULE_COLORS = [
  '#4A90D9', // Blue
  '#50C878', // Green
  '#FF6B6B', // Red
  '#FFB347', // Orange
  '#9B59B6', // Purple
  '#3498DB', // Light Blue
  '#E74C3C', // Crimson
  '#2ECC71', // Emerald
  '#F39C12', // Gold
  '#1ABC9C', // Teal
] as const;

// Icon options for modules
export const MODULE_ICONS = [
  'folder',
  'book',
  'brain',
  'graduation-cap',
  'flask',
  'code',
  'chart-line',
  'lightbulb',
  'puzzle-piece',
  'atom',
] as const;
```

**File:** `frontend/src/features/study-sessions/types/session.types.ts`

```typescript
/**
 * Study Session Types
 * ===================
 * Type definitions for study session feature.
 */

export type SessionStatus = 'active' | 'paused' | 'completed' | 'archived';

export interface StudySession {
  id: string;
  title: string;
  moduleIds: string[];
  status: SessionStatus;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
  settings: SessionSettings;
}

export interface SessionSettings {
  mode?: 'assistant' | 'tutor';
  enableThinking?: boolean;
  topK?: number;
}

export interface SessionCreateInput {
  moduleIds: string[];
  title?: string;
  settings?: SessionSettings;
}

export interface SessionUpdateInput {
  title?: string;
  status?: SessionStatus;
  settings?: SessionSettings;
}

export interface Message {
  id: string;
  sessionId: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
  modelUsed?: string;
  sources: string[];
  thinkingContent?: string;
  tokenCount?: number;
}

export interface MessageCreateInput {
  role: 'user' | 'assistant';
  content: string;
  modelUsed?: string;
  sources?: string[];
}

export interface QueryRequest {
  query: string;
  mode?: 'assistant' | 'tutor';
  enableThinking?: boolean;
}

export interface QueryResponse {
  answer: string;
  sources: SourceInfo[];
  modelUsed: string;
  modulesSearched: string[];
  crossModuleConcepts?: CrossModuleConcept[];
  thoughtSummary?: string;
}

export interface SourceInfo {
  id: string;
  title: string;
  moduleId: string;
}

export interface CrossModuleConcept {
  name: string;
  definition: string;
  modules: Array<{ id: string; name: string }>;
  moduleCount: number;
}

export interface SessionStats {
  sessionId: string;
  title: string;
  status: SessionStatus;
  createdAt: string;
  updatedAt: string;
  totalMessages: number;
  userMessages: number;
  assistantMessages: number;
  totalTokens: number;
  uniqueSourcesCount: number;
  modules: Array<{ id: string; name: string }>;
  durationMinutes: number;
}
```

#### Task 10.3.2: API Client Functions

**File:** `frontend/src/features/modules/api/modulesApi.ts`

```typescript
/**
 * Modules API Client
 * ==================
 * HTTP client functions for module management.
 */

import { apiClient } from '@/api/client';
import type {
  Module,
  ModuleCreateInput,
  ModuleUpdateInput,
  ModuleListResponse,
  ModuleStats,
  ModuleDocument,
  DocumentAssignRequest,
  DocumentAssignResponse,
  ModuleFilters,
} from '../types/module.types';

const BASE_URL = '/api/modules';

export const modulesApi = {
  /**
   * List all modules for current user.
   */
  async getModules(filters?: ModuleFilters): Promise<ModuleListResponse> {
    const params = new URLSearchParams();
    if (filters?.includeArchived) {
      params.set('include_archived', 'true');
    }
    
    const response = await apiClient.get<ModuleListResponse>(
      `${BASE_URL}?${params.toString()}`
    );
    return response.data;
  },

  /**
   * Get a single module by ID.
   */
  async getModule(moduleId: string): Promise<Module> {
    const response = await apiClient.get<Module>(`${BASE_URL}/${moduleId}`);
    return response.data;
  },

  /**
   * Create a new module.
   */
  async createModule(input: ModuleCreateInput): Promise<Module> {
    const response = await apiClient.post<Module>(BASE_URL, input);
    return response.data;
  },

  /**
   * Update a module.
   */
  async updateModule(moduleId: string, input: ModuleUpdateInput): Promise<Module> {
    const response = await apiClient.patch<Module>(
      `${BASE_URL}/${moduleId}`,
      input
    );
    return response.data;
  },

  /**
   * Delete a module.
   */
  async deleteModule(moduleId: string, reassignTo = 'unassigned'): Promise<void> {
    await apiClient.delete(`${BASE_URL}/${moduleId}?reassign_to=${reassignTo}`);
  },

  /**
   * Get documents in a module.
   */
  async getModuleDocuments(
    moduleId: string,
    limit = 100,
    offset = 0
  ): Promise<{ documents: ModuleDocument[]; total: number }> {
    const response = await apiClient.get(
      `${BASE_URL}/${moduleId}/documents?limit=${limit}&offset=${offset}`
    );
    return response.data;
  },

  /**
   * Assign documents to a module.
   */
  async assignDocuments(
    moduleId: string,
    documentIds: string[]
  ): Promise<DocumentAssignResponse> {
    const response = await apiClient.post<DocumentAssignResponse>(
      `${BASE_URL}/${moduleId}/documents`,
      { document_ids: documentIds }
    );
    return response.data;
  },

  /**
   * Remove a document from a module.
   */
  async removeDocument(
    moduleId: string,
    documentId: string,
    reassignTo = 'unassigned'
  ): Promise<void> {
    await apiClient.delete(
      `${BASE_URL}/${moduleId}/documents/${documentId}?reassign_to=${reassignTo}`
    );
  },

  /**
   * Get module statistics.
   */
  async getModuleStats(moduleId: string): Promise<ModuleStats> {
    const response = await apiClient.get<ModuleStats>(
      `${BASE_URL}/${moduleId}/stats`
    );
    return response.data;
  },
};
```

**File:** `frontend/src/features/study-sessions/api/sessionsApi.ts`

```typescript
/**
 * Study Sessions API Client
 * =========================
 * HTTP client functions for study session management.
 */

import { apiClient } from '@/api/client';
import type {
  StudySession,
  SessionCreateInput,
  SessionUpdateInput,
  Message,
  MessageCreateInput,
  QueryRequest,
  QueryResponse,
  SessionStats,
  SessionStatus,
} from '../types/session.types';

const BASE_URL = '/api/sessions';

export const sessionsApi = {
  /**
   * List sessions for current user.
   */
  async getSessions(filters?: {
    status?: SessionStatus;
    moduleId?: string;
    limit?: number;
    offset?: number;
  }): Promise<StudySession[]> {
    const params = new URLSearchParams();
    if (filters?.status) params.set('status', filters.status);
    if (filters?.moduleId) params.set('module_id', filters.moduleId);
    if (filters?.limit) params.set('limit', String(filters.limit));
    if (filters?.offset) params.set('offset', String(filters.offset));
    
    const response = await apiClient.get<StudySession[]>(
      `${BASE_URL}?${params.toString()}`
    );
    return response.data;
  },

  /**
   * Get a session by ID.
   */
  async getSession(sessionId: string): Promise<StudySession> {
    const response = await apiClient.get<StudySession>(
      `${BASE_URL}/${sessionId}`
    );
    return response.data;
  },

  /**
   * Create a new session.
   */
  async createSession(input: SessionCreateInput): Promise<StudySession> {
    const response = await apiClient.post<StudySession>(BASE_URL, {
      module_ids: input.moduleIds,
      title: input.title,
      settings: input.settings,
    });
    return response.data;
  },

  /**
   * Update a session.
   */
  async updateSession(
    sessionId: string,
    input: SessionUpdateInput
  ): Promise<StudySession> {
    const response = await apiClient.patch<StudySession>(
      `${BASE_URL}/${sessionId}`,
      input
    );
    return response.data;
  },

  /**
   * Delete a session.
   */
  async deleteSession(sessionId: string): Promise<void> {
    await apiClient.delete(`${BASE_URL}/${sessionId}`);
  },

  /**
   * Get message history for a session.
   */
  async getMessages(
    sessionId: string,
    limit = 50,
    before?: string
  ): Promise<Message[]> {
    const params = new URLSearchParams();
    params.set('limit', String(limit));
    if (before) params.set('before', before);
    
    const response = await apiClient.get<Message[]>(
      `${BASE_URL}/${sessionId}/messages?${params.toString()}`
    );
    return response.data;
  },

  /**
   * Add a message to a session.
   */
  async addMessage(
    sessionId: string,
    input: MessageCreateInput
  ): Promise<Message> {
    const response = await apiClient.post<Message>(
      `${BASE_URL}/${sessionId}/messages`,
      input
    );
    return response.data;
  },

  /**
   * Execute a query in session context.
   */
  async query(sessionId: string, request: QueryRequest): Promise<QueryResponse> {
    const response = await apiClient.post<QueryResponse>(
      `${BASE_URL}/${sessionId}/query`,
      {
        query: request.query,
        mode: request.mode || 'assistant',
        enable_thinking: request.enableThinking || false,
      }
    );
    return response.data;
  },

  /**
   * Get session statistics.
   */
  async getSessionStats(sessionId: string): Promise<SessionStats> {
    const response = await apiClient.get<SessionStats>(
      `${BASE_URL}/${sessionId}/stats`
    );
    return response.data;
  },
};
```

#### Task 10.3.3: TanStack Query Hooks

**File:** `frontend/src/features/modules/hooks/useModules.ts`

```typescript
/**
 * Module Query Hooks
 * ==================
 * TanStack Query hooks for module data fetching and caching.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { modulesApi } from '../api/modulesApi';
import type {
  Module,
  ModuleCreateInput,
  ModuleUpdateInput,
  ModuleFilters,
  ModuleStats,
} from '../types/module.types';

// Query key factory for type-safe, consistent keys
export const moduleKeys = {
  all: ['modules'] as const,
  lists: () => [...moduleKeys.all, 'list'] as const,
  list: (filters?: ModuleFilters) => [...moduleKeys.lists(), filters] as const,
  details: () => [...moduleKeys.all, 'detail'] as const,
  detail: (id: string) => [...moduleKeys.details(), id] as const,
  stats: (id: string) => [...moduleKeys.all, 'stats', id] as const,
  documents: (id: string) => [...moduleKeys.all, 'documents', id] as const,
};

/**
 * Fetch all modules with optional filters.
 */
export function useModules(filters?: ModuleFilters) {
  return useQuery({
    queryKey: moduleKeys.list(filters),
    queryFn: () => modulesApi.getModules(filters),
    staleTime: 30_000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Fetch a single module by ID.
 */
export function useModule(moduleId: string) {
  return useQuery({
    queryKey: moduleKeys.detail(moduleId),
    queryFn: () => modulesApi.getModule(moduleId),
    enabled: !!moduleId,
  });
}

/**
 * Fetch module statistics.
 */
export function useModuleStats(moduleId: string) {
  return useQuery({
    queryKey: moduleKeys.stats(moduleId),
    queryFn: () => modulesApi.getModuleStats(moduleId),
    enabled: !!moduleId,
    staleTime: 60_000, // 1 minute
  });
}

/**
 * Fetch documents in a module.
 */
export function useModuleDocuments(moduleId: string, limit = 100) {
  return useQuery({
    queryKey: moduleKeys.documents(moduleId),
    queryFn: () => modulesApi.getModuleDocuments(moduleId, limit),
    enabled: !!moduleId,
  });
}

/**
 * Create module mutation.
 */
export function useCreateModule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: ModuleCreateInput) => modulesApi.createModule(input),
    onSuccess: (newModule) => {
      // Invalidate module lists to refetch
      queryClient.invalidateQueries({ queryKey: moduleKeys.lists() });
      
      // Optionally add to cache immediately
      queryClient.setQueryData(
        moduleKeys.detail(newModule.id),
        newModule
      );
    },
  });
}

/**
 * Update module mutation with optimistic update.
 */
export function useUpdateModule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: ModuleUpdateInput }) =>
      modulesApi.updateModule(id, input),

    onMutate: async ({ id, input }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: moduleKeys.detail(id) });

      // Snapshot previous value
      const previousModule = queryClient.getQueryData<Module>(
        moduleKeys.detail(id)
      );

      // Optimistically update
      if (previousModule) {
        queryClient.setQueryData<Module>(moduleKeys.detail(id), {
          ...previousModule,
          ...input,
          updatedAt: new Date().toISOString(),
        });
      }

      return { previousModule };
    },

    onError: (err, { id }, context) => {
      // Rollback on error
      if (context?.previousModule) {
        queryClient.setQueryData(moduleKeys.detail(id), context.previousModule);
      }
    },

    onSettled: (_, __, { id }) => {
      // Refetch after mutation
      queryClient.invalidateQueries({ queryKey: moduleKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: moduleKeys.lists() });
    },
  });
}

/**
 * Delete module mutation.
 */
export function useDeleteModule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (moduleId: string) => modulesApi.deleteModule(moduleId),
    onSuccess: (_, moduleId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: moduleKeys.detail(moduleId) });
      // Refetch lists
      queryClient.invalidateQueries({ queryKey: moduleKeys.lists() });
    },
  });
}

/**
 * Assign documents to module mutation.
 */
export function useAssignDocuments() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      moduleId,
      documentIds,
    }: {
      moduleId: string;
      documentIds: string[];
    }) => modulesApi.assignDocuments(moduleId, documentIds),
    
    onSuccess: (_, { moduleId }) => {
      // Invalidate module documents and stats
      queryClient.invalidateQueries({ queryKey: moduleKeys.documents(moduleId) });
      queryClient.invalidateQueries({ queryKey: moduleKeys.stats(moduleId) });
      queryClient.invalidateQueries({ queryKey: moduleKeys.detail(moduleId) });
    },
  });
}
```

**File:** `frontend/src/features/study-sessions/hooks/useStudySession.ts`

```typescript
/**
 * Study Session Query Hooks
 * =========================
 * TanStack Query hooks for study session management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sessionsApi } from '../api/sessionsApi';
import type {
  StudySession,
  SessionCreateInput,
  SessionUpdateInput,
  Message,
  QueryRequest,
  SessionStatus,
} from '../types/session.types';

// Query key factory
export const sessionKeys = {
  all: ['sessions'] as const,
  lists: () => [...sessionKeys.all, 'list'] as const,
  list: (filters?: { status?: SessionStatus; moduleId?: string }) =>
    [...sessionKeys.lists(), filters] as const,
  details: () => [...sessionKeys.all, 'detail'] as const,
  detail: (id: string) => [...sessionKeys.details(), id] as const,
  messages: (id: string) => [...sessionKeys.all, 'messages', id] as const,
  stats: (id: string) => [...sessionKeys.all, 'stats', id] as const,
};

/**
 * Fetch sessions with optional filters.
 */
export function useSessions(filters?: {
  status?: SessionStatus;
  moduleId?: string;
}) {
  return useQuery({
    queryKey: sessionKeys.list(filters),
    queryFn: () => sessionsApi.getSessions(filters),
    staleTime: 30_000,
  });
}

/**
 * Fetch a single session.
 */
export function useSession(sessionId: string) {
  return useQuery({
    queryKey: sessionKeys.detail(sessionId),
    queryFn: () => sessionsApi.getSession(sessionId),
    enabled: !!sessionId,
  });
}

/**
 * Fetch session messages.
 */
export function useSessionMessages(sessionId: string, limit = 50) {
  return useQuery({
    queryKey: sessionKeys.messages(sessionId),
    queryFn: () => sessionsApi.getMessages(sessionId, limit),
    enabled: !!sessionId,
    refetchInterval: false, // Manual refetch after sending
  });
}

/**
 * Fetch session statistics.
 */
export function useSessionStats(sessionId: string) {
  return useQuery({
    queryKey: sessionKeys.stats(sessionId),
    queryFn: () => sessionsApi.getSessionStats(sessionId),
    enabled: !!sessionId,
  });
}

/**
 * Create session mutation.
 */
export function useCreateSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: SessionCreateInput) => sessionsApi.createSession(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sessionKeys.lists() });
    },
  });
}

/**
 * Update session mutation.
 */
export function useUpdateSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      sessionId,
      input,
    }: {
      sessionId: string;
      input: SessionUpdateInput;
    }) => sessionsApi.updateSession(sessionId, input),
    
    onSuccess: (_, { sessionId }) => {
      queryClient.invalidateQueries({ queryKey: sessionKeys.detail(sessionId) });
      queryClient.invalidateQueries({ queryKey: sessionKeys.lists() });
    },
  });
}

/**
 * Delete session mutation.
 */
export function useDeleteSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sessionId: string) => sessionsApi.deleteSession(sessionId),
    onSuccess: (_, sessionId) => {
      queryClient.removeQueries({ queryKey: sessionKeys.detail(sessionId) });
      queryClient.invalidateQueries({ queryKey: sessionKeys.lists() });
    },
  });
}

/**
 * Send query mutation.
 * Handles optimistic UI update for chat interface.
 */
export function useSendQuery() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      sessionId,
      request,
    }: {
      sessionId: string;
      request: QueryRequest;
    }) => sessionsApi.query(sessionId, request),

    onMutate: async ({ sessionId, request }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({
        queryKey: sessionKeys.messages(sessionId),
      });

      // Snapshot previous messages
      const previousMessages = queryClient.getQueryData<Message[]>(
        sessionKeys.messages(sessionId)
      );

      // Optimistically add user message
      const optimisticUserMessage: Message = {
        id: `temp-${Date.now()}`,
        sessionId,
        role: 'user',
        content: request.query,
        createdAt: new Date().toISOString(),
        sources: [],
      };

      queryClient.setQueryData<Message[]>(
        sessionKeys.messages(sessionId),
        (old) => [...(old || []), optimisticUserMessage]
      );

      return { previousMessages, optimisticUserMessage };
    },

    onSuccess: (response, { sessionId }, context) => {
      // Add assistant response to messages
      const assistantMessage: Message = {
        id: `msg-${Date.now()}`,
        sessionId,
        role: 'assistant',
        content: response.answer,
        createdAt: new Date().toISOString(),
        modelUsed: response.modelUsed,
        sources: response.sources.map((s) => s.id),
      };

      queryClient.setQueryData<Message[]>(
        sessionKeys.messages(sessionId),
        (old) => [...(old || []), assistantMessage]
      );

      // Update session (message count changed)
      queryClient.invalidateQueries({
        queryKey: sessionKeys.detail(sessionId),
      });
    },

    onError: (err, { sessionId }, context) => {
      // Rollback optimistic update
      if (context?.previousMessages) {
        queryClient.setQueryData(
          sessionKeys.messages(sessionId),
          context.previousMessages
        );
      }
    },
  });
}
```

#### Task 10.3.4: Zustand Stores

**File:** `frontend/src/stores/moduleStore.ts`

```typescript
/**
 * Module Store
 * ============
 * Zustand store for module selection and UI state.
 * Server data is managed by TanStack Query - this is for UI state only.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface ModuleState {
  // Selected modules for current study session
  selectedModuleIds: string[];
  
  // UI state
  sidebarCollapsed: boolean;
  viewMode: 'grid' | 'list';
  showArchived: boolean;
  searchQuery: string;
  
  // Actions
  selectModule: (moduleId: string) => void;
  deselectModule: (moduleId: string) => void;
  toggleModule: (moduleId: string) => void;
  setSelectedModules: (moduleIds: string[]) => void;
  clearSelection: () => void;
  
  // UI actions
  toggleSidebar: () => void;
  setViewMode: (mode: 'grid' | 'list') => void;
  setShowArchived: (show: boolean) => void;
  setSearchQuery: (query: string) => void;
}

export const useModuleStore = create<ModuleState>()(
  persist(
    (set, get) => ({
      // Initial state
      selectedModuleIds: [],
      sidebarCollapsed: false,
      viewMode: 'grid',
      showArchived: false,
      searchQuery: '',

      // Selection actions
      selectModule: (moduleId) =>
        set((state) => ({
          selectedModuleIds: state.selectedModuleIds.includes(moduleId)
            ? state.selectedModuleIds
            : [...state.selectedModuleIds, moduleId],
        })),

      deselectModule: (moduleId) =>
        set((state) => ({
          selectedModuleIds: state.selectedModuleIds.filter(
            (id) => id !== moduleId
          ),
        })),

      toggleModule: (moduleId) =>
        set((state) => ({
          selectedModuleIds: state.selectedModuleIds.includes(moduleId)
            ? state.selectedModuleIds.filter((id) => id !== moduleId)
            : [...state.selectedModuleIds, moduleId],
        })),

      setSelectedModules: (moduleIds) =>
        set({ selectedModuleIds: moduleIds }),

      clearSelection: () =>
        set({ selectedModuleIds: [] }),

      // UI actions
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      setViewMode: (mode) =>
        set({ viewMode: mode }),

      setShowArchived: (show) =>
        set({ showArchived: show }),

      setSearchQuery: (query) =>
        set({ searchQuery: query }),
    }),
    {
      name: 'aura-module-store',
      storage: createJSONStorage(() => localStorage),
      // Only persist these fields
      partialize: (state) => ({
        selectedModuleIds: state.selectedModuleIds,
        sidebarCollapsed: state.sidebarCollapsed,
        viewMode: state.viewMode,
      }),
    }
  )
);

// Selector hooks for better performance
export const useSelectedModules = () =>
  useModuleStore((state) => state.selectedModuleIds);

export const useModuleSelection = () =>
  useModuleStore((state) => ({
    selectedModuleIds: state.selectedModuleIds,
    selectModule: state.selectModule,
    deselectModule: state.deselectModule,
    toggleModule: state.toggleModule,
    clearSelection: state.clearSelection,
  }));
```

**File:** `frontend/src/stores/sessionStore.ts`

```typescript
/**
 * Session Store
 * =============
 * Zustand store for active session state.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface SessionState {
  // Active session
  activeSessionId: string | null;
  
  // Chat UI state
  inputValue: string;
  isThinkingEnabled: boolean;
  responseMode: 'assistant' | 'tutor';
  
  // Actions
  setActiveSession: (sessionId: string | null) => void;
  setInputValue: (value: string) => void;
  clearInput: () => void;
  toggleThinking: () => void;
  setResponseMode: (mode: 'assistant' | 'tutor') => void;
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      activeSessionId: null,
      inputValue: '',
      isThinkingEnabled: false,
      responseMode: 'assistant',

      setActiveSession: (sessionId) =>
        set({ activeSessionId: sessionId }),

      setInputValue: (value) =>
        set({ inputValue: value }),

      clearInput: () =>
        set({ inputValue: '' }),

      toggleThinking: () =>
        set((state) => ({ isThinkingEnabled: !state.isThinkingEnabled })),

      setResponseMode: (mode) =>
        set({ responseMode: mode }),
    }),
    {
      name: 'aura-session-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        isThinkingEnabled: state.isThinkingEnabled,
        responseMode: state.responseMode,
      }),
    }
  )
);
```

#### Task 10.3.5: UI Components

**File:** `frontend/src/features/modules/components/ModuleBrowser.tsx`

```typescript
/**
 * ModuleBrowser Component
 * =======================
 * Main module management interface.
 */

import React, { useState } from 'react';
import { useModules, useCreateModule, useDeleteModule } from '../hooks/useModules';
import { useModuleStore } from '@/stores/moduleStore';
import { ModuleCard } from './ModuleCard';
import { ModuleCreateDialog } from './ModuleCreateDialog';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { ModuleCreateInput } from '../types/module.types';

export function ModuleBrowser() {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  
  // Zustand UI state
  const { viewMode, showArchived, searchQuery, setSearchQuery } = useModuleStore();
  
  // TanStack Query data
  const { data, isLoading, error } = useModules({
    includeArchived: showArchived,
  });
  
  const createModule = useCreateModule();
  const deleteModule = useDeleteModule();

  // Filter modules by search
  const filteredModules = React.useMemo(() => {
    if (!data?.modules) return [];
    if (!searchQuery) return data.modules;
    
    const query = searchQuery.toLowerCase();
    return data.modules.filter(
      (m) =>
        m.name.toLowerCase().includes(query) ||
        m.description.toLowerCase().includes(query)
    );
  }, [data?.modules, searchQuery]);

  const handleCreate = async (input: ModuleCreateInput) => {
    await createModule.mutateAsync(input);
    setIsCreateOpen(false);
  };

  const handleDelete = async (moduleId: string) => {
    if (confirm('Are you sure you want to delete this module?')) {
      await deleteModule.mutateAsync(moduleId);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-500 p-4">
        Failed to load modules: {error.message}
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Study Modules</h1>
        <button
          onClick={() => setIsCreateOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 
                     transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Create Module
        </button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search modules..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full max-w-md px-4 py-2 border rounded-lg focus:ring-2 
                     focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Module Grid/List */}
      {filteredModules.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          {searchQuery
            ? 'No modules match your search.'
            : 'No modules yet. Create your first module to get started!'}
        </div>
      ) : (
        <div
          className={
            viewMode === 'grid'
              ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4'
              : 'flex flex-col gap-3'
          }
        >
          {filteredModules.map((module) => (
            <ModuleCard
              key={module.id}
              module={module}
              viewMode={viewMode}
              onDelete={() => handleDelete(module.id)}
            />
          ))}
        </div>
      )}

      {/* Create Dialog */}
      <ModuleCreateDialog
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onCreate={handleCreate}
        isLoading={createModule.isPending}
      />
    </div>
  );
}
```

**File:** `frontend/src/features/modules/components/ModuleCard.tsx`

```typescript
/**
 * ModuleCard Component
 * ====================
 * Card display for a single module.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { useModuleSelection } from '@/stores/moduleStore';
import type { Module } from '../types/module.types';

interface ModuleCardProps {
  module: Module;
  viewMode: 'grid' | 'list';
  onDelete: () => void;
}

export function ModuleCard({ module, viewMode, onDelete }: ModuleCardProps) {
  const { selectedModuleIds, toggleModule } = useModuleSelection();
  const isSelected = selectedModuleIds.includes(module.id);

  const handleSelect = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    toggleModule(module.id);
  };

  if (viewMode === 'list') {
    return (
      <div
        className={`flex items-center gap-4 p-4 bg-white rounded-lg border 
                    transition-all hover:shadow-md ${
                      isSelected ? 'ring-2 ring-blue-500 border-blue-500' : ''
                    }`}
      >
        {/* Color indicator */}
        <div
          className="w-3 h-12 rounded-full"
          style={{ backgroundColor: module.color }}
        />

        {/* Content */}
        <div className="flex-1 min-w-0">
          <Link
            to={`/modules/${module.id}`}
            className="text-lg font-semibold hover:text-blue-600 truncate block"
          >
            {module.name}
          </Link>
          <p className="text-sm text-gray-500 truncate">{module.description}</p>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span>{module.documentCount} docs</span>
          <span>{module.entityCount} concepts</span>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleSelect}
            className={`p-2 rounded-lg transition-colors ${
              isSelected
                ? 'bg-blue-100 text-blue-600'
                : 'hover:bg-gray-100 text-gray-400'
            }`}
            title={isSelected ? 'Deselect' : 'Select for study'}
          >
            <svg className="w-5 h-5" fill={isSelected ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </button>
          <button
            onClick={onDelete}
            className="p-2 rounded-lg hover:bg-red-100 text-gray-400 hover:text-red-600 transition-colors"
            title="Delete module"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    );
  }

  // Grid view
  return (
    <div
      className={`relative p-4 bg-white rounded-lg border transition-all 
                  hover:shadow-md cursor-pointer ${
                    isSelected ? 'ring-2 ring-blue-500 border-blue-500' : ''
                  }`}
      onClick={handleSelect}
    >
      {/* Selection indicator */}
      {isSelected && (
        <div className="absolute top-2 right-2 w-6 h-6 bg-blue-600 rounded-full 
                        flex items-center justify-center">
          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      )}

      {/* Color bar */}
      <div
        className="h-2 rounded-full mb-3"
        style={{ backgroundColor: module.color }}
      />

      {/* Content */}
      <Link
        to={`/modules/${module.id}`}
        onClick={(e) => e.stopPropagation()}
        className="block"
      >
        <h3 className="text-lg font-semibold mb-1 hover:text-blue-600">
          {module.name}
        </h3>
      </Link>
      <p className="text-sm text-gray-500 mb-3 line-clamp-2">
        {module.description || 'No description'}
      </p>

      {/* Stats */}
      <div className="flex items-center gap-3 text-xs text-gray-400">
        <span className="flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {module.documentCount}
        </span>
        <span className="flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          {module.entityCount}
        </span>
      </div>

      {/* Delete button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        className="absolute bottom-2 right-2 p-1.5 rounded hover:bg-red-100 
                   text-gray-400 hover:text-red-600 opacity-0 group-hover:opacity-100 
                   transition-all"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
    </div>
  );
}
```

**File:** `frontend/src/features/study-sessions/components/StudySession.tsx`

```typescript
/**
 * StudySession Component
 * ======================
 * Main study session interface with chat.
 */

import React, { useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import {
  useSession,
  useSessionMessages,
  useSendQuery,
} from '../hooks/useStudySession';
import { useSessionStore } from '@/stores/sessionStore';
import { useModules } from '@/features/modules/hooks/useModules';
import { SessionHeader } from './SessionHeader';
import { MessageList } from './MessageList';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export function StudySession() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  // Store state
  const {
    inputValue,
    setInputValue,
    clearInput,
    isThinkingEnabled,
    responseMode,
  } = useSessionStore();
  
  // Queries
  const { data: session, isLoading: sessionLoading } = useSession(sessionId!);
  const { data: messages, isLoading: messagesLoading } = useSessionMessages(sessionId!);
  const { data: modulesData } = useModules();
  
  // Mutations
  const sendQuery = useSendQuery();

  // Auto-focus input
  useEffect(() => {
    inputRef.current?.focus();
  }, [sessionId]);

  // Get module details for session
  const sessionModules = React.useMemo(() => {
    if (!session?.moduleIds || !modulesData?.modules) return [];
    return modulesData.modules.filter((m) =>
      session.moduleIds.includes(m.id)
    );
  }, [session?.moduleIds, modulesData?.modules]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || sendQuery.isPending) return;

    const query = inputValue.trim();
    clearInput();

    await sendQuery.mutateAsync({
      sessionId: sessionId!,
      request: {
        query,
        mode: responseMode,
        enableThinking: isThinkingEnabled,
      },
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  if (sessionLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        Session not found
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header with module context */}
      <SessionHeader session={session} modules={sessionModules} />

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <MessageList
          messages={messages || []}
          isLoading={messagesLoading}
          isPending={sendQuery.isPending}
        />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t p-4 bg-white">
        <div className="flex items-end gap-3 max-w-4xl mx-auto">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`Ask about ${sessionModules.map((m) => m.name).join(', ')}...`}
              rows={1}
              className="w-full px-4 py-3 pr-12 border rounded-lg resize-none 
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent
                         max-h-40"
              style={{
                minHeight: '48px',
                height: 'auto',
              }}
              disabled={sendQuery.isPending}
            />
            
            {/* Mode indicator */}
            <div className="absolute right-3 top-3 flex items-center gap-2 text-xs text-gray-400">
              <span className="capitalize">{responseMode}</span>
              {isThinkingEnabled && (
                <span className="px-1.5 py-0.5 bg-purple-100 text-purple-600 rounded">
                  Thinking
                </span>
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={!inputValue.trim() || sendQuery.isPending}
            className="px-4 py-3 bg-blue-600 text-white rounded-lg 
                       hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors flex items-center gap-2"
          >
            {sendQuery.isPending ? (
              <LoadingSpinner size="sm" />
            ) : (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
```

### 10.4 Verification Checklist

| Item | Test Method | Expected Result |
|------|-------------|-----------------|
| Module list loads | Open /modules | Grid of modules |
| Create module | Click + button | Dialog opens, creates |
| Module selection | Click module card | Visual feedback, store updated |
| Delete module | Click trash | Confirmation, deleted |
| Session creation | Select modules, start | Session created |
| Chat works | Type and send | Response appears |
| Optimistic updates | Send message | Immediate UI update |
| History loads | Open session | Previous messages shown |
| Error handling | Network fail | Error message shown |

---

## 11. Phase 7: Testing & Optimization

**Duration:** Week 10-12 (15 days)  
**Priority:** P0 (Critical Path)  
**Dependencies:** All previous phases

### 11.1 Objectives

1. Comprehensive unit and integration test coverage
2. End-to-end testing with Playwright
3. Performance optimization and profiling
4. Load testing and benchmarking
5. Documentation finalization

### 11.2 Test Strategy

#### 11.2.1 Backend Unit Tests

**File:** `tests/test_module_manager.py`

```python
"""
Unit tests for ModuleManager service.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from backend.module_manager import (
    ModuleManager,
    Module,
    ModuleNotFoundError,
    ModuleValidationError,
    DuplicateModuleError,
)


class TestModuleManager:
    """Test cases for ModuleManager."""

    @pytest.fixture
    def mock_graph_manager(self):
        """Create mock graph manager."""
        gm = Mock()
        gm.execute_query = Mock(return_value=[])
        gm.create_module_node = Mock(return_value="mod_123")
        return gm

    @pytest.fixture
    def mock_cache(self):
        """Create mock cache."""
        cache = Mock()
        cache.get_module = Mock(return_value=None)
        cache.set_module = Mock(return_value=True)
        cache.delete_module = Mock(return_value=True)
        return cache

    @pytest.fixture
    def module_manager(self, mock_graph_manager, mock_cache):
        """Create ModuleManager with mocks."""
        return ModuleManager(
            graph_manager=mock_graph_manager,
            cache=mock_cache
        )

    # === CREATE TESTS ===

    def test_create_module_success(self, module_manager, mock_graph_manager):
        """Test successful module creation."""
        # Setup
        mock_graph_manager.get_module.return_value = {
            'id': 'mod_123',
            'name': 'Test Module',
            'description': 'Test description',
            'color': '#4A90D9',
            'icon': 'folder',
            'user_id': 'user_1',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'document_count': 0,
            'entity_count': 0
        }

        # Execute
        module = module_manager.create_module(
            name="Test Module",
            user_id="user_1",
            description="Test description"
        )

        # Assert
        assert module.name == "Test Module"
        assert module.user_id == "user_1"
        mock_graph_manager.create_module_node.assert_called_once()

    def test_create_module_empty_name_fails(self, module_manager):
        """Test that empty name raises validation error."""
        with pytest.raises(ModuleValidationError, match="cannot be empty"):
            module_manager.create_module(name="  ", user_id="user_1")

    def test_create_module_long_name_fails(self, module_manager):
        """Test that name over 200 chars raises error."""
        long_name = "x" * 201
        with pytest.raises(ModuleValidationError, match="too long"):
            module_manager.create_module(name=long_name, user_id="user_1")

    def test_create_module_duplicate_fails(self, module_manager, mock_graph_manager):
        """Test that duplicate name raises error."""
        # Setup - module exists
        mock_graph_manager.execute_query.return_value = [{'exists': True}]

        with pytest.raises(DuplicateModuleError, match="already exists"):
            module_manager.create_module(name="Existing", user_id="user_1")

    # === GET TESTS ===

    def test_get_module_from_cache(self, module_manager, mock_cache):
        """Test that cached modules are returned."""
        cached_data = {
            'id': 'mod_123',
            'name': 'Cached Module',
            'description': '',
            'color': '#4A90D9',
            'icon': 'folder',
            'user_id': 'user_1',
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00',
            'document_count': 5,
            'entity_count': 10
        }
        mock_cache.get_module.return_value = cached_data

        module = module_manager.get_module("mod_123")

        assert module.name == "Cached Module"
        assert module.document_count == 5

    def test_get_module_not_found(self, module_manager, mock_graph_manager, mock_cache):
        """Test that non-existent module raises error."""
        mock_cache.get_module.return_value = None
        mock_graph_manager.get_module.return_value = None

        with pytest.raises(ModuleNotFoundError):
            module_manager.get_module("nonexistent")

    # === UPDATE TESTS ===

    def test_update_module_success(self, module_manager, mock_graph_manager, mock_cache):
        """Test successful module update."""
        # Setup existing module
        existing = {
            'id': 'mod_123',
            'name': 'Old Name',
            'description': 'Old desc',
            'color': '#4A90D9',
            'icon': 'folder',
            'user_id': 'user_1',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'document_count': 0,
            'entity_count': 0
        }
        mock_cache.get_module.return_value = existing
        mock_graph_manager.update_module.return_value = True
        mock_graph_manager.get_module.return_value = {
            **existing,
            'name': 'New Name'
        }

        # Execute
        module = module_manager.update_module(
            module_id="mod_123",
            name="New Name"
        )

        # Assert
        assert module.name == "New Name"
        mock_graph_manager.update_module.assert_called_once()

    # === DELETE TESTS ===

    def test_delete_module_success(self, module_manager, mock_graph_manager, mock_cache):
        """Test successful module deletion."""
        # Setup
        existing = {
            'id': 'mod_123',
            'name': 'To Delete',
            'user_id': 'user_1',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        }
        mock_cache.get_module.return_value = existing
        mock_graph_manager.delete_module.return_value = {
            'module_id': 'mod_123',
            'documents_reassigned': 5,
            'deleted': True
        }

        # Execute
        result = module_manager.delete_module("mod_123")

        # Assert
        assert result['deleted'] is True
        assert result['documents_reassigned'] == 5

    def test_delete_system_module_fails(self, module_manager, mock_cache):
        """Test that system modules cannot be deleted."""
        mock_cache.get_module.return_value = {
            'id': 'unassigned',
            'name': 'Unassigned',
            'user_id': 'system',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        }

        with pytest.raises(ModuleValidationError, match="Cannot delete system"):
            module_manager.delete_module("unassigned")

    # === DOCUMENT ASSIGNMENT TESTS ===

    def test_assign_document_success(self, module_manager, mock_graph_manager, mock_cache):
        """Test successful document assignment."""
        mock_cache.get_module.return_value = {'id': 'mod_123', 'name': 'Test'}
        mock_graph_manager.assign_document_to_module.return_value = True

        result = module_manager.assign_document(
            module_id="mod_123",
            document_id="doc_456",
            user_id="user_1"
        )

        assert result is True
        mock_graph_manager.assign_document_to_module.assert_called_once()

    def test_assign_documents_batch(self, module_manager, mock_graph_manager, mock_cache):
        """Test batch document assignment."""
        mock_cache.get_module.return_value = {'id': 'mod_123', 'name': 'Test'}
        mock_graph_manager.assign_document_to_module.return_value = True

        result = module_manager.assign_documents_batch(
            module_id="mod_123",
            document_ids=["doc_1", "doc_2", "doc_3"],
            user_id="user_1"
        )

        assert result['total'] == 3
        assert result['successful'] == 3
        assert result['failed'] == 0
```

#### 11.2.2 Integration Tests

**File:** `tests/test_rag_engine_integration.py`

```python
"""
Integration tests for RAG Engine with module filtering.
"""

import pytest
from unittest.mock import Mock, patch
import asyncio

from backend.rag_engine import RAGEngine
from backend.graph_manager import GraphManager


class TestRAGEngineModuleFiltering:
    """Integration tests for module-filtered RAG queries."""

    @pytest.fixture
    def graph_manager(self):
        """Create real graph manager for integration tests."""
        # Use test database
        return GraphManager(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test_password"
        )

    @pytest.fixture
    def rag_engine(self, graph_manager):
        """Create RAG engine with real graph manager."""
        return RAGEngine(graph_manager=graph_manager)

    @pytest.fixture
    def setup_test_data(self, graph_manager):
        """Set up test data in Neo4j."""
        # Create test modules
        graph_manager.create_module_node({
            'id': 'test_mod_1',
            'name': 'Machine Learning',
            'user_id': 'test_user'
        })
        graph_manager.create_module_node({
            'id': 'test_mod_2',
            'name': 'Statistics',
            'user_id': 'test_user'
        })

        # Create test documents and chunks
        graph_manager.create_document_node({
            'id': 'test_doc_1',
            'title': 'ML Basics',
            'module_id': 'test_mod_1'
        })
        
        # Create chunks with embeddings
        # ... (setup code)
        
        yield
        
        # Cleanup
        graph_manager.execute_query("""
            MATCH (n)
            WHERE n.id STARTS WITH 'test_'
            DETACH DELETE n
        """)

    @pytest.mark.asyncio
    async def test_query_single_module(self, rag_engine, setup_test_data):
        """Test query filtered to single module."""
        result = await rag_engine.query_with_modules(
            user_query="What is machine learning?",
            module_ids=["test_mod_1"],
            mode="assistant"
        )

        assert result["answer"]
        assert result["modules_searched"] == ["test_mod_1"]
        # All sources should be from test_mod_1
        for source in result["sources"]:
            assert source["module_id"] == "test_mod_1"

    @pytest.mark.asyncio
    async def test_query_multiple_modules(self, rag_engine, setup_test_data):
        """Test query across multiple modules."""
        result = await rag_engine.query_with_modules(
            user_query="Explain regression",
            module_ids=["test_mod_1", "test_mod_2"],
            enable_cross_module=True
        )

        assert result["answer"]
        assert set(result["modules_searched"]) == {"test_mod_1", "test_mod_2"}

    @pytest.mark.asyncio
    async def test_empty_module_returns_gracefully(self, rag_engine, setup_test_data):
        """Test query on empty module doesn't error."""
        # Create empty module
        rag_engine.gm.create_module_node({
            'id': 'test_empty_mod',
            'name': 'Empty Module',
            'user_id': 'test_user'
        })

        result = await rag_engine.query_with_modules(
            user_query="Find something",
            module_ids=["test_empty_mod"]
        )

        # Should return graceful response about no content
        assert "not available" in result["answer"].lower() or len(result["sources"]) == 0
```

#### 11.2.3 End-to-End Tests

**File:** `e2e/tests/modules.spec.ts`

```typescript
/**
 * E2E Tests for Module Management
 */

import { test, expect } from '@playwright/test';
import { ModulePage } from '../page-objects/ModulePage';

test.describe('Module Management', () => {
  let modulePage: ModulePage;

  test.beforeEach(async ({ page }) => {
    modulePage = new ModulePage(page);
    await modulePage.goto();
  });

  test('should display module list', async () => {
    await modulePage.waitForModules();
    const moduleCount = await modulePage.getModuleCount();
    expect(moduleCount).toBeGreaterThanOrEqual(0);
  });

  test('should create a new module', async () => {
    const moduleName = `Test Module ${Date.now()}`;
    
    await modulePage.clickCreateModule();
    await modulePage.fillModuleForm({
      name: moduleName,
      description: 'E2E test module',
      color: '#FF6B6B',
    });
    await modulePage.submitModuleForm();

    // Verify module appears
    await expect(modulePage.getModuleByName(moduleName)).toBeVisible();
  });

  test('should select module for study', async () => {
    await modulePage.waitForModules();
    
    // Select first module
    await modulePage.selectModule(0);
    
    // Verify selection state
    const isSelected = await modulePage.isModuleSelected(0);
    expect(isSelected).toBe(true);
  });

  test('should delete a module', async () => {
    // Create a module to delete
    const moduleName = `Delete Me ${Date.now()}`;
    await modulePage.createModule({ name: moduleName });
    
    // Delete it
    await modulePage.deleteModuleByName(moduleName);
    
    // Confirm deletion
    await modulePage.confirmDeletion();
    
    // Verify gone
    await expect(modulePage.getModuleByName(moduleName)).not.toBeVisible();
  });
});

test.describe('Study Session Flow', () => {
  test('should create session and chat', async ({ page }) => {
    const modulePage = new ModulePage(page);
    await modulePage.goto();
    
    // Select modules
    await modulePage.waitForModules();
    await modulePage.selectModule(0);
    
    // Start study session
    await modulePage.startStudySession();
    
    // Wait for session page
    await expect(page).toHaveURL(/\/sessions\//);
    
    // Send a message
    await page.fill('[data-testid="chat-input"]', 'What is the main topic?');
    await page.click('[data-testid="send-button"]');
    
    // Wait for response
    await expect(page.locator('[data-testid="assistant-message"]')).toBeVisible({
      timeout: 30000,
    });
  });
});
```

### 11.3 Performance Optimization

#### 11.3.1 Database Query Optimization

```python
# Optimized queries for common operations

# 1. Batch chunk retrieval with single round-trip
OPTIMIZED_CHUNK_QUERY = """
CALL db.index.vector.queryNodes('chunk_vector_index', $top_k * 2, $embedding)
YIELD node, score
WHERE node.module_id IN $module_ids
WITH node, score
ORDER BY score DESC
LIMIT $top_k

// Single expansion for all chunks
MATCH (d:Document)-[:HAS_CHUNK]->(node)
OPTIONAL MATCH (node)-[:CONTAINS_ENTITY]->(e)
WHERE e.module_id IN $module_ids

RETURN {
    id: node.id,
    text: node.text,
    score: score,
    document: {id: d.id, title: d.title},
    entities: collect(DISTINCT {id: e.id, name: e.name, type: labels(e)[0]})
} as result
"""

# 2. Precomputed module statistics (materialized view pattern)
UPDATE_MODULE_STATS_QUERY = """
MATCH (m:Module {id: $module_id})
OPTIONAL MATCH (m)-[:CONTAINS_DOCUMENT]->(d:Document)
OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
OPTIONAL MATCH (c)-[:CONTAINS_ENTITY]->(e)

WITH m,
     count(DISTINCT d) as doc_count,
     count(DISTINCT c) as chunk_count,
     count(DISTINCT e) as entity_count

SET m.cached_doc_count = doc_count,
    m.cached_chunk_count = chunk_count,
    m.cached_entity_count = entity_count,
    m.stats_updated_at = datetime()

RETURN m
"""
```

#### 11.3.2 Frontend Performance

```typescript
// React performance optimizations

// 1. Virtualized message list for large histories
import { useVirtualizer } from '@tanstack/react-virtual';

function VirtualizedMessageList({ messages }: { messages: Message[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100, // Estimated message height
    overscan: 5,
  });

  return (
    <div ref={parentRef} className="h-full overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            <MessageItem message={messages[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}

// 2. Debounced search input
import { useDebouncedCallback } from 'use-debounce';

function ModuleSearch() {
  const setSearchQuery = useModuleStore((s) => s.setSearchQuery);
  
  const debouncedSetQuery = useDebouncedCallback(
    (value: string) => setSearchQuery(value),
    300
  );

  return (
    <input
      type="text"
      onChange={(e) => debouncedSetQuery(e.target.value)}
      placeholder="Search modules..."
    />
  );
}

// 3. Memoized expensive computations
const filteredModules = useMemo(() => {
  if (!modules || !searchQuery) return modules;
  
  const query = searchQuery.toLowerCase();
  return modules.filter(
    (m) =>
      m.name.toLowerCase().includes(query) ||
      m.description.toLowerCase().includes(query)
  );
}, [modules, searchQuery]);
```

### 11.4 Verification Checklist

| Item | Test Type | Coverage Target |
|------|-----------|-----------------|
| ModuleManager | Unit | 90%+ |
| KGProcessor | Unit | 85%+ |
| SessionManager | Unit | 90%+ |
| RAGEngine module filter | Integration | 80%+ |
| GraphManager queries | Integration | 75%+ |
| Module CRUD flow | E2E | All paths |
| Study session flow | E2E | Happy path |
| Error scenarios | E2E | Key errors |

---

## 12. API Reference

### 12.1 Complete Endpoint Summary

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| **Modules** ||||
| GET | `/api/modules` | List all modules | Yes |
| POST | `/api/modules` | Create module | Yes |
| GET | `/api/modules/{id}` | Get module | Yes |
| PATCH | `/api/modules/{id}` | Update module | Yes |
| DELETE | `/api/modules/{id}` | Delete module | Yes |
| GET | `/api/modules/{id}/documents` | Get documents | Yes |
| POST | `/api/modules/{id}/documents` | Assign documents | Yes |
| DELETE | `/api/modules/{id}/documents/{doc_id}` | Remove document | Yes |
| GET | `/api/modules/{id}/stats` | Get statistics | Yes |
| **Sessions** ||||
| GET | `/api/sessions` | List sessions | Yes |
| POST | `/api/sessions` | Create session | Yes |
| GET | `/api/sessions/{id}` | Get session | Yes |
| PATCH | `/api/sessions/{id}` | Update session | Yes |
| DELETE | `/api/sessions/{id}` | Delete session | Yes |
| GET | `/api/sessions/{id}/messages` | Get history | Yes |
| POST | `/api/sessions/{id}/messages` | Add message | Yes |
| POST | `/api/sessions/{id}/query` | Execute query | Yes |
| GET | `/api/sessions/{id}/stats` | Get analytics | Yes |
| **Module Chat** ||||
| POST | `/api/modules/chat` | Query modules | Yes |
| POST | `/api/modules/{id}/chat` | Query single | Yes |
| POST | `/api/modules/concepts/cross` | Cross-module | Yes |
| **Processing** ||||
| POST | `/api/tasks/process` | Queue processing | Yes |
| GET | `/api/tasks/{id}` | Get task status | Yes |

### 12.2 Request/Response Examples

#### Create Module

```http
POST /api/modules
Content-Type: application/json

{
  "name": "Machine Learning Fundamentals",
  "description": "Core ML concepts and algorithms",
  "color": "#4A90D9",
  "icon": "brain"
}
```

```json
{
  "id": "mod_abc123def456",
  "name": "Machine Learning Fundamentals",
  "description": "Core ML concepts and algorithms",
  "color": "#4A90D9",
  "icon": "brain",
  "createdAt": "2026-01-19T10:30:00Z",
  "updatedAt": "2026-01-19T10:30:00Z",
  "documentCount": 0,
  "entityCount": 0,
  "isArchived": false
}
```

#### Query with Modules

```http
POST /api/modules/chat
Content-Type: application/json

{
  "query": "Explain the difference between supervised and unsupervised learning",
  "moduleIds": ["mod_abc123", "mod_def456"],
  "mode": "tutor",
  "enableThinking": true,
  "enableCrossModule": true,
  "topK": 10
}
```

```json
{
  "answer": "Based on your study materials, supervised learning...[detailed response with citations]",
  "sources": [
    {
      "id": "doc_123",
      "title": "Introduction to Machine Learning",
      "moduleId": "mod_abc123"
    }
  ],
  "modelUsed": "gemini-2.0-flash-001",
  "modulesSearched": ["mod_abc123", "mod_def456"],
  "crossModuleConcepts": [
    {
      "name": "Feature Engineering",
      "definition": "The process of transforming raw data...",
      "modules": [
        {"id": "mod_abc123", "name": "Machine Learning"},
        {"id": "mod_def456", "name": "Data Science"}
      ],
      "moduleCount": 2
    }
  ],
  "thoughtSummary": "I analyzed the query and found..."
}
```

---

## 13. Security & Performance

### 13.1 Security Matrix

| Component | Security Measure | Implementation |
|-----------|-----------------|----------------|
| API Auth | JWT tokens | FastAPI middleware |
| Module Access | User ownership check | Query filter `user_id = $current_user` |
| Document Access | Module membership | Via module relationship |
| Session Access | User ownership | Session.user_id check |
| Rate Limiting | Redis-based | 100 req/min per user |
| Input Validation | Pydantic schemas | All endpoints |
| SQL/Cypher Injection | Parameterized queries | All database calls |
| XSS Prevention | React escaping | Default behavior |
| CORS | Whitelist origins | FastAPI middleware |

### 13.2 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Module list load | < 100ms | P95 latency |
| Module create | < 200ms | P95 latency |
| Document assignment | < 100ms | P95 latency |
| KG processing | < 60s/doc | Average |
| RAG query (single module) | < 2s | P95 latency |
| RAG query (multi-module) | < 3s | P95 latency |
| Vector search | < 100ms | P99 latency |
| Frontend TTI | < 1.5s | Lighthouse |
| Frontend LCP | < 2.5s | Lighthouse |

### 13.3 Caching Strategy

```
┌─────────────────────────────────────────────────────────┐
│                    CACHE LAYERS                          │
├─────────────────────────────────────────────────────────┤
│ L1: React Query Cache (Client)                          │
│     - Module lists: 30s stale, 5min gc                  │
│     - Module details: 60s stale                         │
│     - Session messages: No auto-refetch                 │
├─────────────────────────────────────────────────────────┤
│ L2: Redis Cache (Server)                                │
│     - Module data: 5min TTL                             │
│     - Module stats: 2min TTL                            │
│     - Query results: 5min TTL (hash of query+modules)   │
├─────────────────────────────────────────────────────────┤
│ L3: Neo4j Query Cache (Database)                        │
│     - Cypher query plan cache                           │
│     - HNSW index in memory                              │
└─────────────────────────────────────────────────────────┘

Cache Invalidation Triggers:
- Module create/update/delete → Invalidate module list, detail
- Document assignment → Invalidate module stats, documents
- KG processing complete → Invalidate module stats, query cache
- Session message → Invalidate session detail (message count)
```

---

## 14. Deployment Guide

### 14.1 Environment Requirements

```bash
# Production environment
Python 3.11+
Node.js 20+
Redis 7+
Neo4j 5.15+

# Python packages
fastapi==0.109.0
uvicorn==0.27.0
celery==5.3.6
redis==5.0.1
neo4j==5.16.0
pydantic==2.5.3
google-cloud-aiplatform==1.38.0

# Node packages
react==18.2.0
@tanstack/react-query==5.17.0
zustand==4.4.7
typescript==5.3.3
vite==5.0.10
```

### 14.2 Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - REDIS_HOST=redis
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - neo4j
      - redis

  worker:
    build: ./backend
    command: celery -A backend.tasks worker -l info
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - REDIS_HOST=redis
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - neo4j
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    environment:
      - VITE_API_URL=http://api:8000

  neo4j:
    image: neo4j:5.15-enterprise
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - neo4j_data:/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  neo4j_data:
  redis_data:
```

### 14.3 Deployment Checklist

| Step | Action | Verification |
|------|--------|--------------|
| 1 | Set up Neo4j with vector plugin | `CALL dbms.components()` |
| 2 | Run schema migration | Check constraints |
| 3 | Configure Redis | `redis-cli ping` |
| 4 | Deploy API server | Health check endpoint |
| 5 | Deploy Celery workers | `celery inspect ping` |
| 6 | Build and deploy frontend | Load test page |
| 7 | Configure CORS | Cross-origin test |
| 8 | Set up monitoring | Grafana dashboards |
| 9 | Configure backups | Test restore |
| 10 | Load test | 100 concurrent users |

---

## 15. Implementation Timeline Summary

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1-2 | Phase 1: Schema | Migration script, constraints, indices |
| 2-3 | Phase 2: Module Mgmt | ModuleManager, Cache, API endpoints |
| 3-5 | Phase 3: KG Processor | Entity extraction, Celery tasks |
| 5-7 | Phase 4: RAG Engine | Module filtering, cross-module discovery |
| 7-8 | Phase 5: Sessions | SessionManager, history, analytics |
| 8-10 | Phase 6: Frontend | React components, TanStack Query |
| 10-12 | Phase 7: Testing | Unit, integration, E2E, optimization |

---

**📚 Document Complete!**

This comprehensive implementation plan covers all aspects of the Module-to-Knowledge Graph feature with production-ready code examples, best practices from research, and detailed verification checklists for each phase.

