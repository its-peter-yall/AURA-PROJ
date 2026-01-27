# AI Enablement & Verification Roadmap

**Project:** AURA-NOTES-MANAGER AI Enablement
**Status:** ACTIVE
**Context:** Aligning AURA-NOTES-MANAGER document processing with AURA-CHAT architecture.
**Source:** `AI_ENABLEMENT_PLAN.md`
**Last Updated:** 2026-01-27

## Executive Summary

This roadmap outlines the execution plan to fully enable and verify the AI-powered document processing pipeline in `AURA-NOTES-MANAGER`. The primary objective is to ensure ALL AI model calls (entity extraction, embeddings, summarization) use **Google Vertex AI** via `services/vertex_ai_client.py`, eliminating direct `google.generativeai` API usage for consistency, credential management, and enterprise authentication.

**Key Transformation:** Migrate from dual-client architecture (Vertex AI + direct Gemini API) to unified Vertex AI client across all services.

---

## Pre-Flight Verification

**Execute these commands FIRST** to establish baseline understanding:

```bash
# 1. Check Python environment and imports
cd AURA-NOTES-MANAGER
../../.venv/Scripts/python -c "import api.kg_processor; print('kg_processor imports OK')" 2>&1

# 2. Check current hardcoded model strings in kg_processor.py
grep -n "gemini\|text-embedding" api/kg_processor.py || echo "No model strings found"

# 3. CHECK: Find all google.generativeai usage (should be 0 after migration)
grep -rn "import google.generativeai" api/ services/ || echo "No direct google.generativeai imports found - GOOD"

# 4. CHECK: Verify vertex_ai_client.py is used
grep -rn "from services.vertex_ai_client" api/ services/ | head -20

# 5. Verify Neo4j connection (adjust password as needed)
../../.venv/Scripts/python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://127.0.0.1:7687', auth=('neo4j', 'password'))
driver.verify_connectivity()
print('Neo4j connection OK')
"

# 6. Check if config.py exists and its contents
cat api/config.py 2>/dev/null || echo "config.py does not exist"

# 7. Verify Redis is running
redis-cli ping 2>/dev/null || echo "Redis not running"
```

**Pre-Flight Status Tracking:**

| Check | Command | Expected | Current | Status |
|-------|---------|----------|---------|--------|
| Python imports | `python -c "import api.kg_processor"` | OK | ___ | ⏳ |
| Model strings | `grep "gemini" api/kg_processor.py` | gemini-2.5-flash-lite | ___ | ⏳ |
| **google.generativeai** | `grep -rn "import google.generativeai"` | 0 imports | ___ | ⏳ |
| **vertex_ai_client usage** | `grep -rn "from services.vertex_ai_client"` | >0 imports | ___ | ⏳ |
| Neo4j connection | `python -c "from neo4j import ..."` | OK | ___ | ⏳ |
| Config exists | `cat api/config.py` | File exists | ___ | ⏳ |
| Redis running | `redis-cli ping` | PONG | ___ | ⏳ |

---

## Phase 1: Configuration & Client Unification

**Focus:** Infrastructure & Config
**Status:** IN_PROGRESS
**Plans:**
- [x] `.planning/ai_enablement_plans/01-config/01-01-PLAN.md` - Create api/config.py
- [ ] `.planning/ai_enablement_plans/01-config/01-02-PLAN.md` - Refactor GeminiClient
- [ ] `.planning/ai_enablement_plans/01-config/01-03-PLAN.md` - Audit and Migrate Services
- [ ] `.planning/ai_enablement_plans/01-config/01-04-PLAN.md` - Verify Phase 1 Completion

### Objectives

1. **Centralize Configuration:** Create/update `api/config.py` with LLM model settings, Google Cloud credentials, Neo4j connection, and Redis configuration.
2. **Unify AI Client:** Refactor all AI services to use `services/vertex_ai_client.py` instead of direct `google.generativeai` API.
3. **Remove Hardcoded Values:** Eliminate model name strings from `api/kg_processor.py` and related services.
4. **Verify Connectivity:** Confirm service account, Neo4j, and Redis are accessible.

### Critical: Why Vertex AI Client?

