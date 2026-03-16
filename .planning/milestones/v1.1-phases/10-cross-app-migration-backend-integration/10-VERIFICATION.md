---
phase: 10-cross-app-migration-backend-integration
verified: 2026-03-10T17:56:17Z
status: gaps_found
score: 5/6 must-haves verified
re_verification:
  previous_status: gaps_found
  previous_score: 1/5
  gaps_closed:
    - "Neither application contains direct provider SDK imports outside shared model_router"
    - "Model discovery uses cache with configurable TTL in the 5-60 minute range"
    - "Admin can store, validate, and manage API keys per provider through backend APIs, with keys masked in all responses"
    - "Background workers in both apps can import and use model_router-backed services"
  gaps_remaining: []
  regressions:
    - "AURA-CHAT/test_real_models.py still makes a direct Vertex AI REST generateContent call outside model_router, so the phase goal's 'router exclusively for every LLM call' outcome is not fully achieved."
gaps:
  - truth: "Both applications use model_router exclusively for every LLM call, with no direct provider HTTP bypasses"
    status: failed
    reason: "AURA-CHAT still ships a standalone live connectivity script that builds Vertex AI REST URLs and posts to generateContent directly instead of routing through model_router."
    artifacts:
      - path: "AURA-CHAT/test_real_models.py"
        issue: "Imports Google auth helpers at lines 23-24 and sends direct requests.post() calls to Vertex AI generateContent endpoints at lines 57-78."
    missing:
      - "Migrate the live model connectivity script to model_router or remove it from the application codebase."
      - "Extend the compliance audit to detect direct provider HTTP calls outside shared model_router."
---

# Phase 10: Cross-App Migration + Backend Integration Verification Report

**Phase Goal:** Both applications use the model router exclusively for every LLM call, with admin-configurable defaults, dynamic model discovery, and secure API key management.
**Verified:** 2026-03-10T17:56:17Z
**Status:** gaps_found
**Re-verification:** Yes — after gap closure

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Neither AURA app contains direct provider SDK imports outside `model_router` | ✓ VERIFIED | `tests/test_no_direct_imports.py` now scans app + test dirs, includes ARQ/Celery import-context checks, and passed (`9 passed`). `AURA-CHAT/backend/tests/test_thinking_mode_genai_sdk.py` now imports `backend.utils.vertex_ai_client` / `model_router` instead of `google.genai`. |
| 2 | Admin can set default provider/model for chat, embeddings, and entity extraction via REST endpoints | ✓ VERIFIED | Both settings routers still expose `PUT /api/v1/settings/defaults/{use_case}` with `chat`, `embeddings`, and `entity_extraction`; both routers remain registered in `AURA-CHAT/server/main.py:282` and `AURA-NOTES-MANAGER/api/main.py:254`. |
| 3 | Model discovery returns cached provider model lists with configurable TTL enforced to 5-60 minutes | ✓ VERIFIED | `shared/model_router/src/model_router/cache.py` enforces `MIN_TTL_SECONDS=300` and `MAX_TTL_SECONDS=3600`; both settings routers read `MODEL_CACHE_TTL_SECONDS` and pass it into `ModelCache(..., default_ttl=ttl)`; cache tests passed (`12 passed`). |
| 4 | Admin can store, validate, and manage API keys per provider with masked responses | ✓ VERIFIED | `KeyManager` encrypts + masks keys; both routers expose POST/GET/DELETE/validate endpoints; `_validate_provider_key()` now handles OpenRouter, Vertex AI, and Ollama semantics. `AURA-CHAT/server/tests/test_settings_router.py` passed (`15 passed`). |
| 5 | Background worker paths in both apps reach model_router-backed services | ✓ VERIFIED | NOTES Celery path: `api/tasks/document_processing_tasks.py` → `api/kg_processor.py` → `services.vertex_ai_client.py` / `services.embeddings.py`. CHAT ARQ path: `backend/tasks/worker.py` → `backend/tasks/document_tasks.py` → `backend/document_processor.py` → `backend/llm_entity_extractor.py` / `backend/utils/embeddings.py`. Root audit includes `test_arq_worker_import_context()` and passed. |
| 6 | Both applications use `model_router` exclusively for every LLM call, with no direct provider HTTP bypasses | ✗ FAILED | `AURA-CHAT/test_real_models.py:57-78` builds Vertex AI `generateContent` REST URLs and calls `requests.post(...)` directly using Google auth credentials from lines `23-24`, bypassing `model_router`. |

