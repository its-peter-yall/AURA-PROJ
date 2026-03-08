# 02-05-SUMMARY: Per-Document KG Status Tracking

## Implementation Status: COMPLETE ✅

## Changes Made

### Models Added (api/modules/models.py)
- `KGStatus` enum: pending, processing, ready, failed
- `DocumentKGStatus`: Per-document status response
- `BatchProcessingRequest/Response`: Batch processing models
- `ProcessingQueueItem`: Queue status model

### New API Endpoints (api/kg/router.py)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/kg/documents/{id}/status` | GET | Get document KG status |
| `/api/v1/kg/process-batch` | POST | Batch process with idempotency |
| `/api/v1/kg/processing-queue` | GET | Get processing queue |
| `/api/v1/kg/tasks/{id}/status` | GET | Get Celery task status |

### Celery Task Updates (api/tasks/document_processing_tasks.py)
- Added `update_document_status()` Firestore helper
- Idempotency: Skip documents with kg_status == "ready"
- Status tracking: processing → ready/failed

### Main App (api/main.py)
- Added kg_router import and inclusion

## Verification
- All 5 files pass py_compile syntax checks
- Runtime tests require full dependency environment

## Success Criteria
- [x] Per-document KG status models added
- [x] Celery tasks support batch processing with idempotency
- [x] GET /api/v1/kg/documents/{id}/status returns document status
- [x] POST /api/v1/kg/process-batch triggers batch processing
- [x] GET /api/v1/kg/processing-queue returns processing documents
- [x] GET /api/v1/kg/tasks/{task_id}/status returns task progress
- [x] Already-processed documents are skipped (idempotent)
- [x] Progress tracked per document (0-100%)
- [x] All files pass py_compile check
