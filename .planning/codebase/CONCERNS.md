# Codebase Concerns

**Analysis Date:** 2026-03-10

## Tech Debt

**Split AURA-CHAT backend stack:**
- Issue: HTTP entrypoints live in `AURA-CHAT/server/` while core session and hierarchy routes still live in `AURA-CHAT/backend/`; `AURA-CHAT/server/main.py` imports `backend.routers.sessions` and `backend.routers.student_modules`, and `AURA-CHAT/server/dependencies.py` wires `backend` services directly into the API layer.
- Files: `AURA-CHAT/server/main.py`, `AURA-CHAT/server/dependencies.py`, `AURA-CHAT/backend/routers/sessions.py`, `AURA-CHAT/backend/services/hierarchy.py`
- Impact: ownership boundaries are unclear, tests must know both trees, and refactors can break import-time wiring in two places.
- Fix approach: consolidate route ownership under one backend boundary and leave the other tree as adapters only.

**Large multi-responsibility files:**
- Issue: core behavior is concentrated in very large files: `AURA-NOTES-MANAGER/api/kg_processor.py` (~3769 lines), `AURA-CHAT/backend/rag_engine.py` (~2202 lines), and `AURA-NOTES-MANAGER/frontend/src/pages/AdminDashboard.tsx` (~2168 lines).
- Files: `AURA-NOTES-MANAGER/api/kg_processor.py`, `AURA-CHAT/backend/rag_engine.py`, `AURA-NOTES-MANAGER/frontend/src/pages/AdminDashboard.tsx`
- Impact: debugging and test isolation are expensive, and small changes have a high regression surface.
- Fix approach: split orchestration, persistence, and UI state into smaller modules with narrow tests.

**Firestore path resolution depends on collection scans:**
- Issue: nested documents are repeatedly located by querying stored `id` fields or by recursive traversal instead of stable parent references.
- Files: `AURA-NOTES-MANAGER/api/hierarchy_crud.py`, `AURA-NOTES-MANAGER/api/notes.py`, `AURA-NOTES-MANAGER/api/tasks/document_processing_tasks.py`
- Impact: CRUD cost grows with dataset size and makes delete/update behavior sensitive to data shape.
- Fix approach: persist canonical parent paths or denormalized lookup keys and replace `collection_group(...).where("id" == ...)` lookups in hot paths.

## Known Bugs

**User records can drift between Firestore and Firebase Auth:**
- Symptoms: API updates can return success even when the corresponding Firebase user email or disabled flag was not updated.
- Files: `AURA-NOTES-MANAGER/api/users.py`
- Trigger: `firebase_auth.update_user(...)` failures during email/status changes are swallowed with `pass` at `AURA-NOTES-MANAGER/api/users.py:517`, `AURA-NOTES-MANAGER/api/users.py:563`, and `AURA-NOTES-MANAGER/api/users.py:568`.
- Workaround: manually verify and resync the Firebase Auth record after admin edits.

**AURA-CHAT can boot "healthy" while hierarchy support is unusable:**
- Symptoms: startup succeeds, but hierarchy requests fail later with degraded-mode warnings or 503 responses.
- Files: `AURA-CHAT/server/main.py`, `AURA-CHAT/server/dependencies.py`
- Trigger: Firestore init failures are converted into degraded startup in `AURA-CHAT/server/main.py:146` and rejected only when hierarchy dependencies are requested in `AURA-CHAT/server/dependencies.py:200`.
- Workaround: treat startup warnings as deployment failures and verify Firestore readiness before exposing the service.

## Security Considerations

**Streaming endpoints leak raw exception text to clients:**
- Risk: internal exception messages are sent over SSE payloads and can expose stack-context, provider failures, or query details.
- Files: `AURA-CHAT/server/routers/chat.py`, `AURA-CHAT/backend/routers/sessions.py`
- Current mitigation: server logs capture the failures, but the client payload still includes `"error": str(e)`.
- Recommendations: replace raw exception text with stable error codes and log correlation IDs only.

