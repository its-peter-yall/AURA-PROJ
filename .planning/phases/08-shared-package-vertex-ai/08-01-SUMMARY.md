---
phase: 08-shared-package-vertex-ai
plan: 01
subsystem: infra
tags: [python, pydantic, hatchling, pytest, vertex-ai, model-router]

requires: []
provides:
  - Installable `aura-model-router` shared package scaffold
  - Shared Pydantic request/response contracts and provider enum
  - Unified router error hierarchy with preserved exception causes
  - Provider ABCs with centralized 768-dimension embedding validation
  - Unit tests for types, config, errors, and embedding contracts
affects: [08-02, 08-03, model-router, vertex-ai]

tech-stack:
  added: [hatchling, pydantic, pytest, pytest-asyncio]
  patterns:
    - editable shared Python package
    - Pydantic contract models
    - centralized embedding dimension validation

key-files:
  created:
    - shared/model_router/pyproject.toml
    - shared/model_router/src/model_router/types.py
    - shared/model_router/src/model_router/errors.py
    - shared/model_router/src/model_router/config.py
    - shared/model_router/src/model_router/providers/base.py
    - shared/model_router/tests/test_types.py
    - shared/model_router/tests/test_errors.py
  modified:
    - .gitignore
    - .planning/codebase/STRUCTURE.md
    - .planning/codebase/STACK.md
    - .planning/codebase/CONVENTIONS.md
    - .planning/phases/08-shared-package-vertex-ai/08-01-SUMMARY.md
    - .planning/STATE.md
    - .planning/ROADMAP.md

key-decisions:
  - Use a hatchling-backed editable package at `shared/model_router` so both apps and workers can import one shared contract surface.
  - Normalize Vertex AI config by preferring `VERTEX_REGION`, then falling back to `VERTEX_LOCATION`, then `global`.
  - Enforce the 768-dimension embedding contract in `BaseEmbeddingProvider` instead of repeating validation in provider implementations.

patterns-established:
  - Public package API is re-exported from `model_router.__init__` rather than importing module internals from app code.
  - Embedding providers implement `_embed_raw()` while the base class owns validation and `embed_single()` convenience behavior.

duration: 18 min
completed: 2026-03-10
---

# Phase 8 Plan 01: Package Foundation Summary

**Installable `aura-model-router` package with shared Pydantic contracts, unified provider errors, and 768-dimension embedding validation for downstream providers.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-03-10T07:50:26Z
- **Completed:** 2026-03-10T08:08:26Z
- **Tasks:** 2
- **Files modified:** 19

## Accomplishments
- Created the shared `shared/model_router/` package with hatchling packaging and a stable public API surface.
- Added normalized request/response types, env-backed config models, and a typed router error hierarchy with `__cause__` preservation.
- Added provider ABC contracts plus test coverage for validation, config fallback chains, error behavior, and embedding dimension enforcement.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create shared package structure with types, errors, config, and provider ABCs** - `7b4136d` (feat)
2. **Task 2: Create unit tests for types validation and error hierarchy** - `d765203` (test)

**Plan metadata:** Added in the final docs commit that records this summary, STATE, and ROADMAP updates.

## Files Created/Modified
- `shared/model_router/pyproject.toml` - Editable package metadata, dependencies, and pytest settings.
- `shared/model_router/src/model_router/__init__.py` - Public package exports and version.
- `shared/model_router/src/model_router/types.py` - Shared Pydantic request/response models and provider enum.
- `shared/model_router/src/model_router/errors.py` - Unified error hierarchy with typed subclasses and `__cause__` chaining.
- `shared/model_router/src/model_router/config.py` - Vertex AI and router config with env fallback behavior.
- `shared/model_router/src/model_router/providers/base.py` - Generation and embedding ABC contracts with 768-dimension validation.
- `shared/model_router/tests/test_types.py` - Validation coverage for models, enums, and env-backed config.
- `shared/model_router/tests/test_errors.py` - Error hierarchy and embedding base-class contract coverage.
- `.gitignore` - Explicitly unignored `shared/model_router/tests/conftest.py` so the required test fixture can be committed.
- `.planning/codebase/STRUCTURE.md`, `.planning/codebase/STACK.md`, `.planning/codebase/CONVENTIONS.md` - Updated the generated codebase map for the new shared package location, packaging, and cross-app usage pattern.

## Decisions Made
- Used an editable shared Python package rather than app-local imports so both apps can adopt the same contracts safely.
- Kept `VERTEX_REGION` as the canonical env var while supporting `VERTEX_LOCATION` for compatibility with existing app configuration.
- Centralized embedding vector length enforcement in the base embedding provider to protect the existing 768-dimension indices.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Unignored the shared test fixture**
- **Found during:** Task 2 (Create unit tests for types validation and error hierarchy)
- **Issue:** Root `.gitignore` ignored every `conftest.py`, which prevented the plan-required `shared/model_router/tests/conftest.py` fixture from being committed.
- **Fix:** Added a targeted `!shared/model_router/tests/conftest.py` exception to `.gitignore`.
- **Files modified:** `.gitignore`
- **Verification:** `git status --short --untracked-files=all -- shared/model_router .gitignore` showed the fixture as stageable, and the package tests still passed.
- **Committed in:** `d765203`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The deviation was required to make the planned test fixture commit-ready. No scope creep and no behavior change to the package itself.

## Issues Encountered
- An initial PowerShell test rerun used a relative venv path after `Push-Location` and failed to locate the interpreter. Re-running with the resolved absolute venv path completed successfully.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `08-02` can build on an installable shared package with public exports already verified from the repo root.
- The shared contract surface, config fallback chain, and embedding-dimension guardrails are now covered by 31 passing unit tests.
- No blockers remain for the Vertex AI provider and ModelRouter core work.

---
*Phase: 08-shared-package-vertex-ai*
*Completed: 2026-03-10*
