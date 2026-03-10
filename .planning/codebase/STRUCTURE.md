# Codebase Structure

**Analysis Date:** 2026-03-10

## Directory Layout

```text
AURA-PROJ/
├── .planning/                       # Planning state, milestones, and generated codebase docs
├── AURA-CHAT/                       # Student-facing chat application
│   ├── client/                      # React + Vite frontend
│   ├── server/                      # FastAPI app, auth, schemas, HTTP routers
│   ├── backend/                     # RAG, graph, session, and async task logic
│   ├── tests/                       # Pytest suites grouped by level
│   ├── data/                        # Uploaded/processed document assets
│   └── scripts/                     # Maintenance and support scripts
├── AURA-NOTES-MANAGER/              # Staff explorer and publishing application
│   ├── frontend/                    # React + Vite frontend
│   ├── api/                         # FastAPI routes, Firestore/Neo4j access, feature packages
│   ├── services/                    # Reusable AI, parsing, and enrichment services
│   ├── e2e/                         # Playwright suite and reports
│   ├── pdfs/                        # Generated and uploaded note PDFs
│   └── tools/                       # Utility scripts and one-off helpers
├── shared/                          # Cross-application runtime packages
│   └── model_router/                # Shared model router package (contracts, config, providers, tests)
├── conductor/                       # Cross-project reference docs
├── .github/workflows/               # CI definitions
├── package.json                     # Workspace-level Node tooling
└── requirements.txt                 # Workspace-level Python tooling
```

## Directory Purposes

