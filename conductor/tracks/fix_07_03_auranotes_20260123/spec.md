# Track Specification: Fix 07-03 AURA-NOTES Tests

## Overview
Fix issues in Phase 7-03 AURA-NOTES-MANAGER unit tests to achieve 96+ tests.

## Current State (from Review)
- Test count: 89/96+ (7 short)
- useKGProcessing.test.ts **completely missing** (16 tests)
- 23 store tests missing
- warningTimeoutId clearing not tested
- FileSelectionBar null verification incomplete

## Critical Issues to Fix

### 1. Missing useKGProcessing.test.ts
- Required: 16 tests for useKGProcessing hook
- Currently: File doesn't exist

### 2. Missing Store Tests
- useExplorerStore: 12 tests missing
- useKGProcessing: 8 tests missing
- useSelectionStore: 3 tests missing

### 3. FileSelectionBar Verification
- Component can return null (no files selected)
- Need verification that null is handled correctly

### 4. warningTimeoutId Clearing
- Hook sets timeout for warnings
- Need tests for proper cleanup

## Functional Requirements

### 1. Create useKGProcessing.test.ts (Day 1)
- [ ] Test initial state
- [ ] Test processing state
- [ ] Test success state
- [ ] Test error state
- [ ] Test queue management
- [ ] Test pause/resume
- [ ] Test cancel operation
- [ ] Test progress tracking
- [ ] Test retry functionality
- [ ] Test dependency tracking
- [ ] Test warning display
- [ ] Test warning timeout
- [ ] Test warning clearing
- [ ] Test cleanup on unmount
- [ ] Test concurrent processing
- [ ] Test priority queue

### 2. Add Missing Store Tests (Day 2)
- [ ] useExplorerStore tests (12 tests)
- [ ] useKGProcessing tests (8 tests)
- [ ] useSelectionStore tests (3 tests)

### 3. Fix FileSelectionBar Tests (Day 2)
- [ ] Verify null return handling
- [ ] Add null state tests
- [ ] Test empty selection UI

### 4. Add warningTimeoutId Tests (Day 3)
- [ ] Test timeout creation
- [ ] Test timeout clearing
- [ ] Test cleanup on unmount
- [ ] Test multiple warnings

## Non-Functional Requirements
- All tests must pass (vitest)
- 75%+ component coverage
- 90%+ store/hook coverage
- Test execution time < 60 seconds

## Acceptance Criteria
- [ ] 96+ unit tests implemented
- [ ] useKGProcessing.test.ts created with 16 tests
- [ ] All store tests added
- [ ] warningTimeoutId properly tested
- [ ] All vitest tests pass

## Out of Scope
- Backend tests (07-01)
- Frontend tests (07-02)
- E2E tests (07-04)
