# AURA-NOTES-MANAGER KG Pipeline Enhancement Roadmap

> **Version:** 1.0
> **Created:** January 24, 2026
> **Brief:** `@.planning/KG-ENHANCEMENT-BRIEF.md`
> **Project:** AURA-NOTES-MANAGER
> **Reference:** `@AGENTS.md`, `@.planning/ROADMAP.md`

---

## Agent Behaviour

This section defines behavioral requirements for all agents implementing this roadmap. These rules ensure consistent quality, research-first approach, and proper verification across all phases.

### Core Principles

#### 1. Research-First Principle
- **ALWAYS web-search before implementing** unfamiliar libraries, APIs, or patterns
- **NEVER assume** library behavior — verify with official documentation
- **Search first** when encountering: new npm packages, Python libraries, framework features, or external APIs
- Use `librarian` agent for documentation lookup, `explore` agent for codebase patterns

#### 2. SWE Best Practices
- **Write tests BEFORE or WITH code**, not after — TDD when appropriate
- **Verify with diagnostics**: Run `lsp_diagnostics` before marking tasks complete
- **Build & test**: Always run build/test commands after implementation
- **Type safety first**: Never suppress type errors with `as any`, `@ts-ignore`
- **Error handling**: Never leave empty catch blocks `catch(e) {}`
- **Minimal changes**: Fix bugs without refactoring unrelated code

#### 3. Never Be Lazy
- **Don't skip verification** — always run diagnostics, build, and tests
- **Don't guess** — search for patterns, ask clarification questions when ambiguous
- **Don't partial-ship** — task is complete ONLY when all criteria met
- **Don't assume knowledge** — read the relevant code before modifying
- **Don't skip tests** — verify functionality, not just compilation

#### 4. Certainty Before Conclusion
- **NEVER declare complete** without 100% confidence
- **Verify every requirement** from the original request is addressed
- **Check for regressions**: Run relevant tests before claiming fix
- **Run diagnostics**: Ensure no new errors introduced
- **If uncertain, ask**: Better to clarify than ship broken code

### Plan Structure Template

Use this XML-based structure for all phase plans. Each plan is self-contained and executable by Claude.

```markdown
<objective>
[What and why]
Purpose: [...]
Output: [...]
</objective>

<context>
@.planning/KG-ENHANCEMENT-ROADMAP.md - Roadmap context
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

### Task Type Specifications

| Type | When to Use |
|------|-------------|
| `create` | New file creation |
| `update` | Modify existing file |
| `delete` | Remove file/feature |

### Required Task Fields

| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | create/update/delete |
| `file` | Yes | Exact file path |
| `action` | Yes | Implementation details with code examples |
| `verify` | Yes | Executable verification commands |
| `done` | Yes | Measurable completion criteria |

### Checkpoint Types

| Type | Description |
|------|-------------|
| `checkpoint:human-verify` | Visual/UI verification needed |
| `checkpoint:decision` | Human must choose between options |

### Best Practices

1. **Web-search first**: Before implementing any feature, search for official documentation and best practices
2. **Atomic tasks**: Each task = 15-60 min of Claude work
3. **Descriptive, not prescriptive**: Describe WHAT and WHY, not HOW
4. **Verification**: Always include `py_compile` check
5. **File headers**: Every new file needs header with description and @see

### File Header Requirements

**MANDATORY for every code file created or updated:**

```typescript
// {FILE_NAME}
// {Brief 1-line description of what this file does}

// Longer description (2-4 lines):
// - What problem does this solve?
// - What are the key functions/classes?
// - Any important context for future maintainers

// @see: {Related files}
// @note: {Important caveats or gotchas}
```

**Example (TypeScript):**
```typescript
// api.ts
// Axios client configuration with interceptors for auth and error handling

// Configures base URL, timeout (5min for document processing),
// and adds auth token to all requests. Error interceptor logs
// and rejects promises for consistent error handling across app.

// @see: types/api.ts - Type definitions for API responses
// @note: Always use 127.0.0.1, never localhost (IPv6 issues)
```

**Example (Python):**
```python
# rag_engine.py
# Hybrid RAG engine combining vector search and graph traversal

# Implements query analysis to determine intent (factual/conceptual),
# performs hybrid search (vector + graph), and synthesizes responses
# using retrieved context. Supports configurable similarity thresholds.

