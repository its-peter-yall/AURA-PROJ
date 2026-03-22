# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-15
**Branch:** master
**Cumulative Edition:** Combines AURA-CHAT and AURA-NOTES-MANAGER AGENTS.md

---

## OVERVIEW

Dual-application monorepo: **AURA-CHAT** (student-facing academic RAG chat) + **AURA-NOTES-MANAGER** (staff hierarchy/note management). Both share Google AI stack but use different databases (Neo4j vs Firestore) and frontend patterns.

---

## STRUCTURE

```
AURA-PROJ/
├── .planning/              # Architecture docs (BRIEF.md, ROADMAP.md)
├── AURA-CHAT/              # Student RAG chat with knowledge graph
│   ├── client/             # React 19 + Vite 7 + TypeScript (MODERN)
│   ├── frontend/           # Streamlit legacy (MIGRATING AWAY)
│   ├── server/             # FastAPI modern backend
│   ├── backend/            # Legacy processing (rag_engine, entity_extractor)
│   └── tests/
├── AURA-NOTES-MANAGER/     # Staff hierarchy & notes
│   ├── frontend/           # React 18 + Vite 6 + TypeScript
│   ├── api/                # FastAPI backend
│   ├── services/           # AI/ML layer (STT, summarization)
│   ├── e2e/                # Playwright tests
│   └── tools/
└── .github/workflows/      # CI/CD (4 systems!)
```

---

## WHERE TO LOOK

### AURA-CHAT
| Task | Location |
|------|----------|
| RAG chat development | `AURA-CHAT/client/src/features/chat/` |
| Knowledge graph | `AURA-CHAT/client/src/features/graph/` |
| Module selection UI | `AURA-CHAT/client/src/features/modules/` |
| Study sessions | `AURA-CHAT/client/src/features/study-sessions/` |
| Session management | `AURA-CHAT/backend/routers/sessions.py` |
| Document processing | `AURA-CHAT/backend/` |
| Backend API (chat) | `AURA-CHAT/server/routers/` |
| Authentication | `AURA-CHAT/server/auth/` |

### AURA-NOTES-MANAGER
| Task | Location |
|------|----------|
| Note management | `AURA-NOTES-MANAGER/frontend/src/pages/` |
| KG processing UI | `AURA-NOTES-MANAGER/frontend/src/features/kg/` |
| Audio-to-notes pipeline | `AURA-NOTES-MANAGER/services/` (STT, summarization, PDF) |
| Backend API (notes) | `AURA-NOTES-MANAGER/api/` |

---

## TECHNOLOGY VERSIONS

### AURA-CHAT
| Component | Version |
|-----------|---------|
| React | ^19.2.0 |
| React-DOM | ^19.2.0 |
| Tailwind CSS | ^4.1.18 |
| Vite | ^7.2.4 |
| TypeScript | ~5.9.3 (Strict mode) |
| Pydantic | v2 |
| Python | 3.10+ |
| Neo4j | 5.13 |

### AURA-NOTES-MANAGER
| Component | Version |
|-----------|---------|
| React | ^18.3.1 |
| Vite | ^6.0.5 |
| TypeScript | ~5.6.2 |
| Python | 3.10+ |

---

## DEPENDENCIES

### AURA-CHAT Client
- **Core:** React 19, React-DOM, TypeScript, Vite
- **Routing:** `react-router-dom` ^7.11.0
- **UI/Animation:** `lucide-react`, `tailwindcss`, `framer-motion`, `clsx`, `tailwind-merge`
- **Graph Visualization:** `reagraph` ^4.30.7 (WebGL)
- **Content:** `react-markdown` ^10.1.0, `remark-gfm`, `rehype-raw`, `rehype-sanitize`
- **State/Query:** `@tanstack/react-query` ^5.90.15, `axios`, `zustand`
- **Firebase:** `firebase` ^12.9.0
- **Testing:** `vitest` ^3.2.4, `@playwright/test` ^1.49.0, `@testing-library/react`

### AURA-CHAT Server/Backend
- **Web Framework:** `fastapi` 0.109+, `uvicorn`
- **AI/ML:** `google-cloud-aiplatform` (Gemini SDK), `tenacity` (retry logic)
- **Database:** `neo4j` python driver
- **Task Queue:** `arq` (async Redis-based jobs)
- **Auth:** `firebase-admin`, Firestore client
- **Testing:** `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`

