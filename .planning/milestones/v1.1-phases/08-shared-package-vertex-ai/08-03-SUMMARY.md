---
phase: 08-shared-package-vertex-ai
plan: 03
subsystem: integration
tags: [python, vertex-ai, model-router, compatibility-shims, pytest]

requires:
  - phase: 08-01
    provides: shared package contracts, config models, and provider base classes
  - phase: 08-02
    provides: Vertex AI providers, router runtime, and shared package exports
provides:
  - Vertex-compatible adapter that routes legacy generate_content() calls through
    the shared ModelRouter
  - Additive USE_MODEL_ROUTER shims in both app-local vertex_ai_client modules
  - Import-context verification from repo root, AURA-CHAT, AURA-NOTES-MANAGER,
    and AURA-NOTES-MANAGER/api
  - Shared compat coverage for response shape, generation config passthrough,
    and test-mode behavior
affects: [aura-chat, aura-notes-manager, strangler-fig, model-router]

tech-stack:
  added: []
  patterns:
    - additive feature-flag shims in legacy model loaders
    - synchronous compat wrapper over async shared router calls
    - multi-context import verification for editable shared package usage

key-files:
  created:
    - shared/model_router/src/model_router/compat.py
    - shared/model_router/tests/test_compat.py
    - shared/model_router/tests/test_import_contexts.py
    - .planning/phases/08-shared-package-vertex-ai/08-03-SUMMARY.md
  modified:
    - shared/model_router/src/model_router/__init__.py
    - AURA-CHAT/backend/utils/vertex_ai_client.py
    - AURA-NOTES-MANAGER/services/vertex_ai_client.py

key-decisions:
  - Keep the Strangler Fig shim additive-only by inserting USE_MODEL_ROUTER
    handling inside each app's existing get_model() path.
  - Default USE_MODEL_ROUTER to off so both apps preserve original behavior until
    callers opt into the shared router.
  - Preserve the legacy Vertex response shape by returning compat objects with
    both .text and .candidates[].content.parts[].text access patterns.

patterns-established:
  - Shared compatibility code lives in model_router.compat rather than being
    duplicated inside each app.
  - Import-context tests verify that the editable shared package works from all
    execution roots used by the monorepo.

status: implementation-complete-validation-open
completed: 2026-03-10
---

# Phase 8 Plan 03: Compatibility Shims + Validation Summary

**Shared Vertex compatibility layer and additive `USE_MODEL_ROUTER` shims are in
place for both apps, with shared compat/import verification passing and the final
full-suite regression gate still open when execution paused.**

## Status

- **Implementation:** Complete
- **Shared-package verification:** Passed
- **Cross-app regression verification:** Incomplete at summary time
- **Reason open:** Full AURA-CHAT and AURA-NOTES-MANAGER reruns exposed
  additional unrelated test maintenance issues; debugging was paused before a
  final green rerun completed.

## Accomplishments

- Added `VertexCompatModel` plus response-shape helpers in
  `shared/model_router/src/model_router/compat.py` so legacy
  `generate_content()` callers can delegate through `ModelRouter.generate()`
  without changing their call sites.
- Exported the compat adapter from `model_router.__init__` for stable shared
  imports.
- Added additive-only `USE_MODEL_ROUTER` shims in:
  - `AURA-CHAT/backend/utils/vertex_ai_client.py`
  - `AURA-NOTES-MANAGER/services/vertex_ai_client.py`
- Added shared tests covering compat behavior and import-context verification.
- Verified the editable package import surface from:
  - repo root
  - `AURA-CHAT`
  - `AURA-NOTES-MANAGER`
  - `AURA-NOTES-MANAGER/api`

## Task Commits

Implementation landed as atomic commits:

1. **Task 1: compat shim RED phase** - `6394a1a` (root test)
2. **Task 1: compat adapter GREEN phase** - `e8ee23d` (root feat)
3. **Task 2: import-context verification** - `a533c3b` (root test)
4. **Task 1: AURA-CHAT shim integration** - `051c90d` (`AURA-CHAT`, feat)
5. **Task 1: AURA-NOTES-MANAGER shim integration** - `8a759ea`
   (`AURA-NOTES-MANAGER`, feat)

_Note: Final docs/state commit was deferred because the regression gate had not
been fully closed when this summary was written._

## Files Created/Modified

- `shared/model_router/src/model_router/compat.py` - Sync compat bridge from
  legacy `generate_content()` callers to the shared async router.
- `shared/model_router/src/model_router/__init__.py` - Public export for
  `VertexCompatModel`.
- `shared/model_router/tests/test_compat.py` - Compat response-shape and
  config-handling coverage.
- `shared/model_router/tests/test_import_contexts.py` - Multi-directory import
  verification.
- `AURA-CHAT/backend/utils/vertex_ai_client.py` - Additive
  `USE_MODEL_ROUTER` shim inside `get_model()`.
- `AURA-NOTES-MANAGER/services/vertex_ai_client.py` - Additive
  `USE_MODEL_ROUTER` shim inside `get_model()`.

## Verification Completed

- `shared/model_router/tests/test_compat.py` - **11 passed**
- `shared/model_router/tests/test_import_contexts.py` - **5 passed**
- `shared/model_router` full suite - **75 passed**
- Repo-root import/runtime checks for the shared package and router delegation
  succeeded during execution.

## Deviations from Plan

### Validation spillover beyond shim implementation

The planned zero-regression gate exposed additional unrelated or stale test
issues outside the compat/shim implementation itself. Investigation and partial
cleanup began, but the final all-suite rerun had not been completed when this
summary was requested.

Observed cleanup areas included:

- AURA-NOTES-MANAGER dotenv override behavior affecting auth tests
- AURA-CHAT suite-level environment mutation affecting API startup tests
- stale tests still targeting retired SDK seams or older model-name
  expectations
- follow-on test maintenance surfaced only by full-suite reruns

**Impact on plan:** The compat and shim work itself was implemented as planned,
but final closure of the regression gate remained open.

## Issues Encountered

- The regression-validation requirement for both apps surfaced multiple hidden
  test-environment and stale-test issues that were not directly caused by the
  `USE_MODEL_ROUTER` shims.
- Because Phase 08 uses nested git repositories for both apps, final closeout
  also requires nested-repo commits plus a root gitlink update after regression
  validation is complete.

## User Setup Required

None for the shim implementation itself.

## Next Phase Readiness

- The shared compatibility layer is ready for controlled opt-in use through
  `USE_MODEL_ROUTER=true`.
- Both apps still preserve original behavior by default with
  `USE_MODEL_ROUTER` unset or false.
- To fully close `08-03`, the remaining work is:
  - rerun full AURA-CHAT and AURA-NOTES-MANAGER suites to green
  - commit any remaining regression-cleanup changes in nested repos
  - update `.planning/STATE.md` and any final roadmap/status tracking

---
*Phase: 08-shared-package-vertex-ai*
*Summary written: 2026-03-10*
