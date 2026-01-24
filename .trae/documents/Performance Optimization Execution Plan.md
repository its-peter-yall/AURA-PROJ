# Performance Optimization Plan

Based on the research findings and the provided plan file, here is the execution plan to optimize AURA-CHAT and AURA-NOTES-MANAGER.

## 1. Async Neo4j Migration
**File:** `AURA-CHAT/backend/graph_manager.py`
- **Objective:** Eliminate blocking I/O by migrating to the async Neo4j driver.
- **Actions:**
    - Replace `GraphDatabase` with `AsyncGraphDatabase`.
    - Convert `_connect` to use `async with await self.driver.session()`.
    - Update all query methods (`execute_query`, `execute_write`) to be `async def` and use `await`.
    - Replace `time.sleep()` with `await asyncio.sleep()` in retry logic.
    - Ensure all callers in `rag_engine.py` and routers are updated to await these calls.

## 2. Redis Caching Layer for KG Queries
**File:** `AURA-CHAT/backend/cache/kg_cache.py` (New File)
- **Objective:** Reduce database load by caching frequent Knowledge Graph query results.
- **Actions:**
    - Create a new module for KG caching.
    - Implement `get_cached_query`, `set_cached_query`, and `invalidate_query`.
    - Use hash-based keys: `kg:{hash(query, params)}`.
    - Set default TTL to 5 minutes (300s).
    - Handle Redis connection errors gracefully (fallback to direct query).

## 3. RAG Engine Optimization
**File:** `AURA-CHAT/backend/rag_engine.py`
- **Objective:** Integrate caching and parallelize independent queries.
- **Actions:**
    - Import `kg_cache`.
    - Wrap `semantic_search` and other expensive queries with cache lookups (Cache-Aside pattern).
    - Use `asyncio.gather()` in `semantic_entity_search` to run the 4 entity type queries in parallel instead of sequentially.

## 4. Frontend Component Memoization
**File:** `AURA-CHAT/client/src/features/chat/ChatPage.tsx`
- **Objective:** Reduce excessive re-renders to improve UI responsiveness.
- **Actions:**
    - **Memoize Component:** Wrap `ChatPage` (or its heavy sub-components) with `React.memo()`.
    - **Optimize Handlers:** Wrap event handlers (e.g., `handleSendMessage`) in `useCallback()`.
    - **State Consolidation:** Group related state variables (e.g., UI flags) into a single object where appropriate to reduce render cycles.
    - **Derived State:** Use `useMemo()` for expensive calculations or array transformations (e.g., filtering sessions).

## Verification Plan
- **Backend:** Run existing tests to ensure async migration didn't break logic.
- **Caching:** Verify cache hits/misses via logs or Redis monitor.
- **Frontend:** Check React DevTools Profiler to confirm reduced re-renders.
