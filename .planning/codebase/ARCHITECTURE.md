# Architecture

**Analysis Date:** 2026-03-10

## Pattern Overview

**Overall:** Dual-application monorepo with application-level boundaries, React feature modules on the frontend, and FastAPI adapter layers over Python domain services.

**Key Characteristics:**
- `AURA-CHAT/` separates HTTP adapters in `AURA-CHAT/server/` from graph/RAG/session logic in `AURA-CHAT/backend/`.
- `AURA-NOTES-MANAGER/` combines a React explorer in `AURA-NOTES-MANAGER/frontend/` with a mixed FastAPI backend in `AURA-NOTES-MANAGER/api/` and reusable AI services in `AURA-NOTES-MANAGER/services/`.
- Shared product flow crosses apps: staff-side hierarchy/module publishing in `AURA-NOTES-MANAGER/api/modules/router.py` feeds student-side hierarchy and study-session consumption in `AURA-CHAT/backend/routers/student_modules.py` and `AURA-CHAT/backend/routers/sessions.py`.

## Layers

**Workspace Composition:**
- Purpose: Keep the two products in one repo while preserving separate runtime entry points and deployment surfaces.
- Location: `AURA-CHAT/`, `AURA-NOTES-MANAGER/`, `.planning/`, `.github/workflows/`
- Contains: App-specific code, shared planning docs, CI definitions.
- Depends on: Per-app package manifests and Python requirements.
- Used by: Local development scripts such as `run-all.bat` and planning workflows in `.planning/`.

**AURA-CHAT Client Layer:**
- Purpose: Student-facing chat, graph, document, and settings UI.
- Location: `AURA-CHAT/client/src/`
- Contains: Route shell in `AURA-CHAT/client/src/App.tsx`, feature pages in `AURA-CHAT/client/src/features/`, auth state in `AURA-CHAT/client/src/stores/useAuthStore.ts`, API wrappers in `AURA-CHAT/client/src/lib/api.ts`.
- Depends on: `AURA-CHAT/server/` HTTP endpoints, Firebase client config in `AURA-CHAT/client/src/lib/firebase.ts`, TanStack Query, Zustand.
- Used by: Vite entry point `AURA-CHAT/client/src/main.tsx` and Playwright specs in `AURA-CHAT/client/e2e/*.spec.ts`.

**AURA-CHAT HTTP/API Layer:**
- Purpose: Expose authenticated REST and streaming endpoints while owning app lifecycle and dependency wiring.
- Location: `AURA-CHAT/server/`
- Contains: App bootstrap in `AURA-CHAT/server/main.py`, dependency singletons in `AURA-CHAT/server/dependencies.py`, routers in `AURA-CHAT/server/routers/*.py`, request/response schemas in `AURA-CHAT/server/schemas/*.py`.
- Depends on: Domain services in `AURA-CHAT/backend/`, Firebase auth helpers under `AURA-CHAT/server/auth/`, security middleware in `AURA-CHAT/server/security/middleware.py`.
- Used by: Chat client API calls from `AURA-CHAT/client/src/lib/api.ts`.

**AURA-CHAT Domain/Processing Layer:**
- Purpose: Keep RAG, graph access, chunking, task execution, and session persistence independent of HTTP transport.
- Location: `AURA-CHAT/backend/`
- Contains: `AURA-CHAT/backend/rag_engine.py`, `AURA-CHAT/backend/graph_manager.py`, `AURA-CHAT/backend/session_manager.py`, semantic routing in `AURA-CHAT/backend/semantic_router.py`, async jobs in `AURA-CHAT/backend/tasks/*.py`.
- Depends on: Neo4j, Redis/ARQ, Vertex AI wrappers in `AURA-CHAT/backend/utils/vertex_ai_client.py`.
- Used by: `AURA-CHAT/server/main.py`, `AURA-CHAT/server/routers/chat.py`, `AURA-CHAT/server/routers/documents.py`, and `AURA-CHAT/backend/routers/*.py`.

