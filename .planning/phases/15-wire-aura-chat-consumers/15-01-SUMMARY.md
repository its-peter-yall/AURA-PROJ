---
phase: 15-wire-aura-chat-consumers
plan: "01"
subsystem: infra
tags: [model-router, vertex-ai, openrouter, provider-propagation, json-mode]
requires:
  - phase: 14
    provides: config resolver and allowlist support
provides:
  - Provider-aware VertexCompatModel request building
  - Provider-aware get_model() shim in AURA-CHAT
  - OpenRouter JSON mode translation for structured output
tech-stack:
  added: []
  patterns: [explicit provider propagation, structured-output response_format mapping]
key-files:
  created: [".planning/phases/15-wire-aura-chat-consumers/15-01-SUMMARY.md"]
  modified: ["shared/model_router/src/model_router/compat.py", "shared/model_router/src/model_router/providers/openrouter.py", "AURA-CHAT/backend/utils/vertex_ai_client.py", "shared/model_router/tests/test_compat.py"]
key-decisions:
  - "Pass provider explicitly through the Vertex compatibility shim instead of relying on model-name heuristics."
  - "Translate OpenRouter JSON requests into response_format json_object to preserve structured-output behavior."
patterns-established:
  - "VertexCompatModel stores optional provider and forwards it into GenerateRequest kwargs."
  - "OpenRouterProvider maps application/json to OpenAI-style response_format for compatibility."
requirements-completed: [PP-02, PP-01]
duration: 0 min
completed: 2026-03-23
---

# Phase 15 Plan 01: Shared provider propagation and OpenRouter JSON mode

Provider metadata now flows through the compatibility layer so AURA-CHAT can select explicit providers without falling back to model-name heuristics, and OpenRouter can satisfy structured-output calls with JSON mode.

## Performance

- **Duration:** 0 min
- **Started:** 2026-03-23T07:25:00Z
- **Completed:** 2026-03-23T07:32:43Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added optional `provider` support to `VertexCompatModel` and `get_model()`.
- Forwarded explicit provider values into router request kwargs.
- Added OpenRouter `response_mime_type: application/json` mapping to `response_format: {type: json_object}`.
- Kept the shared model_router test suite green after the shim signature change.

## Task Commits

1. **Task 1: Add provider propagation to VertexCompatModel and get_model()** - `1e6351e` (feat)
2. **Task 2: Add OpenRouter JSON mode translation** - `278b802` (fix)

**Plan metadata:** included in this summary update.

## Files Created/Modified
- `.planning/phases/15-wire-aura-chat-consumers/15-01-SUMMARY.md` - execution summary for the plan
- `shared/model_router/src/model_router/compat.py` - provider-aware request construction
- `AURA-CHAT/backend/utils/vertex_ai_client.py` - provider-aware get_model() shim
- `shared/model_router/src/model_router/providers/openrouter.py` - JSON mode translation
- `shared/model_router/tests/test_compat.py` - updated shim test double signature

## Decisions Made
- Explicit provider propagation is preferred over heuristic detection for reliability.
- OpenRouter JSON mode should be translated in the provider layer, not at call sites, so structured-output use cases remain consistent.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- The root repo and `AURA-CHAT` are nested git repositories, so the AURA-CHAT change was validated in the submodule and then left as a submodule pointer update at the root.
- Existing LSP diagnostics in `vertex_ai_client.py` and `openrouter.py` reported pre-existing import/type-annotation issues unrelated to this change.

## Next Phase Readiness
- Wave 1 infrastructure is ready for the consumer wiring in Phase 15-02 and 15-03.
- Explicit provider plumbing is now available for gatekeeper and entity extraction wiring.

---
*Phase: 15-wire-aura-chat-consumers*
*Completed: 2026-03-23*
