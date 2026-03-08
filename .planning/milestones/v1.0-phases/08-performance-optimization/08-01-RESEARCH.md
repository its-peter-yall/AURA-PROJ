# Research Plan: Exhaustive Performance Optimization

**Phase:** 08-performance-optimization
**Objective:** Identify performance bottlenecks and optimization opportunities across the full stack (AURA-CHAT and AURA-NOTES-MANAGER) without breaking existing functionality.

## Context
The application consists of two main parts:
1.  **AURA-NOTES-MANAGER**: Staff portal for document management, KG processing (Celery), and module management.
2.  **AURA-CHAT**: Student RAG chat with Knowledge Graph (Neo4j), study sessions, and module-aware RAG.

**Stack:**
- **Backend:** Python 3.11, FastAPI, Celery, Neo4j, Redis, Gemini (Vertex AI).
- **Frontend:** React 18, Vite, TypeScript, TanStack Query, Zustand.
- **Infrastructure:** Docker Compose.

## Research Areas

### 1. Backend Performance (FastAPI + Python)
- **Async/Sync Usage:** Identify blocking synchronous calls within async route handlers (especially DB/Network I/O).
- **Serialization:** Check for heavy Pydantic model serialization/validation in hot paths.
- **Database Access:** Analyze Neo4j query patterns. Are we using sessions correctly? Are queries optimized (indexes)?
- **Celery:** Review task granularity. Are tasks too small (overhead) or too large (timeout risk)?

### 2. Knowledge Graph & RAG (Neo4j + Gemini)
- **Vector Search:** Review HNSW index configuration.
- **Graph Traversal:** Analyze `rag_engine.py` and `graph_manager.py` for potentially unbounded traversals or inefficient queries.
- **Embedding Generation:** Check for latency in Gemini API calls. Can we batch better?

### 3. Frontend Performance (React + Vite)
- **Bundle Size:** Analyze import patterns. Are we lazy-loading heavy components?
- **Re-renders:** Identify components with potential excessive re-renders (state management usage).
- **Network Waterfalls:** Check for N+1 API request patterns, especially in the "Module" and "Explorer" views.

### 4. Architecture & Workflow
- **Caching:** Review Redis usage. Are we caching expensive KG queries?
- **Docker/Dev Env:** Is the slow performance due to Docker volume mounts or resource limits?

## Instructions for Agent
1.  **Codebase Exploration:**
    - Search for `def` vs `async def` mismatches.
    - Search for Neo4j query strings (Cypher) and analyze them for obvious performance flaws (e.g., missing labels, broad matches).
    - Check `package.json` and `requirements.txt` for outdated or heavy dependencies.
2.  **Web Research:**
    - Best practices for "FastAPI Neo4j async performance".
    - "React TanStack Query performance optimization patterns".
    - "Celery Redis broker optimization".
3.  **Output:**
    - A list of **Specific Findings** (e.g., "File X uses synchronous `requests` inside async route").
    - A list of **Actionable Recommendations** (e.g., "Refactor X to use `httpx`").
    - A set of **Tools/Benchmarks** we should implement (e.g., "Add `py-spy` to Docker").

**Deliverable:** A comprehensive `FINDINGS.md` document.