**AURA-NOTES Frontend Layer:**
- Purpose: Staff-facing explorer, auth, admin dashboard, and KG processing UI.
- Location: `AURA-NOTES-MANAGER/frontend/src/`
- Contains: App routes in `AURA-NOTES-MANAGER/frontend/src/App.tsx`, page-level orchestration in `AURA-NOTES-MANAGER/frontend/src/pages/ExplorerPage.tsx`, explorer UI under `AURA-NOTES-MANAGER/frontend/src/components/explorer/`, KG feature hooks/components in `AURA-NOTES-MANAGER/frontend/src/features/kg/`, API wrappers in `AURA-NOTES-MANAGER/frontend/src/api/`.
- Depends on: `AURA-NOTES-MANAGER/api/main.py` endpoints, Firebase auth client code, TanStack Query, Zustand.
- Used by: Vite entry point `AURA-NOTES-MANAGER/frontend/src/main.tsx` and E2E specs in `AURA-NOTES-MANAGER/e2e/tests/*.spec.ts`.

**AURA-NOTES API Layer:**
- Purpose: Serve hierarchy CRUD, explorer tree APIs, module publishing APIs, AI-note pipeline endpoints, and newer summary/trend/schema endpoints.
- Location: `AURA-NOTES-MANAGER/api/`
- Contains: Bootstrap in `AURA-NOTES-MANAGER/api/main.py`, explorer tree adapter in `AURA-NOTES-MANAGER/api/explorer.py`, hierarchy read helpers in `AURA-NOTES-MANAGER/api/hierarchy.py`, module API package in `AURA-NOTES-MANAGER/api/modules/`, specialized routers in `AURA-NOTES-MANAGER/api/routers/*.py`.
- Depends on: Firestore config in `AURA-NOTES-MANAGER/api/config.py`, services in `AURA-NOTES-MANAGER/services/`, Neo4j helpers like `AURA-NOTES-MANAGER/api/neo4j_config.py`.
- Used by: `AURA-NOTES-MANAGER/frontend/src/api/*.ts` and student-side consumers proxied through published data.

**AURA-NOTES Service Layer:**
- Purpose: Hold reusable AI, parsing, and enrichment logic away from FastAPI route files.
- Location: `AURA-NOTES-MANAGER/services/`
- Contains: Summaries in `AURA-NOTES-MANAGER/services/summary_service.py`, STT in `AURA-NOTES-MANAGER/services/stt.py`, embeddings/entity extraction in `AURA-NOTES-MANAGER/services/embeddings.py` and `AURA-NOTES-MANAGER/services/llm_entity_extractor.py`, multimodal processors in `AURA-NOTES-MANAGER/services/multimodal/`.
- Depends on: Vertex AI, Deepgram, document parsers, Neo4j/Firestore access through API modules.
- Used by: `AURA-NOTES-MANAGER/api/audio_processing.py`, `AURA-NOTES-MANAGER/api/kg_processor.py`, and `AURA-NOTES-MANAGER/api/routers/*.py`.

## Data Flow

**AURA-CHAT Query Flow:**

1. `AURA-CHAT/client/src/features/chat/ChatPage.tsx` gathers session context, model settings, and streaming callbacks via hooks from `AURA-CHAT/client/src/features/study-sessions/hooks/useStudySession.ts`.
2. `AURA-CHAT/client/src/lib/api.ts` calls `AURA-CHAT/backend/routers/sessions.py` or `AURA-CHAT/server/routers/chat.py`, with auth and department headers populated from `AURA-CHAT/client/src/stores/useAuthStore.ts`.
3. `AURA-CHAT/server/main.py` resolves shared singletons from `AURA-CHAT/server/dependencies.py` and dispatches to `AURA-CHAT/backend/rag_engine.py`, `AURA-CHAT/backend/session_manager.py`, and `AURA-CHAT/backend/semantic_router.py`.
4. `AURA-CHAT/backend/rag_engine.py` retrieves graph/vector context through `AURA-CHAT/backend/graph_manager.py`, consults history from `AURA-CHAT/backend/chat_manager.py`, and streams or returns responses.
5. `AURA-CHAT/backend/routers/sessions.py` persists `StudySession` and `Message` nodes through `AURA-CHAT/backend/session_manager.py`, then the frontend rehydrates from React Query caches.

**AURA-CHAT Document Processing Flow:**

