# GEMINI.md

**For Google Gemini CLI / Vertex AI Context**

**Generated:** 2026-01-19
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

## GOOGLE CLOUD INTEGRATION

### Vertex AI Configuration
```bash
# Required env vars
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=./path/to/service_account.json

# Models used
- gemini-2.5-flash (entity extraction)
- gemini-2.0-flash (chat responses)
- gemini-2.5-pro (complex analysis)
```

### Firestore Setup
```bash
# AURA-NOTES-MANAGER only
DEEPGRAM_API_KEY=your_deepgram_key
GOOGLE_APPLICATION_CREDENTIALS=./serviceAccountKey.json

# Deploy rules
firebase deploy --only firestore:rules,firestore:indexes
```

## KEY PATTERNS

### Entity Extraction (AURA-CHAT)
- Uses `llm_entity_extractor.py` for structured JSON output
- Entities: concepts, topics, methodologies, findings
- Relationships: HAS_CHUNK, CONTAINS_ENTITY, DEFINES, etc.
- Deduplication: exact match + 0.85 semantic similarity threshold

### Audio-to-Notes (AURA-NOTES-MANAGER)
- Deepgram Nova-3 for transcription
- Gemini for content refinement
- PDF generation from transcripts

### Graph-Augmented RAG
- Vector similarity search (Neo4j)
- 2-hop graph traversal for related concepts
- Hybrid retrieval strategy in `rag_engine.py`

## FILE LOCATIONS

| Component | Path |
|-----------|------|
| Vertex AI client | `AURA-NOTES-MANAGER/services/vertex_ai_client.py` |
| Entity extractor | `AURA-CHAT/backend/llm_entity_extractor.py` |
| RAG engine | `AURA-CHAT/backend/rag_engine.py` |
| STT service | `AURA-NOTES-MANAGER/services/stt.py` |
| Summarizer | `AURA-NOTES-MANAGER/services/summarizer.py` |

## DEVELOPMENT NOTES

### AURA-CHAT Stack
```
Frontend: React 19 + Vite + Tailwind + Reagraph
Backend:  FastAPI (server/) + legacy (backend/)
DB:       Neo4j (graph + vector)
AI:       Vertex AI Gemini
```

### AURA-NOTES-MANAGER Stack
```
Frontend: React 18 + Vite + Tailwind + Zustand
Backend:  FastAPI (api/)
DB:       Firestore (NoSQL)
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