| Aspect | Direct `google.generativeai` | `services/vertex_ai_client.py` |
|--------|------------------------------|-------------------------------|
| **Auth** | API key in code | ADC credentials / Service Account |
| **Enterprise** | Personal API key | Project-based authentication |
| **Audit** | Per-user tracking | Project-level audit logs |
| **Consistency** | Mixed pattern | Unified across all services |
| **Billing** | Per-user quotas | Project-level quotas |

### Tasks

#### Task 1.1: Create/Update `api/config.py`

**File:** `AURA-NOTES-MANAGER/api/config.py`

**Required Environment Variables:**

| Variable | Example Value | Description |
|----------|---------------|-------------|
| `VERTEX_PROJECT` | `lucky-processor-480412-n8` | GCP project ID (preferred over GOOGLE_CLOUD_PROJECT) |
| `VERTEX_LOCATION` | `us-central1` | GCP region |
| `VERTEX_CREDENTIALS` | `AURA-NOTES-MANAGER/service_account.json` | Service account path |
| `GOOGLE_APPLICATION_CREDENTIALS` | (auto-set from VERTEX_CREDENTIALS) | Set automatically by vertex_ai_client |
| `NEO4J_URI` | `bolt://127.0.0.1:7687` | Neo4j connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `password` | Neo4j password |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | Redis connection URL |
| `AURA_TEST_MODE` | `false` | Must be `false` for real model calls |

**Deprecated Variables (remove):**

| Variable | Action |
|----------|--------|
| `GEMINI_API_KEY` | Remove - no longer used for model calls |
| `GOOGLE_CLOUD_PROJECT` | Replaced by `VERTEX_PROJECT` |
| `GOOGLE_CLOUD_LOCATION` | Replaced by `VERTEX_LOCATION` |

**Verify:** Config file contains `LLM_ENTITY_EXTRACTION_MODEL` and `EMBEDDING_MODEL` constants.

#### Task 1.2: Refactor `GeminiClient` in `api/kg_processor.py`

**File:** `AURA-NOTES-MANAGER/api/kg_processor.py`

**BEFORE (Current State - DO NOT USE):**
```python
class GeminiClient:
    def __init__(self, api_key=None):
        self.model = "gemini-2.5-flash-lite"  # Hardcoded
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")  # API key auth
        # Uses google.generativeai - BAD

    async def get_embedding(self, text: str):
        import google.generativeai as genai  # WRONG
        genai.configure(api_key=self.api_key)  # WRONG
        result = genai.embed_content(model=self.embedding_model, ...)  # WRONG
```

**AFTER (Target State - USE VERTEX AI):**
```python
from api.config import (
    LLM_ENTITY_EXTRACTION_MODEL,
    EMBEDDING_MODEL,
    AURA_TEST_MODE
)
from services.vertex_ai_client import (
    init_vertex_ai,
    get_model,
    generate_content,
    block_none_safety_settings,
    GenerationConfig,
    normalize_model_name
)


class GeminiClient:
    def __init__(self, api_key=None):
        # Load from config instead of hardcoded
        self.extraction_model = LLM_ENTITY_EXTRACTION_MODEL
        self.embedding_model = EMBEDDING_MODEL

        # NO api_key - uses ADC credentials via vertex_ai_client
        self._client = None

        # Initialize Vertex AI if not in test mode
        if not AURA_TEST_MODE:
            init_vertex_ai()  # Uses VERTEX_PROJECT, VERTEX_LOCATION, VERTEX_CREDENTIALS
```

**Key Changes Required:**
1. **REMOVE** `import google.generativeai` - delete entirely
2. **ADD** `from services.vertex_ai_client import init_vertex_ai, get_model, generate_content`
3. Replace `self.api_key = ...` with ADC credentials via `init_vertex_ai()`
4. Use `get_model(f"models/{self.extraction_model}")` instead of `genai.GenerativeModel()`
5. Use `generate_content(...)` instead of `model.generate_content(...)`
6. Remove all `genai.configure(api_key=...)` calls

#### Task 1.3: Audit and Migrate All Services to Vertex AI

**Services to migrate:**

