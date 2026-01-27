# AI Document Processing Enablement Plan for AURA-NOTES-MANAGER

**Date:** 2026-01-27
**Status:** Draft
**Context:** Aligning AURA-NOTES-MANAGER document processing with AURA-CHAT architecture.

## 1. Executive Summary

This plan outlines the steps to fully enable and verify the AI-powered document processing pipeline in `AURA-NOTES-MANAGER`. The goal is to ensure `kg_processor.py` and its dependencies correctly utilize Google Vertex AI (Gemini 2.5 Flash/Lite) for entity extraction and embeddings, mirroring the production-ready architecture of `AURA-CHAT`. We will also verify the existing Celery asynchronous pipeline.

---

## 0. Pre-Flight Verification Checklist

**Run these commands FIRST to understand current state:**

```bash
# 1. Check Python environment and imports
cd AURA-NOTES-MANAGER
../../.venv/Scripts/python -c "import api.kg_processor; print('kg_processor imports OK')" 2>&1

# 2. Check current hardcoded model strings in kg_processor.py
grep -n "gemini\|text-embedding" api/kg_processor.py || echo "No model strings found"

# 3. Verify Neo4j connection (adjust password as needed)
../../.venv/Scripts/python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://127.0.0.1:7687', auth=('neo4j', 'password'))
driver.verify_connectivity()
print('Neo4j connection OK')
"

# 4. Check if config.py exists and its contents
cat api/config.py 2>/dev/null || echo "config.py does not exist"

# 5. Verify Redis is running
redis-cli ping 2>/dev/null || echo "Redis not running"
```

**Pre-Flight Status Table:**

| Check | Command | Expected | Current |
|-------|---------|----------|---------|
| Python imports | `python -c "import api.kg_processor"` | OK | ___ |
| Model strings | `grep "gemini" api/kg_processor.py` | gemini-2.5-flash-lite | ___ |
| Neo4j connection | `python -c "from neo4j import ..."` | OK | ___ |
| Config exists | `cat api/config.py` | File exists | ___ |
| Redis running | `redis-cli ping` | PONG | ___ |

---

## 1. Prerequisites & Configuration

### 1.1. Environment Variables

**Required in `.env` or `config.py`:**

| Variable | Example Value | Description |
|----------|---------------|-------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | `AURA-NOTES-MANAGER/service_account.json` | Path to service account JSON |
| `GOOGLE_CLOUD_PROJECT` | `lucky-processor-480412-n8` | GCP project ID |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | GCP region (default: us-central1) |
| `GEMINI_API_KEY` | `AIza...` | Optional fallback for direct API |
| `AURA_TEST_MODE` | `false` | Must be `false` for real model calls |
| `NEO4J_URI` | `bolt://127.0.0.1:7687` | Neo4j connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `password` | Neo4j password |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | Redis connection URL |

### 1.2. Service Account Setup

**File:** `AURA-NOTES-MANAGER/service_account.json`

**Verify existence:**
```bash
ls -la AURA-NOTES-MANAGER/service_account.json 2>/dev/null && echo "EXISTS" || echo "MISSING"
```

**Required IAM Role:** `Vertex AI User`

**If missing:**
1. Go to Google Cloud Console → IAM & Admin
2. Find your service account
3. Add role: `Vertex AI User`
4. Download new JSON key file
5. Place at `AURA-NOTES-MANAGER/service_account.json`

### 1.3. Python Dependencies

**Verify installed:**
```bash
../../.venv/Scripts/pip list | grep -E "google-cloud-aiplatform|neo4j|celery|pypdf"
```

**Required packages:**
- `google-cloud-aiplatform>=1.40.0`
- `neo4j>=5.15.0`
- `celery>=5.3.0`
- `pypdf>=3.17.0`
- `python-docx>=1.1.0`

---

## 2. Phase 1: Configuration & Client Unification

### Phase 1 Goal

