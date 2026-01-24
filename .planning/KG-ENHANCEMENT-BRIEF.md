# AURA-NOTES-MANAGER KG Pipeline Enhancement Brief

> **Version:** 1.0
> **Created:** January 24, 2026
> **Project:** KG Pipeline Enhancement (KG-ENH)
> **Scope:** AURA-NOTES-MANAGER only

---

## Vision

Elevate AURA-NOTES-MANAGER's document→knowledge graph pipeline to match AURA-CHAT's sophistication in parsing, chunking, entity/relationship extraction, graph modeling, and retrieval-augmented reasoning. This creates feature parity and a unified experience across both applications.

---

## Problem Statement

AURA-NOTES-MANAGER's current KG pipeline has significant capability gaps compared to AURA-CHAT:

| Feature | AURA-CHAT | AURA-NOTES-MANAGER Gap |
|---------|-----------|------------------------|
| Hierarchical chunking | Parent (1500 tokens) + Child (800 tokens) | Only flat token-based |
| Entity embeddings | All entities get 768-dim vectors | Entities not embedded |
| Entity-entity relationships | 9 relationship types via LLM | Only CONTAINS_ENTITY |
| Semantic entity dedup | Cosine similarity 0.85 threshold | Exact name match only |
| Hybrid search | Vector + Fulltext weighted | Vector only |
| Graph traversal | 2-hop expansion for reasoning | Not implemented |
| Query expansion | Graph-based term addition | Not implemented |
| Position-weighted doc embedding | Title/conclusion boosted | Not implemented |
| DOCX parsing | Supported | Not supported |
| OCR for scanned PDFs | Planned | Not supported |

---

## Solution

Port AURA-CHAT's advanced KG pipeline components to AURA-NOTES-MANAGER, organized into three phases:

### Phase 1: Foundation & Intelligence Layer (6-8 weeks)
- Port hierarchical parent-child chunking
- Port LLM entity extractor with semantic deduplication
- Add entity-entity relationship extraction
- Update Neo4j schema (ParentChunk, vector indices, fulltext)
- Add DOCX parsing support

### Phase 2: Processing & Interaction Capabilities (6-10 weeks)
- Add hybrid search (vector + fulltext)
- Add graph traversal for multi-hop reasoning
- Add query API for interactive analysis
- Add multi-document reasoning
- Add feedback loop for continuous improvement

### Phase 3: Advanced Features & Integration (6-12 weeks)
- Automatic summarization and insight generation
- Smart extraction templates
- AURA-CHAT integration (shared KG views)
- Future multimodal support (audio, handwritten)

---

## Source Implementation Reference

All features to be ported from AURA-CHAT:

| Component | Source File | Key Methods |
|-----------|-------------|-------------|
| Hierarchical chunking | `AURA-CHAT/backend/document_processor.py` | `chunk_text_hierarchical()` |
| Entity-aware chunking | `AURA-CHAT/backend/entity_aware_chunker.py` | `EntityAwareChunker` class |
| LLM entity extraction | `AURA-CHAT/backend/llm_entity_extractor.py` | `extract_entities()`, `extract_relationships()` |
| Graph operations | `AURA-CHAT/backend/graph_manager.py` | Vector/fulltext indices, traversal |
| RAG engine | `AURA-CHAT/backend/rag_engine.py` | Hybrid search, query expansion |
| Embeddings | `AURA-CHAT/backend/utils/embeddings.py` | Batch processing, rate limiting |
| Configuration | `AURA-CHAT/backend/utils/config.py` | All parameter values |

---

## Target Files

| Component | Target Location | Action |
|-----------|-----------------|--------|
| KG Processor | `AURA-NOTES-MANAGER/api/kg_processor.py` | Enhance with hierarchical chunking |
| Entity Extractor | `AURA-NOTES-MANAGER/services/llm_entity_extractor.py` | Create new |
| Entity-Aware Chunker | `AURA-NOTES-MANAGER/services/entity_aware_chunker.py` | Create new |
| Neo4j Config | `AURA-NOTES-MANAGER/api/neo4j_config.py` | Add indices |
| Graph Manager | `AURA-NOTES-MANAGER/api/graph_manager.py` | Create new |
| RAG Engine | `AURA-NOTES-MANAGER/api/rag_engine.py` | Create new (Phase 2) |
| Query Router | `AURA-NOTES-MANAGER/api/routers/query.py` | Create new (Phase 2) |

---

## Configuration Values (Match AURA-CHAT)

```python
# Chunking
CHUNK_SIZE = 800
CHUNK_OVERLAP = 200
PARENT_CHUNK_SIZE = 1500
MIN_CHUNK_TOKENS = 200
MAX_CHUNK_TOKENS = 1200

# Entity Extraction
ENTITY_CONTEXT_WINDOW = 400
LLM_ENTITY_BATCH_SIZE = 3000
ENTITY_DEDUP_SIMILARITY_THRESHOLD = 0.85

# Embeddings
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768

# Retrieval
TOP_K_RETRIEVAL = 15
VECTOR_WEIGHT = 0.7
FULLTEXT_WEIGHT = 0.3
GRAPH_HOP_DEPTH = 2
```

---

## Success Metrics

| Metric | Target | Phase |
|--------|--------|-------|
| Entity extraction accuracy vs AURA-CHAT baseline | ≥ 95% | 1 |
| Relationship precision/recall | ≥ 80% | 1 |
| Chunking coherence score | ≥ 85% | 1 |
| KG processing throughput | 10 docs/min | 1 |
| Hybrid search latency | < 500ms | 2 |
| Query response latency | < 2s | 2 |
| Multi-hop reasoning accuracy | ≥ 80% | 2 |
| User satisfaction rating | ≥ 4.5/5 | 3 |

---

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Backend | FastAPI | 0.109.0 |
| Task Queue | Celery | 5.3.6 |
| Graph Database | Neo4j | 5.15+ |
| Cache/Broker | Redis | 7+ |
| LLM | Gemini | gemini-1.5-flash |
| Embeddings | Gemini | gemini-embedding-001 |
| Vector Search | Neo4j HNSW | Built-in |
| Document Parsing | pdfplumber, python-docx | Latest |

---

## Phase Structure

```
.planning/
├── KG-ENHANCEMENT-BRIEF.md      # This document
├── KG-ENHANCEMENT-ROADMAP.md    # Phase structure
└── phases/
    ├── 09-kg-foundation/        # Phase 1: Foundation
    │   ├── 09-01-PLAN.md        # Neo4j schema updates
    │   ├── 09-02-PLAN.md        # Hierarchical chunking
    │   ├── 09-03-PLAN.md        # LLM entity extractor
    │   ├── 09-04-PLAN.md        # Relationship extraction
    │   ├── 09-05-PLAN.md        # Entity embeddings
    │   ├── 09-06-PLAN.md        # Semantic deduplication
    │   ├── 09-07-PLAN.md        # DOCX parsing
    │   └── 09-08-PLAN.md        # Integration & testing
    ├── 10-kg-interaction/       # Phase 2: Interaction
    │   ├── 10-01-PLAN.md        # Hybrid search
    │   ├── 10-02-PLAN.md        # Graph traversal
    │   ├── 10-03-PLAN.md        # Query API
    │   └── ...
    └── 11-kg-advanced/          # Phase 3: Advanced
        ├── 11-01-PLAN.md        # Summarization
        └── ...
```

---

## Next Action

1. Create KG-ENHANCEMENT-ROADMAP.md with detailed phase breakdown
2. Create Phase 09 directory and atomic plans
3. Begin with 09-01-PLAN.md: Neo4j Schema Updates
