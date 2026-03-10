# Technology Stack

**Analysis Date:** 2026-03-10

## Languages

**Primary:**
- Python 3.10+ - Backend APIs, async workers, graph processing, and AI services in `AURA-CHAT/server/main.py`, `AURA-CHAT/backend/utils/config.py`, `AURA-NOTES-MANAGER/api/main.py`, `AURA-NOTES-MANAGER/services/stt.py`
- TypeScript 5.9 / 5.6 - Frontend applications and E2E tooling in `AURA-CHAT/client/package.json`, `AURA-CHAT/client/vite.config.ts`, `AURA-NOTES-MANAGER/frontend/package.json`, `AURA-NOTES-MANAGER/frontend/vite.config.ts`

**Secondary:**
- JavaScript/JSON/YAML - Tooling and CI configuration in `AURA-CHAT/client/eslint.config.js`, `AURA-NOTES-MANAGER/frontend/eslint.config.js`, `.github/workflows/ci.yml`, `.github/workflows/e2e-tests.yml`, `AURA-NOTES-MANAGER/firebase.json`

## Runtime

**Environment:**
- Python 3.10 in CI and container builds in `.github/workflows/ci.yml`, `.github/workflows/e2e-tests.yml`, `AURA-CHAT/Dockerfile`, `AURA-NOTES-MANAGER/api/Dockerfile`
- Node.js 20 in CI and frontend containers in `.github/workflows/ci.yml`, `.github/workflows/e2e-tests.yml`, `AURA-CHAT/client/Dockerfile`, `AURA-NOTES-MANAGER/frontend/Dockerfile`

**Package Manager:**
- npm with lockfiles present in `package-lock.json`, `AURA-CHAT/client/package-lock.json`, `AURA-NOTES-MANAGER/frontend/package-lock.json`, `AURA-NOTES-MANAGER/package-lock.json`, `AURA-NOTES-MANAGER/e2e/package-lock.json`
- pip with requirements files in `requirements.txt`, `AURA-CHAT/requirements.txt`, `AURA-NOTES-MANAGER/requirements.txt`
- Lockfile: present for Node, missing for Python dependency pinning beyond requirements files

## Frameworks

**Core:**
- React 19.2.0 + Vite 7.2.4 - Student-facing SPA in `AURA-CHAT/client/package.json`, bootstrapped by `AURA-CHAT/client/vite.config.ts`
- React 18.3.1 + Vite 6.0.5 - Staff-facing SPA in `AURA-NOTES-MANAGER/frontend/package.json`, bootstrapped by `AURA-NOTES-MANAGER/frontend/vite.config.ts`
- FastAPI 0.109+ / 0.115.0 - HTTP API layers in `AURA-CHAT/requirements.txt`, `AURA-CHAT/server/main.py`, `AURA-NOTES-MANAGER/requirements.txt`, `AURA-NOTES-MANAGER/api/main.py`

**Testing:**
- Vitest 3.2.4 - Frontend unit tests in `AURA-CHAT/client/package.json`, `AURA-NOTES-MANAGER/frontend/package.json`
- Playwright 1.49-1.50 - Browser E2E suites in `AURA-CHAT/client/playwright.config.ts`, `AURA-NOTES-MANAGER/frontend/playwright.config.ts`, `AURA-NOTES-MANAGER/e2e/playwright.config.ts`
- Pytest + pytest-cov + pytest-asyncio - Python tests in `AURA-CHAT/pyproject.toml`, `AURA-CHAT/requirements.txt`, `AURA-NOTES-MANAGER/requirements.txt`
- Jest + Firebase Rules Unit Testing - Firestore rules tests in `AURA-NOTES-MANAGER/frontend/package.json`, `AURA-NOTES-MANAGER/firebase.json`

**Build/Dev:**
- Tailwind CSS 4 + `@tailwindcss/vite` - Styling pipeline in `AURA-CHAT/client/package.json`, `AURA-CHAT/client/vite.config.ts`
- ESLint flat config - TypeScript linting in `AURA-CHAT/client/eslint.config.js`, `AURA-NOTES-MANAGER/frontend/eslint.config.js`
- Uvicorn - FastAPI app server in `AURA-CHAT/Dockerfile`, `AURA-NOTES-MANAGER/api/Dockerfile`
- Docker - Container build targets in `AURA-CHAT/Dockerfile`, `AURA-CHAT/client/Dockerfile`, `AURA-NOTES-MANAGER/api/Dockerfile`, `AURA-NOTES-MANAGER/frontend/Dockerfile`

## Key Dependencies

