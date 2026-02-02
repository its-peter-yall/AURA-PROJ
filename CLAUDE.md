# CLAUDE.md

**For Claude Code (Anthropic CLI)**

**Generated:** 2026-02-02
**Branch:** master

---

## COMPREHENSIVE REFERENCES

### Conductor Documentation

| File | Summary | When to Read |
|------|---------|--------------|
| `conductor/tech-stack.md` | Technical architecture, technology versions, dependencies, API ports, database configuration, performance targets | Before adding new dependencies or changing infrastructure |
| `conductor/product.md` | Product vision, dual-application overview, user personas (staff/student), core workflows (content publishing, study sessions), success metrics | When implementing new features or understanding user flows |
| `conductor/product-guidelines.md` | Design system (Cyber Yellow #FFD400), tone of voice (Friendly/Educational), accessibility guidelines (WCAG 2.1 AA), CSS variables, component styling | For UI changes, ensuring accessibility compliance, maintaining brand consistency |
| `conductor/workflow.md` | Development workflow, TDD requirements, task lifecycle, phase completion protocol, quality gates, commit guidelines, emergency procedures | Starting new tasks, following development process, handling emergencies |
| `conductor/code_styleguides/general.md` | Cross-language principles: readability, consistency, simplicity, maintainability, documentation | All code changes |
| `conductor/code_styleguides/python.md` | Google Python Style Guide: pylint, 80-char lines, 4-space indent, docstrings, naming conventions, type annotations | Python development |
| `conductor/code_styleguides/typescript.md` | Google TypeScript Style Guide: no `any`, no default exports, single quotes, triple equals, named exports, type inference | TypeScript/React development |

### Planning Documentation

| File | Summary | When to Read |
|------|---------|--------------|
| `.planning/BRIEF.md` | Dual-project architecture diagram, problem statement, solution overview, technology stack, project mapping, next actions | Understanding overall architecture, starting new phases |
| `.planning/ROADMAP.md` | 7-phase implementation roadmap (12 weeks), detailed phase breakdowns, database schema, API endpoints, testing plans, checkpointing protocol | Planning work, understanding current phase, creating task plans |

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

## RECENT ARCHITECTURAL CHANGES (January-February 2026)

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

## PROJECT CONTEXT

Dual-application monorepo with two independent but related apps sharing Google AI stack but using different databases and frontend patterns.

### AURA-CHAT (Student-Facing Academic RAG)

**Technology Stack:**
- **Frontend:** React 19 + Vite + TypeScript (MODERN)
- **Backend:** FastAPI + Neo4j + Vertex AI
- **Legacy:** Streamlit frontend (`frontend/`) and legacy processing (`backend/`)
- **Purpose:** Academic RAG chat with knowledge graph visualization

**Key Architecture:**
- **Dual Database Strategy:** Neo4j for knowledge graph, Firestore for session data
- **Session-Based Architecture:** Maintains conversation context across sessions
- **Thinking Mode:** Implements detailed reasoning before responses

**Key Files:**
- Frontend: `AURA-CHAT/client/src/features/{chat,documents,graph,settings}/`
- Backend: `AURA-CHAT/server/routers/`, `AURA-CHAT/backend/`
- Tests: `AURA-CHAT/tests/`

### AURA-NOTES-MANAGER (Staff Portal)

**Technology Stack:**
- **Frontend:** React 18 + Vite + TypeScript
- **Backend:** FastAPI + Firestore + Gemini/Deepgram
- **Purpose:** Staff hierarchy and note management with AI-powered audio-to-notes

**Key Architecture:**
- **Services Abstraction Layer:** STT, summarization, PDF generation isolated in `services/`
- **E2E Testing:** Sequential execution (`fullyParallel: false`) for DB consistency
- **Dual AI Providers:** Gemini for text, Deepgram for audio transcription

**Key Files:**
- Frontend: `AURA-NOTES-MANAGER/frontend/src/pages/`, `src/api/`, `src/stores/`
- Backend: `AURA-NOTES-MANAGER/api/`, `AURA-NOTES-MANAGER/services/`
- E2E Tests: `AURA-NOTES-MANAGER/e2e/`
- Tools: `AURA-NOTES-MANAGER/tools/`

---

## CRITICAL ANTI-PATTERNS

### Repository Structure
1. **Nested Git repos:** Both `AURA-CHAT/` and `AURA-NOTES-MANAGER/` have own `.git/` — avoid cross-repo operations
2. **Dual frontends in AURA-CHAT:** Use `client/` (React 19, modern), NOT `frontend/` (Streamlit legacy)
3. **Split backend in AURA-CHAT:** Prefer `server/` (modern FastAPI) over `backend/` (legacy)
4. **4 CI/CD systems:** GitHub Actions + GitLab CI + Jenkins + Docker Compose — confusion risk, verify which system applies

### Common Mistakes
- **Using global Python:** Always use the root venv (`../.venv` or `../../.venv`)
- **Using `localhost`:** Always use `127.0.0.1` to avoid IPv6 issues
- **Installing packages globally:** NEVER install dependencies globally
- **Using `any` type:** Never suppress TypeScript errors with `as any` or `@ts-ignore`
- **Empty catch blocks:** Never leave `catch(e) {}` — always handle errors

---

## CODING STANDARDS

See **Conventions** section above for detailed standards. Quick reference:

### TypeScript (Google TypeScript Style Guide)
- **NO `any` type** — use `unknown` or specific types
- **Named exports ONLY** (no default exports)
- **Strict mode:** `noUnusedLocals`, `noUnusedParameters` enabled
- **Path alias:** `@/*` → `./src/*`
- **Feature-based architecture:** `src/features/{name}/{Page,components,hooks}/`
- **ESLint flat config** with React hooks rules
- **Custom theme:** "Cyber Yellow" primary color `#FFD400`
- **Reagraph** for 3D graph visualization (AURA-CHAT)
- **TailwindCSS** with `@/` path alias

### Python (Google Python Style Guide)
- **4-space indent**, 80-char line limit
- **Router pattern:** `router = APIRouter(prefix="/path", tags=["Tag"])`
- **Dependency injection** via `Depends()`
- **F-strings** for formatting
- **Global exception handler** in `main.py`
- **Root venv usage:** Always use `../.venv/Scripts/python` or `../../.venv/Scripts/python`

---

## FILE HEADER REQUIREMENTS (MANDATORY)

**Required for:** `.ts`, `.tsx`, `.py`, `.pyi`, `.js`, `.jsx`

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
// Hybrid RAG engine combining vector search and graph traversal

# Implements query analysis to determine intent (factual/conceptual),
# performs hybrid search (vector + graph), and synthesizes responses
# using retrieved context. Supports configurable similarity thresholds.

# @see: schemas/query.py - Query schema definitions
// @note: 2-hop graph traversal limits may need tuning for large graphs
```

**Enforcement:**
- Existing files without headers: Add when modifying significantly (>30% changes)
- New files: ALWAYS add header before first write
- Configuration files (tsconfig.json, pyproject.toml): Optional but encouraged

---

## QUICK REFERENCE

| Task | Location |
|------|----------|
| RAG chat development | `AURA-CHAT/client/src/features/chat/` |
| Knowledge graph visualization | `AURA-CHAT/client/src/features/graph/` |
| Document processing | `AURA-CHAT/backend/` |
| Note management | `AURA-NOTES-MANAGER/frontend/src/pages/` |
| Audio-to-notes pipeline | `AURA-NOTES-MANAGER/services/` |
| Backend API (chat) | `AURA-CHAT/server/routers/` |
| Backend API (notes) | `AURA-NOTES-MANAGER/api/` |

---

## CLAUDE CODE SPECIFIC INSTRUCTIONS

### Critical Operational Guidelines

1. **Network Addresses:**
   - **Always use `127.0.0.1` not `localhost`** to avoid IPv6 issues
   - Never assume `localhost` will resolve correctly

2. **Timeouts:**
   - **5-minute timeout** for document processing endpoints (configured in Axios/TanStack Query)
   - Extended timeouts for large file uploads and AI processing

3. **Tool Usage:**
   - **Use Read tool before Edit tool** — file must exist before editing
   - **Use Bash tool for git operations**, not file editing tools
   - **Never use file editing tools** for git operations

4. **Agent Delegation:**
   - **Parallelize work** using multiple agents for independent tasks
   - **Use `frontend-ui-ux-engineer` agent** for all visual/styling/layout changes
   - **Use `explore` agent** for finding codebase patterns and existing implementations
   - **Use `librarian` agent** for external documentation lookup
   - **Use `oracle` agent** for: architecture decisions, 2+ failed fix attempts, complex debugging
   - **Use `document-writer` agent** for documentation tasks

5. **Research First:**
   - **ALWAYS web-search before implementing** unfamiliar libraries, APIs, or patterns
   - **NEVER assume** library behavior — verify with official documentation
   - **Search first** when encountering: new npm packages, Python libraries, framework features, or external APIs

---

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

---

## SUMMARY

This monorepo contains two related but distinct applications:

1. **AURA-CHAT**: Modern React 19 + FastAPI + Neo4j + Vertex AI for student academic RAG chat
2. **AURA-NOTES-MANAGER**: React 18 + FastAPI + Firestore + Gemini/Deepgram for staff note management

**Key Principles:**
- Use root venv for ALL Python operations
- Use `127.0.0.1` never `localhost`
- Add MANDATORY file headers to all code files
- Follow Google style guides for TypeScript and Python
- Delegate visual work to `frontend-ui-ux-engineer`
- Use agents for parallel work and extended sessions
- Research before implementing unfamiliar patterns
- Verify with diagnostics before marking complete

**Reference the conductor documentation** for detailed specifications on technology stack, product requirements, design guidelines, workflow, and coding standards.