| File | Current Pattern | Migrate To |
|------|-----------------|------------|
| `services/embeddings.py` | `google.generativeai` | `vertex_ai_client.py` or `aiplatform.TextEmbeddingModel` |
| `services/llm_entity_extractor.py` | `google.generativeai` | `vertex_ai_client.py` |
| `services/answer_synthesizer.py` | `google.generativeai` | `vertex_ai_client.py` |
| `services/summary_service.py` | `google.generativeai` | `vertex_ai_client.py` |

**Check all services for `google.generativeai` usage:**
```bash
# Find all direct Gemini API usage
grep -rn "import google.generativeai" AURA-NOTES-MANAGER/

# Expected: should find files that need migration
```

**Migration pattern for each service:**
```python
# BEFORE
import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content(prompt)

# AFTER
from services.vertex_ai_client import get_model, generate_content, GenerationConfig
init_vertex_ai()  # Called once at module level or in __init__
model = get_model("models/gemini-2.5-flash-lite")  # Use configured model
response = generate_content(
    model=model,
    contents=prompt,
    generation_config=GenerationConfig(temperature=0.1)
)
```

#### Task 1.4: Sync `services/embeddings.py`

**File:** `AURA-NOTES-MANAGER/services/embeddings.py`

**AFTER:**
```python
from api.config import EMBEDDING_MODEL
from services.vertex_ai_client import init_vertex_ai

# Initialize Vertex AI at module level
init_vertex_ai()

# Use aiplatform.TextEmbeddingModel for embeddings
from google.cloud import aiplatform

embedding_model = aiplatform.TextEmbeddingModel(EMBEDDING_MODEL)

async def get_embedding(text: str) -> list:
    """Generate embedding using Vertex AI Text Embedding."""
    embeddings = embedding_model.get_embeddings([text])
    return embeddings[0].values
```

### Phase 1 Verification Commands

```bash
# 1. Verify NO google.generativeai imports remain
echo "=== Checking for google.generativeai imports ==="
count=$(grep -rn "import google.generativeai" AURA-NOTES-MANAGER/api AURA-NOTES-MANAGER/services 2>/dev/null | wc -l)
echo "google.generativeai imports found: $count"
if [ "$count" -eq 0 ]; then
    echo "✅ PASS: No direct google.generativeai imports"
else
    echo "❌ FAIL: Found $count imports - needs migration"
    grep -rn "import google.generativeai" AURA-NOTES-MANAGER/api AURA-NOTES-MANAGER/services
fi
echo ""

# 2. Verify vertex_ai_client is used
echo "=== Checking vertex_ai_client usage ==="
grep -rn "from services.vertex_ai_client" AURA-NOTES-MANAGER/api AURA-NOTES-MANAGER/services | head -10
echo ""

# 3. Verify config imports work
../../.venv/Scripts/python -c "from api.config import LLM_ENTITY_EXTRACTION_MODEL, EMBEDDING_MODEL; print(f'Extraction: {LLM_ENTITY_EXTRACTION_MODEL}, Embedding: {EMBEDDING_MODEL}')"

# 4. Verify kg_processor uses config
../../.venv/Scripts/python -c "
from api.kg_processor import GeminiClient
client = GeminiClient()
print(f'Extraction model: {client.extraction_model}')
print(f'Embedding model: {client.embedding_model}')
"

# 5. Verify embeddings.py imports
../../.venv/Scripts/python -c "from services.embeddings import EMBEDDING_MODEL; print(f'Embedding model: {EMBEDDING_MODEL}')"
```

**Expected Output:**
```
✅ PASS: No direct google.generativeai imports
Extraction model: gemini-2.5-flash-lite
Embedding model: text-embedding-004
```

### Phase 1 Deliverables

- [x] `api/config.py` with centralized configuration
- [ ] Refactored `api/kg_processor.py` (no hardcoded model strings)
- [ ] Updated `services/embeddings.py` synced with config
- [ ] All services use `services/vertex_ai_client.py` (not `google.generativeai`)
- [ ] `GEMINI_API_KEY` removed from all code and `.env`
- [ ] `verify_phase_1.py` script passes

---

## Phase 2: Knowledge Graph Processor Enhancement

**Focus:** Core Logic Implementation
**Status:** PLANNED
**Plans:** `.planning/ai_enablement_plans/02-processor/`