**Critical:**
- `neo4j` - Graph database driver powering RAG graph access and KG storage in `AURA-CHAT/backend/graph_manager.py`, `AURA-NOTES-MANAGER/api/neo4j_config.py`
- `google-cloud-aiplatform` / `vertexai` / `google-genai` / `google-generativeai` - Gemini and Vertex AI access in `AURA-CHAT/requirements.txt`, `AURA-CHAT/backend/utils/vertex_ai_client.py`, `AURA-NOTES-MANAGER/requirements.txt`, `AURA-NOTES-MANAGER/services/vertex_ai_client.py`, `AURA-NOTES-MANAGER/services/genai_client.py`
- `firebase-admin` + `firebase` - Shared auth and Firestore access across backends and frontends in `AURA-CHAT/server/auth/firebase_auth.py`, `AURA-CHAT/server/auth/firestore_client.py`, `AURA-CHAT/client/src/lib/firebase.ts`, `AURA-NOTES-MANAGER/api/config.py`, `AURA-NOTES-MANAGER/frontend/src/api/firebaseClient.ts`
- `@tanstack/react-query` + `zustand` - Frontend data fetching and local state in `AURA-CHAT/client/package.json`, `AURA-NOTES-MANAGER/frontend/package.json`

**Infrastructure:**
- `redis` - Cache/pubsub and queue backing store in `AURA-CHAT/backend/tasks/worker.py`, `AURA-CHAT/server/routers/websocket.py`, `AURA-NOTES-MANAGER/api/config.py`, `AURA-NOTES-MANAGER/api/main.py`
- `arq` - Async worker queue for AURA-CHAT background jobs in `AURA-CHAT/requirements.txt`, `AURA-CHAT/backend/tasks/worker.py`, `AURA-CHAT/server/dependencies.py`
- `celery` - Async worker queue for AURA-NOTES document processing in `AURA-NOTES-MANAGER/requirements.txt`, `AURA-NOTES-MANAGER/api/tasks/document_processing_tasks.py`
- `deepgram-sdk` - Speech-to-text for notes pipeline in `AURA-NOTES-MANAGER/requirements.txt`, `AURA-NOTES-MANAGER/services/stt.py`
- `axios` / native `fetch` - Frontend HTTP clients in `AURA-CHAT/client/src/lib/api.ts`, `AURA-NOTES-MANAGER/frontend/src/api/client.ts`
- `reagraph` - 3D graph visualization in `AURA-CHAT/client/package.json`
- `PyMuPDF`, `pypdf`, `pdfplumber`, `python-docx`, `fpdf2` - Document and PDF processing in `AURA-CHAT/requirements.txt`, `AURA-NOTES-MANAGER/requirements.txt`, `AURA-NOTES-MANAGER/api/audio_processing.py`

## Configuration

**Environment:**
- Backend settings come from environment variables loaded in `AURA-CHAT/backend/utils/config.py`, `AURA-CHAT/server/config.py`, `AURA-NOTES-MANAGER/api/config.py`, `AURA-NOTES-MANAGER/api/main.py`
- Frontend runtime config uses Vite env vars in `AURA-CHAT/client/src/lib/api.ts`, `AURA-CHAT/client/src/lib/firebase.ts`, `AURA-NOTES-MANAGER/frontend/src/api/firebaseClient.ts`, `AURA-NOTES-MANAGER/frontend/src/api/client.ts`
- Firebase emulator/rules config is defined in `AURA-NOTES-MANAGER/firebase.json`
- `.env` files are present at repo root, `AURA-CHAT/.env`, `AURA-NOTES-MANAGER/.env`, and frontend subprojects; treat them as secret-bearing environment configuration files

**Build:**
- TypeScript and Vite config live in `AURA-CHAT/client/tsconfig.app.json`, `AURA-CHAT/client/tsconfig.json`, `AURA-CHAT/client/vite.config.ts`, `AURA-NOTES-MANAGER/frontend/tsconfig.app.json`, `AURA-NOTES-MANAGER/frontend/tsconfig.json`, `AURA-NOTES-MANAGER/frontend/vite.config.ts`
- CI/CD and quality gates are defined in `.github/workflows/ci.yml` and `.github/workflows/e2e-tests.yml`
- Pytest and coverage config for AURA-CHAT live in `AURA-CHAT/pyproject.toml`

## Platform Requirements

**Development:**
- Node.js 20 and npm for the React/Vite apps in `.github/workflows/ci.yml`, `AURA-CHAT/client/Dockerfile`, `AURA-NOTES-MANAGER/frontend/Dockerfile`
- Python 3.10+ with root virtualenv for backend work in `AURA-CHAT/pyproject.toml`, `.github/workflows/ci.yml`, `AURA-NOTES-MANAGER/requirements.txt`
- Local Neo4j, Redis, Firebase credentials, and Google Cloud credentials are required by `AURA-CHAT/backend/utils/config.py`, `AURA-CHAT/server/auth/firebase_auth.py`, `AURA-NOTES-MANAGER/api/config.py`, `AURA-NOTES-MANAGER/api/neo4j_config.py`

**Production:**
- Containerized deployment targets are the current production shape, with API and frontend images defined in `AURA-CHAT/Dockerfile`, `AURA-CHAT/client/Dockerfile`, `AURA-NOTES-MANAGER/api/Dockerfile`, `AURA-NOTES-MANAGER/frontend/Dockerfile`
- GitHub Actions drives test, security scan, and image build automation in `.github/workflows/ci.yml` and `.github/workflows/e2e-tests.yml`

---

*Stack analysis: 2026-03-10*