Remove hardcoded model names and use a centralized configuration, mirroring `AURA-CHAT/backend/utils/config.py`.

---

### Step 1.1: Create/Update `api/config.py`

**File:** `AURA-NOTES-MANAGER/api/config.py`

**If file does NOT exist:**
```python
# config.py
# Centralized configuration for AURA-NOTES-MANAGER AI pipeline

import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file if exists
from dotenv import load_dotenv
dotenv_path = BASE_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)


# =============================================================================
# LLM MODEL CONFIGURATION
# =============================================================================

LLM_ENTITY_EXTRACTION_MODEL = os.getenv(
    "LLM_ENTITY_EXTRACTION_MODEL",
    "gemini-2.5-flash-lite"
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "text-embedding-004"
)

LLM_ENTITY_MAX_PARALLEL = int(os.getenv("LLM_ENTITY_MAX_PARALLEL", "2"))


# =============================================================================
# GOOGLE CLOUD CONFIGURATION
# =============================================================================

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    str(BASE_DIR / "service_account.json")
)


# =============================================================================
# NEO4J CONFIGURATION
# =============================================================================

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


# =============================================================================
# REDIS/CELERY CONFIGURATION
# =============================================================================

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_EXPIRES = int(os.getenv("CELERY_RESULT_EXPIRES", "3600"))


# =============================================================================
# APPLICATION SETTINGS
# =============================================================================

AURA_TEST_MODE = os.getenv("AURA_TEST_MODE", "true").lower() == "true"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
```

**If file EXISTS:**
Add only the LLM_MODEL_CONFIGURATION section if not present, otherwise merge carefully.

---

### Step 1.2: Refactor `GeminiClient` in `api/kg_processor.py`

**File:** `AURA-NOTES-MANAGER/api/kg_processor.py`

**BEFORE (Current State - approximate):**
```python
class GeminiClient:
    def __init__(self, api_key=None):
        self.model = "gemini-2.5-flash-lite"  # Hardcoded
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        # ... rest of init
```

**AFTER (Target State):**
```python
# At the top of file, after other imports
from api.config import (
    LLM_ENTITY_EXTRACTION_MODEL,
    EMBEDDING_MODEL,
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_APPLICATION_CREDENTIALS,
    GOOGLE_CLOUD_LOCATION,
    AURA_TEST_MODE
)


class GeminiClient:
    def __init__(self, api_key=None):
        # Load from config instead of hardcoded
        self.extraction_model = LLM_ENTITY_EXTRACTION_MODEL
        self.embedding_model = EMBEDDING_MODEL
        
        # Use API key from config or parameter
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        # Initialize Vertex AI client if not in test mode
        if not AURA_TEST_MODE:
            self._init_vertex_ai()
        else:
            self.client = None
            self.embedding_client = None
    
    def _init_vertex_ai(self):
        """Initialize Google Cloud Vertex AI clients."""
        try:
            from google.cloud import aiplatform
            from google.oauth2 import service_account
            
            credentials = service_account.Credentials.from_service_account_file(
                GOOGLE_APPLICATION_CREDENTIALS
            )
            
            aiplatform.init(
                project=GOOGLE_CLOUD_PROJECT,
                location=GOOGLE_CLOUD_LOCATION,
                credentials=credentials
            )
            
            # Initialize prediction client for Gemini
            self.client = aiplatform.PredictionServiceClient(
                client_options={
                    "api_endpoint": f"{GOOGLE_CLOUD_LOCATION}-aiplatform.googleapis.com"
                }
            )
            
            # Initialize embedding client
            self.embedding_client = aiplatform.TextEmbeddingModel(
                name=self.embedding_model
            )
            
        except Exception as e:
            logging.error(f"Failed to initialize Vertex AI: {e}")
            raise
    
    async def extract_entities(self, text: str) -> dict:
        """Extract entities using configured Gemini model."""
        # Use self.extraction_model (not hardcoded string)
        # ... implementation
        pass
    
    async def generate_embedding(self, text: str) -> list:
        """Generate embedding using configured embedding model."""
        # Use self.embedding_model (not hardcoded string)
        # ... implementation
        pass
```