### Objectives

1. **Port Entity-Aware Chunking:** Import `entity_aware_chunker.py` logic from AURA-CHAT to preserve semantic boundaries and entity context.
2. **Port Structured Entity Extractor:** Import `llm_entity_extractor.py` with XML prompt + JSON schema approach from AURA-CHAT.
3. **Integrate Services:** Update `api/kg_processor.py` to use new services.
4. **Add Robust Error Handling:** Implement `tenacity` retry logic for LLM calls.

### Tasks

#### Task 2.1: Verify/Port `chunk_text_hierarchical`

**Reference:** `AURA-CHAT/backend/entity_aware_chunker.py`

**Key differences to check:**
- [ ] Uses semantic boundaries (paragraphs, sections) not just character count
- [ ] Preserves entity context across chunks
- [ ] Configurable chunk size (default ~1000 tokens)

```bash
# Compare implementation
head -20 AURA-CHAT/backend/entity_aware_chunker.py
head -20 AURA-NOTES-MANAGER/api/kg_processor.py | grep -A20 "def chunk_text"
```

#### Task 2.2: Port `LLMEntityExtractor` from AURA-CHAT

**File to check/create:** `AURA-NOTES-MANAGER/services/llm_entity_extractor.py`
**Reference:** `AURA-CHAT/backend/llm_entity_extractor.py`

**AURA-CHAT approach (Structured Output with JSON Schema):**
```python
SYSTEM_PROMPT = """<instruction>
You are an expert entity extraction system. Extract entities and relationships from academic documents.
</instruction>
<output_format>
Return a JSON object with:
- "entities": List of {name, type, description, source_chunk}
- "relationships": List of {source, target, relationship_type, description}
</output_format>
<rules>
- Only extract entities mentioned in the text
- Use consistent naming (prefer proper nouns)
- Academic entities: Concept, Person, Organization, Location, Event, Citation
</rules>
"""

async def extract_entities(text: str) -> dict:
    """Extract entities using structured output."""
    response = await model.generate_content_async(
        f"{SYSTEM_PROMPT}\n\nText:\n{text}",
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": {
                "type": "object",
                "properties": {
                    "entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "description": {"type": "string"},
                                "source_chunk": {"type": "string"}
                            }
                        }
                    },
                    "relationships": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                                "target": {"type": "string"},
                                "relationship_type": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    )
    return json.loads(response.text)
```

#### Task 2.3: Verify Entity Extraction Uses New Model Config

**Check in `api/kg_processor.py` or `services/llm_entity_extractor.py`:**
```python
# CORRECT - uses config
model_name = LLM_ENTITY_EXTRACTION_MODEL  # or client.extraction_model

# WRONG - hardcoded
model_name = "gemini-1.5-pro"  # or any hardcoded string
```

#### Task 2.4: Add Error Handling & Fallbacks

**Add to `api/kg_processor.py`:**
```python
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Custom exception for entity extraction failures."""
    pass


class VertexAIError(Exception):
    """Custom exception for Vertex AI API errors."""
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type((VertexAIError, json.JSONDecodeError))
)
async def extract_entities_with_retry(text: str, client: GeminiClient) -> dict:
    """Extract entities with automatic retry on failure."""
    try:
        return await client.extract_entities(text)
    except Exception as e:
        logger.warning(f"Extraction attempt failed: {e}")
        raise
```

### Phase 2 Verification Commands

```bash
# 1. Check all imports work
../../.venv/Scripts/python -c "
from api.kg_processor import KnowledgeGraphProcessor
from services.llm_entity_extractor import extract_entities
print('All imports successful')
"

# 2. Test entity extraction (small text)
../../.venv/Scripts/python -c "
import asyncio
from services.llm_entity_extractor import extract_entities

async def test():
    result = await extract_entities('Machine learning is a subset of artificial intelligence.')
    print(f'Extracted {len(result.get(\"entities\", []))} entities')

asyncio.run(test())
"
```

### Phase 2 Deliverables

