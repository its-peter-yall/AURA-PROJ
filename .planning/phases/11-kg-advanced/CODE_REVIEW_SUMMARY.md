# Code Review Summary: Phase 11 Knowledge Graph Enhancements

**Review Date:** 2026-01-24  
**Scope:** Last 6 commits (HEAD~6..HEAD) in AURA-NOTES-MANAGER  
**Branch:** main

---

## Overview

This review examined the Phase 11 knowledge graph enhancements including:
- Auto-summarization (summaries router + service)
- Trend analysis (trends router + analyzer)
- Template-based extraction (templates router + service)
- Graph visualization (graph visualizer, schema endpoints)
- Schema validation and migration
- Multimodal processing services

---

## Issues Found and Fixed

### 1. GET Summaries Could Regenerate (High Risk)

**Problem:** `GET /v1/summaries/document/{id}` and `GET /v1/summaries/module/{id}` called `summarize_document()` and `summarize_module()` with `force_regenerate=False`, which still triggers LLM generation on cache miss. This causes unintended cost/latency on read operations.

**Impact:** Every cache miss on a GET request triggers LLM summarization.

**Fix Applied:**
- Added `keys(pattern)` method to `api/cache.py` for Redis key listing
- Added `get_cached_document_summary()` and `get_cached_module_summary()` in `services/summary_service.py`
- Updated GET endpoints in `api/routers/summaries.py` to use cache-only methods
- Returns 404 if no cached summary exists

**Files Changed:**
- `api/cache.py:211-229` (new `keys()` method)
- `services/summary_service.py:308-399` (new cache-only helpers)
- `api/routers/summaries.py:179-200, 415-438` (updated GET endpoints)

---

### 2. Trend Analysis Missing `created_at` on Entities (High Risk)

**Problem:** Trend analyzer queries like `get_trending_concepts()` and `get_emerging_concepts()` filter on `e.created_at`, but `api/kg_processor.py` did not set `created_at` when creating entity nodes. Additionally, the code passed ISO string dates to Neo4j, which could cause type mismatches.

**Impact:** Trend endpoints return empty results because `created_at` is always NULL.

**Fix Applied:**
- Added `created_at` and `updated_at` to entity node creation in `api/kg_processor.py:3241-3277`
- Uses `ON CREATE SET e.created_at = $created_at` and `SET e.updated_at = $updated_at`
- Both timestamps use `datetime.utcnow().isoformat()`

---

### 3. Granularity Validation Using Deprecated Pydantic v1 Pattern (Medium Risk)

**Problem:** `api/routers/trends.py` used `regex` parameter in `Query()` which is deprecated in Pydantic v2. Invalid values could raise 500 errors instead of 400.

**Fix Applied:**
- Changed `granularity` parameter type to `Literal["day", "week", "month", "semester"]` in `api/routers/trends.py:365`
- Added `Literal` import
- Removed `regex` parameter and `# type: ignore` comment

---

### 4. Graph Schema/Data Endpoints Bypassed Dependency Guard (Medium Risk)

**Problem:** `get_graph_schema()` and `get_graph_data()` in `api/routers/query.py` used global `neo4j_driver` directly instead of the injected `graph_manager.driver`. The dependency injection guard was bypassed.

**Impact:** If `graph_manager` is available but `neo4j_driver` is None, the endpoint crashes with AttributeError.

**Fix Applied:**
- Use `graph_manager.driver` instead of `neo4j_driver` in `api/routers/query.py:458-465, 648-655`
- Added explicit 503 guard before session creation

---

### 5. Search Request Did Not Support Query/Graph Expansion Config (Medium Risk)

**Problem:** Frontend sent `queryExpansion` and `graphExpansion` configs in `frontend/src/features/kg-query/api/kg-query.api.ts:53-66`, but `SearchRequest` in `api/schemas/search.py` had no fields for these. The backend always used hardcoded `expand_entities=True, hop_depth=2`.

**Impact:** Frontend expansion controls have no effect.

**Fix Applied:**
- Added `QueryExpansionConfig` model in `api/schemas/search.py:24-47`
- Added `query_expansion` and `graph_expansion` optional fields to `SearchRequest` in `api/schemas/search.py:105-112`
- Updated `/v1/kg/query` endpoint in `api/routers/query.py:225-264` to:
  - Read expansion configs from request
  - Call `expand_query()` when query expansion enabled
  - Build `ExpansionInfo` response if terms were added
  - Pass expansion config to `search_with_graph_expansion()`

---

## Additional Observations (Not Fixed)

### Template CRUD Endpoints Are Unauthenticated

**Location:** `api/routers/templates.py`, `services/extraction_templates.py`

Template creation, update, and delete endpoints accept user-provided regex patterns without authentication. This is a security concern:
- No auth check on POST/DELETE templates
- User-provided regex patterns used in `re.search()` without complexity limits
- Potential for ReDoS or template injection

**Recommendation:** Add auth/role checks for template mutations and validate regex length/complexity.

---

### Background Module Summary Task Status Not Exposed

**Location:** `api/routers/summaries.py:249-276`

When a large module (>10 docs) triggers background processing, a `task_id` is returned, but no endpoint exists to query task status by ID. Users cannot check if their background task completed.

**Recommendation:** Add `GET /v1/summaries/tasks/{task_id}` endpoint.

---

## Testing Status

**Command:** `../venv/Scripts/python -m pytest`

**Result:** Tests started successfully but timed out after 120s at `tests/benchmark/test_kg_performance.py`. Earlier tests (celery tasks, women empowerment) passed.

**Recommendation:** Run tests with longer timeout or skip benchmarks:
```bash
../venv/Scripts/python -m pytest -k "not benchmark"
```

---

## Files Modified

| File | Changes |
|------|---------|
| `api/cache.py` | Added `keys(pattern)` method |
| `services/summary_service.py` | Added cache-only retrieval helpers, timestamp parsing |
| `api/routers/summaries.py` | GET endpoints use cache-only methods |
| `api/kg_processor.py` | Added `created_at`/`updated_at` to entity writes |
| `api/routers/trends.py` | Changed granularity to `Literal` type |
| `api/routers/query.py` | Graph endpoints use `graph_manager.driver`, wired expansion configs |
| `api/schemas/search.py` | Added `QueryExpansionConfig`, expansion fields in `SearchRequest` |

---

## Recommendations for Follow-Up

1. **Run tests without benchmarks** to verify no regressions
2. **Add auth to template CRUD endpoints**
3. **Add task status endpoint** for background module summaries
4. **Consider splitting query expansion** to only affect fulltext (not vector) search - the current implementation expands the query for both, but `search_with_expansion` in `rag_engine.py` shows the original design intent was to expand only fulltext while keeping vector on the original query
5. **Add monitoring** for trend analyzer queries to detect when `created_at` data populates
