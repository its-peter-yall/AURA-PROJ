---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Multi-Provider LLM Architecture
status: active
last_updated: "2026-03-10T17:56:17Z"
last_activity: "2026-03-10 - Re-verified Phase 10 after plans 10-05 and 10-06; one direct Vertex REST bypass remains in AURA-CHAT/test_real_models.py"
progress:
  total_phases: 6
  completed_phases: 1
  total_plans: 12
  completed_plans: 11
---

# Project State

## Project Reference

See: [PROJECT.md](./PROJECT.md) (updated 2026-03-10)

**Core value:** Module-centric learning with persistent study sessions and multi-provider LLM access
**Current focus:** Phase 10 follow-up gap closure -- one direct Vertex REST bypass still blocks the router-only goal before Phase 11 can begin

## Current Position

Phase: 11 of 13 (Frontend Provider Settings)
Plan: 2 of 4 complete (11-02 done)
Status: Active
Last activity: 2026-03-11 - Completed Plan 11-02 (Admin Settings UI)

Progress: [█████████░] 94%

## Performance Metrics

**Velocity:**
- Total plans completed: 11
- Average duration: 11 min
- Total execution time: 126 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 08 | 2 | 36 min | 18 min |
| 09 | 3 | 10 min | 3 min |
| 10 | 6 | 80 min | 13 min |

*Updated after each plan completion*
| Phase 09 P02 | 2 min | 2 tasks | 3 files |
| Phase 09 P03 | 2 min | 2 tasks | 4 files |
| Phase 10 P01 | 10 min | 2 tasks | 9 files |
| Phase 10 P03 | 21 min | 2 tasks | 3 files |
| Phase 10 P02 | 10 min | 3 tasks | 9 files |
| Phase 10 P04 | 17 min | 2 tasks | 5 files |
| Phase 10-cross-app-migration-backend-integration P05 | 8 min | 2 tasks | 2 files |
| Phase 10-cross-app-migration-backend-integration P06 | 14 min | 2 tasks | 5 files |
| Phase 11 P02 | 6m | 2 tasks | 7 files |

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
- [Phase 10]: Use constructor-injected async Redis clients in shared config helpers
- [Phase 10]: Fail fast when AURA_MASTER_KEY is missing for API key encryption
- [Phase 10]: Serialize cached ModelInfo payloads with model_dump(mode='json') for Redis round-trips
- [Phase 10]: Preserve AURA-CHAT's existing vertex_ai_client import surface by exposing model_router-backed compatibility shims instead of changing consumer imports.
- [Phase 10]: Keep batching, rate limiting, and retry orchestration inside AURA-CHAT's EmbeddingService while delegating single-batch embedding execution to router.embed().
- [Phase 10]: Validate OpenRouter API keys with a temporary OpenRouterProvider health check and report unsupported providers as unvalidated.
- [Phase 10]: Serve aggregate settings model discovery via ModelCache fan-out so all model listing endpoints share identical cache semantics and dependency overrides.
- [Phase 10]: Preserve AURA-NOTES-MANAGER consumer imports by rewriting the service hub files as router-backed façades instead of editing downstream modules.
- [Phase 10]: Use AST-based forbidden-import scanning so regression tests catch real imports without flagging string literals in verification scripts.
- [Phase 10]: Compliance verification must also catch direct provider HTTP bypasses, not just SDK imports, because router-only guarantees can still be violated by standalone live scripts.
- [Phase 10-cross-app-migration-backend-integration]: Keep the live thinking verification end-to-end, but drive it through model_router generate/stream calls while retaining the legacy façade import surface for compatibility visibility.
- [Phase 10-cross-app-migration-backend-integration]: Extend the forbidden-import audit to scan dedicated test directories and verify the AURA-CHAT ARQ worker import chain in subprocess context.
- [Phase 10-cross-app-migration-backend-integration]: Read MODEL_CACHE_TTL_SECONDS in each settings router, but enforce the 300-3600 second contract centrally inside shared ModelCache helpers.
- [Phase 10-cross-app-migration-backend-integration]: Return validation metadata and JSON null for Ollama so the admin API distinguishes not-applicable validation from an actual failed credential check.
- [Phase 11]: Search filtering for model picker hides empty providers to keep UI clean
- [Phase 11]: Model picker uses auto-expansion during search while preserving user state during normal browsing
- [Phase 11]: CSS variable-based indentation enables clean multi-level hierarchy rendering in model items

### Pending Todos

- Phase 10 follow-up: migrate or remove `AURA-CHAT/test_real_models.py` and extend the compliance audit to catch direct provider HTTP bypasses.
- Phase 08 Plan 03: close the outstanding cross-app regression validation and nested-repo docs/state follow-up.

### Blockers/Concerns

- [Phase 8]: Compatibility shim rollout in 08-03 must preserve behavior across the new shared google-genai wrapper and the legacy Notes SDK surface.
- [Phase 8]: Celery worker editable-install import resolution still needs verification during compatibility shim rollout.
- [Phase 8]: `08-03-SUMMARY.md` is present on disk but still documents validation-open status, so the phase is not yet fully closed.
- [Phase 9]: Live OpenRouter reasoning-field behavior (`reasoning_content` vs fallback fields) still needs end-to-end validation in a later integration phase.
- [Phase 10]: `AURA-CHAT/test_real_models.py` still builds direct Vertex AI REST `generateContent` requests, so Phase 10 needs another gap-closure cycle before Phase 11 work starts.

## Session Continuity

Last session: 2026-03-10
Stopped at: Re-verified Phase 10 gap closure; found remaining direct Vertex REST bypass in `AURA-CHAT/test_real_models.py`
Resume file: None
Next action: Run `/gsd-plan-phase 10 --gaps` to create the follow-up gap-closure plan

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 1 | Replace DOM confirm dialog with UI theme dialog for user deletion in User Management | 2026-02-23 | 7cb43a1 | [1-replace-dom-confirm-dialog-with-ui-theme](./quick/1-replace-dom-confirm-dialog-with-ui-theme/) |
| 7 | Update AGENTS.md, CLAUDE.md, and GEMINI.md to reflect current codebase | 2026-03-06 | 2e57d3a | [7-update-agents-md-claude-md-and-gemini-md](./quick/7-update-agents-md-claude-md-and-gemini-md/) |
| 8 | Fix shared model-router invalid metadata provider handling and OpenRouter metadata HTTP classification | 2026-03-10 | 7dff94d | [8-fix-model-router-invalid-provider-handli](./quick/8-fix-model-router-invalid-provider-handli/) |
