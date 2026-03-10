---
phase: 10-cross-app-migration-backend-integration
plan: 05
subsystem: testing
tags: [model-router, vertex-ai, audit, arq, aura-chat, aura-notes-manager]

# Dependency graph
requires:
  - phase: 10-cross-app-migration-backend-integration
    provides: AURA-CHAT model-router façade migration from 10-03
  - phase: 10-cross-app-migration-backend-integration
    provides: Cross-app no-direct-imports audit baseline from 10-04
provides:
  - AURA-CHAT live thinking test rewritten to use router-backed access instead of direct SDK imports
  - Cross-app forbidden-import audit coverage for Python test files
  - ARQ worker import-context verification for AURA-CHAT alongside NOTES Celery coverage
affects: [10-06-gap-closure, 11-frontend-settings-model-ui, 13-polish-integration-testing]

# Tech tracking
tech-stack:
  added: []
  patterns: [router-backed live verification scripts, AST forbidden-import audit covering worker contexts and test directories]

key-files:
  created: []
  modified: [AURA-CHAT/backend/tests/test_thinking_mode_genai_sdk.py, tests/test_no_direct_imports.py]

key-decisions:
  - "Keep the live thinking verification end-to-end, but drive it through model_router generate/stream calls while retaining the legacy façade import surface for compatibility visibility."
  - "Extend the forbidden-import audit to scan dedicated test directories and verify the AURA-CHAT ARQ worker import chain in subprocess context."

patterns-established:
  - "Migration verification pattern: live provider checks should use router-backed façade surfaces, never direct SDK imports."
  - "Compliance audit pattern: scan both application and test Python files, then pair static import checks with worker-context subprocess imports."

# Metrics
duration: 8 min
completed: 2026-03-10
---

# Phase 10 Plan 05: Test import cleanup and ARQ audit closure Summary

**AURA-CHAT's live thinking-mode check now uses router-backed generation paths, and the cross-app forbidden-import audit covers test files plus ARQ worker import contexts.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-10T17:28:31Z
- **Completed:** 2026-03-10T17:37:03Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Rewrote the AURA-CHAT live thinking test so it no longer imports `google.genai` directly and still prints thinking/content output for manual verification.
- Expanded the root compliance audit to scan chat and notes test directories for forbidden provider SDK imports.
- Added AURA-CHAT ARQ worker subprocess verification so both background-worker paths now prove model-router-backed imports.

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite thinking mode test to use model_router façade** - `b52d1f8` (fix)
2. **Task 2: Expand no-direct-imports audit to cover test files + ARQ worker context** - `5e45f4d` (feat)

**Plan metadata:** pending root planning metadata commit

## Files Created/Modified
- `AURA-CHAT/backend/tests/test_thinking_mode_genai_sdk.py` - Live integration script now verifies thinking mode through router-backed generate and stream calls instead of direct SDK imports.
- `tests/test_no_direct_imports.py` - Cross-app AST audit now scans test files and verifies NOTES Celery plus CHAT ARQ worker import contexts.

## Decisions Made
- Kept the live thinking verification script end-to-end and credential-driven, but routed it through shared router APIs so the no-direct-import contract also applies to verification code.
- Added a dedicated ARQ worker import-context test instead of overloading the Celery check, because AURA-CHAT's background processing uses ARQ rather than Celery.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Verification gaps 1 and 4 are closed with automated regression coverage.
- Phase 10 gap closure can proceed to Plan 10-06 for cache TTL and provider-aware key validation work.

## Self-Check: PASSED

- Verified summary file exists on disk.
- Verified task commit `b52d1f8` exists in the nested `AURA-CHAT` repository.
- Verified task commit `5e45f4d` exists in the root repository.
- Verified key modified files exist: `AURA-CHAT/backend/tests/test_thinking_mode_genai_sdk.py` and `tests/test_no_direct_imports.py`.
