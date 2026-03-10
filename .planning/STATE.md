---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Multi-Provider LLM Architecture
status: active
last_updated: "2026-03-10T15:25:27Z"
last_activity: "2026-03-10 - Completed Quick Task 8 (shared router metadata invalid-provider handling + OpenRouter metadata HTTP error normalization, 50 focused tests passing)"
progress:
  total_phases: 6
  completed_phases: 1
  total_plans: 6
  completed_plans: 5
---

# Project State

## Project Reference

See: [PROJECT.md](./PROJECT.md) (updated 2026-03-10)

**Core value:** Module-centric learning with persistent study sessions and multi-provider LLM access
**Current focus:** Phase 9 closed -- OpenRouter Provider + Streaming Normalization

## Current Position

Phase: 9 of 13 (OpenRouter Provider + Streaming Normalization)
Plan: 3 of 3 complete (09-03 done)
Status: Phase complete
Last activity: 2026-03-10 -- Completed 09-03 router metadata and Vertex thinking gap closure verification

Progress: [████████░░] 80%

## Performance Metrics

**Velocity:**
- Total plans completed: 5
- Average duration: 9 min
- Total execution time: 46 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 08 | 2 | 36 min | 18 min |
| 09 | 3 | 10 min | 3 min |

*Updated after each plan completion*
| Phase 09 P02 | 2 min | 2 tasks | 3 files |
| Phase 09 P03 | 2 min | 2 tasks | 4 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [v1.1 scoping]: Shared package at project root (`shared/model_router/`), not LiteLLM or LangChain
- [v1.1 scoping]: Vertex AI (full) + OpenRouter (full) + Ollama (stub only)
- [v1.1 scoping]: Hybrid UI (global settings page + inline contextual selectors)
- [v1.1 scoping]: Embeddings locked to Vertex AI per deployment (768-dim HNSW indices)
- [v1.1 scoping]: Frontend components built in AURA-CHAT first, copied to AURA-NOTES-MANAGER
- [Phase 08]: Use a hatchling-backed editable package at shared/model_router — Both AURA apps and background workers need one installable contract surface without sys.path hacks.
- [Phase 08]: Prefer VERTEX_REGION but fall back to VERTEX_LOCATION in shared config — The two apps already use different env var names, so the shared package must normalize them for a safe migration path.
- [Phase 08]: Enforce 768-dimension embeddings in BaseEmbeddingProvider — Central validation protects the existing Neo4j HNSW indices and keeps the invariant in one place.
- [Phase 08]: Use lazy google-genai client initialization in VertexAIProvider — The shared package must preserve AURA_TEST_MODE behavior and avoid touching GCP auth during imports or unit tests.
- [Phase 08]: Keep embeddings locked to Vertex AI at the router boundary — Embedding provider overrides must fail fast so the shared package protects the existing 768-dimension deployment assumptions.
- [Phase 08]: Reuse the REST embedding flow for shared Vertex embeddings — The REST path matches the AURA-CHAT implementation and keeps the shared package independent from app-local embedding helper modules.
- [Phase 09]: Keep OpenRouter's openai SDK import lazy inside the provider — test mode and non-OpenRouter installs must remain import-safe until the provider is actually used.
- [Phase 09]: Use OpenAI-compatible client calls for generation/streaming but direct REST calls for `/models` and `/auth/key` — OpenRouter metadata endpoints are outside the standard chat client surface.
- [Phase 09]: Auto-register OpenRouter whenever test mode is enabled or an API key is configured — slash-form model IDs should resolve cleanly without manual provider bootstrap.
- [Phase 09]: Validate cross-provider stream normalization with fake provider clients in tests — AURA_TEST_MODE returns canned streams, so deterministic fakes are needed to exercise provider-specific chunk normalization without network access.
- [Phase 09]: Keep OpenRouter thinking translation covered as a pure helper contract — Budget-to-effort mapping and graceful degradation are deterministic rules that should stay fast and SDK-independent in the shared package tests.
- [Phase 09]: Expose list_models() and health_check() on ModelRouter while keeping OpenRouter credit balance behind get_provider()
- [Phase 09]: Cover Gemini thinking parity with fake stream chunks and helper fixtures so regression tests remain offline
- [Quick 8]: Metadata-only provider coercion should raise ModelUnavailableError with the original invalid string instead of leaking enum ValueError exceptions from public router metadata APIs.
- [Quick 8]: OpenRouter `/models` and `/auth/key` metadata failures should classify 401/403 as AuthenticationError and 429 as RateLimitError, including Retry-After when available.

### Pending Todos

- Phase 08 Plan 03: close the outstanding cross-app regression validation and nested-repo docs/state follow-up.

### Blockers/Concerns

- [Phase 8]: Compatibility shim rollout in 08-03 must preserve behavior across the new shared google-genai wrapper and the legacy Notes SDK surface.
- [Phase 8]: Celery worker editable-install import resolution still needs verification during compatibility shim rollout.
- [Phase 8]: `08-03-SUMMARY.md` is present on disk but still documents validation-open status, so the phase is not yet fully closed.
- [Phase 9]: Live OpenRouter reasoning-field behavior (`reasoning_content` vs fallback fields) still needs end-to-end validation in a later integration phase.

## Session Continuity

Last session: 2026-03-10
Stopped at: Completed quick task 8
Resume file: .planning/phases/08-shared-package-vertex-ai/08-03-PLAN.md

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 1 | Replace DOM confirm dialog with UI theme dialog for user deletion in User Management | 2026-02-23 | 7cb43a1 | [1-replace-dom-confirm-dialog-with-ui-theme](./quick/1-replace-dom-confirm-dialog-with-ui-theme/) |
| 7 | Update AGENTS.md, CLAUDE.md, and GEMINI.md to reflect current codebase | 2026-03-06 | 2e57d3a | [7-update-agents-md-claude-md-and-gemini-md](./quick/7-update-agents-md-claude-md-and-gemini-md/) |
| 8 | Fix shared model-router invalid metadata provider handling and OpenRouter metadata HTTP classification | 2026-03-10 | 7dff94d | [8-fix-model-router-invalid-provider-handli](./quick/8-fix-model-router-invalid-provider-handli/) |