- [ ] `services/entity_aware_chunker.py` (ported from AURA-CHAT)
- [ ] `services/llm_entity_extractor.py` (ported from AURA-CHAT with XML prompt + JSON schema)
- [ ] Updated `api/kg_processor.py` (with integration)
- [ ] `tenacity` retry logic implemented
- [ ] Entity extraction uses `gemini-2.5-flash-lite` via Vertex AI
- [ ] Embeddings use `text-embedding-004` via Vertex AI
- [ ] `verify_phase_2.py` script passes

---

## Phase 3: Celery Pipeline Verification

**Focus:** Async Pipeline & Testing
**Status:** PLANNED
**Plans:** `.planning/ai_enablement_plans/03-pipeline/`

### Objectives

1. **Verify Celery Configuration:** Confirm `api/celery_config.py` matches standards.
2. **Audit Document Processing Task:** Verify `api/tasks/document_processing_tasks.py` implementation.
3. **Create End-to-End Test:** Build `test_celery_tasks.py` for full pipeline verification.
4. **Verify Data Persistence:** Confirm Neo4j contains correctly structured nodes and relationships.

### Tasks

#### Task 3.1: Verify Celery Configuration

**File:** `AURA-NOTES-MANAGER/api/celery_config.py` (or in `main.py`)

**Should contain:**
```python
from celery import Celery
from api.config import REDIS_URL, CELERY_RESULT_EXPIRES

celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    worker_prefetch_multiplier=1,
    worker_concurrency=2,
    result_expires=CELERY_RESULT_EXPIRES,
    task_queues={
        "kg_processing": {
            "exchange": "kg_processing",
            "routing_key": "kg_processing"
        }
    }
)
```

#### Task 3.2: Verify Document Processing Task

**File:** `AURA-NOTES-MANAGER/api/tasks/document_processing_tasks.py`

**Verify content matches:**
```python
from api.celery_config import celery_app
from api.kg_processor import KnowledgeGraphProcessor
from services.llm_entity_extractor import extract_entities
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="kg_processing.process_document")
def process_document_task(self, document_id: str, file_path: str, module_id: str, user_id: str):
    """
    Process document and extract knowledge graph entities.
    
    Args:
        document_id: Unique document identifier
        file_path: Path to document file
        module_id: Module context
        user_id: User who initiated processing
    """
    try:
        # Update task status
        self.update_state(state="PROCESSING", meta={"status": "Extracting text..."})
        
        # Initialize processor
        processor = KnowledgeGraphProcessor()
        
        # Run full pipeline
        result = processor.process_document(
            file_path=file_path,
            module_id=module_id,
            user_id=user_id,
            document_id=document_id
        )
        
        return {
            "status": "SUCCESS",
            "document_id": document_id,
            "entities_count": result.get("entities_count", 0),
            "chunks_count": result.get("chunks_count", 0)
        }
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}", exc_info=True)
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise
```

#### Task 3.3: Start Redis Server

**Check if Redis is running:**
```bash
redis-cli ping
```
**Expected:** `PONG`

**If not running, start Redis:**
```bash
# Windows (if installed via chocolatey)
redis-server

# Or via Docker
docker run -d -p 6379:6379 redis:alpine
```

#### Task 3.4: Start Celery Worker

**Terminal 1 - Start Worker:**
```bash
cd AURA-NOTES-MANAGER
../../.venv/Scripts/celery -A api.tasks worker -l info -Q kg_processing -P solo --concurrency=2
```

**Expected Output:**
```
[tasks]
  . kg_processing.process_document

[2026-01-27 10:00:00,000] INFO/MainProcess] Connected to redis://127.0.0.1:6379/0
[2026-01-27 10:00:00,001] INFO/MainProcess] mingle: searching for neighbors
[2026-01-27 10:00:00,002] INFO/MainProcess] mingle: sync with [celery@hostname]
[2026-01-27 10:00:00,003] INFO/MainProcess] worker ready.
```

#### Task 3.5: Create and Run Test Script

**File:** `AURA-NOTES-MANAGER/api/test_celery_tasks.py`

**Run Test:**
```bash
# Terminal 2 - Run test (keep worker running in Terminal 1)
cd AURA-NOTES-MANAGER
../../.venv/Scripts/python api/test_celery_tasks.py
```

#### Task 3.6: Verify Neo4j Data