**Key Changes:**
1. Import from `api.config` at top of file
2. Replace `"gemini-2.5-flash-lite"` with `LLM_ENTITY_EXTRACTION_MODEL`
3. Replace `"text-embedding-004"` with `EMBEDDING_MODEL`
4. Initialize Vertex AI properly using service account

---

### Step 1.3: Sync `services/embeddings.py`

**File:** `AURA-NOTES-MANAGER/services/embeddings.py`

**BEFORE:**
```python
EMBEDDING_MODEL = "text-embedding-004"  # Hardcoded
```

**AFTER:**
```python
from api.config import EMBEDDING_MODEL
```

**If `api.config` doesn't exist yet:**
```python
import os
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
```

---

### Step 1.4: Verify Phase 1 Completion

**Run these commands:**
```bash
# 1. Verify config imports work
../../.venv/Scripts/python -c "from api.config import LLM_ENTITY_EXTRACTION_MODEL, EMBEDDING_MODEL; print(f'Extraction: {LLM_ENTITY_EXTRACTION_MODEL}, Embedding: {EMBEDDING_MODEL})"

# 2. Verify kg_processor uses config
../../.venv/Scripts/python -c "
from api.kg_processor import GeminiClient
client = GeminiClient()
print(f'Extraction model: {client.extraction_model}')
print(f'Embedding model: {client.embedding_model}')
"

# 3. Verify embeddings.py imports
../../.venv/Scripts/python -c "from services.embeddings import EMBEDDING_MODEL; print(f'Embedding model: {EMBEDDING_MODEL})"
```

**Expected Output:**
```
Extraction model: gemini-2.5-flash-lite
Embedding model: text-embedding-004
```

---

## 3. Phase 2: Knowledge Graph Processor Enhancement

### Phase 2 Goal

Ensure `kg_processor.py` fully implements the AURA-CHAT pipeline logic with correct entity extraction and relationship detection.

---

### Step 2.1: Verify Pipeline Steps

**File:** `AURA-NOTES-MANAGER/api/kg_processor.py`

**Verify each step exists:**

| Step | Function Name | Check Command |
|------|---------------|---------------|
| Text Extraction | `extract_text_from_file()` | `grep -n "def extract_text" api/kg_processor.py` |
| Chunking | `chunk_text_hierarchical()` | `grep -n "def chunk_text" api/kg_processor.py` |
| Embedding | `generate_embeddings()` | `grep -n "def generate" api/kg_processor.py` |
| Entity Extraction | `extract_entities()` | `grep -n "def extract_entities" api/kg_processor.py` |
| Graph Storage | `store_in_graph()` | `grep -n "def store" api/kg_processor.py` |

**If any step is missing:**
1. Check if function exists in separate file (e.g., `services/`)
2. Port from `AURA-CHAT/backend/` if needed

---

### Step 2.2: Verify/Port `chunk_text_hierarchical`

**Reference:** `AURA-CHAT/backend/entity_aware_chunker.py`

**Compare implementation:**
```bash
# Show first 20 lines of AURA-CHAT implementation
head -20 AURA-CHAT/backend/entity_aware_chunker.py

# Compare with AURA-NOTES-MANAGER implementation
head -20 AURA-NOTES-MANAGER/api/kg_processor.py | grep -A20 "def chunk_text"
```

**Key differences to check:**
- [ ] Uses semantic boundaries (paragraphs, sections) not just character count
- [ ] Preserves entity context across chunks
- [ ] Configurable chunk size (default ~1000 tokens)

---

### Step 2.3: Port `LLMEntityExtractor` from AURA-CHAT

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