# @see: schemas/query.py - Query schema definitions
# @note: 2-hop graph traversal limits may need tuning for large graphs
```

**Enforcement:**
- File headers are REQUIRED for: `.ts`, `.tsx`, `.py`, `.pyi`, `.js`, `.jsx`
- Existing files without headers: Add when modifying significantly (>30% changes)
- New files: ALWAYS add header before first write
- Configuration files (tsconfig.json, pyproject.toml): Optional but encouraged

### Delegation Guidelines

| Domain | Delegate To | When |
|--------|-------------|------|
| Visual/UI changes | `frontend-ui-ux-engineer` | Styling, layout, animations |
| External docs | `librarian` | Library API, official docs |
| Codebase patterns | `explore` | Finding existing implementations |
| Architecture review | `oracle` | Multi-system tradeoffs, design |
| Documentation | `document-writer` | READMEs, guides, AGENTS.md |
| Hard debugging | `oracle` | After 2+ failed fix attempts |

### Evidence Requirements

Task is NOT complete without:
- [ ] `lsp_diagnostics` clean on changed files
- [ ] Build passes (if applicable)
- [ ] Tests pass (or explicit note of pre-existing failures)
- [ ] User's original request fully addressed

### Naming Conventions

- Phase folder: `phases/XX-kg-foundation/`, `phases/XX-kg-interaction/`, `phases/XX-kg-advanced/`
- Plan file: `XX-YY-PLAN.md` (XX=phase, YY=sub-plan)
- Summary file: `XX-YY-SUMMARY.md`

**Example:** `phases/09-kg-foundation/09-01-PLAN.md`

### Verification Commands

Always include these verification steps in task definitions:

```bash
# Python syntax check
python -m py_compile path/to/file.py

# Python linting
pylint path/to/file.py

# TypeScript/JS linting
npm run lint -- path/to/file.ts

# Build verification
npm run build

# Test execution
pytest path/to/test_file.py
npm test -- path/to/test_file.ts
```

### Performance Standards

| Metric | Target | Measurement |
|--------|--------|-------------|
| KG processing | 10 docs/min | Phase 09 |
| Hybrid search latency | < 500ms | Phase 10 |
| Query response latency | < 2s | Phase 10 |
| Entity extraction accuracy | ≥ 95% vs AURA-CHAT | Phase 09 |
| Relationship precision | ≥ 80% | Phase 09 |
| Chunking coherence | ≥ 85% | Phase 09 |

### Research Workflow

When implementing features, follow this research sequence:

1. **Web search** for official documentation and best practices
2. **Read existing implementations** in AURA-CHAT (source files)
3. **Consult AGENTS.md** for project-specific conventions
4. **Check ROADMAP.md** for phase context and dependencies
5. **Implement** with TDD approach
6. **Verify** with diagnostics, build, and tests

### Error Handling Protocol

- Never leave empty catch blocks `catch(e) {}`
- Always log errors with context
- Return meaningful error messages to users
- Include error handling in initial implementation, not as afterthought
- Test error paths, not just success paths

### Code Quality Gates

Before marking any task complete:

1. **Syntax**: Code compiles without errors
2. **Types**: No `as any` or `@ts-ignore` suppressions
3. **Linting**: Passes all linting rules
4. **Tests**: All tests pass (unit + integration)
5. **Coverage**: Meet phase-specific coverage targets
6. **Documentation**: File headers present on all new files
7. **Integration**: Works with existing system components

---

## Roadmap Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                    KG PIPELINE ENHANCEMENT (18-30 weeks)                          │
├────────────────────────┬────────────────────────┬────────────────────────────────┤
│       Phase 09         │       Phase 10         │          Phase 11              │
│  Foundation & Intel    │  Interaction Layer     │    Advanced Features           │
│     (6-8 weeks)        │     (6-10 weeks)       │       (6-12 weeks)             │
│                        │                        │                                 │
│  • Neo4j Schema        │  • Hybrid Search       │  • Auto Summarization          │
│  • Hierarchical Chunk  │  • Graph Traversal     │  • Smart Templates             │
│  • LLM Entity Extract  │  • Query API           │  • AURA-CHAT Integration       │
│  • Relationships       │  • Multi-doc Reasoning │  • Multimodal Support          │
│  • Entity Embeddings   │  • Feedback Loop       │  • Insights Generation         │
│  • Semantic Dedup      │  • Interactive UI      │  • Trend Analysis              │
│  • DOCX Parsing        │                        │                                 │
└────────────────────────┴────────────────────────┴────────────────────────────────┘
```