**Open Neo4j Browser and run:**
```cypher
// Check processed documents
MATCH (d:Document)
RETURN d.document_id, d.filename, d.status, d.entities_count, d.created_at
ORDER BY d.created_at DESC
LIMIT 5

// Check extracted entities
MATCH (e:Entity)
RETURN e.name, e.type, e.description
LIMIT 20

// Check relationships
MATCH ()-[r:RELATED_TO]->()
RETURN r.source, r.target, r.relationship_type
LIMIT 10
```

**Expected Results:**
```
Document nodes with status="processed"
Entity nodes with type: Concept, Person, etc.
Relationship edges between entities
```

### Phase 3 Verification Table

| Check | Command | Expected |
|-------|---------|----------|
| Worker starts | `celery worker ...` | "worker ready" |
| Task submits | `python test_celery_tasks.py` | Task ID displayed |
| Task completes | Check worker output | "SUCCESS" |
| Neo4j has data | Cypher query | Document + Entity nodes |
| No errors | Check logs | Empty error section |

### Phase 3 Deliverables

- [ ] Verified `api/celery_config.py` matches standards
- [ ] Verified `api/tasks/document_processing_tasks.py`
- [ ] `test_celery_tasks.py` created and passes
- [ ] `post_verification.py` (Comprehensive system check)
- [ ] Celery worker starts without errors
- [ ] Neo4j contains Document, Entity, and Relationship nodes
- [ ] `verify_phase_3.py` script passes

---

## Rollback Plan

**If issues arise during implementation:**

### Rollback 1: Revert Configuration Changes

```bash
# Revert config.py changes
git checkout HEAD -- api/config.py

# Or restore from backup
cp api/config.py.bak api/config.py
```

### Rollback 2: Revert kg_processor.py Changes

```bash
git checkout HEAD -- api/kg_processor.py
```

### Rollback 3: Clear Redis Queue

```bash
# Purge all pending tasks
celery -A api.tasks purge -f

# Or purge specific queue
celery -A api.tasks purge -f -Q kg_processing
```

### Rollback 4: Restart Services

```bash
# Restart Celery worker
# (Ctrl+C existing worker, then restart)

# Verify basic functionality
../../.venv/Scripts/python -c "
from api.kg_processor import KnowledgeGraphProcessor
print('Basic import works - rollback successful')
"
```

---

## Post-Implementation Verification

**Run this comprehensive check after completing all phases:**

```bash
#!/bin/bash
# post_verification.sh

echo "=== AURA-NOTES-MANAGER AI Pipeline Verification ==="
echo ""

# 1. Config Check
echo "1. Configuration Check:"
../../.venv/Scripts/python -c "from api.config import LLM_ENTITY_EXTRACTION_MODEL, EMBEDDING_MODEL; print(f'   Extraction: {LLM_ENTITY_EXTRACTION_MODEL}'); print(f'   Embedding: {EMBEDDING_MODEL}')"
echo ""

# 2. Import Check
echo "2. Import Verification:"
../../.venv/Scripts/python -c "
from api.kg_processor import KnowledgeGraphProcessor, GeminiClient
from services.llm_entity_extractor import extract_entities
from services.embeddings import generate_embedding
print('   All imports successful')
"
echo ""

# 3. Model Config Check
echo "3. Model Configuration:"
../../.venv/Scripts/python -c "
from api.kg_processor import GeminiClient
client = GeminiClient()
print(f'   Using model: {client.extraction_model}')
print(f'   Using embedding: {client.embedding_model}')
"
echo ""

# 4. Neo4j Check
echo "4. Neo4j Data Check:"
../../.venv/Scripts/python -c "
from neo4j import GraphDriver
from api.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
driver = GraphDriver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
with driver.session() as session:
    result = session.run('MATCH (d:Document) RETURN count(d) as count')
    count = result.single()['count']
    print(f'   Documents in DB: {count}')
"
echo ""

echo "=== Verification Complete ==="
```

---

## Success Criteria

### Pre-Flight Verification
- [ ] All environment checks pass (Python, Neo4j, Redis)
- [ ] `google.generativeai` imports = 0
- [ ] `vertex_ai_client.py` imports > 0