1. `AURA-CHAT/client/src/features/documents/DocumentsPage.tsx` uploads files through `AURA-CHAT/client/src/lib/api.ts`.
2. `AURA-CHAT/server/routers/documents.py` saves uploads into `AURA-CHAT/data/` and enqueues background jobs using the ARQ pool from `AURA-CHAT/server/dependencies.py`.
3. `AURA-CHAT/backend/tasks/worker.py` boots separate Redis and Neo4j worker resources.
4. `AURA-CHAT/backend/tasks/document_tasks.py` and `AURA-CHAT/backend/document_processor.py` extract text, chunk content, embed, and index the results through `AURA-CHAT/backend/graph_manager.py`.
5. `AURA-CHAT/server/routers/jobs.py` and `AURA-CHAT/server/routers/websocket.py` expose progress back to the client.

**AURA-NOTES Explorer and KG Flow:**

1. `AURA-NOTES-MANAGER/frontend/src/pages/ExplorerPage.tsx` fetches the tree with `AURA-NOTES-MANAGER/frontend/src/api/explorerApi.ts` and stores UI-only state in `AURA-NOTES-MANAGER/frontend/src/stores/useExplorerStore.ts`.
2. `AURA-NOTES-MANAGER/api/explorer.py` assembles Firestore nested collections into `ExplorerNode` trees; `AURA-NOTES-MANAGER/api/hierarchy_crud.py` mutates hierarchy entities.
3. `AURA-NOTES-MANAGER/frontend/src/features/kg/hooks/useKGProcessing.ts` starts processing batches and polls queue state.
4. `AURA-NOTES-MANAGER/api/kg_processor.py` orchestrates parsing, entity extraction, chunking, embeddings, and Neo4j writes using helpers from `AURA-NOTES-MANAGER/services/`.
5. Published module metadata from `AURA-NOTES-MANAGER/api/modules/router.py` becomes available to student flows consumed in `AURA-CHAT/backend/routers/student_modules.py`.

**AURA-NOTES Audio-to-Notes Flow:**

1. `AURA-NOTES-MANAGER/frontend/src/components/explorer/UploadDialog.tsx` submits audio or document files.
2. `AURA-NOTES-MANAGER/api/audio_processing.py` validates file size and starts a background pipeline tracked in its in-memory job store.
3. Service steps run through `AURA-NOTES-MANAGER/services/stt.py`, `AURA-NOTES-MANAGER/services/coc.py`, `AURA-NOTES-MANAGER/services/summarizer.py`, and `AURA-NOTES-MANAGER/services/pdf_generator.py`.
4. Generated PDFs are stored under `AURA-NOTES-MANAGER/pdfs/` and exposed through `/api/pdfs/*` in `AURA-NOTES-MANAGER/api/main.py`.
5. Created note records are attached back into the Firestore hierarchy for explorer rendering.

**State Management:**
- `AURA-CHAT/client/src/App.tsx` and `AURA-NOTES-MANAGER/frontend/src/main.tsx` use TanStack Query for server state and caching.
- `AURA-CHAT/client/src/stores/useAuthStore.ts` keeps auth identity and department context; `AURA-NOTES-MANAGER/frontend/src/stores/useExplorerStore.ts` keeps explorer UI state, selection, and dialogs.
- Server-side long-lived state lives in singleton dependencies in `AURA-CHAT/server/dependencies.py` and app state in `AURA-CHAT/server/main.py`.

## Key Abstractions

**GraphManager:**
- Purpose: Single Neo4j access abstraction for search, schema setup, and graph persistence.
- Examples: `AURA-CHAT/backend/graph_manager.py`, `AURA-NOTES-MANAGER/api/graph_manager.py`, `AURA-NOTES-MANAGER/api/neo4j_config.py`
- Pattern: Infrastructure gateway with async query helpers and index/constraint ownership.

**RAGEngine:**
- Purpose: Central query orchestration for retrieval, prompt assembly, model selection, and response streaming.
- Examples: `AURA-CHAT/backend/rag_engine.py`, `AURA-CHAT/server/routers/chat.py`, `AURA-CHAT/backend/routers/sessions.py`
- Pattern: Domain service called by thin HTTP routers.

