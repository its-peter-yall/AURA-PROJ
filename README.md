# AURA - Academic Understanding & Research Assistant

> **Version:** 2.0 (Module-Centric Architecture)
> **Last Updated:** April 2026

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Applications](#applications)
  - [AURA-CHAT](#aura-chat)
  - [AURA-NOTES-MANAGER](#aura-notes-manager)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Running the Applications](#running-the-applications)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Contributing](#contributing)

---

## Overview

AURA is a dual-application academic platform that transforms how students and staff interact with educational content through AI-powered knowledge graphs and Retrieval-Augmented Generation (RAG).

**Vision:** Transform document-centric learning into a module-centric platform where users organize documents into thematic modules, study within focused context-aware sessions, and explore interconnected knowledge graphs.

**Key Capabilities:**
- **Knowledge Graph Generation** - Automatically extract entities and relationships from academic documents
- **Module-Aware RAG Chat** - Query documents with natural language, augmented by cross-document relationships
- **3D Graph Visualization** - Explore knowledge connections via interactive WebGL graph explorer
- **Audio-to-Notes Pipeline** - Convert voice recordings into structured notes using STT and AI summarization
- **Hierarchical Content Management** - Organize content via Department > Semester > Subject > Module hierarchy

---

## Architecture

```
                    AURA-NOTES-MANAGER (Staff Portal)
    ┌─────────────────────────────────────────────────────────────┐
    │  Document Management    Module Organization    KG Processing│
    │  • PDF/Text Upload      • Hierarchy CRUD       • Chunk/Embed│
    │  • Audio-to-Notes       • Module Publishing    • Extract    │
    └──────────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │        Neo4j KG (Shared)     │
                    │  • Graph + Vector Index      │
                    │  • Module-scoped entities    │
                    └─────────────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │                    AURA-CHAT (Student Chat)                  │
                    │  ┌─────────────────────────────────────────────────────┐    │
                    │  │ Module Selection      Study Sessions      RAG Chat   │    │
                    │  │ • Browse modules      • Persistent chats  • Streaming│    │
                    │  │ • Multi-select        • Context-aware     • Citations│    │
                    │  └─────────────────────────────────────────────────────┘    │
                    └─────────────────────────────────────────────────────────────┘
```

---

## Applications

### AURA-CHAT

**Student-facing academic RAG chat with knowledge graph exploration.**

| Feature | Description |
|---------|-------------|
| **Module-Aware RAG** | Query academic documents with responses augmented by cross-document relationships |
| **Study Sessions** | Persistent chat sessions scoped to selected modules with full message history |
| **3D Graph Explorer** | Interactive WebGL visualization of knowledge graph connections (Reagraph) |
| **Thinking Mode** | Visualize LLM reasoning process with Gemini 2.0 Flash Thinking |
| **Document Management** | Upload, process, and manage academic documents |
| **Real-time Updates** | WebSocket-powered job progress tracking |

**Technology:** React 19 + Vite 7 + TypeScript 5.9 (Strict) + Tailwind CSS 4 | FastAPI + Neo4j + Vertex AI

**Ports:** Frontend `5173` | Backend `8000`

---

### AURA-NOTES-MANAGER

**Staff portal for hierarchy management, note processing, and knowledge graph generation.**

| Feature | Description |
|---------|-------------|
| **Hierarchical Explorer** | Navigate Department > Semester > Subject > Module structure |
| **Document Upload** | Upload PDF, DOC, TXT files to specific modules |
| **Audio-to-Notes** | Transcribe voice recordings via Deepgram, summarize with AI, export to PDF |
| **KG Processing** | Chunk documents, extract entities/relationships, generate embeddings, store in Neo4j |
| **Module Publishing** | Review knowledge graphs before publishing to students |
| **Role-Based Access** | Admin (full), Staff (department), Student (read-only) |

**Technology:** React 18 + Vite 6 + TypeScript 5.6 + Tailwind CSS | FastAPI + Firestore + Neo4j + Deepgram

**Ports:** Frontend `5173` | Backend `8001`

---

## Technology Stack

### Frontend

| Component | AURA-CHAT | AURA-NOTES-MANAGER |
|-----------|-----------|-------------------|
| React | ^19.2.0 | ^18.3.1 |
| TypeScript | ~5.9.3 (Strict) | ~5.6.2 |
| Vite | ^7.2.4 | ^6.0.5 |
| Tailwind CSS | ^4.1.18 | ^3.x |
| State Management | Zustand + TanStack Query | Zustand + TanStack Query |
| Routing | react-router-dom ^7.11 | - |
| Graph Viz | reagraph ^4.30.7 (WebGL) | - |
| Testing | Vitest + Playwright | Vitest + Playwright |

### Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API Framework | FastAPI 0.109+ | HTTP API layer |
| Python | 3.10+ | Runtime |
| Graph Database | Neo4j 5.13+ | Knowledge graph + vector search |
| Document DB | Firebase Firestore | Notes/permissions data |
| Cache/Queue | Redis 7+ | ARQ task queue, caching |
| AI/ML (Chat) | Google Vertex AI / Gemini | RAG, embeddings, extraction |
| AI/ML (Notes) | Google Gemini + Deepgram | STT, summarization |
| Task Queue | ARQ (async Redis) | Background document processing |
| Auth | Firebase Auth | Email/password authentication |

### Shared Components

- **Model Router** (`shared/model_router/`) - Provider-agnostic Python package for generation and embedding contracts
- **Dual AI SDKs** - Vertex AI SDK (advanced features) + Google Generative AI SDK (standard completions)

---

## Prerequisites

### Required Software

- **Python** 3.10+ (3.11 recommended)
- **Node.js** 18+ (with npm)
- **Neo4j** 5.13+ (Community Edition)
- **Redis** 7+

### External Services

- **Google Cloud Project** with Vertex AI enabled
- **Firebase Project** with Firestore enabled
- **Deepgram Account** (for audio transcription - AURA-NOTES-MANAGER)

### Service Account Setup

1. Create a Firebase project at [https://console.firebase.google.com/](https://console.firebase.google.com/)
2. Enable Firestore in the Firebase Console
3. Generate a service account key:
   - Go to Project Settings > Service Accounts
   - Click "Generate New Private Key"
   - Save as `serviceAccountKey.json` (add to `.gitignore` - **never commit**)

---

## Installation & Setup

### 1. Clone and Enter Project

```bash
git clone <repository-url>
cd AURA-PROJ
```

### 2. Python Environment Setup

**Always use the root virtual environment for all Python tasks.**

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

> **Important:** Never install dependencies globally or create local venvs in subdirectories.

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
# Neo4j Configuration
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# Google Cloud / Firebase
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=./serviceAccountKey.json

# Deepgram (AURA-NOTES-MANAGER)
DEEPGRAM_API_KEY=your_deepgram_api_key

# Redis
REDIS_URL=redis://127.0.0.1:6379

# Test Mode
AURA_TEST_MODE=false
```

> **Security:** Never commit `.env`, credential files, or keys to git. The repository uses gitleaks CI to prevent secret leaks.

### 4. Frontend Setup

#### AURA-CHAT Client

```bash
cd AURA-CHAT/client
npm install
```

#### AURA-NOTES-MANAGER Frontend

```bash
cd AURA-NOTES-MANAGER/frontend
npm install
```

### 5. Firebase Rules Deployment (AURA-NOTES-MANAGER)

```bash
firebase login
firebase use <your-project-id>
firebase deploy --only firestore:rules,firestore:indexes
```

---

## Running the Applications

### AURA-CHAT

**Terminal 1 - Backend:**
```bash
# From project root with venv activated
uvicorn AURA-CHAT.server.main:app --reload --port 8000
```
API: http://127.0.0.1:8000

**Terminal 2 - Frontend:**
```bash
cd AURA-CHAT/client
npm run dev
```
Frontend: http://127.0.0.1:5173

### AURA-NOTES-MANAGER

**Terminal 1 - Backend:**
```bash
# From project root with venv activated
uvicorn AURA-NOTES-MANAGER.api.main:app --reload --port 8001
```
API: http://127.0.0.1:8001

**Terminal 2 - Frontend:**
```bash
cd AURA-NOTES-MANAGER/frontend
npm run dev
```
Frontend: http://127.0.0.1:5173 (or next available port)

### Test Accounts (AURA-NOTES-MANAGER - Mock Auth)

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@test.com | Admin123! |
| Staff | staff@test.com | Staff123! |
| Student | student@test.com | Student123! |

---

## Development Workflow

### Code Style

We follow the **Google Style Guide** for both TypeScript and Python:

- **TypeScript:** Single quotes, explicit semicolons, no `var`, no default exports, strict types
- **Python:** 80-character line limit, 4-space indentation, docstrings required
- **File Headers:** Mandatory for all `.ts`, `.tsx`, `.py` files

### Branch Strategy

- `master` - Production-ready code
- Feature branches: `feature/description`
- Phase branches for major milestones (see `.planning/ROADMAP.md`)

### Commit Standards

- Write tests before or with code (TDD preferred)
- Run diagnostics before committing
- Ensure builds pass and tests are green
- Update documentation when changing architecture

---

## Testing

### Test Organization

| Level | Tool | Target | Location |
|-------|------|--------|----------|
| **Unit (Python)** | pytest | >85% coverage | `AURA-CHAT/tests/`, `AURA-NOTES-MANAGER/api/tests/` |
| **Unit (Frontend)** | Vitest | >80% coverage | `*/src/**/*.test.tsx` |
| **E2E** | Playwright | All browsers | `AURA-CHAT/client/e2e/`, `AURA-NOTES-MANAGER/frontend/e2e/` |
| **Performance** | pytest-benchmark | Targets met | `tests/performance/` |
| **Load** | Locust | 5 scenarios | `tests/load/locustfile.py` |

### Running Tests

**AURA-CHAT:**
```bash
# Python tests (from project root with venv)
python -m pytest AURA-CHAT/tests/ -v
python -m pytest --cov=backend --cov=server AURA-CHAT/tests/

# Frontend unit tests
cd AURA-CHAT/client && npm run test

# E2E tests (parallel execution)
cd AURA-CHAT/client && npm run test:e2e
```

**AURA-NOTES-MANAGER:**
```bash
# Python tests (from project root with venv)
python -m pytest AURA-NOTES-MANAGER/api/tests/ -v

# Frontend unit tests
cd AURA-NOTES-MANAGER/frontend && npm test

# E2E tests (sequential for DB consistency)
cd AURA-NOTES-MANAGER/frontend && npm run test:e2e
```

### Quality Gates

Before marking any task complete:
- [ ] All unit tests pass
- [ ] Code coverage meets targets (>80% frontend, >85% backend)
- [ ] E2E tests pass
- [ ] No linting errors (`npm run lint`)
- [ ] Type checking passes (`npx tsc --noEmit`)

---

## Environment Variables

| Variable | Description | Required By | Example |
|----------|-------------|-------------|---------|
| `NEO4J_URI` | Neo4j connection string | Both | `neo4j://127.0.0.1:7687` |
| `NEO4J_USER` | Neo4j username | Both | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | Both | `password` |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | Both | `aura-project-123` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | Both | `./serviceAccountKey.json` |
| `DEEPGRAM_API_KEY` | Deepgram API key for STT | AURA-NOTES-MANAGER | `dg_abc123...` |
| `REDIS_URL` | Redis connection for task queue | Both | `redis://127.0.0.1:6379` |
| `AURA_TEST_MODE` | Enable test mode features | Both | `false` |
| `GEMINI_API_KEY` | Gemini API key (legacy) | Both | `AIza...` |

> **Note:** Use `127.0.0.1` in URLs, never `localhost` (to avoid IPv6 issues).

---

## Project Structure

```
AURA-PROJ/
|
├── AURA-CHAT/                          # Student RAG Chat Application
│   ├── client/                         # React 19 + Vite 7 + TypeScript (Modern)
│   │   ├── src/
│   │   │   ├── features/               # Feature-based architecture
│   │   │   │   ├── auth/               # Login page
│   │   │   │   ├── chat/               # RAG chat interface
│   │   │   │   ├── documents/          # Document management
│   │   │   │   ├── graph/              # 3D Reagraph visualization
│   │   │   │   ├── modules/            # Module/course management
│   │   │   │   ├── settings/           # App configuration
│   │   │   │   └── study-sessions/     # Session CRUD hooks
│   │   │   ├── components/             # Shared components
│   │   │   ├── stores/                 # Zustand auth state
│   │   │   ├── lib/                    # API client, Firebase, utils
│   │   │   ├── hooks/                  # Custom hooks
│   │   │   └── types/                  # TypeScript types
│   │   └── e2e/                        # Playwright E2E tests
│   ├── server/                         # FastAPI modern backend
│   │   ├── routers/                    # API endpoints (auth, chat, docs, graph, jobs)
│   │   ├── auth/                       # Firebase auth, Firestore client
│   │   └── schemas/                    # Pydantic request/response schemas
│   ├── backend/                        # Legacy processing (migrating)
│   │   ├── chat_manager.py             # Chat orchestration
│   │   ├── document_processor.py       # Pipeline orchestrator
│   │   ├── rag_engine.py               # Vector search + graph traversal
│   │   ├── graph_manager.py            # Cypher querying
│   │   ├── llm_entity_extractor.py     # Gemini entity extraction
│   │   └── tasks/                      # ARQ background workers
│   └── tests/                          # Primary test suite
│       ├── api/                        # API endpoint tests
│       ├── backend/                    # Backend logic tests
│       ├── integration/                # Integration tests
│       ├── e2e/                        # End-to-end tests
│       ├── performance/                # Performance benchmarks
│       └── load/                       # Load tests (Locust)
│
├── AURA-NOTES-MANAGER/                 # Staff Portal Application
│   ├── frontend/                       # React 18 + Vite 6 + TypeScript
│   │   ├── src/
│   │   │   ├── api/                    # Typed fetch wrappers
│   │   │   ├── components/             # React components
│   │   │   │   ├── explorer/           # File explorer (ListView, GridView, SidebarTree)
│   │   │   │   ├── layout/             # Header, Sidebar
│   │   │   │   └── ui/                 # UI primitives
│   │   │   ├── features/kg/            # Knowledge Graph feature module
│   │   │   ├── pages/                  # ExplorerPage, LoginPage, AdminDashboard
│   │   │   ├── stores/                 # Zustand stores
│   │   │   └── types/                  # TypeScript interfaces
│   │   └── e2e/                        # Playwright E2E tests (canonical)
│   ├── api/                            # FastAPI backend
│   │   ├── main.py                     # Server entry point
│   │   ├── hierarchy_crud.py           # CRUD operations
│   │   ├── explorer.py                 # Explorer endpoints
│   │   ├── audio_processing.py         # Audio pipeline
│   │   ├── kg_processor.py             # Knowledge graph processing
│   │   └── config.py                   # Configuration
│   ├── services/                       # AI/ML layer (STT, summarization, PDF)
│   ├── e2e/                            # DEPRECATED - use frontend/e2e/
│   └── tools/                          # Utility scripts
│
├── shared/                             # Shared components
│   └── model_router/                   # Provider-agnostic AI model router
│
├── .planning/                          # Architecture & planning docs
│   ├── BRIEF.md                        # Dual-project architecture overview
│   ├── ROADMAP.md                      # Implementation phases (7 phases, 12 weeks)
│   ├── RESEARCH.md                     # Technology validation research
│   └── codebase/                       # Comprehensive codebase documentation
│       ├── ARCHITECTURE.md             # Product vision and architecture
│       ├── STACK.md                    # Technology specifications
│       ├── TESTING.md                  # Development workflow and quality gates
│       ├── CONVENTIONS.md              # Coding conventions
│       ├── STRUCTURE.md                # Directory layout
│       ├── INTEGRATIONS.md             # External service integrations
│       └── CONCERNS.md                 # Known issues and tech debt
│
├── conductor/                          # Shared conductor documentation
│   ├── tech-stack.md                   # Complete technology stack
│   ├── product.md                      # Product features and workflows
│   ├── product-guidelines.md           # AI assistant tone and design
│   └── workflow.md                     # Development processes
│
├── requirements.txt                    # Consolidated Python dependencies
├── AGENTS.md                           # AI agent knowledge base (coding assistants)
├── CLAUDE.md                           # Claude-specific knowledge base
└── .github/workflows/                  # CI/CD pipelines (GitHub Actions)
```

---

## Documentation

### Comprehensive Architecture Docs

| Document | Purpose | Location |
|----------|---------|----------|
| **Architecture** | Product vision, core capabilities, technical architecture | `.planning/codebase/ARCHITECTURE.md` |
| **Stack** | Technology choices and specifications | `.planning/codebase/STACK.md` |
| **Testing** | TDD workflow, quality gates, definition of done | `.planning/codebase/TESTING.md` |
| **Conventions** | Coding conventions for TypeScript, Python, HTML/CSS | `.planning/codebase/CONVENTIONS.md` |
| **Structure** | Directory layout and where to add new code | `.planning/codebase/STRUCTURE.md` |
| **Integrations** | External service integrations and configuration | `.planning/codebase/INTEGRATIONS.md` |
| **Concerns** | Known tech debt, security, performance issues | `.planning/codebase/CONCERNS.md` |

### Project Planning

| Document | Purpose |
|----------|---------|
| **BRIEF.md** | Dual-project architecture overview and vision |
| **ROADMAP.md** | Implementation phases (7 phases, 12 weeks) and current status |
| **RESEARCH.md** | Technology validation and research findings |

### Developer References

| Document | Purpose |
|----------|---------|
| **AGENTS.md** | Comprehensive knowledge base for AI coding assistants |
| **CLAUDE.md** | Claude-specific project context and conventions |
| **GEMINI.md** | Gemini LLM integration guide |

---

## Contributing

### Getting Started

1. Read `.planning/codebase/ARCHITECTURE.md` and `.planning/codebase/CONVENTIONS.md`
2. Set up your development environment (see [Installation](#installation--setup))
3. Pick a task from `.planning/ROADMAP.md`
4. Write tests first, then implement (TDD)

### Code Standards

- **TypeScript:** Strict mode enabled, no `any` type, no default exports
- **Python:** 80-character lines, type hints required, docstrings mandatory
- **File Headers:** Required for all new/modified files
- **Tests:** >80% frontend coverage, >85% backend coverage
- **Error Handling:** Never leave empty catch blocks

### Before Submitting

1. Run all relevant tests
2. Ensure builds pass (`npm run build` for frontend)
3. Run linting (`npm run lint` / `pylint`)
4. Update documentation if architecture changes
5. Verify no secrets are committed

---

## License

This project is proprietary and confidential. All rights reserved.

---

## Support

For questions or issues:
- Check `.planning/codebase/CONCERNS.md` for known issues
- Review `AGENTS.md` for developer context
- Consult `.planning/ROADMAP.md` for current phase status

---

**AURA - Transforming Academic Discovery Through AI-Powered Knowledge Graphs**
