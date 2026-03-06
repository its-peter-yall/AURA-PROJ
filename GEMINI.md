# GEMINI.md

**For Google Gemini CLI / Vertex AI Context**

**Generated:** 2026-03-06
**Branch:** master

## PROJECT OVERVIEW

Dual-application monorepo built on Google Cloud stack:

### AURA-CHAT
- **AI:** Google Vertex AI (Gemini for entity extraction, RAG chat)
- **DB:** Neo4j 5.x (knowledge graph with vector search)
- **Frontend:** React 19 + Vite + TypeScript

### AURA-NOTES-MANAGER
- **AI:** Google Gemini (summarization), Deepgram Nova-3 (STT)
- **DB:** Firebase Firestore (NoSQL)
- **Frontend:** React 18 + Vite + TypeScript

## COMPREHENSIVE REFERENCES

### Conductor Documentation

#### conductor/tech-stack.md
Complete technology stack documentation covering:
- **Frontend Technologies**: React 19.2.0 (AURA-CHAT) / React 18.3.1 (AURA-NOTES-MANAGER), Vite 7.2.4/6.0.5, TypeScript 5.9.3/5.6.2
- **State Management**: TanStack Query 5.90.15/5.62.0 (server state), Zustand 5.0.2 (client state)
- **Backend Stack**: Python 3.10+, FastAPI 0.115.0+, Celery 5.4.0, Redis 7+, Neo4j 5.15+
- **AI/ML**: Google Gemini (Latest), Vertex AI 1.39+, Deepgram SDK 3.5.0
- **Database**: Neo4j (graph + vector), Firestore (NoSQL), Redis (caching/broker)
- **Graph Visualization**: Reagraph 4.30.7 (3D WebGL knowledge graph)

#### conductor/product.md
Product features and workflows for the Module-to-Knowledge Graph (M2KG) platform:
- **Vision**: Transform AURA from document-centric to module-centric learning platform
- **AURA-NOTES-MANAGER (Staff)**: Document management, module organization, KG processing, module publishing
- **AURA-CHAT (Student)**: Module selection UI, study sessions, module-aware RAG
- **Core Workflows**: Content publishing workflow (staff), Study session workflow (students)
- **Success Metrics**: Module creation <100ms, Document assignment <50ms, KG processing <60s/doc, RAG query <2-3s