**Score:** 5/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `AURA-CHAT/backend/tests/test_thinking_mode_genai_sdk.py` | Router-backed live thinking verification | ✓ VERIFIED | No banned SDK imports; uses `get_default_router()` and façade imports. |
| `tests/test_no_direct_imports.py` | Cross-app forbidden-import + worker-context audit | ✓ VERIFIED | Covers app dirs, test dirs, NOTES Celery import context, and CHAT ARQ import context. |
| `shared/model_router/src/model_router/cache.py` | Shared cache with enforced TTL bounds | ✓ VERIFIED | Substantive TTL validation and cache wiring. |
| `shared/model_router/tests/test_model_cache.py` | TTL bounds regression coverage | ✓ VERIFIED | Valid/invalid/default TTL cases covered; test suite passed. |
| `AURA-CHAT/server/routers/settings.py` | CHAT defaults/models/key management API | ✓ VERIFIED | Wired to `SettingsStore`, `ModelCache`, `KeyManager`, env TTL, and provider-aware validation. |
| `AURA-NOTES-MANAGER/api/routers/settings.py` | NOTES defaults/models/key management API | ✓ VERIFIED | Mirrors CHAT router and imports successfully. |
| `AURA-CHAT/backend/tasks/worker.py` | CHAT background-worker import path | ✓ VERIFIED | ARQ worker imports document task path that reaches router-backed extractor/embeddings services. |
| `AURA-NOTES-MANAGER/api/tasks/document_processing_tasks.py` | NOTES Celery processing path | ✓ VERIFIED | Celery tasks invoke KG processor wired to router-backed LLM/embedding façades. |
| `AURA-CHAT/test_real_models.py` | No direct provider-call bypasses | ✗ FAILED | Direct Vertex REST client remains outside shared router. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `AURA-CHAT/backend/tests/test_thinking_mode_genai_sdk.py` | `backend/utils/vertex_ai_client.py` | façade import | WIRED | Imports `GenerationConfig` and `get_model`; live checks call `get_default_router().generate/stream()`. |
| `tests/test_no_direct_imports.py` | `AURA-CHAT/backend/tasks/worker.py` | `test_arq_worker_import_context()` | WIRED | Subprocess imports `WorkerSettings`, `get_model`, and `EmbeddingService`; audit passed. |
| `AURA-CHAT/server/routers/settings.py` | `shared/model_router/cache.py` | `ModelCache(... default_ttl=ttl)` | WIRED | Reads `MODEL_CACHE_TTL_SECONDS` and injects bounded TTL into shared cache. |
| `AURA-NOTES-MANAGER/api/routers/settings.py` | `shared/model_router/cache.py` | `ModelCache(... default_ttl=ttl)` | WIRED | Same TTL wiring as CHAT. |
| `AURA-CHAT/server/routers/settings.py` | router provider validation | `get_default_router().get_provider(...).health_check()` | WIRED | Vertex AI validation path now uses provider health check; OpenRouter uses stored-key validator; Ollama returns null/not-applicable. |
| `AURA-NOTES-MANAGER/api/routers/settings.py` | router provider validation | `get_default_router().get_provider(...).health_check()` | WIRED | Same provider-aware validation flow as CHAT. |
| `AURA-CHAT/test_real_models.py` | Vertex AI | direct `requests.post(...:generateContent)` | NOT_WIRED | Bypasses shared router entirely. |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
| --- | --- | --- |
| `CONFIG-01` | ✓ SATISFIED | Defaults endpoints exist in both apps for `chat`, `embeddings`, and `entity_extraction`. |
| `CONFIG-03` | ✓ SATISFIED | Shared cache now has bounded configurable TTL and is wired into both routers. |
| `CONFIG-04` | ✓ SATISFIED | Encrypted masked key management and provider-aware validation are implemented in both routers. |
| `UI-03` | ✓ SATISFIED | No direct provider SDK imports remain in either app outside `model_router`; root audit passed. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `AURA-CHAT/test_real_models.py` | 23-24, 57-78 | Direct provider auth + raw Vertex REST `generateContent` call | 🛑 Blocker | Violates the phase-goal requirement that every LLM call route through `model_router`. |
| `AURA-CHAT/backend/tasks/embedding_tasks.py` | 51 | `NotImplementedError(...)` | ⚠️ Warning | Separate background embedding task path remains stubbed, though it did not block the verified Phase 10 worker import path. |

### Gaps Summary

Plans **10-05** and **10-06** do fully close the **previous verification gaps**:

- direct SDK imports in app test code are gone, and the audit now covers test files + CHAT ARQ worker context;
- model discovery TTL is now configurable and bounded to 5-60 minutes;
- provider API key validation is now provider-aware;
- cross-app background worker import coverage now matches actual architecture (NOTES Celery, CHAT ARQ).

However, the **phase goal is still not fully achieved**. A new goal-level blocker remains outside the prior gap set: `AURA-CHAT/test_real_models.py` still performs direct Vertex AI REST calls instead of using the shared router. So the re-verification closes the old gaps, but the codebase still does **not** satisfy “model router exclusively for every LLM call.”

---

_Verified: 2026-03-10T17:56:17Z_
_Verifier: Claude (gsd-verifier)_