### AURA-NOTES-MANAGER Frontend
- React 18, TypeScript 5.6, Vite 6
- State: Zustand, TanStack Query
- Styling: Tailwind CSS
- Testing: Vitest, Playwright

### AURA-NOTES-MANAGER Backend
- FastAPI (Python 3.10+), Uvicorn
- Database: Firebase Firestore, Neo4j, Redis
- AI/ML: Google Gemini, Deepgram (STT), Vertex AI

---

## BUILD, LINT, AND TEST COMMANDS

### AURA-CHAT

#### Client
```bash
cd AURA-CHAT/client
npm install
npm run dev                    # Dev server (http://127.0.0.1:5173)
npm run build                  # Build (tsc -b && vite build)
npm run lint                   # ESLint
npx tsc --noEmit               # Type-only check
npm run test                   # Vitest (unit tests)
npm run test:e2e               # Playwright E2E tests
npm run test:coverage          # Coverage report
```

#### Server & Backend (from project root with root venv)
```bash
# Run server
uvicorn AURA-CHAT.server.main:app --reload --port 8000

# Run tests (ALWAYS from project root with root venv)
python -m pytest AURA-CHAT/tests/
python -m pytest AURA-CHAT/tests/backend/
python -m pytest AURA-CHAT/tests/api/
python -m pytest --cov=backend --cov=server AURA-CHAT/tests/
```

### AURA-NOTES-MANAGER

#### Frontend
```bash
cd AURA-NOTES-MANAGER/frontend
npm run dev              # Start dev server (port 5173)
npm run build            # Type check + production build
npm run lint             # ESLint check
npm test                 # Run Vitest unit tests
npm run test:e2e         # Run Playwright E2E tests
npm run test:e2e:ui      # Run E2E tests with UI
npm run test:e2e:headed  # Run E2E tests with visible browser
```

#### Backend (from project root with root venv)
```bash
# Start server
uvicorn AURA-NOTES-MANAGER.api.main:app --reload --port 8001

# Run tests
python -m pytest AURA-NOTES-MANAGER/api/tests/
python -m pytest --cov=api --cov-report=html
```

### Python Environment (ALL Python Tasks)
- **ALWAYS use the root virtual environment** (`../.venv` or `../../.venv`)
- **NEVER install dependencies globally** or create local venvs

```bash
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install packages (from project root with venv activated)
pip install <package>
pip install -r requirements.txt
```

---

## CODE STYLE GUIDELINES

### TypeScript/JavaScript (Google TypeScript Style Guide)

**Variables & Declarations:**
- Use `const` by default, `let` when reassignment needed
- **NEVER use `var`** (forbidden)
- Use ES6 modules (`import`/`export`), no `namespace`

**Exports:**
- Use **named exports** (e.g., `export { MyClass }`)
- **DO NOT use default exports**

**Types:**
- **Avoid `any` type** — use `unknown` or specific types
- **Avoid type assertions** (`as SomeType`) unless justified
- Prefer `T[]` for simple types, `Array<T>` for complex unions
- Use optional parameters (`?`) instead of `| undefined`