**HierarchyService / Explorer Tree:**
- Purpose: Translate Firestore hierarchy data into navigation-friendly APIs.
- Examples: `AURA-CHAT/backend/services/hierarchy.py`, `AURA-NOTES-MANAGER/api/hierarchy.py`, `AURA-NOTES-MANAGER/api/explorer.py`
- Pattern: Read-service layer over nested Firestore collections with pagination or tree shaping.

**Module Publishing Boundary:**
- Purpose: Separate staff-owned module lifecycle from student consumption.
- Examples: `AURA-NOTES-MANAGER/api/modules/router.py`, `AURA-NOTES-MANAGER/api/modules/service.py`, `AURA-NOTES-MANAGER/api/modules/publishing.py`
- Pattern: Versioned feature package with router/service/publishing split.

**Session-Oriented Chat Context:**
- Purpose: Make chat persistence explicit through `StudySession` and `Message` nodes rather than transient browser state.
- Examples: `AURA-CHAT/backend/session_manager.py`, `AURA-CHAT/backend/routers/sessions.py`, `AURA-CHAT/client/src/features/study-sessions/hooks/useStudySession.ts`
- Pattern: Domain model with backend persistence plus React Query hooks.

## Entry Points

**AURA-CHAT Frontend:**
- Location: `AURA-CHAT/client/src/main.tsx`
- Triggers: Vite browser boot.
- Responsibilities: Mount React app, import global styles, hand off to `AURA-CHAT/client/src/App.tsx`.

**AURA-CHAT API Server:**
- Location: `AURA-CHAT/server/main.py`
- Triggers: `uvicorn server.main:app` or direct Python execution.
- Responsibilities: Startup/shutdown lifecycle, Firestore + Neo4j service init, middleware, router registration for both `server/routers/` and `backend/routers/`.

**AURA-CHAT Background Worker:**
- Location: `AURA-CHAT/backend/tasks/worker.py`
- Triggers: ARQ worker process.
- Responsibilities: Separate async job runtime for document, audio, and embedding tasks.

**AURA-NOTES Frontend:**
- Location: `AURA-NOTES-MANAGER/frontend/src/main.tsx`
- Triggers: Vite browser boot.
- Responsibilities: Create QueryClient, mount `AURA-NOTES-MANAGER/frontend/src/App.tsx`, load explorer styles.

**AURA-NOTES API Server:**
- Location: `AURA-NOTES-MANAGER/api/main.py`
- Triggers: `uvicorn main:app --port 8001` or direct Python execution.
- Responsibilities: Load env, mount legacy and versioned routers, configure CORS/rate limiting, serve PDFs, expose health/readiness endpoints.

## Error Handling

**Strategy:** HTTP layers catch domain exceptions, translate them to `HTTPException` or structured JSON, and rely on centralized logging plus degraded startup where possible.

**Patterns:**
- `AURA-CHAT/server/main.py` installs a global exception handler and keeps Firestore-dependent routes in degraded mode when initialization fails.
- `AURA-CHAT/server/dependencies.py` and `AURA-CHAT/backend/session_manager.py` log failures close to infrastructure boundaries and return safe fallbacks where the UI can recover.
- `AURA-NOTES-MANAGER/api/main.py` wraps rate limiting, CORS, and security headers at the app boundary, while route files such as `AURA-NOTES-MANAGER/api/audio_processing.py` degrade gracefully when optional AI dependencies are missing.

## Cross-Cutting Concerns

**Logging:** Structured logger helpers are centralized in `AURA-CHAT/backend/utils/logging_config.py` and `AURA-NOTES-MANAGER/api/logging_config.py`/module-level loggers.
**Validation:** Request validation is handled by Pydantic models in `AURA-CHAT/server/schemas/*.py`, `AURA-CHAT/backend/routers/sessions.py`, `AURA-NOTES-MANAGER/api/modules/models.py`, and route-local models in `AURA-NOTES-MANAGER/api/explorer.py` and `AURA-NOTES-MANAGER/api/audio_processing.py`.
**Authentication:** Frontends initialize Firebase auth in `AURA-CHAT/client/src/stores/useAuthStore.ts` and `AURA-NOTES-MANAGER/frontend/src/stores/useAuthStore.ts`; backend enforcement lives in `AURA-CHAT/server/auth/` and notes auth sync routes such as `AURA-NOTES-MANAGER/api/auth_sync.py`.

---

*Architecture analysis: 2026-03-10*