**Dynamic Cypher labels and relationship types are interpolated into queries:**
- Risk: query structure is built with f-strings instead of a fixed allowlist, which is dangerous when values originate from extracted document relationships.
- Files: `AURA-CHAT/backend/graph_manager.py`, `AURA-CHAT/backend/document_processor.py`
- Current mitigation: none detected beyond application-level conventions.
- Recommendations: map entity and relationship types through explicit allowlists before constructing Cypher in `AURA-CHAT/backend/graph_manager.py:459`.

**Streaming routes skip security headers entirely:**
- Risk: `/stream` requests bypass `SecurityHeadersMiddleware`, so streaming responses do not receive the same CSP and browser-hardening headers as standard responses.
- Files: `AURA-CHAT/server/security/middleware.py`
- Current mitigation: `X-Content-Type-Options` is manually added in `AURA-CHAT/backend/routers/sessions.py:847` for one SSE route.
- Recommendations: attach a streaming-safe header policy instead of returning early at `AURA-CHAT/server/security/middleware.py:267`.

**Development servers are exposed on all interfaces:**
- Risk: local dev instances listen on the network by default.
- Files: `AURA-NOTES-MANAGER/frontend/vite.config.ts`, `AURA-NOTES-MANAGER/api/main.py`, `AURA-CHAT/server/main.py`
- Current mitigation: not applicable for trusted local machines only.
- Recommendations: default to loopback-only binds for development and document when `host: true` or `0.0.0.0` is required.

## Performance Bottlenecks

**Pagination is implemented by loading full Firestore result sets into memory:**
- Problem: module listing computes totals with `all_docs = list(query.stream())` and slices results in Python.
- Files: `AURA-NOTES-MANAGER/api/modules/service.py`
- Cause: Firestore count/pagination is not modeled separately from fetch logic.
- Improvement path: use cursors for pagination and a separate lightweight count strategy or cached counts.

**Hierarchy and note operations repeatedly scan entire sibling collections:**
- Problem: create/update flows read whole collections to generate unique names or locate nested documents.
- Files: `AURA-NOTES-MANAGER/api/hierarchy_crud.py`, `AURA-NOTES-MANAGER/api/notes.py`, `AURA-NOTES-MANAGER/api/users.py`
- Cause: uniqueness and path lookup depend on `stream()` over sibling or collection-group queries.
- Improvement path: add indexed natural keys or counters and avoid full scans for common writes.

**Document processing stores entities and relationships sequentially:**
- Problem: `AURA-CHAT/backend/document_processor.py` processes every entity and relationship one-by-one, and `AURA-CHAT/backend/graph_manager.py` executes one query per relationship.
- Files: `AURA-CHAT/backend/document_processor.py`, `AURA-CHAT/backend/graph_manager.py`
- Cause: no batching layer exists between extraction output and Neo4j writes.
- Improvement path: batch entity upserts and relationship creation with `UNWIND` queries and bounded concurrency.

**Graph visualization defaults are heavy for dense graphs:**
- Problem: the graph page defaults to `limit: 500` and `depth: 2`, which can overwhelm WebGL rendering and client memory on large datasets.
- Files: `AURA-CHAT/client/src/features/graph/GraphPage.tsx`, `AURA-CHAT/client/src/hooks/useGraphQuery.ts`
- Cause: aggressive default fetch size and client-side rendering of large result sets.
- Improvement path: lower default limits, require progressive expansion, and surface truncation more aggressively.

## Fragile Areas

**Recursive Firestore delete flow:**
- Files: `AURA-NOTES-MANAGER/api/hierarchy_crud.py`
- Why fragile: delete behavior depends on recursive collection walking, local file deletion, and best-effort exception swallowing in `delete_document_recursive()`.
- Safe modification: change delete semantics only with integration coverage for Firestore structure and filesystem cleanup.
- Test coverage: gaps around recursive delete failure modes and partial cleanup handling.

**Session and chat persistence paths:**
- Files: `AURA-CHAT/server/routers/chat.py`, `AURA-CHAT/backend/routers/sessions.py`, `AURA-CHAT/backend/session_manager.py`
- Why fragile: several failure branches log and return `[]`, `False`, or SSE error events, which can mask persistence failures as empty data.
- Safe modification: preserve response contracts, then add explicit failure telemetry before altering return semantics.
- Test coverage: streaming happy paths exist, but failure-path assertions are thin for persistence and cache sync behavior.

