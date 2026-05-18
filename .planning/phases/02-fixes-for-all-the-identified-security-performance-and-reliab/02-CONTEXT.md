# Phase 2: Fixes for all the identified security, performance, and reliability issues - Context

**Gathered:** 2026-05-03
**Status:** Ready for planning
**Source:** Deep-dive security/performance audit

<domain>
## Phase Boundary

This phase covers production-hardening fixes across both AURA-CHAT and AURA-NOTES-MANAGER for issues identified in a comprehensive audit. The fixes span:

1. **Security:** Exception sanitization on streaming endpoints, Cypher query allowlist validation, Firebase Auth sync error handling, security headers on streaming routes
2. **Performance:** Firestore cursor-based pagination, batched Neo4j writes, progressive graph loading
3. **Reliability:** Health probe fails on Firestore init failure, dev server binding defaults

All issues were verified against live codebase. No redesign required — this is disciplined hardening work.

</domain>

<decisions>
## Implementation Decisions

### Security
- **D-01:** Streaming error payloads must NOT include raw exception messages. Replace `str(e)` with generic sanitized messages in SSE responses.
  - Files: `AURA-CHAT/server/routers/chat.py:879-889`, `AURA-CHAT/backend/routers/sessions.py:671-681`
- **D-02:** `SecurityHeadersMiddleware` must NOT skip streaming routes entirely. Remove `/stream` bypass or add a reduced-but-safe header set for SSE.
  - File: `AURA-CHAT/server/security/middleware.py:239-242`
- **D-03:** Dynamic Cypher label/relationship interpolation in `graph_manager.py` must validate against allowlists before executing.
  - Files: `AURA-CHAT/backend/graph_manager.py` (lines 408-413, 532-536, 766-769)
  - Allowlist: `Topic`, `Concept`, `Methodology`, `Finding` for entities; relationship types from `config.LLM_RELATIONSHIP_TYPES`
- **D-04:** Firebase Auth `update_user()` failures in AURA-NOTES-MANAGER must be surfaced, not silently swallowed.
  - File: `AURA-NOTES-MANAGER/api/users.py:528-534, 550-554, 592-601`

### Performance
- **D-05:** Firestore pagination must use cursor-based or limit-based server-side pagination, not `list(query.stream())` + Python slicing.
  - File: `AURA-NOTES-MANAGER/api/modules/service.py:162-169`
- **D-06:** Neo4j relationship writes must use `UNWIND` batch queries instead of one query per relationship.
  - File: `AURA-CHAT/backend/document_processor.py:961-969` (loop calling `create_relationship`)
- **D-07:** Graph visualization defaults must be lowered for progressive loading.
  - Files: `AURA-CHAT/client/src/features/graph/GraphPage.tsx:271-272`, `AURA-CHAT/server/routers/graph.py:178-179`

### Reliability/DevEx
- **D-08:** FastAPI dev server bind address should default to `127.0.0.1` in `__main__` blocks, not `0.0.0.0`.
  - Files: `AURA-CHAT/server/main.py:241-244`, `AURA-NOTES-MANAGER/api/main.py:582-585`
- **D-09:** Vite dev server in NOTES frontend should not expose to all interfaces.
  - File: `AURA-NOTES-MANAGER/frontend/vite.config.ts:50-53` (`host: true`)

### Firestore Startup
- **D-10:** Firestore degraded startup behavior is BY DESIGN (readiness returns `not_ready`). No fix needed unless liveness-only deployments exist. Document behavior.
  - File: `AURA-CHAT/server/main.py:82-103`

### Hierarchy CRUD
- **D-11:** Sibling uniqueness checks stream entire collections. Accept as known limitation for prototype; document as tech debt.
  - File: `AURA-NOTES-MANAGER/api/hierarchy_crud.py`

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Security & Error Handling
- `AURA-CHAT/server/routers/chat.py` — Streaming chat endpoint with error handling
- `AURA-CHAT/backend/routers/sessions.py` — Session streaming endpoint
- `AURA-CHAT/server/security/middleware.py` — SecurityHeadersMiddleware with streaming bypass
- `AURA-NOTES-MANAGER/api/users.py` — Firebase Auth sync with bare except/pass

### Cypher / Graph
- `AURA-CHAT/backend/graph_manager.py` — Neo4j query builder with dynamic labels
- `AURA-CHAT/backend/document_processor.py` — Document pipeline calling graph operations
- `AURA-CHAT/backend/llm_entity_extractor.py` — Entity/relationship extraction with validation

### Performance
- `AURA-NOTES-MANAGER/api/modules/service.py` — Firestore pagination with full collection load
- `AURA-CHAT/client/src/features/graph/GraphPage.tsx` — Graph visualization defaults
- `AURA-CHAT/server/routers/graph.py` — Graph API with limit/depth defaults

### DevEx / Config
- `AURA-CHAT/server/main.py` — FastAPI entry point with Firestore init
- `AURA-NOTES-MANAGER/api/main.py` — FastAPI entry point
- `AURA-NOTES-MANAGER/frontend/vite.config.ts` — Vite dev server config

### Project Conventions
- `AGENTS.md` — Coding style, file headers, error handling patterns
- `.planning/codebase/CONVENTIONS.md` — TypeScript/Python style guides
- `.planning/codebase/TESTING.md` — Test coverage gates (>80% frontend, >85% backend)

</canonical_refs>

<specifics>
## Specific Ideas

- Exception sanitization: Replace `"error": str(e)` with `"error": "internal_error"` and log `exc_info=True` server-side only.
- Cypher allowlist: Add `_validate_label(label)` helper that checks against `{"Topic", "Concept", "Methodology", "Finding", "Document", "Chunk", "ParentChunk"}`.
- Auth sync: Replace `except Exception: pass` with `except Exception as e: logger.error(...); raise HTTPException(...)` or at minimum log and surface.
- Firestore pagination: Use `query.limit(page_size).offset((page-1)*page_size).stream()` or cursor-based pagination.
- Neo4j batching: Build `UNWIND $relationships AS rel MATCH (a:{label} {id: rel.source_id}) ...` style batch queries.
- Graph defaults: Lower default limit from 500 to 100-150; depth from 2 to 1 with UI expand option.
- Dev bind: Change `host="0.0.0.0"` to `host="127.0.0.1"` in `__main__` blocks; remove `host: true` from Vite.

</specifics>

<deferred>
## Deferred Ideas

- Full monitoring stack (Prometheus, Grafana, Sentry) — out of scope for this phase
- React version alignment (CHAT 19 vs NOTES 18) — architectural decision, not a quick fix
- Cache invalidation strategy redesign — architectural decision
- Cost alerts & budget guardrails — out of scope
- Ollama local provider — out of scope

</deferred>

---

*Phase: 02-fixes-for-all-the-identified-security-performance-and-reliab*
*Context gathered: 2026-05-03 via deep-dive audit*
