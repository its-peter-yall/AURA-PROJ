# Track Specification: Fix 07-02 Frontend Tests

## Overview
Fix critical issues in Phase 7-02 AURA-CHAT frontend unit tests to achieve 140+ tests with proper MSW mocking.

## Current State (from Review)
- Test count: 87/140+ (53 short)
- MSW package NOT installed
- No MSW handlers file (uses vi.mock instead)
- 7 test files missing (GraphView, SettingsPage, ErrorBoundary, etc.)
- Placeholder files present

## Critical Issues to Fix

### 1. MSW Not Installed
- Required for proper API mocking per plan
- Currently using vi.mock which is insufficient

### 2. Missing Test Files
- GraphView.test.tsx (15 tests)
- SettingsPage.test.tsx (10 tests)
- ErrorBoundary.test.tsx (8 tests)
- useChatConfig.test.ts (8 tests)
- useAutoSave.test.ts (8 tests)
- useCitation.test.ts (8 tests)
- integration.test.ts (8 tests)

### 3. Placeholder Tests
- Several test files contain placeholder content
- No meaningful assertions

## Functional Requirements

### 1. Install and Configure MSW (Day 1)
- [ ] Install msw package in AURA-CHAT/client
- [ ] Create handlers.ts for API mocking
- [ ] Configure vitest with MSW
- [ ] Create mock API responses for all endpoints

### 2. Create Missing Test Files (Day 2-3)
- [ ] GraphView.test.tsx - 15 tests for 3D graph visualization
- [ ] SettingsPage.test.tsx - 10 tests for settings page
- [ ] ErrorBoundary.test.tsx - 8 tests for error boundary
- [ ] useChatConfig.test.ts - 8 tests for chat config hook
- [ ] useAutoSave.test.ts - 8 tests for auto-save hook
- [ ] useCitation.test.ts - 8 tests for citation hook
- [ ] integration.test.ts - 8 integration tests

### 3. Fix Existing Tests (Day 3-4)
- [ ] Replace placeholder content with real tests
- [ ] Add meaningful assertions
- [ ] Test edge cases and error states
- [ ] Verify all tests pass with MSW

## Non-Functional Requirements
- All tests must pass (vitest)
- 75%+ component coverage
- 90%+ hook coverage
- Test execution time < 60 seconds

## Acceptance Criteria
- [ ] 140+ unit tests implemented
- [ ] MSW properly configured and working
- [ ] All placeholder files replaced with real tests
- [ ] All vitest tests pass
- [ ] No placeholder content in test files

## Out of Scope
- Backend tests (07-01)
- E2E tests (07-04)
- Performance benchmarks (07-05)
