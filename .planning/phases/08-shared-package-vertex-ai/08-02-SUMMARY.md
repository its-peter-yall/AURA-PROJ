---
phase: 08-shared-package-vertex-ai
plan: 02
subsystem: infra
tags: [python, vertex-ai, google-genai, model-router, pytest]

requires:
  - phase: 08-01
    provides: shared package contracts, config models, base providers, and
      error hierarchy
provides:
  - Vertex AI generation and embedding providers for the shared package
  - ModelRouter runtime with provider routing, delegation, and singleton access
  - Shared package exports for router entry points from the repo root
  - 28 new shared-package tests covering provider behavior and routing
affects: [08-03, model-router, vertex-ai, compatibility-shims]

tech-stack:
  added: []
  patterns:
    - lazy Vertex AI client initialization
    - model-name-based provider routing
    - deployment-wide embedding-provider lock

key-files:
  created:
    - shared/model_router/src/model_router/providers/vertex_ai.py
    - shared/model_router/src/model_router/router.py
    - shared/model_router/tests/test_vertex_ai_provider.py
    - shared/model_router/tests/test_router.py
  modified:
    - shared/model_router/src/model_router/__init__.py
    - .planning/codebase/STRUCTURE.md
    - .planning/phases/08-shared-package-vertex-ai/08-02-SUMMARY.md
    - .planning/STATE.md
    - .planning/ROADMAP.md

key-decisions:
  - Vertex AI generation uses a lazy google-genai client so test mode never
    touches GCP auth.
  - Vertex embeddings follow the AURA-CHAT REST endpoint pattern while the
    router rejects runtime switches away from Vertex AI.
  - ModelRouter only auto-registers Vertex providers when test mode is enabled
    or a Vertex project is configured.

patterns-established:
  - Provider modules expose deterministic test-mode behavior without importing
    live SDK clients at import time.
  - Router convenience methods accept kwargs, build shared request models, and
    resolve providers from explicit overrides or model-name shape.

duration: 18 min
completed: 2026-03-10
---

# Phase 8 Plan 02: Vertex AI Provider + ModelRouter Core Summary

**Vertex AI generation and embedding providers with a shared ModelRouter that
routes Gemini requests, enforces Vertex-only embeddings, and works from the
repo root in test mode.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-03-10T08:09:18Z
- **Completed:** 2026-03-10T08:27:18Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Added `VertexAIProvider` and `VertexAIEmbeddingProvider` with test-mode
  behavior, lazy real-mode wiring, and unified error mapping.
- Added `ModelRouter` with provider registration, model-name routing,
  embedding-provider guardrails, and repo-root singleton access.
- Expanded shared-package coverage from 31 to 59 passing tests with focused
  provider and router suites.

## Task Commits

Each task was committed atomically:

1. **Task 1: Vertex AI provider RED phase** - `ff19189` (test)
2. **Task 1: Vertex AI provider GREEN phase** - `9b7e8de` (feat)
3. **Task 2: ModelRouter RED phase** - `c679539` (test)
4. **Task 2: ModelRouter GREEN phase** - `2654779` (feat)

**Plan metadata:** Added in the final docs commit that records this summary,
STATE, ROADMAP, and codebase-map updates.

_Note: This TDD plan completed with RED and GREEN commits for both tasks; no
separate refactor commit was needed._

## Files Created/Modified
- `shared/model_router/src/model_router/providers/vertex_ai.py` - Vertex AI
  generation provider, embedding provider, stream normalization, and error
  mapping.
- `shared/model_router/src/model_router/router.py` - ModelRouter registry,
  provider resolution, convenience methods, and singleton helpers.
- `shared/model_router/src/model_router/__init__.py` - Public exports for
  router entry points.
- `shared/model_router/tests/test_vertex_ai_provider.py` - Test-mode provider
  coverage for generate, stream, embed, and error mapping behavior.
- `shared/model_router/tests/test_router.py` - Router delegation, routing,
  embedding restrictions, and singleton tests.
- `.planning/codebase/STRUCTURE.md` - Shared package key files updated to
  include the router runtime and Vertex AI provider modules.

## Decisions Made
- Used lazy google-genai client initialization inside `VertexAIProvider` so
  importing the shared package in test mode never triggers real auth.
- Kept embeddings on the Vertex-only path by letting `ModelRouter.embed()`
  reject non-Vertex provider overrides.
- Reused the AURA-CHAT REST-style embedding endpoint pattern for the shared
  embedding provider to avoid coupling the package to app-local modules.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- A combined PowerShell verification command intermittently returned no output,
  so the final pytest run and root import checks were rerun as separate
  commands. All verification steps still passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `08-03` can now replace app-local compatibility shims with calls into
  `ModelRouter` and the shared Vertex AI providers.
- Repo-root imports and test-mode runtime checks already prove the shared
  package can serve both apps from one install surface.
- OpenRouter-style model names already route to the OpenRouter slot and fail
  cleanly with `ModelUnavailableError` until the next provider phases arrive.

---
*Phase: 08-shared-package-vertex-ai*
*Completed: 2026-03-10*