**Admin dashboard page state:**
- Files: `AURA-NOTES-MANAGER/frontend/src/pages/AdminDashboard.tsx`
- Why fragile: one page owns user CRUD, hierarchy CRUD, tab state, modal state, and per-department fetch loops.
- Safe modification: extract API hooks and tab-specific child components before changing workflow logic.
- Test coverage: no dedicated `AdminDashboard` test file detected.

## Scaling Limits

**Firestore hierarchy scale:**
- Current capacity: acceptable for small-to-moderate trees because many endpoints still stream entire sibling sets.
- Limit: write latency and admin list views will degrade as departments, semesters, modules, notes, and users grow.
- Scaling path: replace collection scans with indexed lookups, counters, and cursor-based pagination in `AURA-NOTES-MANAGER/api/hierarchy_crud.py`, `AURA-NOTES-MANAGER/api/users.py`, and `AURA-NOTES-MANAGER/api/modules/service.py`.

**Knowledge graph processing throughput:**
- Current capacity: single-document processing works, but the pipeline is dominated by sequential extraction, embedding, and write steps.
- Limit: larger documents and higher concurrency will increase wall-clock time and worker contention.
- Scaling path: break `AURA-NOTES-MANAGER/api/kg_processor.py` and `AURA-CHAT/backend/document_processor.py` into resumable pipeline stages with batch writes and clearer backpressure.

## Dependencies at Risk

**Cross-app frontend version drift:**
- Risk: the two apps run different major React/Vite/TypeScript combinations, making shared patterns and future library upgrades harder to coordinate.
- Impact: fixes and shared UI ideas do not transfer cleanly between `AURA-CHAT` and `AURA-NOTES-MANAGER`.
- Migration plan: align versions gradually, starting with shared tooling expectations in `AURA-CHAT/client/package.json` and `AURA-NOTES-MANAGER/frontend/package.json`.

**Workspace tooling ambiguity:**
- Risk: there are multiple package roots, and the repo root `package.json` contains only a minimal dependency set including a suspicious `"-"` package entry.
- Impact: contributors can install or run tooling in the wrong package root and get inconsistent dependency graphs.
- Migration plan: either formalize workspaces at the repo root or remove the root manifest if it is not authoritative.

## Missing Critical Features

**No strong automated quality gate for coverage:**
- Problem: backend coverage in `AURA-CHAT/pyproject.toml` only enforces `fail_under = 30`, AURA-CHAT client thresholds are commented out in `AURA-CHAT/client/vitest.config.ts`, and AURA-NOTES-MANAGER frontend coverage config in `AURA-NOTES-MANAGER/frontend/vite.config.ts` sets no thresholds.
- Blocks: reliable regression prevention in the largest and most change-prone modules.

## Test Coverage Gaps

**Admin and user-management flows:**
- What's not tested: the monolithic admin page and its combined hierarchy/user workflows.
- Files: `AURA-NOTES-MANAGER/frontend/src/pages/AdminDashboard.tsx`, `AURA-NOTES-MANAGER/api/users.py`
- Risk: regressions in permissions, filtering, and sync behavior can ship without direct UI or API coverage.
- Priority: High

**Background document status updates:**
- What's not tested: direct unit coverage for lookup/update helpers in the Celery wrapper.
- Files: `AURA-NOTES-MANAGER/api/tasks/document_processing_tasks.py`
- Risk: status transitions can silently stop updating Firestore while the worker continues processing.
- Priority: Medium

**Failure-path behavior in session and streaming endpoints:**
- What's not tested: sanitization and recovery when streaming or persistence fails mid-response.
- Files: `AURA-CHAT/server/routers/chat.py`, `AURA-CHAT/backend/routers/sessions.py`, `AURA-CHAT/backend/session_manager.py`
- Risk: client-visible errors and silent data loss remain easy to reintroduce.
- Priority: Medium

---

*Concerns audit: 2026-03-10*