**If AURA-NOTES-MANAGER version is outdated:**
1. Copy the entire `llm_entity_extractor.py` from `AURA-CHAT/backend/`
2. Modify imports to use AURA-NOTES-MANAGER's `api.config`
3. Update function calls to use AURA-NOTES-MANAGER's `GeminiClient`

---

### Step 2.4: Verify Entity Extraction Uses New Model Config

**Check in `api/kg_processor.py` or `services/llm_entity_extractor.py`:**
```python
# CORRECT - uses config
model_name = LLM_ENTITY_EXTRACTION_MODEL  # or client.extraction_model

# WRONG - hardcoded
model_name = "gemini-1.5-pro"  # or any hardcoded string
```

**If hardcoded found:**
```bash
# Find hardcoded model strings
grep -rn "gemini-1\|gemini-pro\|gemini-flash" api/kg_processor.py services/llm_entity_extractor.py
```

Replace all with config references.

---

### Step 2.5: Error Handling & Fallbacks

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

---

### Step 2.6: Verify Phase 2 Completion

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

---

## 4. Phase 3: Celery Pipeline Verification

### Phase 3 Goal

Confirm the async worker correctly orchestrates the processor with proper error handling and Redis integration.

---

### Step 3.1: Verify Celery Configuration

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

---

### Step 3.2: Verify Document Processing Task

**File:** `AURA-NOTES-MANAGER/api/tasks/document_processing_tasks.py`

**Verify content:**
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

---

### Step 3.3: Start Redis Server

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

---

### Step 3.4: Start Celery Worker

**Terminal 1 - Start Worker:**
```bash
cd AURA-NOTES-MANAGER
..\\.venv\\Scripts\\celery -A api.tasks worker -l info -Q kg_processing -P solo --concurrency=2
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

---

### Step 3.5: Create and Run Test Script

**File:** `AURA-NOTES-MANAGER/api/test_celery_tasks.py`

```python
# test_celery_tasks.py
# Test script for verifying Celery document processing pipeline

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables (adjust paths as needed)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(project_root / "service_account.json")
os.environ["GOOGLE_CLOUD_PROJECT"] = "lucky-processor-480412-n8"
os.environ["AURA_TEST_MODE"] = "false"

from api.tasks.document_processing_tasks import process_document_task
from api.config import NEO4J_PASSWORD


def test_celery_pipeline():
    """Test the full Celery document processing pipeline."""
    
    # Use a sample PDF if exists, otherwise create test text file
    sample_pdf = project_root / "test_data" / "sample_document.pdf"
    test_text_file = project_root / "test_data" / "test_document.txt"
    
    if not sample_pdf.exists():
        # Create a simple test document
        test_text_file.parent.mkdir(exist_ok=True)
        test_text_file.write_text("""
# Machine Learning

Machine learning is a subset of artificial intelligence that focuses on building systems that learn from data.

## Neural Networks

Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes (neurons).

## Deep Learning

Deep learning is a subset of machine learning that uses multi-layered neural networks (deep neural networks).
        
Key concepts:
- Supervised learning
- Unsupervised learning
- Reinforcement learning
        """.strip())
        file_path = str(test_text_file)
    else:
        file_path = str(sample_pdf)
    
    print(f"Testing with file: {file_path}")
    
    # Submit task
    task = process_document_task.delay(
        document_id="test-doc-001",
        file_path=file_path,
        module_id="CS101",
        user_id="test-user"
    )
    
    print(f"Task submitted with ID: {task.id}")
    print("Waiting for result...")
    
    # Wait for result (with timeout)
    result = task.get(timeout=120)
    
    print(f"\n{'='*50}")
    print("RESULT:")
    print(f"{'='*50}")
    print(f"Status: {result.get('status', 'UNKNOWN')}")
    print(f"Entities extracted: {result.get('entities_count', 0)}")
    print(f"Chunks created: {result.get('chunks_count', 0)}")
    
    if result.get("status") == "SUCCESS":
        print("\n✅ Celery pipeline test PASSED")
    else:
        print(f"\n❌ Celery pipeline test FAILED: {result}")
    
    return result


