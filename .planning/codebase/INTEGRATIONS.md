# External Integrations

**Analysis Date:** 2026-03-10

## APIs & External Services

**AI / LLM:**
- Google Vertex AI / Gemini - Chat generation, entity extraction, summarization, and embeddings
  - SDK/Client: `google-cloud-aiplatform`, `vertexai`, `google-genai`, `google-generativeai` in `AURA-CHAT/backend/utils/vertex_ai_client.py`, `AURA-NOTES-MANAGER/services/vertex_ai_client.py`, `AURA-NOTES-MANAGER/services/genai_client.py`
  - Auth: `VERTEX_PROJECT`, `VERTEX_REGION`, `VERTEX_CREDENTIALS`, `GOOGLE_APPLICATION_CREDENTIALS`, optional `GOOGLE_API_KEY` in `AURA-CHAT/backend/utils/config.py`, `AURA-CHAT/server/config.py`, `AURA-NOTES-MANAGER/api/config.py`

**Speech / Audio:**
- Deepgram - Speech-to-text for audio-to-notes processing
  - SDK/Client: `deepgram-sdk` in `AURA-NOTES-MANAGER/services/stt.py`
  - Auth: `DEEPGRAM_API_KEY` in `AURA-NOTES-MANAGER/services/stt.py`

**Identity / Browser Security:**
- Firebase Auth - Browser sign-in and backend token verification for both apps
  - SDK/Client: Web SDK in `AURA-CHAT/client/src/lib/firebase.ts`, `AURA-NOTES-MANAGER/frontend/src/api/firebaseClient.ts`; Admin SDK in `AURA-CHAT/server/auth/firebase_auth.py`, `AURA-NOTES-MANAGER/api/config.py`, `AURA-NOTES-MANAGER/api/auth.py`
  - Auth: `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`, `VITE_FIREBASE_PROJECT_ID`, `VITE_FIREBASE_STORAGE_BUCKET`, `VITE_FIREBASE_MESSAGING_SENDER_ID`, `VITE_FIREBASE_APP_ID`, plus service-account path env vars on the backend
- Firebase App Check + reCAPTCHA Enterprise - Frontend abuse protection for Notes Manager
  - SDK/Client: `initializeAppCheck` and `ReCaptchaEnterpriseProvider` in `AURA-NOTES-MANAGER/frontend/src/api/firebaseClient.ts`
  - Auth: `VITE_RECAPTCHA_ENTERPRISE_SITE_KEY`

## Data Storage

**Databases:**
- Neo4j - Primary graph and vector store for AURA-CHAT RAG and AURA-NOTES KG features
  - Connection: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
  - Client: `neo4j` driver in `AURA-CHAT/backend/graph_manager.py`, `AURA-CHAT/backend/tasks/worker.py`, `AURA-NOTES-MANAGER/api/neo4j_config.py`
- Firestore - User records, hierarchy trees, module metadata, and note metadata
  - Connection: `FIREBASE_CREDENTIALS`, `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_AUTH_CREDENTIALS`, `USE_REAL_FIREBASE`
  - Client: `firebase_admin.firestore`, `google.cloud.firestore.AsyncClient` in `AURA-CHAT/server/auth/firestore_client.py`, `AURA-NOTES-MANAGER/api/config.py`, `AURA-NOTES-MANAGER/api/auth.py`

**File Storage:**
- Local filesystem only
  - AURA-CHAT uploads use `UPLOAD_DIR` in `AURA-CHAT/server/config.py`
  - AURA-NOTES generated PDFs and uploads use `pdfs/` paths in `AURA-NOTES-MANAGER/api/main.py` and `AURA-NOTES-MANAGER/api/audio_processing.py`

**Caching:**
- Redis - Cache, pub/sub, and queue backend
  - Connection: `REDIS_URL` or host/port/db fields from env in `AURA-CHAT/backend/utils/config.py`, `AURA-NOTES-MANAGER/api/config.py`
  - Client: `redis.asyncio` in `AURA-CHAT/backend/tasks/worker.py`, `AURA-CHAT/server/routers/websocket.py`; sync Redis health usage in `AURA-NOTES-MANAGER/api/main.py`

## Authentication & Identity

**Auth Provider:**
- Firebase Auth with Firestore-backed user metadata
  - Implementation: Frontends sign in with Firebase Web SDK in `AURA-CHAT/client/src/stores/useAuthStore.ts` and `AURA-NOTES-MANAGER/frontend/src/stores/useAuthStore.ts`; backends verify bearer tokens and sync user profiles in `AURA-CHAT/server/routers/auth.py`, `AURA-CHAT/server/auth/firebase_auth.py`, `AURA-NOTES-MANAGER/api/auth.py`, `AURA-NOTES-MANAGER/api/auth_sync.py`

