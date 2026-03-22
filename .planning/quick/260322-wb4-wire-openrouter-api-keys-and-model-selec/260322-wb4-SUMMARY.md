---
phase: quick
plan: 260322-wb4
subsystem: shared/model_router
tags: [settings-store, model-routing, gatekeeper, summarization, redis]
dependency_graph:
  requires: [shared/model_router settings_store]
  provides: [admin-configurable models for gatekeeper and summarization]
  affects:
    - AURA-CHAT/backend/llm_gatekeeper.py
    - AURA-CHAT/server/routers/settings.py
    - AURA-NOTES-MANAGER/api/routers/settings.py
    - AURA-NOTES-MANAGER/services/summary_service.py
    - AURA-NOTES-MANAGER/services/summarizer.py
tech_stack:
  added:
    - model_router.settings_store.get_default_sync integration
  patterns:
    - Admin default resolution with graceful Redis fallback
    - Vertex-only gatekeeper model selection (skips OpenRouter)
key_files:
  created: []
  modified:
    - AURA-CHAT/backend/llm_gatekeeper.py
    - AURA-CHAT/server/routers/settings.py
    - AURA-NOTES-MANAGER/api/routers/settings.py
    - AURA-NOTES-MANAGER/services/summary_service.py
    - AURA-NOTES-MANAGER/services/summarizer.py
decisions:
  - Gatekeeper only uses Vertex AI admin defaults (skips OpenRouter because
    response_mime_type is Vertex-specific)
  - SummaryService resolves admin model in __init__, not per-call
  - Summarizer resolves admin model at function entry (stateless function)
  - Both settings routers accept "summarization" as a valid use case
metrics:
  duration: "8 min"
  completed: "2026-03-22"
  tasks_completed: 2
  files_modified: 5
---

# Phase quick Plan 260322-wb4: Wire SettingsStore Model Defaults Summary

## One-liner

Wired hardcoded LLM models in gatekeeper and summarization services to read
admin-configured defaults from the shared SettingsStore (Redis), following the
established embeddings pattern.

## What Was Built

### Task 1: Wire gatekeeper and add summarization use case

**Files modified:**
- `AURA-CHAT/backend/llm_gatekeeper.py` — Added SettingsStore model resolution
  with Vertex-only guard and graceful fallback
- `AURA-CHAT/server/routers/settings.py` — Added "summarization" to
  ALLOWED_USE_CASES
- `AURA-NOTES-MANAGER/api/routers/settings.py` — Added "summarization" to
  ALLOWED_USE_CASES

**Key behavior:**
- Gatekeeper reads "gatekeeper" use case from SettingsStore before using
  hardcoded "gemini-2.5-flash-lite" fallback
- OpenRouter defaults are skipped (logged) because gatekeeper requires
  `response_mime_type` which is Vertex-specific
- Redis unavailability is handled gracefully with `exc_info=True` debug logging

### Task 2: Wire summary services to read from SettingsStore

**Files modified:**
- `AURA-NOTES-MANAGER/services/summary_service.py` — Added SettingsStore
  resolution in `__init__` and defined missing `_get_model()` method
- `AURA-NOTES-MANAGER/services/summarizer.py` — Added SettingsStore resolution
  before LLM calls, replaced hardcoded "gemini-2.5-pro"

**Key behavior:**
- `SummaryService` resolves admin default on init, storing in `self.model_name`
- `generate_university_notes()` resolves admin default at function entry
- Both fall back to `LLM_SUMMARIZATION_MODEL` env default when Redis unavailable

## Verification Results

| Check | Status |
|-------|--------|
| Gatekeeper imports clean | PASS |
| NOTES service imports clean | PASS |
| Both settings routers accept summarization | PASS |
| No hardcoded "gemini-2.5-flash-lite" in gatekeeper resolution | PASS (env fallback only) |
| No hardcoded "gemini-2.5-pro" in summarizer resolution | PASS |

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

All modified files exist and contain expected changes:
- `AURA-CHAT/backend/llm_gatekeeper.py` — `get_default_sync.*gatekeeper` pattern found
- `AURA-CHAT/server/routers/settings.py` — `summarization` in ALLOWED_USE_CASES
- `AURA-NOTES-MANAGER/api/routers/settings.py` — `summarization` in ALLOWED_USE_CASES
- `AURA-NOTES-MANAGER/services/summary_service.py` — `get_default_sync.*summarization` pattern found
- `AURA-NOTES-MANAGER/services/summarizer.py` — `get_default_sync.*summarization` pattern found
