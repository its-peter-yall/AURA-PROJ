# Document-to-KnowledgeGraph Pipeline Comparison
# AURA-CHAT vs AURA-NOTES-MANAGER

## Scope and Sources
- AURA-CHAT core pipeline: [document_processor.py](file:///d:/Peter/AURA%20Twin%20Proj/AURA-PROJ/AURA-CHAT/backend/document_processor.py), [llm_entity_extractor.py](file:///d:/Peter/AURA%20Twin%20Proj/AURA-PROJ/AURA-CHAT/backend/llm_entity_extractor.py), [entity_aware_chunker.py](file:///d:/Peter/AURA%20Twin%20Proj/AURA-PROJ/AURA-CHAT/backend/entity_aware_chunker.py), [semantic_chunker.py](file:///d:/Peter/AURA%20Twin%20Proj/AURA-PROJ/AURA-CHAT/backend/semantic_chunker.py), [embeddings.py](file:///d:/Peter/AURA%20Twin%20Proj/AURA-PROJ/AURA-CHAT/backend/utils/embeddings.py), [config.py](file:///d:/Peter/AURA%20Twin%20Proj/AURA-PROJ/AURA-CHAT/backend/utils/config.py)
- AURA-CHAT API workflow & graph schema: [documents.py](file:///d:/Peter/AURA%20Twin%20Proj/AURA-PROJ/AURA-CHAT/server/routers/documents.py), [graph.py](file:///d:/Peter/AURA%20Twin%20Proj/AURA-PROJ/AURA-CHAT/server/schemas/graph.py)
- AURA-NOTES-MANAGER core pipeline: [kg_processor.py](file:///d:/Peter/AURA%20Twin%20Proj/AURA-PROJ/AURA-NOTES-MANAGER/api/kg_processor.py), [document_processing_tasks.py](file:///d:/Peter/AURA%20Twin%20Proj/AURA-PROJ/AURA-NOTES-MANAGER/api/tasks/document_processing_tasks.py), [config.py](file:///d:/Peter/AURA%20Twin%20Proj/AURA-PROJ/AURA-NOTES-MANAGER/api/config.py)
- AURA-NOTES-MANAGER components: [embeddings.py](file:///d:/Peter/AURA%20Twin%20Proj/AURA-PROJ/AURA-NOTES-MANAGER/services/embeddings.py), [llm_entity_extractor.py](file:///d:/Peter/AURA%20Twin%20Proj/AURA-PROJ/AURA-NOTES-MANAGER/services/llm_entity_extractor.py), [entity_aware_chunker.py](file:///d:/Peter/AURA%20Twin%20Proj/AURA-PROJ/AURA-NOTES-MANAGER/services/entity_aware_chunker.py), [docx_parser.py](file:///d:/Peter/AURA%20Twin%20Proj/AURA-PROJ/AURA-NOTES-MANAGER/services/document_parsers/docx_parser.py)
- AURA-NOTES-MANAGER graph schema: [neo4j_schema.py](file:///d:/Peter/AURA%20Twin%20Proj/AURA-PROJ/AURA-NOTES-MANAGER/api/schemas/neo4j_schema.py), [neo4j_config.py](file:///d:/Peter/AURA%20Twin%20Proj/AURA-PROJ/AURA-NOTES-MANAGER/api/neo4j_config.py)

## 1) Pipeline Architecture
### AURA-CHAT (AURA-CHAT/backend + server)
1. Upload via FastAPI (`/documents/upload`) → register file path
2. Process via FastAPI (`/documents/process/{id}`) → `DocumentProcessor.process_document`
3. Text extraction (PDF/DOCX/TXT) → clean text
4. LLM entity extraction + embeddings for entities
5. Hierarchical chunking (parent + child) with fallback
6. Relationship extraction (entity-entity)
7. Chunk embeddings (Vertex AI) + store in Neo4j

Key flow is synchronous per request and stored directly via `DocumentProcessor.store_document_graph` and `GraphManager` calls.

### AURA-NOTES-MANAGER (api + services)
1. Task enqueue via Celery (`process_document_task`) with Firestore status updates
2. `KnowledgeGraphProcessor.process_document` loads text (file, Firestore content, or pdf_url)
3. Chunking (entity-aware/semantic/hierarchical options)
4. Embedding generation for chunks and optionally entities
5. Entity extraction (LLM-based or template-based)
6. Neo4j storage with module_id tagging
7. Firestore status synchronization on completion

Key flow is asynchronous and task-driven with progress reporting and idempotency safeguards.

## 2) Component Analysis
| Stage | AURA-CHAT | AURA-NOTES-MANAGER | Similarity |
|---|---|---|---|
| Document parsing | pdfplumber + PyPDF2 for PDF, python-docx for DOCX, text read fallback | PyMuPDF (fitz) for PDF, DocxParser (python-docx) for DOCX, text read fallback | Similar intent, different PDF stack and DOCX parsing depth |
| Text cleaning | `clean_text` normalizes whitespace, preserves paragraph breaks | `chunk_text_hierarchical` normalizes unicode and preserves paragraphs; parse stage keeps raw text | Similar normalization goals |
| Chunking | Hierarchical parent/child chunking; fallback to token/paragraph chunking; optional entity-aware chunker | Entity-aware chunker; hierarchical chunking option; sentence/fixed fallback utilities | Similar concepts; different default paths |
| Embeddings | Vertex AI REST via `EmbeddingService` (text-embedding-004, 768-dim) | Vertex AI SDK via `EmbeddingService` (text-embedding-004, 768-dim) | Functionally similar; different client implementation |
| Entity extraction | LLMEntityExtractor in backend | LLMEntityExtractor in services + template-based extractor | Similar LLM extraction; Notes adds templates and semantic dedup |
| Relationship extraction | LLM entity relationships and CONTAINS_ENTITY via chunk text matching | LLM extraction with entity relationships; schema supports richer relation set | Similar idea; Notes has more relationship types |
| Graph storage | Neo4j nodes: Document, ParentChunk, Chunk, Topic/Concept/Methodology/Finding; relationships via direct Cypher | Neo4j nodes with module_id and extended schema (Definition, Citation, Module, etc.) | Similar storage; Notes has broader schema and module scoping |

## 3) Configuration & Parameters
### AURA-CHAT
- `backend/utils/config.py` defines chunk sizes, overlap, entity extraction toggles, relationship types, and embedding model settings.
- Uses `VERTEX_PROJECT`, `VERTEX_CREDENTIALS`, `LLM_ENTITY_EXTRACTION_MODEL`, and chunking parameters like `CHUNK_SIZE`, `CHUNK_OVERLAP`, `MIN_CHUNK_TOKENS`, `MAX_CHUNK_TOKENS`.

### AURA-NOTES-MANAGER
- `api/config.py` provides Vertex AI settings, Neo4j settings, Firestore client init, and test mode.
- `KnowledgeGraphProcessor` constructor uses chunk parameters (`chunk_size=800`, overlap=100) and optional hierarchical chunking.
- Task-level runtime settings include Celery timeouts/retries and Firestore status updates.

## 4) Dependencies & Libraries (Pipeline-Relevant)
### AURA-CHAT
- Neo4j: `neo4j`
- Google Vertex AI / GenAI: `google-cloud-aiplatform`, `vertexai`, `google-genai`
- Document parsing: `pdfplumber`, `pypdf`, `python-docx`
- Tokenization: `tiktoken`
- Web/API: `fastapi`, `uvicorn`

### AURA-NOTES-MANAGER
- Neo4j: `neo4j`
- Google Vertex AI / GenAI: `vertexai`, `google-generativeai`, `google-auth`
- Document parsing: `PyMuPDF`, `python-docx`
- Task queue: `celery`
- Firestore: `firebase-admin`, `google-cloud-firestore`
- Tokenization: `tiktoken`

## 5) Input / Output Formats
### Input Formats
- **AURA-CHAT:** PDF, DOCX, TXT via upload endpoint.
- **AURA-NOTES-MANAGER:** PDF, DOCX, TXT; also Firestore-stored content or linked `pdf_url`.

### Knowledge Graph Output Schema
- **AURA-CHAT:** Document, ParentChunk, Chunk, Topic, Concept, Methodology, Finding. Relationships: HAS_CHUNK, HAS_PARENT_CHUNK, HAS_CHILD, CONTAINS_ENTITY, and LLM entity-entity relationships.
- **AURA-NOTES-MANAGER:** Same base types plus Definition, Citation, Module, Feedback, and session-related nodes. Relationships include a richer entity-entity set (DEFINES, DEPENDS_ON, EXTENDS, IMPLEMENTS, REFERENCES, etc.) and module scoping via `module_id`.

## 6) Code Logic Differences
### AURA-CHAT Distinctives
- Synchronous processing via API requests; uses in-memory upload registry between upload and process steps.
- Document-level embedding computed as a position-weighted average of chunk embeddings.
- Entity dedup uses semantic search in Neo4j before creation.
- Chunk-entity linking uses word-boundary regex matching on chunk text.

### AURA-NOTES-MANAGER Distinctives
- Asynchronous Celery workflow with progress tracking and Firestore status sync.
- Module scoping (`module_id`) is propagated and stored on all nodes.
- Supports template-based extraction for specific note types and semantic dedup via embeddings.
- Multiple text sources: file path, Firestore content, or Firestore-linked file URLs.

## 7) Similarity vs Divergence Summary
### Exact Similarities
- Both implement the core stages: text extraction → chunking → embeddings → entity extraction → Neo4j storage.
- Both use Gemini/Vertex AI for embeddings and LLM-based entity extraction.
- Both support PDF/DOCX/TXT as primary document formats.

### Minor Variations
- Different PDF parsing stacks (pdfplumber/PyPDF2 vs PyMuPDF).
- Different embedding client implementations (REST vs Vertex AI SDK).
- Chunking defaults differ (AURA-CHAT uses hierarchical by default; Notes has multiple strategies with entity-aware emphasis).

### Significant Divergences
- AURA-NOTES-MANAGER is task-based with Celery, Firestore integration, and module-scoped KG nodes.
- AURA-NOTES-MANAGER supports template-based extraction and a broader KG schema (Definition/Citation/Module).
- AURA-CHAT has a simpler synchronous API pipeline without Firestore status lifecycle.

## Final Assessment
The pipelines are **structurally similar at the stage level** and share common design goals (LLM entity extraction, semantic chunking, embedding-based retrieval, and Neo4j storage). However, they are **not functionally equivalent** in practice. AURA-NOTES-MANAGER has evolved into a more feature-rich, asynchronous, module-scoped pipeline with Firestore orchestration and template-based extraction, whereas AURA-CHAT remains a synchronous, document-centric pipeline with a narrower schema and simpler orchestration.