## Monitoring & Observability

**Error Tracking:**
- None detected as an external SaaS integration; logging is application-local in `AURA-CHAT/backend/utils/logging_config.py` and `AURA-NOTES-MANAGER/api/logging_config.py`

**Logs:**
- Structured/server logging via project logging helpers and FastAPI middleware in `AURA-CHAT/server/main.py`, `AURA-CHAT/backend/utils/logging_config.py`, `AURA-NOTES-MANAGER/api/main.py`, `AURA-NOTES-MANAGER/api/logging_config.py`
- Health probes expose dependency state in `AURA-CHAT/server/routers/health.py` and `AURA-NOTES-MANAGER/api/main.py`

## CI/CD & Deployment

**Hosting:**
- Docker container deployment targets are defined for both APIs and both frontends in `AURA-CHAT/Dockerfile`, `AURA-CHAT/client/Dockerfile`, `AURA-NOTES-MANAGER/api/Dockerfile`, `AURA-NOTES-MANAGER/frontend/Dockerfile`

**CI Pipeline:**
- GitHub Actions - Test, security scan, E2E, and image build workflows in `.github/workflows/ci.yml` and `.github/workflows/e2e-tests.yml`

## Environment Configuration

**Required env vars:**
- AURA-CHAT backend: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `VERTEX_PROJECT`, `VERTEX_REGION`, `VERTEX_CREDENTIALS` or `GOOGLE_APPLICATION_CREDENTIALS`, `REDIS_HOST`/`REDIS_PORT` or Redis URL equivalents, `FIREBASE_CREDENTIALS`, `AURA_TEST_MODE` from `AURA-CHAT/backend/utils/config.py`, `AURA-CHAT/server/config.py`, `AURA-CHAT/server/auth/firebase_auth.py`
- AURA-CHAT client: `VITE_API_URL`, Firebase `VITE_FIREBASE_*` values from `AURA-CHAT/client/src/lib/api.ts`, `AURA-CHAT/client/src/lib/firebase.ts`
- AURA-NOTES backend: `VERTEX_PROJECT`, `VERTEX_LOCATION`, `VERTEX_CREDENTIALS`, `GOOGLE_APPLICATION_CREDENTIALS`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `REDIS_URL`, `DEEPGRAM_API_KEY`, `USE_REAL_FIREBASE`, `GOOGLE_AUTH_CREDENTIALS`, `ENVIRONMENT`, `ALLOWED_ORIGINS`, `AURA_TEST_MODE` from `AURA-NOTES-MANAGER/api/config.py`, `AURA-NOTES-MANAGER/api/main.py`, `AURA-NOTES-MANAGER/services/stt.py`
- AURA-NOTES frontend: Firebase `VITE_FIREBASE_*`, `VITE_RECAPTCHA_ENTERPRISE_SITE_KEY`, `VITE_USE_MOCK_AUTH` from `AURA-NOTES-MANAGER/frontend/src/api/firebaseClient.ts`, `AURA-NOTES-MANAGER/frontend/src/api/client.ts`, `AURA-NOTES-MANAGER/frontend/playwright.config.ts`

**Secrets location:**
- `.env` files are present at repo root, `AURA-CHAT/.env`, `AURA-CHAT/client/.env`, `AURA-NOTES-MANAGER/.env`, and `AURA-NOTES-MANAGER/frontend/.env`; treat them as secret-bearing environment files
- Firebase and Google service-account JSON paths are supplied through env vars and read by `AURA-CHAT/server/auth/firebase_auth.py`, `AURA-CHAT/server/auth/firestore_client.py`, `AURA-NOTES-MANAGER/api/config.py`, `AURA-NOTES-MANAGER/services/vertex_ai_client.py`

## Webhooks & Callbacks

**Incoming:**
- None detected; APIs expose HTTP and WebSocket endpoints only, with WebSocket job progress at `AURA-CHAT/server/routers/websocket.py`

**Outgoing:**
- Redis pub/sub messages for job progress in `AURA-CHAT/server/routers/websocket.py` and `AURA-CHAT/backend/tasks/progress.py`
- External API calls go to Vertex AI/Gemini and Deepgram from `AURA-CHAT/backend/utils/vertex_ai_client.py`, `AURA-NOTES-MANAGER/services/vertex_ai_client.py`, `AURA-NOTES-MANAGER/services/genai_client.py`, `AURA-NOTES-MANAGER/services/stt.py`

---

*Integration audit: 2026-03-10*
