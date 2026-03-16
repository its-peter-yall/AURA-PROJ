---
phase: 11-frontend-provider-settings-model-selection
plan: 03
subsystem: AURA-CHAT
tags: ["frontend", "ui", "model-selection", "session-persistence"]
dependency_graph:
  requires: ["11-01", "11-02"]
  provides: ["UI-02", "CONFIG-02"]
  affects: ["ChatPage", "utils"]
tech_stack:
  added: ["InlineModelPicker", "useModelStore integration"]
  patterns: ["Hierarchical model selection", "Session model persistence"]
key_files:
  created:
    - AURA-CHAT/client/src/features/chat/components/InlineModelPicker.tsx
    - AURA-CHAT/client/src/features/chat/components/InlineModelPicker.test.tsx
  modified:
    - AURA-CHAT/client/src/features/chat/ChatPage.tsx
    - AURA-CHAT/client/src/features/chat/ChatPage.test.tsx
    - AURA-CHAT/client/src/lib/utils.ts
decisions:
  - "Use InlineModelPicker as a compact replacement for the flat Dropdown in the chat input bar"
  - "Persist model selection per session ID in Zustand's useModelStore (sessionStorage)"
  - "Update formatModelLabel to handle API display_name and OpenRouter vendor prefixes"
metrics:
  duration: 15m
  completed_date: "2026-03-11"
---

# Phase 11 Plan 03: Compact Model Selection Summary

Successfully implemented the compact `InlineModelPicker` and integrated it into the `ChatPage`. This provides students with the ability to switch models mid-session while ensuring their selection is persisted to `sessionStorage` and restored when resuming the session.

## One-liner
Compact hierarchical model picker with session-bound persistence for the AURA-CHAT interface.

## Key Accomplishments

### 1. InlineModelPicker Component
- Built a compact, searchable, and hierarchical model picker that fits into the chat input controls bar.
- Reuses the `useGroupedModels` hook to display models grouped by provider (Vertex AI, OpenRouter, Ollama).
- Features a CPU icon trigger with truncation for long model names and a popover that opens above the button.

### 2. ChatPage Integration
- Replaced the legacy flat `Dropdown` with the new `InlineModelPicker`.
- Integrated `useModelStore` to persist the selected model per session ID.
- Updated `effectiveModel` derivation logic to prioritize manual selection -> persisted session model -> server default.

### 3. Utility Updates
- Enhanced `formatModelLabel` in `lib/utils.ts` to support optional `displayName` from the API.
- Added logic to strip the vendor prefix from OpenRouter model IDs (e.g., `openai/gpt-4o` -> `Gpt 4o`) before formatting.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed broken ChatPage.test.tsx**
- **Found during:** Task 2 verification
- **Issue:** The existing `ChatPage.test.tsx` was written for an older version of `ChatPage` that included the session sidebar. Since the sidebar was moved to `MainLayout.tsx`, the tests were failing to find "Sessions" and "Test Session 1".
- **Fix:** Updated the test to use `MemoryRouter` with a `sessionId` in the URL to activate the chat area, and removed/updated tests that were no longer applicable to the isolated `ChatPage` component.
- **Files modified:** `AURA-CHAT/client/src/features/chat/ChatPage.test.tsx`
- **Commit:** `ead9f64`

## Self-Check: PASSED
- [x] InlineModelPicker renders correctly (verified in isolation and integration tests)
- [x] Model selection persists to sessionStorage via useModelStore (verified in tests)
- [x] Resuming a session restores the previously selected model (verified in tests)
- [x] formatModelLabel handles new requirements (verified)
- [x] All 92 chat feature tests pass

## Commits
- `1aa9817`: feat(11-03): add InlineModelPicker component
- `ead9f64`: feat(11-03): integrate InlineModelPicker into ChatPage