**`.planning/`:**
- Purpose: Hold planning artifacts and generated mapper output.
- Contains: `D:\Peter\AURA Twin Proj\AURA-PROJ\.planning\STATE.md`, `D:\Peter\AURA Twin Proj\AURA-PROJ\.planning\PROJECT.md`, milestone folders, and `D:\Peter\AURA Twin Proj\AURA-PROJ\.planning\codebase\`.
- Key files: `D:\Peter\AURA Twin Proj\AURA-PROJ\.planning\STATE.md`, `D:\Peter\AURA Twin Proj\AURA-PROJ\.planning\BRIEF.md`.

**`AURA-CHAT/client/`:**
- Purpose: Student UI application.
- Contains: Route shell, feature pages, hooks, shared components, auth store, E2E tests in sibling `AURA-CHAT/client/e2e/`.
- Key files: `AURA-CHAT/client/src/main.tsx`, `AURA-CHAT/client/src/App.tsx`, `AURA-CHAT/client/src/lib/api.ts`, `AURA-CHAT/client/src/features/chat/ChatPage.tsx`.

**`AURA-CHAT/server/`:**
- Purpose: FastAPI entry point and transport-layer concerns.
- Contains: `main.py`, dependency providers, auth package, security middleware, routers, schemas.
- Key files: `AURA-CHAT/server/main.py`, `AURA-CHAT/server/dependencies.py`, `AURA-CHAT/server/routers/chat.py`, `AURA-CHAT/server/routers/documents.py`.

**`AURA-CHAT/backend/`:**
- Purpose: Domain and infrastructure code for graph/RAG/session behavior.
- Contains: Core services, task worker code, backend-specific routers, utils.
- Key files: `AURA-CHAT/backend/rag_engine.py`, `AURA-CHAT/backend/graph_manager.py`, `AURA-CHAT/backend/session_manager.py`, `AURA-CHAT/backend/tasks/worker.py`.

**`AURA-CHAT/tests/`:**
- Purpose: Python verification across unit, integration, performance, load, and security layers.
- Contains: `unit/`, `integration/`, `performance/`, `load/`, `security/`.
- Key files: `AURA-CHAT/tests/unit/test_session_crud.py`, `AURA-CHAT/tests/integration/test_session_manager_integration.py`, `AURA-CHAT/tests/load/locustfile.py`.

**`AURA-NOTES-MANAGER/frontend/`:**
- Purpose: Staff explorer/admin frontend.
- Contains: Pages, explorer components, KG feature module, API wrappers, stores, tests.
- Key files: `AURA-NOTES-MANAGER/frontend/src/main.tsx`, `AURA-NOTES-MANAGER/frontend/src/App.tsx`, `AURA-NOTES-MANAGER/frontend/src/pages/ExplorerPage.tsx`, `AURA-NOTES-MANAGER/frontend/src/api/explorerApi.ts`.

**`AURA-NOTES-MANAGER/api/`:**
- Purpose: Backend endpoints plus Firestore/Neo4j-facing data logic.
- Contains: Legacy top-level route files, newer packages under `modules/` and `routers/`, migrations, tests.
- Key files: `AURA-NOTES-MANAGER/api/main.py`, `AURA-NOTES-MANAGER/api/explorer.py`, `AURA-NOTES-MANAGER/api/hierarchy_crud.py`, `AURA-NOTES-MANAGER/api/modules/router.py`.

**`AURA-NOTES-MANAGER/services/`:**
- Purpose: Shared AI and document-processing implementations.
- Contains: STT, summarization, embeddings, entity extraction, multimodal processors, document parsers.
- Key files: `AURA-NOTES-MANAGER/services/stt.py`, `AURA-NOTES-MANAGER/services/summary_service.py`, `AURA-NOTES-MANAGER/services/multimodal/processor.py`.

**`AURA-NOTES-MANAGER/e2e/`:**
- Purpose: Playwright test project and generated reports.
- Contains: `tests/`, `playwright.config.ts`, `playwright-report/`, `test-results/`.
- Key files: `AURA-NOTES-MANAGER/e2e/tests/explorer.spec.ts`, `AURA-NOTES-MANAGER/e2e/tests/audio.spec.ts`.

**`shared/`:**
- Purpose: Host installable cross-application Python packages shared by both AURA apps.
- Contains: `shared/model_router/` with `src/model_router/`, `tests/`, and package metadata in `pyproject.toml`.
- Key files: `shared/model_router/pyproject.toml`, `shared/model_router/src/model_router/__init__.py`, `shared/model_router/src/model_router/providers/base.py`.

## Key File Locations

**Entry Points:**
- `AURA-CHAT/client/src/main.tsx`: Boots the student React app.
- `AURA-CHAT/server/main.py`: Boots the student FastAPI API and mounts all routers.
- `AURA-CHAT/backend/tasks/worker.py`: Boots the ARQ worker for background jobs.
- `AURA-NOTES-MANAGER/frontend/src/main.tsx`: Boots the staff React app.
- `AURA-NOTES-MANAGER/api/main.py`: Boots the staff FastAPI API.

**Configuration:**
- `package.json`: Workspace-level Node dependencies and helper scripts.
- `requirements.txt`: Workspace-level Python dependencies.
- `shared/model_router/pyproject.toml`: Shared Python package metadata and editable-install entry point.
- `AURA-CHAT/pyproject.toml`: Chat-specific Python tooling/config.
- `AURA-NOTES-MANAGER/package.json`: Notes Manager frontend/E2E commands.
- `AURA-NOTES-MANAGER/firebase.json`: Firebase emulator/hosting configuration.

**Core Logic:**
- `AURA-CHAT/backend/rag_engine.py`: Retrieval and response orchestration.
- `AURA-CHAT/backend/graph_manager.py`: Neo4j graph gateway.
- `AURA-CHAT/backend/session_manager.py`: Study session persistence and cache integration.
- `AURA-NOTES-MANAGER/api/kg_processor.py`: Document-to-KG conversion pipeline.
- `AURA-NOTES-MANAGER/api/modules/service.py`: Module lifecycle business rules.
- `AURA-NOTES-MANAGER/services/summary_service.py`: Summary synthesis service.

**Testing:**
- `AURA-CHAT/tests/`: Pytest suites for chat/backend/server behavior.
- `AURA-CHAT/client/e2e/`: Student Playwright specs.
- `AURA-NOTES-MANAGER/frontend/src/**/*.test.tsx`: Staff UI unit/integration tests.
- `AURA-NOTES-MANAGER/api/tests/`: Backend tests such as `AURA-NOTES-MANAGER/api/tests/test_rbac.py`.
- `AURA-NOTES-MANAGER/e2e/tests/`: Staff Playwright specs.

## Naming Conventions

**Files:**
- React pages use `*Page.tsx`: `AURA-CHAT/client/src/features/graph/GraphPage.tsx`, `AURA-NOTES-MANAGER/frontend/src/pages/ExplorerPage.tsx`.
- React hooks use `use*.ts` or `use*.tsx`: `AURA-CHAT/client/src/features/chat/hooks/useChat.ts`, `AURA-NOTES-MANAGER/frontend/src/features/kg/hooks/useKGProcessing.ts`.
- FastAPI router modules are singular concern files: `AURA-CHAT/server/routers/chat.py`, `AURA-NOTES-MANAGER/api/explorer.py`, `AURA-NOTES-MANAGER/api/modules/router.py`.
- Domain/service Python files are noun-based: `AURA-CHAT/backend/rag_engine.py`, `AURA-NOTES-MANAGER/services/entity_deduplicator.py`.

**Directories:**
- Frontend features live in `src/features/<feature-name>/`: `AURA-CHAT/client/src/features/study-sessions/`, `AURA-NOTES-MANAGER/frontend/src/features/kg/`.
- Shared UI is grouped by concern: `AURA-CHAT/client/src/components/ui/`, `AURA-NOTES-MANAGER/frontend/src/components/explorer/`, `AURA-NOTES-MANAGER/frontend/src/components/layout/`.
- Python backend subdomains split by responsibility: `AURA-CHAT/server/routers/`, `AURA-CHAT/backend/tasks/`, `AURA-NOTES-MANAGER/api/modules/`, `AURA-NOTES-MANAGER/services/multimodal/`.

## Where to Add New Code

**New student-facing feature in AURA-CHAT:**
- Primary code: `AURA-CHAT/client/src/features/<feature-name>/`
- Route wiring: `AURA-CHAT/client/src/App.tsx`
- Shared UI pieces: `AURA-CHAT/client/src/components/` or `AURA-CHAT/client/src/components/ui/`
- Tests: co-locate as `AURA-CHAT/client/src/features/<feature-name>/**/*.test.tsx`; add end-to-end coverage in `AURA-CHAT/client/e2e/` when the feature spans routes.

**New AURA-CHAT API endpoint:**
- HTTP contract and request validation: `AURA-CHAT/server/routers/<concern>.py` and `AURA-CHAT/server/schemas/<concern>.py`
- Business logic: `AURA-CHAT/backend/` service or utility module
- Dependency wiring: `AURA-CHAT/server/dependencies.py` only when a reusable singleton/provider is needed
- Tests: `AURA-CHAT/tests/api/` or `AURA-CHAT/tests/integration/` depending whether the feature crosses infrastructure.

**New AURA-CHAT background job:**
- Job implementation: `AURA-CHAT/backend/tasks/<job_name>.py`
- Worker registration: `AURA-CHAT/backend/tasks/worker.py`
- Job progress/reporting: `AURA-CHAT/backend/tasks/progress.py` and `AURA-CHAT/server/routers/jobs.py` if the UI needs visibility.

**New staff-facing explorer behavior in AURA-NOTES-MANAGER:**
- Page orchestration: `AURA-NOTES-MANAGER/frontend/src/pages/ExplorerPage.tsx`
- Reusable explorer widgets: `AURA-NOTES-MANAGER/frontend/src/components/explorer/`
- UI-only state: `AURA-NOTES-MANAGER/frontend/src/stores/useExplorerStore.ts`
- Server calls: `AURA-NOTES-MANAGER/frontend/src/api/explorerApi.ts`
- Backend counterpart: extend `AURA-NOTES-MANAGER/api/explorer.py` or `AURA-NOTES-MANAGER/api/hierarchy_crud.py` based on read vs write behavior.

**New staff backend feature in AURA-NOTES-MANAGER:**
- Prefer feature packages for newer versioned work: `AURA-NOTES-MANAGER/api/modules/` or `AURA-NOTES-MANAGER/api/routers/`
- Extend top-level route files only when the concern already lives there, such as `AURA-NOTES-MANAGER/api/audio_processing.py` or `AURA-NOTES-MANAGER/api/explorer.py`
- Put reusable logic in `AURA-NOTES-MANAGER/services/` instead of expanding route files with AI/process code.

**Utilities:**
- Shared frontend helpers: `AURA-CHAT/client/src/lib/` or `AURA-NOTES-MANAGER/frontend/src/lib/`
- Shared Python helpers inside app boundaries: `AURA-CHAT/backend/utils/` or `AURA-NOTES-MANAGER/services/`
- Cross-app Python runtime packages: `shared/<package>/src/<package>/` with tests in the package-local `shared/<package>/tests/` folder
- Cross-workspace documentation or planning helpers: `.planning/` or `conductor/`, not inside app runtime directories.

## Special Directories

**`.planning/codebase/`:**
- Purpose: Generated architecture/reference docs consumed by other GSD commands.
- Generated: Yes
- Committed: Yes

**`AURA-CHAT/tests/`:**
- Purpose: Primary backend/server verification for AURA-CHAT.
- Generated: No
- Committed: Yes

**`AURA-NOTES-MANAGER/e2e/playwright-report/`:**
- Purpose: Generated Playwright HTML reports.
- Generated: Yes
- Committed: Yes

**`AURA-NOTES-MANAGER/pdfs/`:**
- Purpose: Runtime storage for generated/uploaded note PDFs served by `AURA-NOTES-MANAGER/api/main.py`.
- Generated: Yes
- Committed: Yes

**`AURA-CHAT/data/`:**
- Purpose: Chat-side uploaded document storage and processing inputs.
- Generated: Yes
- Committed: Mixed; treat contents as runtime artifacts unless a file is already intentionally tracked.

---

*Structure analysis: 2026-03-10*
