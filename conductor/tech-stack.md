# AURA Technology Stack

> **Version:** 2.0
> **Last Updated:** 2026-02-02
> **Type:** Technical Architecture Document

## Overview

AURA is a dual-application monorepo with separate frontend and backend stacks optimized for each application's specific requirements while sharing common infrastructure.

## Frontend Architecture

### AURA-CHAT (Student-Facing)

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **UI Framework** | React | 19.2.0 | Component-based UI |
| **Build Tool** | Vite | 7.2.4 | Fast development and bundling |
| **Language** | TypeScript | 5.9.3 | Type safety |
| **State Management** | TanStack Query | 5.90.15 | Server state, caching |
| **Routing** | React Router DOM | 7.11.0 | SPA routing |
| **Styling** | TailwindCSS | 4.1.18 | Utility-first CSS |
| **Graph Visualization** | Reagraph | 4.30.7 | 3D WebGL knowledge graph |
| **HTTP Client** | Axios | 1.13.2 | API requests |
| **Markdown Rendering** | React Markdown | 10.1.0 | Render markdown content |
| **API Mocking** | MSW (Mock Service Worker) | 2.12.7 | Mock API for testing |
| **Testing** | Vitest | 3.2.4 | Unit testing |
| **E2E Testing** | Playwright | 1.49.0 | Browser automation |

### AURA-NOTES-MANAGER (Staff Portal)

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **UI Framework** | React | 18.3.1 | Component-based UI |
| **Build Tool** | Vite | 6.0.5 | Fast development and bundling |
| **Language** | TypeScript | 5.6.2 | Type safety |
| **State Management** | Zustand | 5.0.2 | Client UI state |
| **State Management** | TanStack Query | 5.62.0 | Server state, caching |
| **Routing** | React Router DOM | 7.1.0 | SPA routing |
| **Styling** | TailwindCSS | Latest | Utility-first CSS |
| **Animations** | Framer Motion | 12.24.12 | UI animations |
| **Notifications** | Sonner | 2.0.7 | Toast notifications |
| **Testing** | Vitest | 3.2.4 | Unit testing |
| **E2E Testing** | Playwright | 1.50.0 | Browser automation |

## Backend Architecture

### AURA-CHAT Backend Structure

The AURA-CHAT backend is split into two components:

| Component | Location | Technology | Purpose |
|-----------|----------|------------|---------|
| **Modern API** | `server/` | FastAPI 0.115.0+ | Primary REST API, router pattern |
| **Legacy AI Logic** | `backend/` | Python | Document processing, RAG engine, entity extraction |

### AURA-NOTES-MANAGER Backend Structure

| Component | Location | Technology | Purpose |
|-----------|----------|------------|---------|
| **REST API** | `api/` | FastAPI 0.115.0+ | Main API endpoints |
| **AI/ML Services** | `services/` | Python | STT (Deepgram), summarization, PDF generation |

### Shared Backend Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Runtime** | Python | 3.10+ | Backend execution |
| **Web Framework** | FastAPI | 0.115.0+ | REST API |
| **ASGI Server** | Uvicorn | 0.32.0+ | ASGI server |
| **Task Queue** | Celery | 5.4.0 | Async task processing |
| **Broker** | Redis | 7+ | Message broker |
| **Graph Database** | Neo4j | 5.25.0+ | Knowledge graph storage + vector search |
| **NoSQL Database** | Firestore | - | Hierarchical note storage |
| **Audio** | Deepgram SDK | 3.5.0 | Speech-to-text |

### Python Dependencies

```txt
# Core Framework
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
python-multipart>=0.0.9
python-dotenv>=1.0.0

# Database
neo4j>=5.25.0
redis>=5.0.0
firebase-admin>=6.0.0
google-cloud-firestore>=2.0.0

# AI/ML
google-generativeai>=0.3.0
vertexai>=1.0.0
google-cloud-aiplatform>=1.39.0

# Document Processing
PyPDF2>=3.0.0
pdfplumber>=0.10.0
python-docx>=0.8.11
PyMuPDF>=1.24.10
fpdf2>=2.7.9

# Task Queue
celery>=5.4.0

# Utilities
numpy>=1.24.0
tiktoken>=0.5.0
requests>=2.31.0
httpx>=0.25.0
slowapi>=0.1.0
PyJWT>=2.8.0
```

## AI/ML Stack

### Gemini Models

| Model | Version | Use Case |
|-------|---------|----------|
| **Gemini 2.5 Flash** | 2.5-flash | Fast, cost-effective responses |
| **Gemini 2.5 Flash Lite** | 2.5-flash-lite | Lightweight inference |
| **Gemini 2.0 Flash** | 2.0-flash | Balanced performance |
| **Gemini 2.5 Pro** | 2.5-pro | High-quality reasoning |
| **Gemini 3 Flash Preview** | 3-flash-preview | Latest preview features |
| **Text Embedding** | text-embedding-004 | 768-dimensional embeddings |

### AI SDKs

| SDK | Version | Application | Purpose |
|-----|---------|-------------|---------|
| **Google Generative AI SDK** | >=0.3.0 | AURA-CHAT | Thinking mode, chat responses |
| **Vertex AI SDK** | >=1.39.0 | Both | Enterprise AI, embeddings, enterprise features |
| **Deepgram SDK** | 3.5.0 | AURA-NOTES-MANAGER | Speech-to-text transcription |

### AI Capabilities

- **AURA-CHAT**: Hybrid RAG with vector search + graph traversal, thinking mode support
- **AURA-NOTES-MANAGER**: Audio transcription, document summarization, PDF generation

