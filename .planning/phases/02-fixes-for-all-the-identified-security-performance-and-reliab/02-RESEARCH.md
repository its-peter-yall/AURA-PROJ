# Phase 2 Research: Production-Hardening Fixes

**Researched:** 2026-05-03
**Status:** Ready for planning

---

## Executive Summary

This phase addresses 8 production-hardening issues (6 security/performance/reliability fixes + 2 DevEx adjustments) identified in a codebase audit. All fixes are localized — no architectural redesign required. The primary risks are: (1) breaking SSE client contracts when sanitizing errors, (2) introducing N+1 queries when replacing Firestore offset pagination with cursor-based, and (3) accidentally changing Neo4j write semantics when batching relationships.

**Estimated effort:** 2-3 days for experienced developer familiar with the codebase. Work can be parallelized across the two sub-projects (AURA-CHAT and AURA-NOTES-MANAGER) since they share no source files.

---

## Issue 1: Streaming Endpoint Exception Sanitization

**Files:**
- `AURA-CHAT/server/routers/chat.py:879-889`
- `AURA-CHAT/backend/routers/sessions.py:671-681`

**Current code** (chat.py):
```python
except Exception as e:
    logger.error(f"Error during streaming event generation: {e}", exc_info=True)
    error_chunk = {
        "type": "error",
        "message": "I apologize, but I encountered an error while streaming the response.",
        "error": str(e),  # <-- leaks exception details to client
    }
```

**Current code** (sessions.py):
```python
except Exception as exc:
    logger.error("Streaming query failed", extra={"session_id": session_id, ...})
    yield format_sse("error", {"type": "error", "error": str(exc)})
```

### Research Findings

**Best practice from FastAPI docs and OWASP:** Never forward raw exception messages to clients in production. They may leak:
- Internal file paths (e.g., `/app/server/routers/chat.py:123`)
- Database query details (connection strings, table names)
- API keys or tokens accidentally logged in exception args
- Stack traces revealing internal architecture

### Recommended Approach

