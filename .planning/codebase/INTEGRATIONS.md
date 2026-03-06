# External Integrations

**Analysis Date:** 2026-02-20

## APIs & External Services

**Google Cloud / Vertex AI (Primary LLM Provider):**
- **Gemini 2.5 Flash / Gemini 3 Flash** - Chat generation with thinking mode support
  - SDK: `vertexai` (GenerativeModel) for thinking mode, `google-genai` for standard chat
  - Auth: Service account via `GOOGLE_APPLICATION_CREDENTIALS` (path to JSON key)
  - Project: `VERTEX_PROJECT` environment variable
  - Endpoint: `https://vertex-ai.googleapis.com` (regional routing based on model)
  - Purpose: RAG-powered chat responses with optional extended reasoning
  - Implementation: `backend/utils/vertex_ai_client.py` handles model initialization and routing
  - Models supported:
    - `gemini-2.5-flash-lite`, `gemini-2.5-flash`, `gemini-2.5-flash-001`
    - `gemini-3-flash-preview` (routes to global region)
    - `gemini-2.0-flash-001` (legacy, no thinking mode)

**Google Vertex AI Embeddings:**
- **text-embedding-004** - Text vector embeddings via REST API
  - SDK: REST API (via `requests` library, not SDK)
  - Auth: Service account credentials with access token
  - Endpoint: Regional `https://{region}-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/publishers/google/models/text-embedding-004:predict`
  - Batch size: 16 texts per request (configurable: `EMBEDDING_BATCH_SIZE`)
  - Dimensions: 768 (configurable: `EMBEDDING_DIMENSIONS`)
  - Rate limit: 300 requests/min client-side throttling (configurable: `EMBEDDING_RPM_LIMIT`)
  - Retry: Exponential backoff (1s initial, 2x multiplier, 30s max) on 429/503
  - Implementation: `backend/utils/embeddings.py` handles batching, rate limiting, retry logic
  - Purpose: Generate vector embeddings for documents/chunks and queries for semantic search

**Google Cloud Firestore (Potential - Not currently used):**
- Not detected in current codebase
- Neo4j used exclusively for all persistent storage

## Data Storage

**Databases:**
- **Neo4j** 5.13.0+
  - Connection: `neo4j://` or `bolt://` URI via `NEO4J_URI` (default: `bolt://localhost:7687`)
  - Auth: Username/password via `NEO4J_USER`, `NEO4J_PASSWORD` (required)
  - Client: `neo4j` Python driver
  - Purpose: Knowledge graph storage, semantic search, session storage
  - Schema:
    - **Node types:** Document, Chunk, ParentChunk, Topic, Concept, Methodology, Finding, StudySession, Message
    - **Vector indices:** HNSW indices for 768-dim embeddings (semantic search)
    - **Fulltext index:** Apache Lucene for lexical search
  - Implementation: `backend/graph_manager.py` handles all graph operations
  - Features:
    - Document-to-entity relationships (ADDRESSES_TOPIC, MENTIONS_CONCEPT, USES_METHODOLOGY, SUPPORTS)
    - Chunk hierarchy (Document → ParentChunk → Chunk)
    - Entity relationships (DEFINES, DEPENDS_ON, USES, SUPPORTS, CONTRADICTS, DERIVED_FROM, RELATED_TO, CAUSES)
    - Session and message storage with ordering (HAS_MESSAGE with message_order property)

**Caching:**
- **Redis** 5.0.0+ (optional, degrades gracefully)
  - Connection: `redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}`
  - Hostname: `REDIS_HOST` (default: `localhost`)
  - Port: `REDIS_PORT` (default: `6379`)
  - Database: `REDIS_DB` (default: `0`)
  - Enabled: `REDIS_ENABLED` (default: `true`)
  - TTL: 24 hours for session caching
  - Purpose: Fast retrieval of active study sessions and module metadata
  - Implementation: `backend/session_manager.py` uses Redis with key prefix `session:`
  - Graceful degradation: If Redis is unavailable, system falls back to Neo4j queries (slower but functional)

**File Storage:**
- **Local filesystem only**
  - Upload directory: `data/uploads/` (configurable via `UPLOAD_DIR`)
  - Maximum file size: 200MB (configurable via `MAX_UPLOAD_SIZE_MB`)
  - Allowed formats: `.pdf`, `.docx`, `.txt` (hardcoded in `server/config.py`)
  - Processing: Document processing timeout is 5 minutes (300 seconds)

## Authentication & Identity

**Auth Provider:**
- **Custom** - No external auth provider
- Implementation: Currently stateless or session-based via Neo4j StudySession nodes
- JWT support available via `PyJWT` 2.8.0+ but not currently used for API authentication
- Session management: `backend/session_manager.py` creates and manages StudySession nodes with user_id

## Monitoring & Observability

