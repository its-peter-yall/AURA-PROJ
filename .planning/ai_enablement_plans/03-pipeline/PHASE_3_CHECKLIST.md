# Phase 3 Post-Verification Checklist

## Pre-Verification
- [ ] Redis is running (127.0.0.1:6379).
- [ ] Neo4j is running (bolt://127.0.0.1:7687).
- [ ] `.env` configured with VERTEX, NEO4J, and REDIS settings.
- [ ] Root venv is available at `../.venv/Scripts/python`.
- [ ] Set `AURA_TEST_MODE=true` to skip Redis/Neo4j checks if needed.

## Core Functionality
- [ ] `api/verify_phase_3.py` runs without errors.
- [ ] Celery app configuration validated (broker, backend, serializers).
- [ ] Celery tasks registered: process_document, process_batch.

## Integration
- [ ] Phase 2 services import: chunker + LLM entity extractor.
- [ ] KnowledgeGraphProcessor available via `api/kg_processor.py`.
- [ ] Vertex AI client module imports without errors.

## Testing
- [ ] `api/test_celery_tasks.py` imports and reports success.
- [ ] `api/test_celery_tasks_e2e.py` completes with Redis + Neo4j.

## Data Verification
- [ ] `api/verify_neo4j_data.py` reports data for a processed document.
- [ ] Neo4j contains Document, Entity, Relationship nodes for test document.

## Documentation
- [ ] `api/PHASE_3_SUMMARY.md` completed and reviewed.
- [ ] `.planning/ai_enablement_plans/03-pipeline/SUMMARY.md` updated.

## Verification Commands
- [ ] `../.venv/Scripts/python api/verify_phase_3.py`
- [ ] `../.venv/Scripts/python -c "import sys; sys.path.insert(0, 'api'); from config import REDIS_URL, NEO4J_URI, LLM_ENTITY_EXTRACTION_MODEL; from tasks.document_processing_tasks import app, process_document_task; from kg_processor import KnowledgeGraphProcessor; print('Quick verification passed')"`

## Sign-Off
- [ ] All checks passed.
- [ ] Issues recorded and resolved (if any).
- [ ] Phase 3 approved for completion.