---

## Phase 09: Foundation & Intelligence Layer

**Duration:** 6-8 weeks
**Status:** COMPLETED ✓ (2026-01-24)
**Project:** AURA-NOTES-MANAGER
**Source:** KG-ENHANCEMENT-BRIEF.md + AURA-CHAT implementation
**Review:** `.planning/phases/09-kg-foundation/09-09-REVIEW-SUMMARY.md`

### Objectives
1. Update Neo4j schema with ParentChunk nodes and vector indices
2. Port hierarchical parent-child chunking from AURA-CHAT
3. Port LLM entity extractor with structured prompts
4. Add entity-entity relationship extraction (9 types)
5. Add entity embeddings for all entity types
6. Add semantic deduplication (0.85 cosine threshold)
7. Add DOCX parsing support
8. Integration testing and validation

### Atomic Plans (8 plans, 2-3 tasks each)

| Plan | Focus | Deliverables |
|------|-------|--------------|
| **09-01** | Neo4j Schema Updates | ParentChunk node, vector indices for entities, fulltext index |
| **09-02** | Hierarchical Chunking | Port `chunk_text_hierarchical()` to kg_processor.py |
| **09-03** | LLM Entity Extractor | Create `services/llm_entity_extractor.py` with extraction prompts |
| **09-04** | Relationship Extraction | Add 9 relationship types (DEFINES, DEPENDS_ON, USES, etc.) |
| **09-05** | Entity Embeddings | Generate 768-dim embeddings for Topic, Concept, Methodology, Finding |
| **09-06** | Semantic Deduplication | Add cosine similarity dedup with 0.85 threshold |
| **09-07** | DOCX Parsing | Add python-docx support to document parsing |
| **09-08** | Integration Testing | Validate full pipeline, benchmark against AURA-CHAT |

### Graph Schema (Target)

```cypher
-- ParentChunk node (NEW)
(:ParentChunk {
  id: String!,
  document_id: String!,
  module_id: String,
  text: String!,
  tokens: Integer,
  position: Integer,
  embedding: [Float]!,
  created_at: DateTime!
})

-- Entity nodes with embeddings (ENHANCED)
(:Topic|Concept|Methodology|Finding {
  id: String!,
  name: String!,
  definition: String,
  module_id: String,
  embedding: [Float]!,        -- NEW
  confidence: Float,
  mention_count: Integer,
  created_at: DateTime!
})

-- New relationships
(:Document)-[:HAS_PARENT_CHUNK]->(:ParentChunk)
(:ParentChunk)-[:HAS_CHILD]->(:Chunk)
(:Entity)-[:DEFINES|DEPENDS_ON|USES|SUPPORTS|CONTRADICTS|EXTENDS|IMPLEMENTS|REFERENCES|RELATED_TO]->(:Entity)
```

### Vector Indices (Target)

```cypher
-- Existing (verify)
CREATE VECTOR INDEX chunk_vector_index IF NOT EXISTS
FOR (c:Chunk) ON (c.embedding)
OPTIONS { indexConfig: { `vector.dimensions`: 768, `vector.similarity_function`: 'cosine' } }

-- NEW indices
CREATE VECTOR INDEX parent_chunk_vector_index IF NOT EXISTS
FOR (p:ParentChunk) ON (p.embedding)
OPTIONS { indexConfig: { `vector.dimensions`: 768, `vector.similarity_function`: 'cosine' } }

CREATE VECTOR INDEX topic_vector_index IF NOT EXISTS
FOR (t:Topic) ON (t.embedding)
OPTIONS { indexConfig: { `vector.dimensions`: 768, `vector.similarity_function`: 'cosine' } }

CREATE VECTOR INDEX concept_vector_index IF NOT EXISTS
FOR (c:Concept) ON (c.embedding)
OPTIONS { indexConfig: { `vector.dimensions`: 768, `vector.similarity_function`: 'cosine' } }

CREATE VECTOR INDEX methodology_vector_index IF NOT EXISTS
FOR (m:Methodology) ON (m.embedding)
OPTIONS { indexConfig: { `vector.dimensions`: 768, `vector.similarity_function`: 'cosine' } }

CREATE VECTOR INDEX finding_vector_index IF NOT EXISTS
FOR (f:Finding) ON (f.embedding)
OPTIONS { indexConfig: { `vector.dimensions`: 768, `vector.similarity_function`: 'cosine' } }

-- Fulltext index for hybrid search
CREATE FULLTEXT INDEX chunk_fulltext_index IF NOT EXISTS
FOR (c:Chunk) ON EACH [c.text]
```

