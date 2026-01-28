# AURA Technology Stack

> **Version:** 1.0
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

### Shared Backend Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Runtime** | Python | 3.10+ | Backend execution |
| **Web Framework** | FastAPI | 0.115.0+ | REST API |
| **ASGI Server** | Uvicorn | 0.32.0+ | ASGI server |
| **Task Queue** | Celery | 5.4.0 | Async task processing |
| **Broker** | Redis | 7+ | Message broker |
| **Graph Database** | Neo4j | 5.15+ | Knowledge graph storage + vector search |
| **NoSQL Database** | Firestore | - | Hierarchical note storage |
| **AI/Embeddings** | Google Gemini | Latest | LLM responses |
| **AI Platform** | Vertex AI | 1.39+ | Enterprise AI features |
| **Audio** | Deepgram SDK | 3.5.0 | Speech-to-text |

### Python Dependencies

```txt
# Core Framework
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
python-multipart>=0.0.9
python-dotenv>=1.0.0

# Database
neo4j>=5.15.0
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
PyMuPDF>=1.24.0

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

## Database Architecture

### Neo4j Graph Database

**Purpose:** Store knowledge graphs with entities, relationships, and vector embeddings

**Key Features:**
- Node types: Document, Chunk, Concept, Topic, Finding, Methodology, Other
- HNSW vector index for semantic search (768-dimensional embeddings)
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

## Development Tools

### Code Quality

| Tool | Purpose |
|------|---------|
| ESLint | JavaScript/TypeScript linting |
| Ruff | Python linting (fast, modern) |
| TypeScript | Type checking |
| Pydantic | Python validation |

### Testing

| Type | Tools |
|------|-------|
| Unit (Python) | pytest, pytest-asyncio, pytest-cov |
| Unit (JS) | Vitest |
| E2E | Playwright |
| Benchmark | pytest-benchmark, locust |

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
│   ├── client/             # React 19 frontend
│   └── server/             # FastAPI backend
├── AURA-NOTES-MANAGER/     # Staff portal
│   ├── frontend/           # React 18 frontend
│   ├── api/                # FastAPI backend
│   └── services/           # Audio processing
├── conductor/              # Conductor setup files
├── .planning/              # Project planning docs
└── .venv/                   # Python virtual environment
```

### Nested Git Repositories

**Important:** Both `AURA-CHAT/` and `AURA-NOTES-MANAGER/` contain their own `.git/` directories. Avoid cross-repo operations.

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
