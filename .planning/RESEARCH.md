# M2KG Web Research Findings

> Research Date: January 19, 2026
> Based on Final-Module-2-KG.md low-level implementation plan

---

## 1. Neo4j 5.x Vector Search Best Practices

### 1.1 HNSW Index Configuration

**Source:** [Neo4j Vector Index Documentation](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/)

```cypher
CREATE VECTOR INDEX chunk_vector_index IF NOT EXISTS
FOR (c:Chunk) ON (c.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine',
    `vector.hnsw.m`: 16,
    `vector.hnsw.ef_construction`: 200,
    `vector.quantization.enabled`: true
  }
}
```

**Key Settings:**
| Parameter | Recommended Value | Impact |
|-----------|-------------------|--------|
| `vector.dimensions` | 768 (Gemini) | Embedding size |
| `vector.similarity_function` | cosine | Best for text |
| `vector.hnsw.m` | 16-32 | Connections per node |
| `vector.hnsw.ef_construction` | 100-200 | Build-time quality |
| `vector.quantization.enabled` | true | Memory optimization |

**2025 Update:** Neo4j 2025.01+ requires Java 21+ with `--add-modules=jdk.incubator.vector` for vector operations.

### 1.2 Vector Search Query Pattern

```cypher
CALL db.index.vector.queryNodes(
  'chunk_vector_index',
  10,                    -- top_k
  $query_embedding
) YIELD node, score
WHERE node.module_id IN $module_ids
RETURN node, score
ORDER BY score DESC
```

---

## 2. FastAPI + Celery Integration (2025)

### 2.1 Event Loop Best Practice

**Source:** [Celery + FastAPI Production Guide](https://medium.com/@dewasheesh.rana/celery-redis-fastapi-the-ultimate-2025-production-guide-broker-vs-backend-explained-5b84ef508fa7)

**Critical Issue:** Celery blocks FastAPI's event loop if not configured properly.

**Solution - Run Celery in Separate Thread:**
```python
# backend/tasks/celery_app.py
from celery import Celery
from celery.platforms import import_if_str
import multiprocessing

def run_celery_worker():
    """Run Celery worker in separate process to avoid blocking event loop."""
    app = Celery('aura_tasks')
    app.worker_main(['worker', '--loglevel=info'])

# In FastAPI startup:
import threading
worker_thread = threading.Thread(target=run_celery_worker, daemon=True)
worker_thread.start()
```

### 2.2 Task Best Practices

**Source:** [Advanced Celery Tips](https://www.vintasoftware.com/blog/celery-wild-tips-and-tricks-run-async-tasks-real-world)

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
)
def process_document_to_kg(self, document_id: str, module_id: str):
    """Idempotent task with automatic retry and acknowledgment."""
    # Implementation with progress tracking
    self.update_state(state='PROCESSING', meta={'progress': 50})
    ...
```

---

## 3. GraphRAG Implementation Patterns

### 3.1 Graph-Enhanced Vector Search (Recommended)

**Source:** [GraphRAG Field Guide](https://neo4j.com/blog/developer/graphrag-field-guide-rag-patterns/)

```
┌─────────────────────────────────────────────────────────────────┐
│                    GraphRAG Architecture                        │
├─────────────────────────────────────────────────────────────────┤
│  User Query                                                     │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────────┐                                            │
│  │ Vector Similarity│──▶ Initial Chunks (top_k=20)             │
│  │     Search       │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         Graph Traversal (2-hop within modules)           │   │
│  │  - CONTAINS_ENTITY relationships                         │   │
│  │  - RELATES_TO relationships                              │   │
│  │  - DEPENDS_ON relationships                              │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Context Assembly + Ranking                  │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              LLM Generation with Citations               │   │
│  └─────────────────────────────────────────────────────────┘   │
```

### 3.2 Module-Aware Retrieval Pattern

```python
async def module_aware_retrieve(
    self,
    query: str,
    module_ids: List[str],
    top_k: int = 20
) -> List[RetrievalResult]:
    """
    Module-filtered GraphRAG retrieval.
    Stays within module boundaries during graph traversal.
    """
    # Phase 1: Vector search with module filter
    query_embedding = await self.embed(query)
    initial_chunks = await self.graph_manager.vector_search(
        embedding=query_embedding,
        top_k=top_k,
        filter_clause="WHERE node.module_id IN $module_ids"
    )

    # Phase 2: Graph expansion within module boundaries
    chunk_ids = [c.id for c in initial_chunks[:10]]
    expanded = await self.graph_manager.expand_within_modules(
        node_ids=chunk_ids,
        max_hops=2,
        module_ids=module_ids
    )

    return self._merge_and_rank(initial_chunks, expanded)
```

---

## 4. React Knowledge Graph Visualization

### 4.1 Library Comparison (2025)

| Library | Type | Best For | Consideration |
|---------|------|----------|---------------|
| **ReGraph** | Commercial | Enterprise knowledge graphs | Declarative React API, high performance |
| **Cytoscape.js** | Open Source | General graph visualization | Requires React wrapper, flexible |
| **React Flow** | Open Source | Node-based UIs, workflows | Not optimized for large graphs |
| **KeyLines** | Commercial | Large-scale temporal graphs | Imperative API |

**Source:** [React Graph Visualization Guide](https://cambridge-intelligence.com/react-graph-visualization-library/)

### 4.2 Recommendation

For AURA M2KG, **Cytoscape.js with react-cytoscapejs wrapper** provides:
- Open source (MIT)
- Good balance of features and performance
- Active community
- Supports knowledge graph layouts (cola, fcose)

**Alternative:** If enterprise features needed (time-based views, advanced filtering), consider ReGraph.

---

## 5. Key 2025 Technology Updates

### 5.1 Neo4j 5.x Changes
- Vector search now uses Apache Lucene's HNSW implementation
- Java 21+ required for vector operations (2025.01+)
- `CREATE VECTOR INDEX` replaces legacy procedures

### 5.2 FastAPI Patterns
- BackgroundTasks for short tasks, Celery for long-running
- Async dependencies preferred over sync
- Proper event loop separation from Celery critical

### 5.3 RAG Evolution
- "Context Engineering" trending over pure RAG
- GraphRAG becoming standard for complex reasoning
- Hybrid retrieval (vector + graph) outperforms pure vector

---

## 6. Action Items from Research

1. **Update Phase 1:** Add Java 21+ requirement to deployment docs
2. **Update Phase 3:** Implement Celery in separate thread/process pattern
3. **Update Phase 4:** Use Graph-Enhanced Vector Search pattern (not pure vector)
4. **Frontend Decision:** Start with Cytoscape.js, evaluate ReGraph later
5. **Quantization:** Enable by default for memory optimization

---

## 7. Sources

- [Neo4j Vector Index Documentation](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/)
- [GraphRAG Field Guide](https://neo4j.com/blog/developer/graphrag-field-guide-rag-patterns/)
- [React Graph Visualization Guide](https://cambridge-intelligence.com/react-graph-visualization-library/)
- [Celery + FastAPI Production Guide](https://medium.com/@dewasheesh.rana/celery-redis-fastapi-the-ultimate-2025-production-guide-broker-vs-backend-explained-5b84ef508fa7)
- [Advanced Celery Tips](https://www.vintasoftware.com/blog/celery-wild-tips-and-tricks-run-async-tasks-real-world)