### Configuration Values

```python
# Chunking (match AURA-CHAT)
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
```

### Exit Criteria
- [ ] ParentChunk nodes created with proper relationships
- [ ] All entity types have vector indices
- [ ] Fulltext index operational
- [ ] Hierarchical chunking produces parent/child structure
- [ ] 4 entity types extracted (Topic, Concept, Methodology, Finding)
- [ ] 9 relationship types extracted
- [ ] Entity embeddings generated and stored
- [ ] Semantic deduplication reduces duplicates by ≥30%
- [ ] DOCX files parsed successfully
- [ ] Benchmark: ≥95% entity extraction accuracy vs AURA-CHAT

---

## Phase 10: Processing & Interaction Capabilities

**Duration:** 6-10 weeks
**Status:** COMPLETED ✓ (2026-01-24)
**Project:** AURA-NOTES-MANAGER
**Prerequisites:** Phase 09 complete ✓
**Plans:** `.planning/phases/10-kg-interaction/`
**Review:** `.planning/phases/10-kg-interaction/10-07-SUMMARY.md`

### Objectives
1. Add hybrid search (vector + fulltext weighted)
2. Add graph traversal for multi-hop reasoning
3. Create query API for interactive analysis
4. Enable multi-document reasoning
5. Add feedback loop for continuous improvement
6. Build interactive UI components

### Atomic Plans (7 plans, 2-3 tasks each)

| Plan | Focus | Deliverables |
|------|-------|--------------|
| **10-01** | Hybrid Search | Create `api/rag_engine.py` with vector+fulltext weighted search |
| **10-02** | Graph Traversal | Add `expand_graph_context()` for 2-hop entity expansion |
| **10-03** | Query Expansion | Add graph-based query term expansion |
| **10-04** | Query API | Create `api/routers/query.py` with analysis endpoints |
| **10-05** | Multi-doc Reasoning | Enable batch reasoning across module documents |
| **10-06** | Feedback Loop | Add relevance feedback storage and retrieval |
| **10-07** | Interactive UI | Add KG query components to frontend |

### API Endpoints (Target)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/kg/query` | Hybrid search + graph expansion |
| POST | `/v1/kg/analyze` | Summarize/compare/extract actions |
| POST | `/v1/kg/feedback` | Submit relevance feedback |
| GET | `/v1/kg/graph/schema` | Get graph schema |
| GET | `/v1/kg/graph/data` | Get graph data for visualization |

### Hybrid Search Configuration

```python
# Retrieval weights
VECTOR_WEIGHT = 0.7
FULLTEXT_WEIGHT = 0.3
TOP_K_RETRIEVAL = 15
GRAPH_HOP_DEPTH = 2
PARENT_CHUNK_BOOST = 1.2
```

### Exit Criteria
- [x] Hybrid search operational with configurable weights
- [x] Graph traversal expands to 2-hop relationships
- [x] Query API responds < 2s for single module
- [x] Query API responds < 3s for multi-module
- [x] Feedback stored and retrievable
- [x] UI components functional

---

## Phase 11: Advanced Features & Integration

**Duration:** 6-12 weeks
**Status:** READY FOR EXECUTION
**Project:** AURA-NOTES-MANAGER + AURA-CHAT integration
**Prerequisites:** Phase 10 complete ✓
**Plans:** `.planning/phases/11-kg-advanced/` (to be created)

### Objectives
1. Automatic summarization at note/module levels
2. Trend analysis across semesters/modules
3. Smart extraction templates (lecture notes, research, meetings)
4. AURA-CHAT integration (shared KG views)
5. Future multimodal support preparation

### Atomic Plans (6 plans, 2-3 tasks each)

