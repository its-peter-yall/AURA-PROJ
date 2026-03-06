# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-06
**Branch:** master

## OVERVIEW

Dual-application monorepo: **AURA-CHAT** (student-facing academic RAG chat) + **AURA-NOTES-MANAGER** (staff hierarchy/note management). Both share Google AI stack but use different databases (Neo4j vs Firestore) and frontend patterns.

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

## ANTI-PATTERNS (THIS PROJECT)

- **Nested Git repos**: Both `AURA-CHAT/` and `AURA-NOTES-MANAGER/` have own `.git/` — avoid cross-repo operations
- **Dual frontends in AURA-CHAT**: `client/` (modern) vs `frontend/` (Streamlit legacy) — always use `client/`
- **4 CI/CD systems**: GitHub Actions + GitLab CI + Jenkins + Docker Compose — confusion risk
- **Split backend in AURA-CHAT**: `server/` (modern) vs `backend/` (legacy) — prefer `server/`

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
// @note: 2-hop graph traversal limits may need tuning for large graphs
```

**Enforcement:**
- File headers are REQUIRED for: `.ts`, `.tsx`, `.py`, `.pyi`, `.js`, `.jsx`
- Existing files without headers: Add when modifying significantly (>30% changes)
- New files: ALWAYS add header before first write
- Configuration files (tsconfig.json, pyproject.toml): Optional but encouraged

---

## RECENT ARCHITECTURAL CHANGES (January-March 2026)

### Thinking Mode Implementation
**Date:** January 2026

Introduced dual-SDK approach for AI model access:
- **Vertex AI SDK** (`vertexai`): Advanced features like thinking mode with Gemini 2.0 Flash Thinking Experimental
- **Google Generative AI SDK** (`google-genai`): Standard chat completions

**Key Implementation:**
```python
# AURA-CHAT/server/services/gemini_service.py
from vertexai.generative_models import GenerativeModel  # For thinking mode
import google.generativeai as genai  # For standard chat
```

**When to use each:**
- Thinking mode queries → Vertex AI SDK (returns thinking content + response)
- Standard chat queries → Google Generative AI SDK
- Both use `GOOGLE_CLOUD_PROJECT` and `GOOGLE_APPLICATION_CREDENTIALS`

### Session-Based Chat Architecture
**Date:** January 2026

Migrated from stateless chat to persistent study sessions:
- **StudySession nodes** in Neo4j with `module_ids`, `status`, `message_count`
- **Message nodes** linked via `:HAS_MESSAGE` relationship with ordering
- **Session resume** functionality preserves context across browser sessions

**Key Files:**
- `AURA-CHAT/backend/routers/sessions.py` - Session CRUD endpoints
- `AURA-CHAT/client/src/features/study-sessions/` - Session UI components

### Module Hierarchy Navigation
**Date:** January 2026

Implemented 4-level hierarchy for academic content organization:
- **Department** → **Semester** → **Subject** → **Module**
- Each Module contains assigned documents with knowledge graph status
- Module selection UI supports multi-select and cross-module discovery

**Key Features:**
- `kg_status` field: draft → processing → ready → published
- Module-aware RAG filtering by `module_id`
- Cross-module concept discovery via Neo4j queries

### Dual Backend Strategy
**Date:** Ongoing

AURA-CHAT maintains two backend directories:
- **`server/`** (Modern): FastAPI, async patterns, new features
- **`backend/`** (Legacy): Rag engine, entity extractor (migrating)

**Guideline:** Prefer `server/` for new features. Use `backend/` only when extending existing KG processing.

### Feature-Based Frontend Organization
**Date:** January 2026

Both applications use feature-based architecture:
```
src/features/{feature-name}/
├── components/     # React components
├── hooks/          # Custom hooks
├── types/          # TypeScript types
└── utils/          # Helpers
```

**Key Features:**
- AURA-CHAT: `chat/`, `graph/`, `modules/`, `study-sessions/`
- AURA-NOTES-MANAGER: `kg/` (NEW), `notes/`

---

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

---

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

---

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
- **Phase 6**: Frontend Implementation (Weeks 10-11) - PLANNED
- **Phase 7**: Testing & Optimization (Week 12) - PLANNED (224+ tests, 70+ E2E tests, Docker)

### Quick Task 1: DOM Confirm Dialog Replacement
**Date:** February 2026

Replaced native browser `confirm()` dialog with custom UI-themed dialog component in User Management:
- New `ConfirmDialog` component using project's Cyber Yellow (#FFD400) design system
- Consistent styling with existing modal patterns
- Improved accessibility with proper ARIA attributes
- Located in `AURA-NOTES-MANAGER/frontend/src/components/ConfirmDialog.tsx`

### Key Takeaways by Document

**`conductor/tech-stack.md`:**
- AURA-CHAT: React 19 + Vite 7 + TypeScript 5.9, AURA-NOTES: React 18 + Vite 6
- Backend: Python 3.10+, FastAPI 0.115+, Celery 5.4, Redis 7+, Neo4j 5.15+
- Ports: CHAT (8000/5173), NOTES (8001/5173)
- Performance targets: <100ms module ops, <2s RAG queries, >90% coverage

**`conductor/product.md`:**
- AURA-NOTES-MANAGER: Staff portal for document management, module organization, KG processing, publishing
- AURA-CHAT: Student chat with module selection, study sessions, module-aware RAG
- Core workflow: Staff creates modules → uploads docs → processes KG → publishes → Students select modules → study with AI

**`conductor/product-guidelines.md`:**
- Tone: Friendly/Educational — acknowledge, answer, explain, extend
- Colors: Cyber Yellow (#FFD400), Deep Black (#0A0A0A), Dark Gray (#1A1A1A)
- Accessibility: WCAG 2.1 AA, keyboard navigation, screen reader support, 4.5:1 contrast
- All interactive elements need visible focus ring in Cyber Yellow

**`conductor/workflow.md`:**
- Plan is source of truth — all work tracked in `plan.md`
- TDD mandatory — write failing tests before implementation (Red → Green → Refactor)
- Coverage target: >80% for all modules
- Phase completion requires: automated tests pass, manual verification plan, checkpoint commit with git note
- Commit format: `<type>(<scope>): <description>`

**`conductor/code_styleguides/python.md`:**
- Run `pylint` on all code
- Max 80 characters per line, 4-space indent
- Docstrings required for all public APIs (Args, Returns, Raises)
- Naming: `snake_case` (functions/vars), `PascalCase` (classes), `ALL_CAPS` (constants)
- Type annotations strongly encouraged

**`conductor/code_styleguides/typescript.md`:**
- Never use `var`, always `const`/`let`
- Named exports only — no default exports
- No `any` type — prefer `unknown` or specific types
- Single quotes for strings, semicolons required
- No `#private` fields — use TypeScript `private`

**`.planning/BRIEF.md`:**
- Vision: Transform from document-centric to module-centric learning platform
- Module system: Department → Semester → Topic hierarchy
- Study sessions: Persistent chat with module context and message history
- Key files: `kg_processor.py`, `module_manager.py`, `rag_engine.py`, `session_manager.py`

**`.planning/ROADMAP.md`:**
- Phase 1-3: AURA-NOTES-MANAGER (Database, KG Processor, Module Management)
- Phase 4-5: AURA-CHAT (Module Integration, Study Sessions)
- Phase 6: Frontend implementation (both apps)
- Phase 7: Testing & Optimization (224+ tests, Docker Compose)
- Success metrics: <100ms module ops, <60s/doc KG processing, <2s RAG query

---

**END OF AGENTS.md**
