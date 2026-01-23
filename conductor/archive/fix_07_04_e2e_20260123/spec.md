# Track Specification: Fix 07-04 E2E Tests

## Overview
Fix issues in Phase 7-04 integration and E2E tests to achieve 135+ tests with mobile support and CI/CD workflows.

## Current State (from Review)
- Test count: 115/135 (20 short)
- No mobile browser projects
- No GitHub Actions/GitLab CI/Jenkins workflows
- No mobile.spec.ts or performance.spec.ts files
- Hardcoded waitForTimeout calls

## Critical Issues to Fix

### 1. Missing Mobile Browser Projects
- iPhone 12 configuration missing
- Pixel 5 configuration missing
- iPad configuration missing

### 2. Missing Test Files
- mobile.spec.ts (20 tests)
- performance.spec.ts (10 tests)

### 3. Missing CI/CD Workflows
- GitHub Actions workflow
- GitLab CI configuration
- Jenkins pipeline

### 4. Test Quality Issues
- Hardcoded waitForTimeout calls
- No proper waiting strategies
- Inconsistent test patterns

## Functional Requirements

### 1. Add Mobile Browser Configurations (Day 1)
- [ ] Add iPhone 12 project to Playwright config
- [ ] Add Pixel 5 project to Playwright config
- [ ] Add iPad project to Playwright config
- [ ] Configure viewport sizes
- [ ] Configure user agents
- [ ] Configure device emulation

### 2. Create Missing Test Files (Day 2)
- [ ] mobile.spec.ts (20 tests for mobile flow)
- [ ] performance.spec.ts (10 tests for performance)
- [ ] Add mobile navigation tests
- [ ] Add touch interaction tests
- [ ] Add responsive layout tests

### 3. Create CI/CD Workflows (Day 3)
- [ ] Create .github/workflows/e2e-tests.yml
- [ ] Create .gitlab-ci.yml
- [ ] Create Jenkinsfile
- [ ] Configure parallel execution
- [ ] Configure mobile test runs
- [ ] Configure reporting

### 4. Fix Test Quality (Day 3-4)
- [ ] Replace waitForTimeout with proper waits
- [ ] Add explicit waits for elements
- [ ] Add network idle waiting
- [ ] Add retry logic
- [ ] Add test isolation

## Non-Functional Requirements
- All tests must pass (Playwright)
- Mobile tests on 3 devices
- CI/CD completion < 30 minutes
- Proper reporting and artifacts

## Acceptance Criteria
- [ ] 135+ E2E tests implemented
- [ ] 3 mobile browser projects configured
- [ ] mobile.spec.ts created (20 tests)
- [ ] performance.spec.ts created (10 tests)
- [ ] GitHub Actions workflow created
- [ ] GitLab CI configuration created
- [ ] Jenkins pipeline created
- [ ] No hardcoded waitForTimeout

## Out of Scope
- Unit tests (07-01, 07-02, 07-03)
- Performance benchmarks (07-05)