| Plan | Focus | Deliverables |
|------|-------|--------------|
| **11-01** | Auto Summarization | Module-level and note-level summaries via LLM |
| **11-02** | Trend Analysis | Cross-module concept frequency and evolution |
| **11-03** | Smart Templates | Structured extraction for different note types |
| **11-04** | AURA-CHAT Schema Compat | Ensure shared KG schema compatibility |
| **11-05** | Unified Graph Views | Module-level graph visualization across both apps |
| **11-06** | Multimodal Prep | Audio ingestion hooks (Deepgram/Whisper), OCR prep |

### Integration Points

```
AURA-NOTES-MANAGER                      AURA-CHAT
┌─────────────────┐                    ┌─────────────────┐
│  Staff Portal   │                    │  Student Chat   │
│                 │                    │                 │
│  • Create notes │                    │  • RAG queries  │
│  • Process KG   │ ───── Neo4j ───── │  • Study sess   │
│  • Publish      │     (Shared)       │  • Cross-module │
│                 │                    │                 │
└─────────────────┘                    └─────────────────┘
```

### Exit Criteria
- [ ] Auto summaries generated for modules
- [ ] Trend analysis available
- [ ] ≥3 smart templates operational
- [ ] Unified KG views across both apps
- [ ] Multimodal hooks in place (not fully implemented)

---

## Implementation Timeline

| Week | Phase | Focus |
|------|-------|-------|
| 1-2 | 09 | Neo4j schema + hierarchical chunking |
| 3-4 | 09 | LLM entity extractor + relationships |
| 5-6 | 09 | Entity embeddings + semantic dedup |
| 7-8 | 09 | DOCX parsing + integration testing |
| 9-10 | 10 | Hybrid search + graph traversal |
| 11-12 | 10 | Query API + multi-doc reasoning |
| 13-14 | 10 | Feedback loop + interactive UI |
| 15-18 | 11 | Summarization + trend analysis |
| 19-22 | 11 | Smart templates + AURA-CHAT integration |
| 23-26 | 11 | Unified views + multimodal prep |

---

## File Reference

### Source (AURA-CHAT - to port from)

| File | Purpose |
|------|---------|
| `backend/document_processor.py` | Hierarchical chunking, position-weighted embeddings |
| `backend/entity_aware_chunker.py` | Entity-aware chunk boundaries |
| `backend/llm_entity_extractor.py` | Entity extraction prompts, relationship extraction |
| `backend/graph_manager.py` | Neo4j operations, vector indices, traversal |
| `backend/rag_engine.py` | Hybrid search, query expansion |
| `backend/utils/embeddings.py` | Embedding generation, batch processing |
| `backend/utils/config.py` | All configuration values |

### Target (AURA-NOTES-MANAGER - to create/modify)

| File | Action | Phase |
|------|--------|-------|
| `api/neo4j_config.py` | Add indices | 09-01 |
| `api/kg_processor.py` | Enhance with hierarchical chunking | 09-02 |
| `services/llm_entity_extractor.py` | Create new | 09-03 |
| `services/entity_aware_chunker.py` | Create new | 09-02 |
| `services/embeddings.py` | Create new | 09-05 |
| `api/graph_manager.py` | Create new | 10-02 |
| `api/rag_engine.py` | Create new | 10-01 |
| `api/routers/query.py` | Create new | 10-04 |
| `services/summarizer.py` | Create new | 11-01 |

---

## Success Metrics

| Metric | Target | Phase |
|--------|--------|-------|
| Entity extraction accuracy | ≥ 95% vs AURA-CHAT | 09 |
| Relationship precision | ≥ 80% | 09 |
| Chunking coherence | ≥ 85% | 09 |
| KG processing throughput | 10 docs/min | 09 |
| Hybrid search latency | < 500ms | 10 |
| Query response latency | < 2s | 10 |
| Multi-hop reasoning accuracy | ≥ 80% | 10 |
| User satisfaction | ≥ 4.5/5 | 11 |

---

## Roadmap Evolution

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-24 | Initial roadmap from enhancement plan |

---

## Next Steps

1. **Review Agent Behaviour section** - All implementers must read and follow behavioral guidelines
2. Create `.planning/phases/09-kg-foundation/` directory
3. Create 09-01-PLAN.md: Neo4j Schema Updates
4. Execute Phase 09 plans sequentially