### Phase 1 Completion
- [ ] `api/config.py` created with centralized model configuration
- [ ] `kg_processor.py` imports from config, no hardcoded model strings
- [ ] `services/embeddings.py` synced with config
- [ ] `GEMINI_API_KEY` removed from all code
- [ ] All services use `services/vertex_ai_client.py` (not `google.generativeai`)

### Phase 2 Completion
- [ ] `chunk_text_hierarchical` matches AURA-CHAT logic
- [ ] `llm_entity_extractor.py` uses XML prompt + JSON schema approach
- [ ] Entity extraction uses `gemini-2.5-flash-lite` via Vertex AI
- [ ] Embeddings use `text-embedding-004` via Vertex AI

### Phase 3 Completion
- [ ] Celery worker starts without errors
- [ ] `test_celery_tasks.py` completes with SUCCESS
- [ ] Neo4j contains Document, Entity, and Relationship nodes

### Overall Success
- [ ] All configuration is centralized (no hardcoded "gemini-..." strings)
- [ ] `post_verification.py` runs successfully
- [ ] Celery worker processes a sample document without errors
- [ ] Rollback plan tested and verified
- [ ] All validation criteria pass

---

## File Reference Summary

| File | Purpose | Phase |
|------|---------|-------|
| `AURA-NOTES-MANAGER/services/vertex_ai_client.py` | **Unified Vertex AI client** | 1 |
| `AURA-NOTES-MANAGER/api/config.py` | Centralized configuration | 1 |
| `AURA-NOTES-MANAGER/api/kg_processor.py` | Main KG processing logic | 1, 2 |
| `AURA-NOTES-MANAGER/services/embeddings.py` | Embedding generation | 1 |
| `AURA-NOTES-MANAGER/services/llm_entity_extractor.py` | Entity extraction | 2 |
| `AURA-NOTES-MANAGER/services/entity_aware_chunker.py` | Semantic chunking | 2 |
| `AURA-NOTES-MANAGER/api/celery_config.py` | Celery configuration | 3 |
| `AURA-NOTES-MANAGER/api/tasks/document_processing_tasks.py` | Celery task | 3 |
| `AURA-NOTES-MANAGER/api/test_celery_tasks.py` | Verification script | 3 |
| `AURA-CHAT/backend/utils/config.py` | Reference config | 1 |
| `AURA-CHAT/backend/utils/vertex_ai_client.py` | Reference Vertex AI client | 1, 2 |
| `AURA-CHAT/backend/llm_entity_extractor.py` | Reference entity extractor | 2 |
| `AURA-CHAT/backend/entity_aware_chunker.py` | Reference chunking logic | 2 |

---

## Migration Quick Reference

### Before (Mixed Pattern - WRONG)
```python
# api/kg_processor.py
import google.generativeai as genai
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")
```

### After (Unified Vertex AI - CORRECT)
```python
# api/kg_processor.py
from services.vertex_ai_client import get_model, generate_content, GenerationConfig
from api.config import LLM_ENTITY_EXTRACTION_MODEL

model = get_model(f"models/{LLM_ENTITY_EXTRACTION_MODEL}")
response = generate_content(model, prompt, generation_config=GenerationConfig(...))
```

### Environment Variables Change
| Old Variable | New Variable | Notes |
|--------------|--------------|-------|
| `GEMINI_API_KEY` | (removed) | No longer used |
| `GOOGLE_CLOUD_PROJECT` | `VERTEX_PROJECT` | Renamed |
| `GOOGLE_CLOUD_LOCATION` | `VERTEX_LOCATION` | Renamed |
| (new) | `VERTEX_CREDENTIALS` | Path to service account |

---

## Milestones

- **v0.1** - Pre-flight verification complete
- **v0.2** - Phase 1 complete (Configuration & Client Unification)
- **v0.3** - Phase 2 complete (Knowledge Graph Processor Enhancement)
- **v0.4** - Phase 3 complete (Celery Pipeline Verification)
- **v1.0** - All phases complete, post-verification passes

---

## Related Documents

- `AI_ENABLEMENT_PLAN.md` - Source plan document
- `BRIEF.md` - Project vision
- `ROADMAP.md` - Master roadmap
- `.planning/phases/` - Detailed phase plans

---

**End of Roadmap**
