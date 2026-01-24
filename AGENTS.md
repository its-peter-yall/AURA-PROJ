# PROJECT KNOWLEDGE BASE

**Generated:** 2026-01-19
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
| Note management | `AURA-NOTES-MANAGER/frontend/src/pages/` |
| Audio-to-notes pipeline | `AURA-NOTES-MANAGER/services/` |
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
# @note: 2-hop graph traversal limits may need tuning for large graphs
```

**Enforcement:**
- File headers are REQUIRED for: `.ts`, `.tsx`, `.py`, `.pyi`, `.js`, `.jsx`
- Existing files without headers: Add when modifying significantly (>30% changes)
- New files: ALWAYS add header before first write
- Configuration files (tsconfig.json, pyproject.toml): Optional but encouraged
