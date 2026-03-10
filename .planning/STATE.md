---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Multi-Provider LLM Architecture
status: active
last_updated: "2026-03-10T08:27:18Z"
last_activity: "2026-03-10 - Completed Phase 8 Plan 02 (Vertex AI provider, ModelRouter core, 59 tests passing)"
progress:
  total_phases: 6
  completed_phases: 0
  total_plans: 3
  completed_plans: 2
---

# Project State

## Project Reference

See: [PROJECT.md](./PROJECT.md) (updated 2026-03-10)

**Core value:** Module-centric learning with persistent study sessions and multi-provider LLM access
**Current focus:** Phase 8 -- Shared Package Foundation + Vertex AI Migration

## Current Position

Phase: 8 of 13 (Shared Package Foundation + Vertex AI Migration)
Plan: 3 of 3 (08-03 next)
Status: In progress
Last activity: 2026-03-10 -- Completed 08-02 Vertex AI provider and ModelRouter core

Progress: [███████░░░] 67%

## Performance Metrics

**Velocity:**
- Total plans completed: 2
- Average duration: 18 min
- Total execution time: 0.6 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 08 | 2 | 36 min | 18 min |

*Updated after each plan completion*

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

### Pending Todos

- Phase 08 Plan 03: add compatibility shims and zero-regression verification in both apps.

### Blockers/Concerns

- [Phase 8]: Compatibility shim rollout in 08-03 must preserve behavior across the new shared google-genai wrapper and the legacy Notes SDK surface.
- [Phase 8]: Celery worker editable-install import resolution still needs verification during compatibility shim rollout.

## Session Continuity

Last session: 2026-03-10
Stopped at: Completed 08-02-PLAN.md (Vertex AI provider and ModelRouter core)
Resume file: .planning/phases/08-shared-package-vertex-ai/08-03-PLAN.md

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 1 | Replace DOM confirm dialog with UI theme dialog for user deletion in User Management | 2026-02-23 | 7cb43a1 | [1-replace-dom-confirm-dialog-with-ui-theme](./quick/1-replace-dom-confirm-dialog-with-ui-theme/) |
| 7 | Update AGENTS.md, CLAUDE.md, and GEMINI.md to reflect current codebase | 2026-03-06 | 2e57d3a | [7-update-agents-md-claude-md-and-gemini-md](./quick/7-update-agents-md-claude-md-and-gemini-md/) |