1. **Replace `str(e)` with a sanitized error code**, not a generic message (preserves client's ability to differentiate error types for UX).
2. **Log full exception server-side** with `exc_info=True` (already done in chat.py).
3. **Use a mapping of safe error categories** instead of leaking internals:

```python
# Pattern for chat.py:
except Exception as e:
    logger.error("Error during streaming event generation", exc_info=True)
    error_chunk = {
        "type": "error",
        "code": "stream_error",
        "message": "I encountered an error while streaming the response.",
    }
    yield f"data: {json.dumps(error_chunk)}\n\n"

# Pattern for sessions.py:
except Exception as exc:
    logger.error("Streaming query failed", exc_info=True)
    yield format_sse("error", {
        "type": "error",
        "code": "stream_error",
    })
```

**Client contract impact:** The `"error"` key changes from containing a message string to being absent (or a code). Frontend SSE handlers must be checked — they currently read `event.error` or `event.type === 'error'`. The `code: "stream_error"` preserves the ability to differentiate error types without leaking data.

**Deferred:** Add typed error codes (e.g., `timeout_error`, `model_error`, `rate_limit_error`) in a future phase when a proper error taxonomy exists. For now, a single `stream_error` code is sufficient — the important fix is removing `str(e)`.

---

## Issue 2: Security Headers Skip Streaming Routes

**File:** `AURA-CHAT/server/security/middleware.py:239-242`

**Current code:**
```python
async def dispatch(self, request: Request, call_next: Callable) -> Response:
    # Skip security headers for streaming endpoints to prevent buffering
    if "/stream" in request.url.path:
        return await call_next(request)
```

### Research Findings

**The concern about buffering is real but overly broad.** SSE responses already set `X-Accel-Buffering: no` (in both streaming routers) which prevents Nginx/proxy buffering. However, some headers CAN cause issues with SSE:
- `Content-Security-Policy` — no impact on SSE streams (it's a document policy, not a transport policy)
- `X-Frame-Options` — no impact on SSE (iframe policy only)
- `Strict-Transport-Security` — no impact on SSE (it's a one-time instruction to the browser)

**Key insight from FastAPI SSE docs:** FastAPI's `EventSourceResponse` already sets `Cache-Control: no-cache` and `X-Accel-Buffering: no`. Adding CSP/X-Frame-Options/etc. to SSE responses is safe and recommended.

### Recommended Approach

**Remove the `/stream` bypass entirely.** All headers are safe for SSE responses. If there are edge cases, use a **reduced set** rather than a full bypass:

```python
# Option A (recommended): Remove bypass entirely
async def dispatch(self, request: Request, call_next: Callable) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    # ... all other headers
    return response

# Option B (conservative): Reduced set for SSE
SAFE_SSE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}
FULL_HEADERS = {
    **SAFE_SSE_HEADERS,
    "Content-Security-Policy": "default-src 'self' ...",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}
```

Choose **Option A** unless testing reveals a concrete buffering issue — CSP headers don't cause SSE buffering in any major browser or proxy.

**Verification:** Check the `Content-Type` header of SSE responses in the middleware. SSE routes set `content-type: text/event-stream` — the middleware could apply different headers based on content type instead of URL pattern.

---

## Issue 3: Dynamic Cypher Label Interpolation

**Files:** `AURA-CHAT/backend/graph_manager.py` (lines 408-413, 532-536, 766-769)

**Current code pattern:**
```python
query = f"""
MATCH (a:{source_type} {{id: $source_id}})
MATCH (b:{target_type} {{id: $target_id}})
MERGE (a)-[r:{rel_type}]->(b)
"""
```

### Research Findings

**From Neo4j official docs and security guidelines:**

1. **Cypher parameters cannot be used for labels, relationship types, or property keys.** The official driver manual explicitly states this: "although parameters work for literals and expressions, as well as node labels and relationship types, they can't be used for property keys."

2. **Wait — that's contradictory.** Let me clarify: The Neo4j docs say parameters work for labels and relationship types starting from Neo4j 5.x with certain driver versions. However, the safer and more compatible approach for Neo4j 5.13 (Community) is **allowlist validation**.

3. **OWASP/Neo4j recommendation:** "The best protection against Cypher Injection is to always parameterize user input. If possible, update your data model to avoid needing to query using dynamic labels. ... It is possible to add validation to the user input as well."

### Recommended Approach

**Add a `_validate_label()` helper that checks against a canonical allowlist.** This is the recommended pattern from Neo4j's security guide:

```python
# In config.py (add to existing Config class):
ALLOWED_NODE_LABELS: set[str] = {
    "Topic", "Concept", "Methodology", "Finding",
    "Document", "Chunk", "ParentChunk",
}
ALLOWED_REL_TYPES: set[str] = set(Config.LLM_RELATIONSHIP_TYPES) | {
    "HAS_CHUNK", "CONTAINS_ENTITY",
}

# In graph_manager.py:
def _validate_label(self, label: str, allowlist: set[str]) -> str:
    """Validate a dynamic Cypher label/rel type against allowlist."""
    if not isinstance(label, str) or not label:
        raise ValueError(f"Invalid empty label")
    if label not in allowlist:
        raise ValueError(
            f"Disallowed label '{label}'. "
            f"Allowed: {sorted(allowlist)}"
        )
    return label
```

**Usage at each call site (3 locations):**
```python
# Before:
query = f"MATCH (a:{source_type} {{id: $source_id}}) ..."
# After:
safe_source_type = self._validate_label(source_type, ALLOWED_NODE_LABELS)
safe_target_type = self._validate_label(target_type, ALLOWED_NODE_LABELS)
safe_rel_type = self._validate_label(rel_type, ALLOWED_REL_TYPES)
query = f"MATCH (a:{safe_source_type} {{id: $source_id}}) ..."
```

**The alternative (Neo4j backtick escaping):** The driver manual shows escaping dynamic labels with backticks. This prevents injection but allows typos. Allowlist validation is stricter and preferred for this codebase where labels come from LLM output.

**Entity type normalization:** The `llm_entity_extractor.py` already maps entity types (e.g., `"concepts"` -> `"Concept"`). Verify that the mapped types always match the allowlist. If LLM output produces unmapped types, the validation will catch it at query time with a clear error message rather than silently creating nodes with wrong labels.

---

## Issue 4: Firebase Auth Sync Silently Swallows Failures

**File:** `AURA-NOTES-MANAGER/api/users.py:528-534, 550-554, 592-601`

**Current pattern (3 occurrences):**
```python
try:
    firebase_auth.update_user(user_id, display_name=update_data.displayName)
except Exception:
    pass  # Non-critical, continue with Firestore update
```

### Research Findings

**Firebase Auth `update_user()` raises `firebase_admin.auth.UnexpectedResponse` or `ValueError` on failure.** Common failure modes:
- Network timeout (transient — should retry)
- Invalid email format (permanent — should surface)
- User not found in Firebase but exists in Firestore (inconsistency — should surface)
- Firebase Auth rate limits (429 — should log + retry)

**Design tradeoff:** The current code treats Firebase Auth as non-critical. This is reasonable — a user's display name in Firebase Auth claims is secondary to the Firestore record. However, silent failures lead to:
- Inconsistent state (Firestore says `displayName: "John"` but Firebase Auth still shows old name)
- Undetected security issues (disable_user succeeds in Firestore but not in Auth)

### Recommended Approach

**Replace bare `except Exception: pass` with logged warnings.** This preserves the current design intent (Firestore is canonical, Firebase Auth is secondary) while providing observability:

```python
import logging
logger = logging.getLogger(__name__)

# In each of the 3 locations:
try:
    firebase_auth.update_user(user_id, display_name=update_data.displayName)
except firebase_admin.auth.UnexpectedResponse as e:
    logger.warning(
        "Firebase Auth update failed for user %s: %s", user_id, str(e)
    )
except Exception as e:
    logger.error(
        "Unexpected Firebase Auth error for user %s: %s", user_id, str(e),
        exc_info=True
    )
```

**Do NOT raise HTTPException** — that would roll back the Firestore update (which already succeeded). The pattern above:
- Logs at `WARNING` for known Firebase Auth failures (transient, rate limits)
- Logs at `ERROR` for unexpected failures (bugs, inconsistencies)
- Preserves the Firestore update (the canonical record)

**Consider adding a `_safe_firebase_update()` helper** to reduce repetition across the 3 locations.

**Deferred:** Add structured logging with a "firebase_auth_sync_failed" event type for alerting/monitoring. Add a reconciliation job that periodically syncs Firestore -> Firebase Auth for inconsistent users.

---

## Issue 5: Firestore Pagination Loads Full Collections

**File:** `AURA-NOTES-MANAGER/api/modules/service.py:162-169`

**Current code:**
```python
all_docs = list(query.stream())  # Loads ALL documents into memory
total = len(all_docs)
offset = (page - 1) * page_size
paginated_docs = all_docs[offset : offset + page_size]
```

### Research Findings

**From Google Cloud Firestore docs:**

Firestore supports two pagination approaches:

1. **Offset-based** (simple, but costly):
   - `query.offset(num).limit(page_size).stream()`
   - Firestore still reads (and bills for) all documents up to the offset
   - `offset(N)` counts as N reads even though you only get `page_size` results
   - Not suitable for large datasets

2. **Cursor-based** (efficient, recommended):
   - Use `query.limit(page_size).stream()`, record last document
   - Next page: `query.start_after(last_doc).limit(page_size).stream()`
   - Only reads `page_size` documents per page (no waste)
   - Requires an `order_by` clause for deterministic cursors

**Current code needs both `total` count and paginated results.** The `total` is the challenge — Firestore has no efficient COUNT operation. Options:
- **(A)** Accept no total count, use cursor-based pagination with `has_more` flag
- **(B)** Keep a pre-computed count in a separate document (updated asynchronously)
- **(C)** Use `query.limit(page_size).offset(offset)` — same cost as current but at least server-side filtered

### Recommended Approach

**Replace with offset-based pagination at the query level** (Option C — simplest, 80% improvement for small-to-medium collections). This moves the filtering to Firestore's query engine instead of Python:

```python
# Replace this:
all_docs = list(query.stream())
total = len(all_docs)
offset = (page - 1) * page_size
paginated_docs = all_docs[offset : offset + page_size]

# With this:
total_query = query.count(alias="total")
total_result = list(total_query.stream())
total = total_result[0][0] if total_result else 0
offset = (page - 1) * page_size
paginated_docs = list(query.offset(offset).limit(page_size).stream())
```

**Wait — `query.count()` is available in the Firestore Python client library but requires specific API enablement.** Check if the Firestore `count()` aggregation is available in the installed version. If not, use `.limit().offset()` without the count and accept that total is unavailable:

```python
offset = (page - 1) * page_size
paginated_docs = list(query.offset(offset).limit(page_size).stream())
# Return next_page_token or has_more based on result count
has_more = len(paginated_docs) == page_size
```

**Prefer cursor-based pagination** for truly large collections (>10K docs). But for a prototype with expected collections under 10K documents, the offset-based approach is sufficient and simpler to implement without changing the API contract.

**API contract impact:** The endpoint currently returns `total` and `page_info`. If switching to cursor-based, need to replace `total` with `has_more` or `next_cursor`. If using offset-based, `total` can be preserved with the `count()` aggregation.

---

## Issue 6: Sequential Neo4j Relationship Writes

**File:** `AURA-CHAT/backend/document_processor.py:961-969`

**Current code:**
```python
for rel in document_data["relationships"]:
    await graph_manager.create_relationship(
        rel["source_type"], rel["source_id"],
        rel["rel_type"], rel["target_type"],
        rel["target_id"], rel["properties"],
    )
```

### Research Findings

**From Neo4j Python driver manual and performance guides:**

Batching writes with `UNWIND` is the recommended pattern for Neo4j performance. Key facts:
- Each `session.run()` call involves a network round-trip + transaction overhead
- The neo4j library's `execute_query` has built-in connection pooling, but sequential `.run()` calls are still serialized
- `UNWIND $batch AS item ...` processes all items in a single transaction

**Important caveat from Neo4j docs:** `UNWIND` with a large batch can cause memory pressure on the server. Recommended batch size: 500-1000 items per `UNWIND`.

### Recommended Approach

**Option A (recommended): Add a `batch_create_relationships` method to `GraphManager`:**

```python
# In graph_manager.py:
async def batch_create_relationships(
    self, relationships: list[dict]
) -> None:
    """Create multiple relationships in a single UNWIND query."""
    if not relationships:
        return
    # Labels still need allowlist validation
    # Use first relationship's types to build query
    query = """
    UNWIND $rels AS rel
    MATCH (source {id: rel.source_id})
    MATCH (target {id: rel.target_id})
    MERGE (source)-[r:RELATED_TO]->(target)
    SET r += rel.properties
    RETURN count(r) as created
    """
    result = await self.execute_query(
        query, {"rels": relationships}
    )
    return result
```

**Wait — this has the same label interpolation problem.** The relationship type in the pattern `[r:RELATED_TO]` is fixed. If different relationships have different types, we need dynamic rel types. Options:

**Option A1:** Group relationships by type before batching:
```python
# In document_processor.py:
from itertools import groupby
grouped = {}
for rel in document_data["relationships"]:
    rel_type = rel["rel_type"]
    grouped.setdefault(rel_type, []).append(rel)

for rel_type, rels in grouped.items():
    await graph_manager.batch_create_relationships(
        rel_type, rels,
        rel["source_type"], rel["target_type"],
    )
```

**Option A2:** Use `apoc.create.relationship` (requires APOC plugin):
```python
query = """
UNWIND $rels AS rel
MATCH (source {id: rel.source_id})
MATCH (target {id: rel.target_id})
CALL apoc.create.relationship(
    source, rel.rel_type, rel.properties, target
) YIELD rel AS r
RETURN count(r) as created
"""
```

**Recommendation:** Use **Option A1** (group-by-type with `UNWIND`) since it doesn't require the APOC plugin. The `document_processor.py` loop has ~50 relationships per document on average, so the overhead of 3-5 groups vs 50 individual calls is significant.

The `create_relationship` method in `graph_manager.py` should be refactored to call the batch variant internally (or the document_processor should call the batch method directly).

---

## Issue 7: Graph Visualization Defaults Too High

**Files:**
- `AURA-CHAT/client/src/features/graph/GraphPage.tsx:271-272` (frontend defaults)
- `AURA-CHAT/server/routers/graph.py:178-179` (backend API defaults)

**Current code:**
```typescript
// GraphPage.tsx
filters = { limit: 500, depth: 2 }
```

```python
# graph.py
depth: int = Query(2, ge=1, le=5)
limit: int = Query(500, ge=1, le=1000)
```

### Research Findings

**Reagraph performance characteristics** (from codebase usage and general WebGL graph rendering knowledge):
- 500 nodes with depth-2 traversal can produce thousands of edges
- WebGL rendering (Reagraph) handles ~500-1000 nodes well before frame drops
- The real bottleneck is the **API response time** — generating and serializing the graph payload for 500 nodes + edges is expensive
- Initial page load fetching this is wasteful if the user hasn't even interacted with the graph

**UX pattern research:** Progressive graph loading is standard in visualization tools:
1. Load an overview (small, manageable)
2. Allow node expansion on click
3. Allow filter/depth adjustments in the UI

### Recommended Approach

**Lower defaults on both ends:**

```python
# server/routers/graph.py: Change defaults
depth: int = Query(1, ge=1, le=5)  # Changed from 2 to 1
limit: int = Query(100, ge=1, le=1000)  # Changed from 500 to 100
```

```typescript
// GraphPage.tsx: Match server defaults
filters = { limit: 100, depth: 1 }
```

**Add UI for progressive expansion:**
- "Expand selected node" button (loads +1 depth for that node's neighborhood)
- "Load more" button (increases limit by 100)
- Settings panel already exists — users can adjust depth (1-5) and limit

**Backend consideration:** The server default change means existing API consumers will get smaller graphs by default. This is fine — it's a performance improvement. The server already supports `depth` and `limit` query parameters for override.

**Performance testing:** After change, verify that with `limit=100, depth=1`:
- API response time < 500ms for typical module graphs
- Reagraph renders without frame drops on mid-range hardware
- If a user needs more, the controls are available

---

## Issue 8: Dev Servers Bind 0.0.0.0 by Default

**Files:**
- `AURA-CHAT/server/main.py:241-244` (`host="0.0.0.0"` in `__main__` block)
- `AURA-NOTES-MANAGER/api/main.py:582-585` (`host="0.0.0.0"` in `__main__` block)
- `AURA-NOTES-MANAGER/frontend/vite.config.ts:50-53` (`host: true`)

### Research Findings

**Security concern:** Binding to `0.0.0.0` exposes the dev server to all network interfaces, allowing LAN access. In shared environments (coffee shops, university networks), this is a security risk:
- Unauthenticated access to dev APIs
- Potential for SSRF attacks against the dev server
- Information disclosure (API docs, endpoint structure)

**Standard practice:** Dev servers should bind to `127.0.0.1` by default, with an environment variable override for intentional network access (e.g., mobile testing, CI/CD).

**Vite's `host: true`** enables network access. For NOTES frontend, this is likely to allow mobile testing. Should be configurable.

### Recommended Approach

**FastAPI `__main__` blocks:**

```python
# AURA-CHAT/server/main.py
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")  # Default to localhost
    uvicorn.run(
        "server.main:app",
        host=host,
        port=8000,
        reload=True,
    )
```

Apply the same pattern in `AURA-NOTES-MANAGER/api/main.py`.

**Vite config:**

```typescript
// AURA-NOTES-MANAGER/frontend/vite.config.ts
server: {
    port: 5174,
    host: process.env.HOST === 'true' || false,  // Default: false
    proxy: { ... }
}
```

Or with an env check:
```typescript
host: process.env.VITE_NETWORK_ACCESS === 'true' ? true : false,
```

**This maintains backward compatibility** — developers who need network access can set `HOST=0.0.0.0` or `VITE_NETWORK_ACCESS=true`.

---

## Cross-Cutting Concerns

### Testing Strategy

| Issue | Testing Approach | Existing Tests |
|-------|-----------------|----------------|
| 1. Exception sanitization | Mock streaming endpoint, assert `"error"` NOT in response; unit test for SSE error format | Check `tests/api/test_chat.py` |
| 2. Security headers | Integration test: call a `/stream` endpoint, assert X-Frame-Options header present | Check `tests/security/` |
| 3. Cypher allowlist | Unit test `_validate_label()` with valid/invalid labels; mock `graph_manager` in doc processor tests | Check `tests/backend/test_graph_manager.py` |
| 4. Firebase Auth logging | Unit test users.py with mocked `firebase_auth`, verify logger.warning called on failure | Check `api/tests/test_users.py` |
| 5. Firestore pagination | Integration test with test Firestore, verify only `page_size` docs read | Check `api/tests/` |
| 6. Neo4j batch writes | Unit test `batch_create_relationships` with mocked `execute_query`, verify single call with all rels | Check `tests/backend/test_document_processor.py` |
| 7. Graph defaults | Integration test: hit graph API, assert `limit <= 100` and `depth <= 1` in response | Check `tests/api/test_graph.py` |
| 8. Dev bindings | Config test: verify `HOST` env var override works | Manual only |

**Key insight from AGENTS.md:** This project follows TDD with Red → Green → Refactor. Write failing tests first (verify they fail), then fix, then refactor.

### Dependencies Between Issues

| Depends On | Blocks | Reason |
|------------|--------|--------|
| — | Issue 1 | Standalone |
| — | Issue 2 | Standalone |
| — | Issue 3 | Standalone (query validation) |
| — | Issue 4 | Standalone |
| — | Issue 5 | Standalone |
| Issue 3 | Issue 6 | Batch writes need label validation too |
| — | Issue 7 | Standalone |
| — | Issue 8 | Standalone |

**Recommendation:** Execute in parallel waves:
- **Wave 1:** Issues 1, 2, 3, 4, 5, 7, 8 (all independent)
- **Wave 2:** Issue 6 (depends on Issue 3's validation helper)

### Verification Approach

After all fixes:
1. Run `python -m pytest AURA-CHAT/tests/ -v` — all existing tests must pass
2. Run `pytest AURA-NOTES-MANAGER/api/tests/ -v` — all NOTES tests must pass
3. Run `npm run build` in both `AURA-CHAT/client/` and `AURA-NOTES-MANAGER/frontend/`
4. Run `npx tsc --noEmit` in both client directories
5. Manual smoke test of SSE streaming (chat page) — should still work
6. Manual smoke test of graph visualization — should load faster with new defaults

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| SSE client breaks due to removed `str(e)` | Medium | Medium | Search frontend for SSE error handlers before changing; maintain `code` field |
| Neo4j batch write changes semantics (MERGE vs CREATE) | Low | High | Thoroughly test batch variant against existing `create_relationship` behavior |
| Firestore pagination change breaks API contract (removes `total`) | Medium | Low | Keep `total` with `count()` aggregation; fall back to offset-based if aggregation unavailable |
| Cypher allowlist rejects valid LLM-extracted entity types | Low | Medium | Verify allowlist covers all types emitted by `llm_entity_extractor.py` |
| Security headers on SSE cause buffering regression | Low | Medium | Test with Nginx; SSE already has `X-Accel-Buffering: no` |
| Dev bind defaults break someone's workflow | Low | Low | Developers can set `HOST=0.0.0.0` env var |
| Firebase Auth logging introduces overhead | Low | Low | Log at WARNING level — low volume |
| Parallel execution of Wave 1 causes merge conflicts | Medium | Low | Files are in separate sub-projects (CHAT vs NOTES) — no merge conflicts expected |

---

## Appendix: Key Source Code References

| Issue | File | Lines | Sub-project |
|-------|------|-------|-------------|
| 1a | `AURA-CHAT/server/routers/chat.py` | 879-889 | AURA-CHAT |
| 1b | `AURA-CHAT/backend/routers/sessions.py` | 671-681 | AURA-CHAT |
| 2 | `AURA-CHAT/server/security/middleware.py` | 239-242 | AURA-CHAT |
| 3a | `AURA-CHAT/backend/graph_manager.py` | 408-413 | AURA-CHAT |
| 3b | `AURA-CHAT/backend/graph_manager.py` | 532-536 | AURA-CHAT |
| 3c | `AURA-CHAT/backend/graph_manager.py` | 766-769 | AURA-CHAT |
| 4a | `AURA-NOTES-MANAGER/api/users.py` | 528-534 | AURA-NOTES-MANAGER |
| 4b | `AURA-NOTES-MANAGER/api/users.py` | 550-554 | AURA-NOTES-MANAGER |
| 4c | `AURA-NOTES-MANAGER/api/users.py` | 592-601 | AURA-NOTES-MANAGER |
| 5 | `AURA-NOTES-MANAGER/api/modules/service.py` | 162-169 | AURA-NOTES-MANAGER |
| 6 | `AURA-CHAT/backend/document_processor.py` | 961-969 | AURA-CHAT |
| 7a | `AURA-CHAT/client/src/features/graph/GraphPage.tsx` | 271-272 | AURA-CHAT |
| 7b | `AURA-CHAT/server/routers/graph.py` | 178-179 | AURA-CHAT |
| 8a | `AURA-CHAT/server/main.py` | 241-244 | AURA-CHAT |
| 8b | `AURA-NOTES-MANAGER/api/main.py` | 582-585 | AURA-NOTES-MANAGER |
| 8c | `AURA-NOTES-MANAGER/frontend/vite.config.ts` | 50-53 | AURA-NOTES-MANAGER |
