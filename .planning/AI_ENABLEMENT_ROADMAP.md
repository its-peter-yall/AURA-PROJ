# AI Enablement & Verification Roadmap

**Project:** AURA-NOTES-MANAGER AI Enablement
**Status:** ACTIVE
**Context:** Aligning AURA-NOTES-MANAGER document processing with AURA-CHAT architecture.
**Source:** `AI_ENABLEMENT_PLAN.md`

## Goals
1. **Unify Configuration:** Centralize AI/Cloud settings in `api/config.py`.
2. **Standardize Client:** Refactor `GeminiClient` to match AURA-CHAT patterns.
3. **Enhance Processor:** Port entity-aware chunking and robust entity extraction.
4. **Verify Pipeline:** Ensure Celery + Redis + Vertex AI pipeline works end-to-end.

---

## Phase 1: Configuration & Client Unification

**Focus:** Infrastructure & Config
**Status:** COMPLETED
**Plans:** `.planning/ai_enablement_plans/01-config/`

### Objectives
- [x] Create centralized `api/config.py` (LLM, Google Cloud, Neo4j, Redis settings)
- [x] Refactor `api/kg_processor.py` to remove hardcoded model strings
- [x] Update `services/embeddings.py` to use new config
- [x] Verify environment variables and service account connectivity

### Deliverables
- `api/config.py`
- Refactored `api/kg_processor.py`
- Updated `services/embeddings.py`
- `verify_phase_1.py` script

---

## Phase 2: Knowledge Graph Processor Enhancement

**Focus:** Core Logic Implementation
**Status:** PLANNED
**Plans:** `.planning/ai_enablement_plans/02-processor/`

### Objectives
- [ ] Port `entity_aware_chunker.py` from AURA-CHAT
- [ ] Port `llm_entity_extractor.py` (Structured Output version) from AURA-CHAT
- [ ] Integrate new services into `api/kg_processor.py`
- [ ] Implement `tenacity` retry logic for LLM calls

### Deliverables
- `services/entity_aware_chunker.py`
- `services/llm_entity_extractor.py`
- Updated `api/kg_processor.py` (with integration)
- `verify_phase_2.py` script

---

## Phase 3: Celery Pipeline Verification

**Focus:** Async Pipeline & Testing
**Status:** PLANNED
**Plans:** `.planning/ai_enablement_plans/03-pipeline/`

### Objectives
- [ ] Verify `api/celery_config.py` matches AURA-CHAT standards
- [ ] Audit `api/tasks/document_processing_tasks.py`
- [ ] Create end-to-end test script `test_celery_tasks.py`
- [ ] Verify Neo4j data persistence (nodes & relationships)

### Deliverables
- Verified `api/celery_config.py`
- Verified `api/tasks/document_processing_tasks.py`
- `test_celery_tasks.py`
- `post_verification.py` (Comprehensive system check)

---

## Success Criteria

- [ ] All configuration is centralized (no hardcoded "gemini-..." strings)
- [ ] `post_verification.py` runs successfully
- [ ] Celery worker processes a sample document without errors
- [ ] Neo4j contains correctly structured Document, Chunk, and Entity nodes
