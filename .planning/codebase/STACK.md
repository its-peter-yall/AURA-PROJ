# Technology Stack

**Analysis Date:** 2026-02-20

## Languages

**Primary:**
- **TypeScript** 5.9.3 - Frontend (React components, hooks, utilities)
- **Python** 3.9+ - Backend (FastAPI server, RAG engine, entity extraction, graph operations)

**Secondary:**
- **JavaScript** - Build configuration and tooling
- **Markdown** - Documentation and schemas

## Runtime

**Environment:**
- **Node.js** - Runtime for React frontend (Vite dev server and build)
- **Python 3.9+** - Runtime for FastAPI backend and processing

**Package Manager:**
- **npm** 9.x+ - Frontend dependencies and scripts
  - Lockfile: `client/package-lock.json` (present)
- **pip** - Python dependencies managed via `pyproject.toml` and `requirements.txt`
  - Virtual environment: Root venv (`../.venv` or `../../.venv` - always use root)

## Frameworks

**Core Frontend:**
- **React** 19.2.0 - UI framework with hooks and functional components
- **React Router** 7.11.0 - Client-side routing and navigation
- **Vite** 7.2.4 - Build tool and dev server (port 5173)

**Core Backend:**
- **FastAPI** 0.109.0+ - ASGI web framework for REST API (port 8000)
- **Uvicorn** 0.27.0+ - ASGI application server with async support

**State Management & HTTP:**
- **TanStack Query (React Query)** 5.90.15 - Server state caching with 5min staleTime
- **Axios** 1.13.2 - HTTP client with interceptors and 5min timeout for document processing

**Graph Visualization:**
- **Reagraph** 4.30.7 - WebGL 3D graph visualization (7 node types: Document, Chunk, Concept, Topic, Finding, Methodology, Other)

**Testing:**
- **Vitest** 3.2.4 - Unit test framework with watch mode and coverage (V8 provider)
- **Playwright** 1.49.0 - E2E testing with parallel execution, multi-browser support (Chromium, Firefox, WebKit, iOS, Android)
- **pytest** 7.0.0+ - Python unit testing framework with coverage reporting
- **pytest-asyncio** 0.21.0+ - Async test support for FastAPI endpoints

**Build & Dev:**
- **TypeScript** 5.9.3 - Type checking with strict mode
- **Tailwind CSS** 4.1.18 - Utility-first CSS with custom "Cyber Yellow" theme
- **@tailwindcss/vite** 4.1.18 - Vite integration for Tailwind
- **ESLint** 9.39.1 - Linting with flat config for React hooks and TypeScript
- **typescript-eslint** 8.46.4 - ESLint TypeScript support

**Testing Libraries:**
- **@testing-library/react** 16.3.1 - React component testing utilities
- **@testing-library/user-event** 14.6.1 - User interaction simulation
- **@testing-library/jest-dom** 6.9.1 - DOM matchers for assertions
- **MSW** 2.12.7 - Mock Service Worker for API mocking in tests
- **jsdom** 27.0.1 - DOM implementation for test environment

**Content & UI:**
- **react-markdown** 10.1.0 - Markdown rendering in chat messages
- **remark-gfm** 4.0.1 - GitHub Flavored Markdown support
- **rehype-sanitize** 6.0.0 - XSS protection for rendered content
- **rehype-raw** 7.0.0 - Raw HTML rendering support
- **lucide-react** 0.562.0 - Icons library
- **clsx** 2.1.1 - Utility for conditional class names
- **tailwind-merge** 3.4.0 - Smart Tailwind class merging

**Python Backend Libraries:**

Data & Graph:
- **neo4j** 5.13.0+ - Python driver for Neo4j graph database connections and queries

Google Cloud & AI:
- **google-cloud-aiplatform** 1.51.0+ - Google Vertex AI official SDK (embeddings via REST API)
- **vertexai** 1.0.0+ - Vertex AI Generative Models SDK (Gemini chat with thinking mode support)
- **google-genai** 1.60.0+ - Google Generative AI SDK (Gemini Chat API with dual-SDK approach for thinking mode)

Document Processing:
- **pypdf** 4.0.0+ - PDF reading and extraction
- **pdfplumber** 0.10.0+ - Advanced PDF text and table extraction
- **python-docx** 0.8.11+ - MS Word document reading and manipulation