**Classes:**
- Use TypeScript's `private`/`protected` modifiers, not `#private` fields
- **NEVER use `public` modifier** (it's the default)
- Mark readonly properties with `readonly`

**Strings & Operators:**
- Use single quotes (`'`) for strings
- Use template literals (`` ` ``) for interpolation and multi-line strings
- Always use `===` and `!==` (never `==` or `!=`)
- Explicitly end statements with semicolons (no ASI reliance)

**Naming Conventions:**
- `UpperCamelCase`: Classes, interfaces, types, enums, decorators
- `lowerCamelCase`: Variables, parameters, functions, methods, properties
- `CONSTANT_CASE`: Global constants, enum values

**Path Alias:**
- `@/*` → `./src/*`

### Python (Google Python Style Guide)

**Imports:**
- Use `import x` for packages/modules
- Use `from x import y` only when `y` is a submodule
- Group imports: standard library, third-party, application

**Formatting:**
- **Line length: 80 characters maximum**
- **Indentation: 4 spaces** (never tabs)
- Two blank lines between top-level definitions

**Naming Conventions:**
- `snake_case`: Modules, functions, methods, variables
- `PascalCase`: Classes
- `ALL_CAPS_WITH_UNDERSCORES`: Constants

**Docstrings:**
- Use `"""triple double quotes"""`
- Every public module, function, class, and method must have a docstring
- Start with one-line summary
- Include `Args:`, `Returns:`, and `Raises:` sections

### File Headers (MANDATORY)

**TypeScript/JavaScript** (`.ts`, `.tsx`, `.js`, `.jsx`):
```typescript
/**
 * ============================================================================
 * FILE: <filename>
 * LOCATION: <filepath>
 * ============================================================================
 *
 * PURPOSE:
 *    Brief 1-line description of what this file does
 *
 * ROLE IN PROJECT:
 *    How this file fits into the larger system (2-3 lines)
 *
 * KEY COMPONENTS:
 *    - Component1: What it does
 *    - Component2: What it does
 *
 * DEPENDENCIES:
 *    - External: List external libraries
 *    - Internal: List internal modules
 *
 * USAGE:
 *    Example code snippet
 * ============================================================================
 */
```

**Python** (`.py`):
```python
"""
========================================================================
FILE: <filename>
LOCATION: <filepath>
========================================================================

PURPOSE:
    Brief description of what this file does

ROLE IN PROJECT:
    How this file fits into the larger system
    - Key responsibility 1
    - Key responsibility 2

KEY COMPONENTS:
    - Component1: What it does
    - Component2: What it does

DEPENDENCIES:
    - External: List external libraries used
    - Internal: List internal modules imported

USAGE:
    Brief usage example or how to run/test
========================================================================
"""
```

### Error Handling

**TypeScript:**
```typescript
try {
    await riskyOperation();
} catch (error) {
    if (error instanceof DuplicateError) {
        // Handle duplicate specifically
    } else {
        console.error('Operation failed:', error);
        throw error;
    }
}
```

**Python:**
```python
try:
    risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise
except Exception as e:
    logger.exception("Unexpected error")
    raise
```

---

## PROJECT STRUCTURES

### AURA-CHAT Client
```
src/
├── features/              # Feature-based architecture
│   ├── auth/             # Login page (Firebase email/password)
│   ├── chat/             # RAG chat interface
│   ├── documents/        # Document management
│   ├── graph/            # 3D Reagraph visualization
│   ├── modules/          # Module/course management
│   ├── settings/         # App configuration
│   └── study-sessions/   # Session CRUD hooks
├── components/
│   ├── MainLayout.tsx    # Collapsible sidebar
│   ├── ProtectedRoute.tsx # Auth guard
│   ├── ErrorBoundary.tsx # React error boundary
│   └── ui/               # Shared UI components
├── stores/
│   └── useAuthStore.ts   # Zustand auth state
├── lib/
│   ├── api.ts            # Axios client + auth interceptor
│   ├── firebase.ts       # Firebase Client SDK init
│   └── utils.ts          # cn(), format utilities
├── hooks/                # Custom hooks
├── types/                # TypeScript types
└── App.tsx, main.tsx    # Root app entry points
```

### AURA-CHAT Server
```
server/
├── routers/
│   ├── auth.py           # Authentication endpoints
│   ├── chat.py           # Chat endpoints with streaming/thinking mode
│   ├── documents.py      # Upload, process, list, delete
│   ├── graph.py          # Graph schema and visualization
│   ├── health.py         # Health checks
│   ├── jobs.py           # Background job status
│   └── websocket.py      # Real-time updates
├── auth/
│   ├── firebase_auth.py  # Firebase token verification
│   ├── firestore_client.py # Firestore access
│   ├── dependencies.py   # FastAPI auth dependencies
│   └── models.py         # Auth Pydantic models
└── schemas/              # Request/response schemas
```

### AURA-CHAT Backend
```
backend/
├── chat_manager.py              # Chat orchestration
├── document_processor.py        # Pipeline orchestrator
├── rag_engine.py                # Vector search + graph traversal
├── graph_manager.py             # Cypher querying
├── llm_entity_extractor.py      # Gemini entity extraction
├── llm_gatekeeper.py            # Query validation
├── session_manager.py           # Study session lifecycle
├── routers/
│   ├── sessions.py              # Session API endpoints
│   └── student_modules.py      # Module management
├── tasks/                       # ARQ background workers
├── services/                    # Hierarchy logic
└── utils/                       # Config, embeddings, logging
```

### AURA-NOTES-MANAGER
```
AURA-NOTES-MANAGER/
├── api/                    # FastAPI backend
│   ├── main.py            # Server entry point
│   ├── hierarchy_crud.py  # CRUD operations
│   ├── explorer.py        # Explorer endpoints
│   ├── audio_processing.py # Audio pipeline
│   ├── kg_processor.py    # Knowledge graph processing
│   └── config.py          # Configuration
├── frontend/              # React frontend
│   ├── src/
│   │   ├── api/          # Typed fetch wrappers
│   │   ├── components/   # React components
│   │   │   ├── explorer/ # File explorer
│   │   │   ├── layout/   # Header, Sidebar
│   │   │   └── ui/       # UI primitives
│   │   ├── features/kg/  # Knowledge Graph feature
│   │   ├── pages/        # ExplorerPage, LoginPage
│   │   ├── stores/       # Zustand stores
│   │   └── types/        # TypeScript interfaces
│   └── e2e/              # Playwright E2E tests
├── services/              # AI/ML layer (STT, summarization)
├── e2e/                   # Root-level E2E tests
└── tools/                 # Utility scripts
```

---

## CONVENTIONS (DEVIATIONS FROM STANDARD)

### Python Environment
- **ALWAYS use the root venv** (`../.venv` or `../../.venv`) for all Python tasks
- **NEVER install dependencies globally** or in subdirectory venvs

### E2E Testing
- **AURA-NOTES-MANAGER**: Sequential (`fullyParallel: false`) for DB consistency
- **AURA-CHAT**: Parallel execution

### Anti-Patterns
- **Nested Git repos**: Both have own `.git/` — avoid cross-repo operations
- **Dual frontends in AURA-CHAT**: `client/` (modern) vs `frontend/` (Streamlit) — always use `client/`
- **4 CI/CD systems**: GitHub Actions + GitLab CI + Jenkins + Docker Compose
- **Split backend in AURA-CHAT**: `server/` (modern) vs `backend/` (legacy) — prefer `server/`

---

## UNIQUE STYLES

- **Services abstraction layer** (AURA-NOTES-MANAGER): STT, summarization, PDF gen isolated in `services/`
- **Dual database strategy**: Neo4j (graph) for chat, Firestore (NoSQL) for notes
- **Dual AI providers**: Vertex AI (chat) vs Gemini + Deepgram (notes)
- **Architecture docs**: Comprehensive specs in `.planning/` and `architecture-spec.md`

---

## ENVIRONMENT VARIABLES

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

---

## TESTING STRATEGY

### Test Organization

| Level | Tool | Target | Location |
|-------|------|--------|----------|
| **Unit (Python)** | pytest | >85% coverage | `AURA-CHAT/tests/`, `AURA-NOTES-MANAGER/api/tests/` |
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

---

## APPLICATION ROUTES

### AURA-CHAT
- `/` - Main application (redirects to chat)
- `/login` - Authentication page
- `/chat` - Chat interface with RAG capabilities
- `/graph` - 3D Graph explorer
- `/documents` - Document management
- `/modules` - Course/module management
- `/settings` - User settings

### AURA-NOTES-MANAGER
- `/` - Explorer page
- `/login` - Authentication
- `/admin` - Admin dashboard

---

## KEY FILES REFERENCE

### AURA-CHAT
| Task | File |
|------|------|
| Login / Auth | `features/auth/LoginPage.tsx` |
| Auth state | `stores/useAuthStore.ts` |
| Route guard | `components/ProtectedRoute.tsx` |
| Firebase SDK | `lib/firebase.ts` |
| Auth types | `types/auth.ts` |
| Chat RAG logic | `features/chat/ChatPage.tsx` |
| Graph visualization | `features/graph/GraphPage.tsx` |
| Module management | `features/modules/` |
| API client | `lib/api.ts` |
| Graph data fetching | `hooks/useGraphQuery.ts` |
| Study sessions | `features/study-sessions/hooks/useStudySession.ts` |

### AURA-NOTES-MANAGER
| Task | Location |
|------|----------|
| API integration | `frontend/src/api/client.ts`, `frontend/src/api/explorerApi.ts` |
| State management | `frontend/src/stores/useExplorerStore.ts`, `frontend/src/stores/useAuthStore.ts` |
| Page structure | `frontend/src/pages/ExplorerPage.tsx`, `frontend/src/pages/LoginPage.tsx` |
| Knowledge Graph | `frontend/src/features/kg/` |
| Custom errors | `frontend/src/api/client.ts` (DuplicateError) |
| Backend entry | `api/main.py` |
| Python config | `api/config.py` |

---

## AGENT BEHAVIOUR

### Research-First Principle
- **ALWAYS web-search before implementing** unfamiliar libraries, APIs, or patterns
- **NEVER assume** library behavior — verify with official documentation
- **Search first** when encountering: new npm packages, Python libraries, framework features, or external APIs

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
- **Parallel execution**: Use background agents for independent tasks
- **Delegate visual work**: Always use `frontend-ui-ux-engineer` agent for styling/layout changes
- **Consult Oracle** for: architecture decisions, 2+ failed fix attempts, complex debugging
- **Use todo tracking**: Mark in_progress → completed in real-time
- **Batch small tasks**: Group related edits, run diagnostics once

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

---

## ARCHITECTURAL CONTEXT

### AURA-CHAT: RAG / Knowledge Graph Architecture
AURA enables researchers to query academic documents using natural language, with responses augmented by cross-document relationships rather than just semantic text matches.

**Processing Pipeline:**
1. Text Extraction
2. Entity & Relationship Extraction (LLM → JSON)
3. Chunking (Entity-Aware)
4. Embedding (Gemini Embedding Model)
5. Indexing (Neo4j Graph + Vector Index)

**Background Task System:**
- Uses ARQ (async Redis queue) for background jobs
- Document processing runs as background tasks
- WebSocket for real-time progress updates

### AURA-NOTES-MANAGER: Staff Portal
- Document management, module organization, KG processing, publishing
- Audio-to-notes pipeline with STT and summarization
- Hierarchy management (Department → Semester → Subject → Module)

---

## RECENT ARCHITECTURAL CHANGES (January-March 2026)

### Thinking Mode Implementation
**Date:** January 2026

Introduced dual-SDK approach for AI model access:
- **Vertex AI SDK** (`vertexai`): Advanced features like thinking mode with Gemini 2.0 Flash Thinking Experimental
- **Google Generative AI SDK** (`google-genai`): Standard chat completions

### Session-Based Chat Architecture
**Date:** January 2026

Migrated from stateless chat to persistent study sessions:
- **StudySession nodes** in Neo4j with `module_ids`, `status`, `message_count`
- **Message nodes** linked via `:HAS_MESSAGE` relationship
- **Session resume** functionality preserves context

### Module Hierarchy Navigation
**Date:** January 2026

Implemented 4-level hierarchy for academic content organization:
- **Department** → **Semester** → **Subject** → **Module**
- `kg_status` field: draft → processing → ready → published
- Module-aware RAG filtering by `module_id`

### Dual Backend Strategy
**Date:** Ongoing

AURA-CHAT maintains two backend directories:
- **`server/`** (Modern): FastAPI, async patterns, new features
- **`backend/`** (Legacy): Rag engine, entity extractor (migrating)

**Guideline:** Prefer `server/` for new features. Use `backend/` only when extending existing KG processing.

---

## COMPREHENSIVE REFERENCES

### AURA-CHAT Documentation
- `.planning/codebase/ARCHITECTURE.md` - Product vision and architecture
- `.planning/codebase/STACK.md` - Technology specifications
- `.planning/codebase/TESTING.md` - Development workflow and quality gates
- `.planning/codebase/CONVENTIONS.md` - Coding conventions for all languages
- `.planning/codebase/STRUCTURE.md` - Directory layout
- `.planning/codebase/INTEGRATIONS.md` - External service integrations
- `.planning/codebase/CONCERNS.md` - Known issues and tech debt

### AURA-NOTES-MANAGER Documentation
- `documentations/code_styleguides/` - Style guide references
-conductor documentation (shared)

### Planning Documentation (Shared)
- `.planning/BRIEF.md` - Dual-project architecture overview
- `.planning/ROADMAP.md` - Implementation phases and current status

### Conductor Documentation (Shared)
- `conductor/tech-stack.md` - Complete technology stack
- `conductor/product.md` - Product features and workflows
- `conductor/product-guidelines.md` - AI assistant tone and design
- `conductor/workflow.md` - Development processes

---

**END OF AGENTS.md**