## Database Architecture

### Neo4j Graph Database

**Purpose:** Store knowledge graphs with entities, relationships, and vector embeddings

**Key Features:**
- Node types: Document, Chunk, Concept, Topic, Finding, Methodology, Other
- HNSW vector index for semantic search (768-dimensional embeddings via text-embedding-004)
- Module tagging for scoped queries
- Cross-module concept discovery

**Connection:** `neo4j://localhost:7687` (configurable via `.env`)

### Firestore

**Purpose:** Hierarchical note management, staff hierarchy data

**Collections:**
- `departments` - Department structure
- `semesters` - Semester information
- `notes` - Staff notes and documents

**Connection:** GCP project configuration via service account

### Redis

**Purpose:** Celery broker, caching layer

**Use Cases:**
- Celery task queue messages
- Session caching
- API rate limiting
- Query result caching

**Connection:** `redis://localhost:6379` (configurable via `.env`)

## API Design

### RESTful Endpoints

All APIs follow REST conventions:

```
GET    /api/resources          # List resources
POST   /api/resources          # Create resource
GET    /api/resources/:id      # Get resource
PUT    /api/resources/:id      # Update resource
DELETE /api/resources/:id      # Delete resource
```

### API Ports

| Application | Port | URL |
|-------------|------|-----|
| AURA-CHAT | 8000 | `http://127.0.0.1:8000` |
| AURA-NOTES-MANAGER | 8001 | `http://127.0.0.1:8001` |

### Frontend Ports

| Application | Port | URL |
|-------------|------|-----|
| AURA-CHAT | 5173 | `http://localhost:5173` |
| AURA-NOTES-MANAGER | 5173 | `http://localhost:5173` |

## Testing Stack

### Frontend Testing

| Type | Technology | Version | Purpose |
|------|------------|---------|---------|
| **Unit Testing** | Vitest | 3.2.4 | Component and hook testing |
| **E2E Testing** | Playwright | 1.49.0/1.50.0 | Browser automation, full workflow testing |
| **API Mocking** | MSW | 2.12.7 | Mock API responses for tests |

### Backend Testing

| Type | Technology | Version | Purpose |
|------|------------|---------|---------|
| **Unit Testing** | pytest | 8.3.3 | Python function and API testing |
| **Async Testing** | pytest-asyncio | Latest | Async/await test support |
| **Coverage** | pytest-cov | Latest | Test coverage reporting |
| **Performance** | pytest-benchmark | Latest | Performance regression testing |
| **Load Testing** | Locust | Latest | API load and stress testing |

### Testing Configuration

- **AURA-CHAT**: Parallel E2E execution for speed
- **AURA-NOTES-MANAGER**: Sequential E2E (`fullyParallel: false`) for database consistency

## Development Tools

### Code Quality

| Tool | Purpose |
|------|---------|
| ESLint | JavaScript/TypeScript linting |
| Ruff | Python linting (fast, modern) |
| TypeScript | Type checking |
| Pydantic | Python validation |

### Package Management

| Component | Manager |
|-----------|---------|
| Root | npm (for Gemini CLI) |
| AURA-CHAT | npm |
| AURA-NOTES-MANAGER | npm |
| Python | pip |

## Infrastructure Notes

### Directory Structure

```
AURA-PROJ/
├── AURA-CHAT/              # Student-facing app
│   ├── client/             # React 19 frontend (modern)
│   ├── server/             # FastAPI backend (modern API)
│   ├── backend/            # Legacy AI processing (rag_engine, entity_extractor)
│   └── tests/              # Test suites
├── AURA-NOTES-MANAGER/     # Staff portal
│   ├── frontend/           # React 18 frontend
│   ├── api/                # FastAPI backend
│   ├── services/           # AI/ML layer (STT, summarization, PDF generation)
│   ├── e2e/                # Playwright E2E tests
│   └── tools/              # Utility scripts
├── conductor/              # Conductor setup files
├── .planning/              # Project planning docs (BRIEF.md, ROADMAP.md)
├── .github/workflows/      # CI/CD (GitHub Actions)
└── .venv/                  # Python virtual environment (root level)
```

### Nested Git Repositories

**Important:** Both `AURA-CHAT/` and `AURA-NOTES-MANAGER/` contain their own `.git/` directories. Avoid cross-repo operations.

### Python Environment

**Always use the root venv** (`../.venv` or `../../.venv`) for all Python tasks. Never install dependencies globally or in subdirectory venvs.

```bash
# Correct - use root venv
../.venv/Scripts/python -m pytest tests/
../.venv/Scripts/python -m pip install <package>

# Wrong - do NOT use global Python
python -m pytest tests/
pip install <package>
```

### Environment Variables

Create `.env` files in each backend directory:

```bash
# AURA-CHAT/.env
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
GEMINI_API_KEY=your-key
REDIS_URL=redis://localhost:6379

# AURA-NOTES-MANAGER/.env
# Same as above plus Firestore credentials
GOOGLE_APPLICATION_CREDENTIALS=path/to/firebase.json
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Module creation | < 100ms |
| Document assignment | < 50ms |
| KG processing | < 60s per document |
| RAG query (single module) | < 2s |
| RAG query (multi-module) | < 3s |
| Frontend build | < 60s |
| Test coverage | > 90% |

## References

| Resource | Location |
|----------|----------|
| AURA-CHAT Standards | `AURA-CHAT/client/CLAUDE.md` |
| AURA-NOTES Standards | `AURA-NOTES-MANAGER/frontend/CLAUDE.md` |
| Root Standards | `CLAUDE.md` |
| Requirements | `requirements.txt` |