Web & API:
- **pydantic** 2.6.0+ - Data validation and serialization with type hints
- **pydantic-settings** 2.1.0+ - Environment configuration management
- **python-multipart** 0.0.9+ - Multipart form parsing for file uploads

Utilities:
- **numpy** 1.24.0+ - Numerical computing (for embeddings and calculations)
- **tiktoken** 0.5.0+ - Token counting for OpenAI models (context window calculations)
- **redis** 5.0.0+ - Redis client for session caching (24h TTL)
- **PyJWT** 2.8.0+ - JWT token handling for authentication
- **python-dotenv** 1.0.0+ - Environment variable loading from .env
- **slowapi** 0.1.0+ - Rate limiting middleware for FastAPI
- **json-repair** 0.35.0+ - JSON parsing and repair utility

Performance & Load Testing:
- **pytest-benchmark** 4.0.0+ - Benchmarking framework for performance testing
- **locust** 2.0.0+ - Load testing framework for stress testing

Logging:
- **Python standard library `logging`** - Centralized logging via `backend/utils/logging_config.py`

## Configuration

**Environment:**
- **.env file** (required, not committed) containing:
  - Neo4j credentials: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
  - Google Cloud: `VERTEX_PROJECT`, `VERTEX_REGION`, `VERTEX_CREDENTIALS` (path to service account JSON), `VERTEX_API_KEY`
  - File uploads: `UPLOAD_DIR`, `MAX_UPLOAD_SIZE_MB` (default: 200MB)
  - Redis: `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_ENABLED`
  - Feature flags: `ENABLE_LLM_ENTITY_EXTRACTION`, `ENABLE_ENTITY_AWARE_CHUNKING`, `ENABLE_THINKING`
  - Models: `RAG_MODEL_DEFAULT`, `LLM_ENTITY_EXTRACTION_MODEL`

**Backend Config Files:**
- `server/config.py` - FastAPI-specific settings (CORS, uploads, feature flags)
- `backend/utils/config.py` - Centralized backend configuration (Neo4j, Vertex AI, RAG, embedding settings)
- `pyproject.toml` - Python project metadata and pytest configuration
- `.env` - Environment variables (keys: NEO4J, GOOGLE_CLOUD, VERTEX, REDIS, EMBEDDING, etc.)

**Frontend Config Files:**
- `client/vite.config.ts` - Vite build config with React plugin, Tailwind integration, path alias (`@/*`), API proxy to `127.0.0.1:8000`
- `client/tsconfig.json` - TypeScript configuration via `tsconfig.app.json` and `tsconfig.node.json`
- `client/tailwind.config.js` - Tailwind CSS configuration with "Cyber Yellow" custom theme and dark mode
- `client/eslint.config.js` - ESLint flat config for TypeScript, React, hooks, and refresh
- `client/vitest.config.ts` - Unit test configuration with jsdom, path alias, coverage settings
- `client/playwright.config.ts` - E2E test configuration with multi-browser/mobile support, parallel execution

**Build Settings:**
- **Frontend Build:** TypeScript type checking → Vite production build → `dist/`
- **Frontend Dev:** Vite dev server on `127.0.0.1:5173` with hot module reload
- **Backend Dev:** `python main.py` or `uvicorn server.main:app --reload` on `127.0.0.1:8000`
- **Python:** Always use root venv for all pip/pytest operations

## Platform Requirements

**Development:**
- Node.js 18+ (for npm and Vite)
- Python 3.9+ (FastAPI, neo4j driver)
- Git
- Neo4j 5.15+ instance running (local or remote)
- Google Cloud Project with Vertex AI API enabled
- GCP service account JSON file with Vertex AI Generative Models permissions

**Production:**
- **Deployment:** Docker containers (Dockerfile present for both frontend and backend)
- **Orchestration:** docker-compose.yml available for local multi-container setup
- **Database:** Neo4j 5.15+ (cloud-hosted or self-managed)
- **LLM Services:** Google Cloud Vertex AI (Gemini models)
- **Cache:** Redis 7.0+ (optional, degrades gracefully if unavailable)
- **Frontend Hosting:** Static file hosting (nginx, Vercel, netlify)
- **Backend Hosting:** ASGI app server (Gunicorn + Uvicorn, AWS ECS, Cloud Run, etc.)

---

*Stack analysis: 2026-02-20*