**Error Tracking:**
- **None detected** - No Sentry, Rollbar, or similar integration

**Logs:**
- **Python standard library `logging`**
  - Centralized setup: `backend/utils/logging_config.py`
  - Format: Structured logging with context (user_id, session_id, document_id)
  - Output: Console (stdout/stderr) for development; can be extended to files or services
  - Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - Components log via named loggers: `api_main`, `session_manager`, `graph_manager`, `rag_engine`, etc.

## CI/CD & Deployment

**Hosting:**
- **Docker-based** - Containerization ready
  - Files: `Dockerfile` (root for backend), `client/Dockerfile` (frontend)
  - Orchestration: `docker-compose.yml` for local multi-container setup
  - Deployment targets: Any Docker-compatible platform (AWS ECS, Google Cloud Run, Kubernetes, etc.)

**CI Pipeline:**
- **Not detected in AURA-CHAT** - `.github/workflows` may exist at project root

## Environment Configuration

**Required env vars (validation in backend/utils/config.py):**

| Variable | Purpose | Required | Example |
|----------|---------|----------|---------|
| `NEO4J_URI` | Graph database connection | Yes | `bolt://localhost:7687` |
| `NEO4J_USER` | Graph database username | Yes | `neo4j` |
| `NEO4J_PASSWORD` | Graph database password | Yes | `your_password` |
| `VERTEX_PROJECT` | GCP project ID | Yes | `my-aura-project` |
| `VERTEX_CREDENTIALS` | Path to service account JSON | Yes | `/path/to/credentials.json` |
| `VERTEX_REGION` | Vertex AI region (non-Gemini-3) | No | `us-central1` (default: `global`) |
| `VERTEX_API_KEY` | Gemini API key (alternate auth) | No | `AIza...` |
| `REDIS_HOST` | Redis hostname | No | `localhost` |
| `REDIS_PORT` | Redis port | No | `6379` |
| `REDIS_DB` | Redis database number | No | `0` |
| `REDIS_ENABLED` | Enable Redis caching | No | `true` |
| `UPLOAD_DIR` | Directory for file uploads | No | `data/uploads` |
| `MAX_UPLOAD_SIZE_MB` | Max upload file size | No | `200` |
| `RAG_MODEL_DEFAULT` | Default chat model | No | `gemini-2.5-flash-lite` |
| `ENABLE_THINKING` | Enable thinking mode | No | `true` |
| `THINKING_BUDGET` | Token budget for thinking | No | `2048` |
| `EMBEDDING_DIMENSIONS` | Embedding vector dimensions | No | `768` |
| `EMBEDDING_BATCH_SIZE` | Texts per embedding request | No | `16` |
| `EMBEDDING_RPM_LIMIT` | Embeddings requests/min limit | No | `300` |
| `DEBUG` | Enable debug mode (shows errors) | No | `false` |
| `AURA_TEST_MODE` | Enable test mode (skips external services) | No | `false` |

**Secrets location:**
- `.env` file in project root (not committed to git)
- Service account JSON pointed to by `VERTEX_CREDENTIALS` (not committed)
- Configuration validation: `backend/utils/config.py:Config.validate()` checks all required vars

## Webhooks & Callbacks

**Incoming:**
- Not detected - No webhook endpoints for external service callbacks

**Outgoing:**
- Not detected - No external service callbacks or event notifications

## API Endpoints

**Chat API:**
- `POST /chat/stream` - Streaming RAG chat with thinking mode support
  - Request: `{"query": "...", "session_id": "...", "module_ids": [...], "enable_thinking": true}`
  - Response: Server-sent events (SSE) streaming text chunks
  - Backend: `server/routers/chat.py`

**Graph API:**
- `POST /graph/data` - Fetch knowledge graph visualization data
  - Request: `{"query": "...", "filters": {...}}`
  - Response: JSON with nodes and edges for Reagraph
  - Backend: `server/routers/graph.py`

**Documents API:**
- `POST /documents/upload` - Upload and process documents
  - Request: multipart/form-data with file
  - Response: Document metadata and processing status
  - Timeout: 5 minutes
  - Backend: `server/routers/documents.py`

**Sessions API:**
- `POST /sessions` - Create study session
- `GET /sessions/{session_id}` - Get session with messages
- `POST /sessions/{session_id}/messages` - Add message to session
- `DELETE /sessions/{session_id}` - Delete session
  - Backend: `backend/routers/sessions.py`

**Module Selection API:**
- `GET /modules` - Get module hierarchy (Department → Semester → Subject → Module)
- `GET /modules/{module_id}` - Get specific module with documents
  - Backend: `backend/routers/student_modules.py`

**Health Check:**
- `GET /health` - Service health status
- `GET /` - API info and documentation links
  - Backend: `server/routers/health.py`

---

*Integration audit: 2026-02-20*