if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv(project_root / ".env")
    
    test_celery_pipeline()
```

**Run Test:**
```bash
# Terminal 2 - Run test (keep worker running in Terminal 1)
cd AURA-NOTES-MANAGER
..\\.venv\\Scripts\\python api/test_celery_tasks.py
```

---

### Step 3.6: Verify Neo4j Data

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

---

### Step 3.7: Verify Phase 3 Completion

| Check | Command | Expected |
|-------|---------|----------|
| Worker starts | `celery worker ...` | "worker ready" |
| Task submits | `python test_celery_tasks.py` | Task ID displayed |
| Task completes | Check worker output | "SUCCESS" |
| Neo4j has data | Cypher query | Document + Entity nodes |
| No errors | Check logs | Empty error section |

---

## 5. Rollback Plan

**If issues arise during implementation:**

### 5.1: Revert Configuration Changes

```bash
# Revert config.py changes
git checkout HEAD -- api/config.py

# Or restore from backup
cp api/config.py.bak api/config.py
```

### 5.2: Revert kg_processor.py Changes

```bash
git checkout HEAD -- api/kg_processor.py
```

### 5.3: Clear Redis Queue

```bash
# Purge all pending tasks
celery -A api.tasks purge -f

# Or purge specific queue
celery -A api.tasks purge -f -Q kg_processing
```

### 4: Restart Services

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

## 6. Post-Implementation Verification

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

## 7. Summary: All Validation Criteria

- [ ] **Pre-Flight:** All environment checks pass (Python, Neo4j, Redis)
- [ ] **Phase 1:** `api/config.py` created with centralized model configuration
- [ ] **Phase 1:** `kg_processor.py` imports from config, no hardcoded model strings
- [ ] **Phase 1:** `services/embeddings.py` synced with config
- [ ] **Phase 2:** `chunk_text_hierarchical` matches AURA-CHAT logic
- [ ] **Phase 2:** `llm_entity_extractor.py` uses XML prompt + JSON schema approach
- [ ] **Phase 2:** Entity extraction uses `gemini-2.5-flash-lite`
- [ ] **Phase 2:** Embeddings use `text-embedding-004`
- [ ] **Phase 3:** Celery worker starts without errors
- [ ] **Phase 3:** `test_celery_tasks.py` completes with SUCCESS
- [ ] **Phase 3:** Neo4j contains Document, Entity, and Relationship nodes
- [ ] **Rollback:** Can revert changes if needed
- [ ] **Post-Verification:** All checks pass

---

## 8. File Reference Summary

| File | Purpose | Phase |
|------|---------|-------|
| `AURA-NOTES-MANAGER/api/config.py` | Centralized configuration | 1 |
| `AURA-NOTES-MANAGER/api/kg_processor.py` | Main KG processing logic | 1, 2 |
| `AURA-NOTES-MANAGER/services/embeddings.py` | Embedding generation | 1 |
| `AURA-NOTES-MANAGER/services/llm_entity_extractor.py` | Entity extraction | 2 |
| `AURA-NOTES-MANAGER/api/celery_config.py` | Celery configuration | 3 |
| `AURA-NOTES-MANAGER/api/tasks/document_processing_tasks.py` | Celery task | 3 |
| `AURA-NOTES-MANAGER/api/test_celery_tasks.py` | Verification script | 3 |
| `AURA-CHAT/backend/utils/config.py` | Reference config | 1 |
| `AURA-CHAT/backend/utils/vertex_ai_client.py` | Reference Vertex AI client | 1, 2 |
| `AURA-CHAT/backend/llm_entity_extractor.py` | Reference entity extractor | 2 |
| `AURA-CHAT/backend/entity_aware_chunker.py` | Reference chunking logic | 2 |
