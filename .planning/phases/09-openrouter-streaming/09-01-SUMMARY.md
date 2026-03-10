---
phase: 09-openrouter-streaming
plan: 01
subsystem: infra
tags: [python, openrouter, openai-sdk, model-router, streaming]

requires:
  - phase: 08-02
    provides: shared router runtime, provider contracts, Vertex AI provider,
      and repo-root package exports
provides:
  - OpenRouter config and optional dependency wiring for the shared package
  - OpenRouterProvider with test-mode generation, streaming, model listing,
    health checks, and credit balance support
  - ModelRouter auto-registration for OpenRouter in test mode or when an API
    key is configured
  - Shared package exports and tests covering OpenRouter behavior and router
    resolution
affects: [09-02, model-router, openrouter, streaming]

tech-stack:
  added: [openai>=1.51.0]
  patterns:
    - lazy optional SDK initialization for OpenRouter access
    - OpenRouter REST endpoint split for models/auth metadata vs chat
    - curated OpenRouter model allowlist for shared package discovery

key-files:
  created:
    - shared/model_router/src/model_router/providers/openrouter.py
    - shared/model_router/tests/test_openrouter_provider.py
  modified:
    - shared/model_router/src/model_router/config.py
    - shared/model_router/src/model_router/router.py
    - shared/model_router/src/model_router/__init__.py
    - shared/model_router/pyproject.toml
    - shared/model_router/tests/test_router.py

key-decisions:
  - OpenRouter keeps the openai SDK import lazy so test mode and non-OpenRouter
    installs do not fail at import time.
  - OpenRouter model listing and credit-balance checks use direct REST calls
    while generation and streaming use the OpenAI-compatible client.
  - ModelRouter auto-registers OpenRouter whenever test mode is enabled or an
    API key is configured so slash-form model IDs resolve cleanly.

patterns-established:
  - Provider modules may combine an SDK for core generation with plain httpx
    calls for provider-specific metadata endpoints.
  - Shared router regression tests must align with provider auto-registration
    behavior in test mode.

duration: 6 min
completed: 2026-03-10
---

# Phase 9 Plan 01: OpenRouter Provider Core Summary

**OpenRouter provider support with test-mode generation, normalized streaming chunks, curated model discovery, credit checks, and router auto-registration in the shared model_router package.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-10T12:30:10Z
- **Completed:** 2026-03-10T12:36:10Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Added `OpenRouterConfig` plus package dependency wiring for the shared router.
- Implemented `OpenRouterProvider` with deterministic test-mode responses,
  lazy SDK loading, unified error mapping, curated model listing, and
  OpenRouter-specific credit/health helpers.
- Extended `ModelRouter` and the public package API so OpenRouter registers
  automatically in test mode and is importable from the repo root.
- Expanded shared-package coverage to 90 passing tests with a dedicated
  OpenRouter provider suite.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add OpenRouterConfig and optional dependency** - `e9465f0` (feat)
2. **Task 2: OpenRouter provider RED phase** - `5b7b072` (test)
3. **Task 2: OpenRouter provider GREEN phase** - `dca2166` (feat)

**Plan metadata:** Added in the final docs commit that records this summary,
STATE, ROADMAP, and requirements/state updates.

_Note: This TDD task completed with RED and GREEN commits; no separate refactor commit was needed._

## Files Created/Modified
- `shared/model_router/src/model_router/config.py` - Adds `OpenRouterConfig`
  and wires it into `RouterConfig.from_env()`.
- `shared/model_router/pyproject.toml` - Declares the `openrouter` optional
  dependency and updates the `all` extras bundle.
- `shared/model_router/src/model_router/providers/openrouter.py` - Implements
  the OpenRouter provider, request translation, streaming normalization,
  error mapping, model listing, health checks, and credit balance lookup.
- `shared/model_router/src/model_router/router.py` - Auto-registers the
  OpenRouter provider when test mode is enabled or an API key is present.
- `shared/model_router/src/model_router/__init__.py` - Re-exports
  `OpenRouterConfig` and `OpenRouterProvider` from the package root.
- `shared/model_router/tests/test_openrouter_provider.py` - Covers provider
  test-mode behavior, package exports, router auto-registration, and error
  mapping without requiring the openai SDK.
- `shared/model_router/tests/test_router.py` - Updates slash-model routing
  expectations to reflect OpenRouter auto-registration in test mode.

## Decisions Made
- Kept `openai` imports lazy inside `openrouter.py` so test mode and installs
  without the optional OpenRouter extra remain safe.
- Used OpenAI-compatible client calls for chat generation/streaming but plain
  REST requests for `/models` and `/auth/key`, matching OpenRouter's API split.
- Returned a curated allowlist of OpenRouter models in test mode so the shared
  package exposes stable families first instead of the full firehose.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated router regression expectation for slash-form models**
- **Found during:** Task 2 verification
- **Issue:** `tests/test_router.py` still expected slash-form OpenRouter model
  IDs to raise `ModelUnavailableError` in test mode.
- **Fix:** Updated the regression test to assert that `ModelRouter` now
  resolves those models to the auto-registered `OpenRouterProvider`.
- **Files modified:** `shared/model_router/tests/test_router.py`
- **Verification:** `../../.venv/Scripts/python.exe -m pytest tests/ -v`
- **Committed in:** `dca2166` (part of Task 2 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** The auto-fix aligned an existing regression test with the
new plan-mandated router behavior. No scope creep.

## Issues Encountered
- A pre-existing router regression test assumed OpenRouter remained
  unavailable in test mode. The full suite caught it immediately, and the
  expectation was updated to the new auto-registration behavior.
- Long PowerShell verification output was truncated by the editor transport, so
  the captured result files were read directly to confirm the final suite pass.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `09-02` can now validate cross-provider streaming normalization and thinking
  config translation on top of a working OpenRouter provider.
- Repo-root imports and test-mode bootstrap checks prove the shared package can
  expose OpenRouter symbols to both AURA applications.
- The shared router now supports OpenRouter model resolution, so downstream app
  migration work can rely on slash-form model IDs without custom bootstrapping.

---
*Phase: 09-openrouter-streaming*
*Completed: 2026-03-10*

## Self-Check: PASSED

- Verified summary, state, roadmap, and requirements files exist on disk.
- Verified task commits `e9465f0`, `5b7b072`, and `dca2166` exist in git history.