#### conductor/product-guidelines.md
AI assistant tone and design guidelines:
- **Tone**: Friendly/Educational - approachable, explanatory, encouraging, patient
- **Response Structure**: Acknowledge → Answer → Explain → Extend
- **Visual Identity**: Cyber Yellow (#FFD400) primary, Deep Black (#0A0A0A) background
- **Accessibility**: WCAG 2.1 Level AA compliance, keyboard navigation, screen reader support
- **Brand Messaging**: Clear, helpful, professional, inclusive language

#### conductor/workflow.md
Development processes and quality gates:
- **Guiding Principles**: Plan is source of truth, tech stack changes documented first, TDD, >80% coverage, UX first
- **Task Workflow**: Select → Mark In Progress → Write Failing Tests (Red) → Implement (Green) → Refactor → Verify Coverage → Commit with Git Notes
- **Quality Gates**: All tests pass, >80% coverage, style guidelines, documentation, type safety, no lint errors, mobile support
- **Definition of Done**: Code implemented, tests passing, coverage met, docs complete, committed with summary

#### CLAUDE.md (Root Coding Standards)

**TypeScript (Google TypeScript Style)**:
- NO `any` type — use `unknown` or specific types
- Named exports ONLY (no default exports)
- Strict mode: `noUnusedLocals`, `noUnusedParameters` enabled
- Path alias: `@/*` → `./src/*`
- Feature-based: `src/features/{name}/{Page,components,hooks}/`

**Python (Google Python Style)**:
- 4-space indent, 80-char lines
- `router = APIRouter(prefix="/path", tags=["Tag"])`
- Dependency injection via `Depends()`
- F-strings for formatting

### Planning Documentation

#### .planning/BRIEF.md
Dual-project architecture overview:
- **Architecture**: AURA-NOTES-MANAGER (Staff Portal) → Neo4j KG (Shared) → AURA-CHAT (Student Chat)
- **Technology Stack**: Python 3.11+, FastAPI 0.109.0, Celery 5.3.6, Neo4j 5.15+, Redis 7+, React 18.2.0, TypeScript 5.3.3, Gemini text-embedding-004 (768-dim)
- **Project Mapping**: 
  - AURA-NOTES-MANAGER: api/migrations/, api/kg_processor.py, api/tasks/, api/module_manager.py
  - AURA-CHAT: backend/graph_manager.py, backend/rag_engine.py, backend/session_manager.py

#### .planning/ROADMAP.md
Implementation phases and current status (Version 2.4):
- **Phase 1**: Database Schema Extension (Weeks 1-2) - COMPLETED ✓
- **Phase 2**: Knowledge Graph Processor (Weeks 3-4) - COMPLETED ✓
- **Phase 3**: Module Management (Weeks 5-6) - COMPLETED ✓
- **Phase 4**: AURA-CHAT Module Integration (Week 7) - COMPLETED ✓
- **Phase 5**: Study Session System (Weeks 8-9) - COMPLETED ✓
- **Phase 6**: Frontend Implementation (Weeks 10-11) - PLANNED ✓
- **Phase 7**: Testing & Optimization (Week 12) - PLANNED (224+ tests, 70+ E2E tests, Docker)

## STRUCTURE

```
AURA-PROJ/
├── .planning/              # Architecture docs (BRIEF.md, ROADMAP.md)
├── AURA-CHAT/              # Student RAG chat with knowledge graph
│   ├── client/             # React 19 + Vite + TypeScript (MODERN)
│   ├── frontend/           # Streamlit legacy (MIGRATING AWAY)
│   ├── server/             # FastAPI modern backend
│   ├── backend/            # Legacy processing (rag_engine, entity_extractor)
│   └── tests/
├── AURA-NOTES-MANAGER/     # Staff hierarchy & notes
│   ├── frontend/           # React 18 + Vite + TypeScript
│   ├── api/                # FastAPI backend
│   ├── services/           # AI/ML layer (STT, summarization)
│   ├── e2e/                # Playwright tests
│   └── tools/
└── .github/workflows/      # CI/CD (4 systems!)
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| RAG chat development | `AURA-CHAT/client/src/features/chat/` |
| Knowledge graph | `AURA-CHAT/client/src/features/graph/` |
| Module selection UI | `AURA-CHAT/client/src/features/modules/` |
| Study sessions | `AURA-CHAT/client/src/features/study-sessions/` |
| Session management | `AURA-CHAT/backend/routers/sessions.py` |
| Note management | `AURA-NOTES-MANAGER/frontend/src/pages/` |
| KG processing UI | `AURA-NOTES-MANAGER/frontend/src/features/kg/` |
| Audio-to-notes pipeline | `AURA-NOTES-MANAGER/services/` (STT, summarization, PDF) |
| Document processing | `AURA-CHAT/backend/` |
| Backend API (chat) | `AURA-CHAT/server/routers/` |
| Backend API (notes) | `AURA-NOTES-MANAGER/api/` |

## CONVENTIONS (DEVIATIONS FROM STANDARD)

### TypeScript/React
- **Google TypeScript Style Guide** enforced (no `any`, named exports only)
- Feature-based architecture: `src/features/{name}/{Page,components,hooks}/`
- Path alias: `@/*` → `./src/*`
- Custom "Cyber Yellow" theme: `#FFD400`
- ESLint flat config with React hooks rules

### Python/FastAPI
- **Google Python Style Guide** enforced (pylint, 4-space indent, 80-char lines)
- Router pattern: `router = APIRouter(prefix="/path", tags=["Tag"])`
- Dependency injection via `Depends()`
- Global exception handler in `main.py`

### Python Environment
- **ALWAYS use the root venv** (`../.venv` or `../../.venv`) for all Python tasks
- **NEVER install dependencies globally** or in subdirectory venvs
- Run Python commands with the root venv:
  ```bash
  # Correct - use root venv
  ../.venv/Scripts/python -m pytest tests/
  ../.venv/Scripts/python -m pip install <package>

  # Wrong - do NOT use global Python
  python -m pytest tests/
  pip install <package>
  ```
- Python test commands must always reference the root venv interpreter

### E2E Testing
- **AURA-NOTES-MANAGER**: Sequential (`fullyParallel: false`) for DB consistency
- **AURA-CHAT**: Parallel execution

## UNIQUE STYLES

- **Services abstraction layer** (AURA-NOTES-MANAGER): STT, summarization, PDF gen isolated in `services/`
- **Dual database strategy**: Neo4j (graph) for chat, Firestore (NoSQL) for notes
- **Dual AI providers**: Vertex AI (chat) vs Gemini + Deepgram (notes)
- **Architecture docs**: Comprehensive specs in `.planning/` and `architecture-spec.md`

## COMMANDS

```bash
# AURA-CHAT
cd AURA-CHAT/client && npm run dev      # Frontend (5173)
cd AURA-CHAT/server && python main.py   # Backend (8000)

# AURA-NOTES-MANAGER
cd AURA-NOTES-MANAGER/frontend && npm run dev   # Frontend (5173)
cd AURA-NOTES-MANAGER/api && python main.py     # Backend (8001)

# E2E Tests
cd AURA-CHAT/client && npm run test:e2e
cd AURA-NOTES-MANAGER && npm run test:e2e
```

## NOTES

- API base: `http://127.0.0.1:8000` (AURA-CHAT) or proxied `/api` (AURA-NOTES-MANAGER)
- Use `127.0.0.1` not `localhost` to avoid IPv6 issues
- 5-min timeout for document processing endpoints
- Read `.planning/BRIEF.md` for architecture context

## ENVIRONMENT VARIABLES

Create `.env` files in each backend directory:

| Variable | Description | Required By | Example |
|----------|-------------|-------------|---------|
| `NEO4J_URI` | Neo4j connection string | Both | `neo4j://localhost:7687` |
| `NEO4J_USER` | Neo4j username | Both | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | Both | `password` |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | Both | `aura-project-123` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | Both | `/path/to/credentials.json` |
| `DEEPGRAM_API_KEY` | Deepgram API key for STT | AURA-NOTES-MANAGER | `dg_abc123...` |
| `REDIS_URL` | Redis connection for Celery | Both | `redis://localhost:6379` |
| `AURA_TEST_MODE` | Enable test mode features | Both | `true` or `false` |
| `GEMINI_API_KEY` | Gemini API key (legacy) | Both | `AIza...` |

**Note:** Use `127.0.0.1` in URLs, never `localhost` (avoid IPv6 issues).

## TESTING STRATEGY

### Test Organization

| Level | Tool | Target | Location |
|-------|------|--------|----------|
| **Unit (Python)** | pytest | >85% coverage | `AURA-CHAT/tests/unit/`, `AURA-NOTES-MANAGER/api/tests/` |
| **Unit (Frontend)** | Vitest | >80% coverage | `*/src/**/*.test.tsx` |
| **E2E** | Playwright | All browsers | `AURA-CHAT/client/e2e/`, `AURA-NOTES-MANAGER/e2e/` |
| **Performance** | pytest-benchmark | Targets met | `tests/performance/` |
| **Load** | Locust | 5 scenarios | `tests/load/locustfile.py` |

### E2E Configuration

**AURA-NOTES-MANAGER:**
```javascript
// playwright.config.ts
fullyParallel: false  // Sequential for DB consistency
```

**AURA-CHAT:**
```javascript
// playwright.config.ts
fullyParallel: true   // Parallel execution supported
```

### Running Tests

```bash
# Always use root venv for Python tests
../.venv/Scripts/python -m pytest AURA-CHAT/tests/ -v
../.venv/Scripts/python -m pytest AURA-NOTES-MANAGER/api/tests/ -v

# Frontend tests
cd AURA-CHAT/client && npm run test:unit
cd AURA-NOTES-MANAGER/frontend && npm run test

# E2E tests
cd AURA-CHAT/client && npm run test:e2e
cd AURA-NOTES-MANAGER && npm run test:e2e
```

### Quality Gates

Before marking complete:
- [ ] All unit tests pass
- [ ] Code coverage meets targets (>80% frontend, >85% backend)
- [ ] E2E tests pass (sequential for NOTES, parallel for CHAT)
- [ ] No linting errors
- [ ] Type checking passes
- [ ] LSP diagnostics clean

## GOOGLE CLOUD INTEGRATION

### Complete Vertex AI Configuration

#### Required Environment Variables
```bash
# Core Google Cloud
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=./path/to/service_account.json
GOOGLE_CLOUD_REGION=us-central1  # Or your preferred region

# AURA-NOTES-MANAGER Firestore
GOOGLE_APPLICATION_CREDENTIALS=./serviceAccountKey.json

# Deepgram (AURA-NOTES-MANAGER)
DEEPGRAM_API_KEY=your_deepgram_key
```

#### Service Account Configuration
```bash
# Create service account
GOOGLE_APPLICATION_CREDENTIALS=./serviceAccountKey.json

# Required roles:
# - roles/aiplatform.user (Vertex AI access)
# - roles/datastore.user (Firestore access)
# - roles/storage.objectViewer (if using GCS)
```

### Gemini Model Specifications

| Model | Version | Purpose | Context Window | Key Features |
|-------|---------|---------|----------------|--------------|
| **gemini-2.5-flash** | Latest | Entity extraction | 1M tokens | Fast, cost-effective, structured JSON output |
| **gemini-2.0-flash** | Latest | Chat responses | 1M tokens | Balanced speed/quality, RAG synthesis |
| **gemini-2.5-pro** | Latest | Complex analysis | 2M tokens | Deep reasoning, multi-step analysis |
| **gemini-2.5-flash-lite** | Latest | Thinking mode | 1M tokens | Lightweight reasoning, budget-friendly |
| **gemini-3-flash-preview** | Preview | Thinking mode | 1M tokens | Next-gen thinking capabilities |

### Embeddings Configuration

**text-embedding-004** (Primary embedding model):
- **Dimensions**: 768
- **Model ID**: `text-embedding-004`
- **Use Cases**: Document chunking, entity similarity, RAG retrieval
- **HNSW Index Configuration**:
  ```cypher
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

### Firestore Setup Instructions

```bash
# Deploy Firestore rules and indexes
firebase deploy --only firestore:rules,firestore:indexes

# Collections structure:
# - departments: Department hierarchy
# - semesters: Semester information  
# - notes: Staff notes and documents
```

## DUAL SDK ARCHITECTURE

### Hybrid Approach Overview

The project uses both SDKs for different use cases:

#### 1. vertexai SDK (Standard API Calls)
**Purpose**: Standard Gemini API interactions, embeddings, entity extraction

**Usage**:
```python
import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project=project_id, location=location)
model = GenerativeModel("gemini-2.0-flash")
response = model.generate_content(prompt)
```

**Use Cases**:
- Entity extraction from documents
- Standard chat responses
- Embedding generation (text-embedding-004)
- Structured JSON output

#### 2. google-genai SDK (Thinking Mode)
**Purpose**: Advanced reasoning and thinking capabilities

**Usage**:
```python
from google import genai
from google.genai import types

client = genai.Client(vertexai=True, project=project_id, location=location)
response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents=prompt,
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(enable_thinking=True)
    )
)
```

**Use Cases**:
- Complex reasoning tasks
- Multi-step analysis
- Chain-of-thought responses

### Migration Rationale

- **vertexai SDK**: Mature, stable, well-documented for standard operations
- **google-genai SDK**: Cutting-edge features (thinking mode, multimodal), active development
- **Hybrid approach**: Leverage stability of vertexai for core operations while using genai for advanced features

### Implementation Details

```python
# SDK Selection Logic
if requires_thinking or complex_reasoning:
    use_genai_sdk()  # google-genai
else:
    use_vertexai_sdk()  # vertexai
```

### Quick Task 1: DOM Confirm Dialog Replacement
**Date:** February 2026

Replaced native browser `confirm()` dialog with custom UI-themed dialog component in User Management:
- New `ConfirmDialog` component using project's Cyber Yellow (#FFD400) design system
- Consistent styling with existing modal patterns
- Improved accessibility with proper ARIA attributes
- Located in `AURA-NOTES-MANAGER/frontend/src/components/ConfirmDialog.tsx`

## AURA-CHAT SPECIFICS

### Thinking Mode Implementation

**Configuration**:
```python
from google import genai
from google.genai import types

client = genai.Client(vertexai=True, project=project_id, location=location)

# Enable thinking mode
response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents=user_message,
    config=types.GenerateContentConfig(
        temperature=0.7,
        max_output_tokens=2048,
        thinking_config=types.ThinkingConfig(enable_thinking=True)
    )
)
```

**Storage**:
- Raw thinking content stored in `Message.thinking_content`
- Processed response in `Message.content`
- Toggle in session settings to show/hide thinking

### Session-Based Architecture

**StudySession Node**:
```cypher
(:StudySession {
  id: String!,
  title: String!,
  module_ids: [String]!,
  user_id: String!,
  status: String!,  # "active", "paused", "completed", "archived"
  message_count: Integer,
  settings: String,
  created_at: DateTime!,
  updated_at: DateTime!,
  is_active: Boolean!
})
```

**Session Flow**:
1. Student selects module(s) from dropdown
2. System creates StudySession with module_ids
3. Messages linked via `:HAS_MESSAGE` relationship
4. Session persists for future reference
5. Analytics tracked (message_count, engagement)

### RAG Engine with Module Filtering

**Module-Filtered Query**:
```python
async def query_with_modules(
    self,
    user_query: str,
    module_ids: List[str],
    session_id: Optional[str] = None,
    enable_cross_module: bool = True
) -> QueryResult:
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

**Cross-Module Discovery**:
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

### Knowledge Graph Visualization with Reagraph

**Technology**: Reagraph 4.30.7 (3D WebGL knowledge graph)

**Features**:
- Interactive 3D graph visualization
- Entity nodes with relationships
- Module-scoped filtering
- Zoom, pan, rotate controls
- Node selection for details

**Implementation**:
```typescript
import { GraphCanvas } from 'reagraph';

// Graph data structure
const graphData = {
  nodes: [
    { id: 'entity1', label: 'Machine Learning', type: 'Concept' },
    { id: 'entity2', label: 'Neural Networks', type: 'Topic' }
  ],
  edges: [
    { id: 'rel1', source: 'entity1', target: 'entity2', label: 'DEFINES' }
  ]
};
```

## AURA-NOTES-MANAGER SPECIFICS

### Deepgram Nova-3 STT Configuration

**SDK**: Deepgram SDK 3.5.0

**Configuration**:
```python
from deepgram import DeepgramClient, PrerecordedOptions

deepgram = DeepgramClient(DEEPGRAM_API_KEY)

options = PrerecordedOptions(
    model="nova-3",
    language="en",
    punctuate=True,
    paragraphs=True,
    diarize=True,  # Speaker identification
    smart_format=True
)

response = deepgram.listen.prerecorded.v("1").transcribe_file(
    audio_file,
    options
)
```

**Features**:
- **Nova-3 Model**: Latest ASR with best accuracy
- **Diarization**: Speaker identification
- **Smart Format**: Automatic punctuation and formatting
- **Paragraphs**: Logical text segmentation

### 4-Step Audio Pipeline

```
Audio Upload
     │
     ▼
┌─────────────────┐
│ 1. TRANSCRIBE   │  → Deepgram Nova-3 STT
│                 │     Speaker-aware transcription
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ 2. REFINE       │  → Gemini content cleanup
│                 │     Remove filler words, format structure
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ 3. SUMMARIZE    │  → Gemini summarization
│                 │     Extract key points, action items
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ 4. PDF GEN      │  → Structured PDF output
│                 │     Formatted transcript + summary
└─────────────────┘
```

**Implementation**:
```python
async def process_audio_to_notes(audio_file: bytes) -> Note:
    # Step 1: Transcribe
    transcript = await stt.transcribe(audio_file)
    
    # Step 2: Refine content
    refined = await gemini.refine_transcript(transcript)
    
    # Step 3: Summarize
    summary = await gemini.summarize(refined)
    
    # Step 4: Generate PDF
    pdf = await pdf_generator.create(refined, summary)
    
    return Note(transcript=refined, summary=summary, pdf=pdf)
```

### KG Processing Workflow

**Document Processing Flow**:
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
│ Extract Entities│  → Gemini LLM extracts entities
│                 │     Types: Topic, Concept, Methodology, Finding
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Build Relations │  → Entity relationships
│                 │     Types: DEFINES, DEPENDS_ON, USES
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Store in Neo4j  │  → All nodes tagged with module_id
└─────────────────┘
```

**Celery Task Configuration**:
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

### Module Publishing System

**Publishing Workflow**:
```
┌─────────┐    ┌──────────┐    ┌─────────┐
│  Draft  │───▶│Processing│───▶│  Ready  │
└─────────┘    └──────────┘    └─────────┘
     │                              │
     │                              ▼
     │                        ┌─────────┐
     │                        │ Review  │
     │                        └─────────┘
     │                              │
     │                              ▼
     │                        ┌─────────┐
     └───────────────────────▶│Published│
                              └─────────┘
```

**Status Values**:
- `draft` - Initial state, editable
- `processing` - KG generation in progress
- `ready` - KG generated, awaiting review
- `published` - Available to students
- `archived` - No longer active

**API Endpoints**:
```
POST /api/modules/{id}/process    → Trigger KG processing
POST /api/modules/{id}/publish    → Publish to students
POST /api/modules/{id}/unpublish  → Unpublish
GET  /api/modules/{id}/kg-status  → Get KG processing status
```

## FILE LOCATIONS

| Component | Path |
|-----------|------|
| Vertex AI client | `AURA-NOTES-MANAGER/services/vertex_ai_client.py` |
| Entity extractor | `AURA-CHAT/backend/llm_entity_extractor.py` |
| RAG engine | `AURA-CHAT/backend/rag_engine.py` |
| Session manager | `AURA-CHAT/backend/session_manager.py` |
| STT service | `AURA-NOTES-MANAGER/services/stt.py` |
| Summarizer | `AURA-NOTES-MANAGER/services/summarizer.py` |
| KG processor | `AURA-NOTES-MANAGER/api/kg_processor.py` |
| Audio processing | `AURA-NOTES-MANAGER/api/audio_processing.py` |

## DEVELOPMENT NOTES

### AURA-CHAT Stack
```
Frontend: React 19 + Vite + Tailwind + Reagraph
Backend:  FastAPI (server/) + legacy (backend/)
DB:       Neo4j (graph + vector)
AI:       Vertex AI Gemini (dual SDK)
```

### AURA-NOTES-MANAGER Stack
```
Frontend: React 18 + Vite + Tailwind + Zustand
Backend:  FastAPI (api/)
DB:       Firestore (NoSQL) + Neo4j (KG)
AI:       Gemini + Deepgram
```

## RUN COMMANDS

```bash
# AURA-CHAT
cd AURA-CHAT/client && npm run dev
cd AURA-CHAT/server && python main.py

# AURA-NOTES-MANAGER
cd AURA-NOTES-MANAGER/frontend && npm run dev
cd AURA-NOTES-MANAGER/api && python main.py
```

## ANTI-PATTERNS TO AVOID

1. **Nested Git repos**: Don't run git commands across subprojects
2. **Legacy code**: Use `client/` not `frontend/` in AURA-CHAT
3. **IPv6 issues**: Always use `127.0.0.1` for localhost
4. **Conflicting CI**: 4 systems exist — verify which applies
5. **SDK confusion**: Use vertexai for standard calls, google-genai for thinking mode

## AGENT BEHAVIOUR

### Research-First Principle
- **ALWAYS web-search before implementing** unfamiliar libraries, APIs, or patterns
- **NEVER assume** library behavior — verify with official documentation
- **Search first** when encountering: new npm packages, Python libraries, framework features, or external APIs
- Use `librarian` agent for documentation lookup, `explore` agent for codebase patterns

### SWE Best Practices
- **Write tests BEFORE or WITH code**, not after — TDD when appropriate
- **Verify with diagnostics**: Run `lsp_diagnostics` before marking tasks complete
- **Build & test**: Always run build/test commands after implementation
- **Type safety first**: Never suppress type errors with `as any`, `@ts-ignore`
- **Error handling**: Never leave empty catch blocks `catch(e) {}`
- **Minimal changes**: Fix bugs without refactoring unrelated code

### Never Be Lazy
- **Don't skip verification** — always run diagnostics, build, and tests
- **Don't guess** — search for patterns, ask clarification questions when ambiguous
- **Don't partial-ship** — task is complete ONLY when all criteria met
- **Don't assume knowledge** — read the relevant code before modifying
- **Don't skip tests** — verify functionality, not just compilation

### Certainty Before Conclusion
- **NEVER declare complete** without 100% confidence
- **Verify every requirement** from the original request is addressed
- **Check for regressions**: Run relevant tests before claiming fix
- **Run diagnostics**: Ensure no new errors introduced
- **If uncertain, ask**: Better to clarify than ship broken code

### Productivity & Intelligence
- **Parallel execution**: Use background agents for independent tasks (explore, librarian, document-writer)
- **Delegate visual work**: Always use `frontend-ui-ux-engineer` agent for styling/layout changes
- **Consult Oracle** for: architecture decisions, 2+ failed fix attempts, complex debugging
- **Use todo tracking**: Mark in_progress → completed in real-time
- **Batch small tasks**: Group related edits, run diagnostics once
- **Think before code**: Understand the problem, then implement
- **Learn from failures**: Document what failed, consult Oracle after 3 attempts

### Delegation Guidelines
| Domain | Delegate To | When |
|--------|-------------|------|
| Visual/UI changes | `frontend-ui-ux-engineer` | Styling, layout, animations |
| External docs | `librarian` | Library API, official docs |
| Codebase patterns | `explore` | Finding existing implementations |
| Architecture review | `oracle` | Multi-system tradeoffs, design |
| Documentation | `document-writer` | READMEs, guides, AGENTS.md |
| Hard debugging | `oracle` | After 2+ failed fix attempts |

### Use Sub-Agents to Extend Sessions
- **Use suitable and available sub-agents whenever possible** to extend the current session by conserving the context window
- Sub-agents are crucial for **long-running tasks** that involve multiple files, complex exploration, or extensive modifications
- Launching sub-agents allows:
  - Fresh context windows for each subtask
  - Parallel execution of independent operations
  - Better focus on specific domains (visual, documentation, debugging)
- Delegate appropriately using the guidelines above — don't try to handle everything in a single session

### Evidence Requirements
Task is NOT complete without:
- [ ] `lsp_diagnostics` clean on changed files
- [ ] Build passes (if applicable)
- [ ] Tests pass (or explicit note of pre-existing failures)
- [ ] User's original request fully addressed

### File Header Requirements
**MANDATORY for every code file created or updated:**

```typescript
// {FILE_NAME}
// {Brief 1-line description of what this file does}

// Longer description (2-4 lines):
// - What problem does this file solve?
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
// @note: 2-hop graph traversal limits may need tuning for large graphs
```

**Enforcement:**
- File headers are REQUIRED for: `.ts`, `.tsx`, `.py`, `.pyi`, `.js`, `.jsx`
- Existing files without headers: Add when modifying significantly (>30% changes)
- New files: ALWAYS add header before first write
- Configuration files (tsconfig.json, pyproject.toml): Optional but encouraged
