# Track Implementation Plan: Fix 07-04 E2E Tests

## Phase 1: Add Mobile Browser Configurations

- [ ] Task: Update Playwright config for mobile
  - [ ] Read current `playwright.config.ts`
  - [ ] Add iPhone 12 project
  - [ ] Add Pixel 5 project
  - [ ] Add iPad project

- [ ] Task: Configure iPhone 12
  - [ ] Viewport: 390x844
  - [ ] User agent: iPhone 12
  - [ ] Device scale factor: 2
  - [ ] Has touch: true

- [ ] Task: Configure Pixel 5
  - [ ] Viewport: 412x915
  - [ ] User agent: Pixel 5
  - [ ] Device scale factor: 2.6
  - [ ] Has touch: true

- [ ] Task: Configure iPad
  - [ ] Viewport: 768x1024
  - [ ] User agent: iPad
  - [ ] Device scale factor: 2
  - [ ] Has touch: true

## Phase 2: Create Missing Test Files

- [ ] Task: Create mobile.spec.ts
  - [ ] Create `AURA-CHAT/e2e/mobile.spec.ts`
  - [ ] Test mobile navigation
  - [ ] Test hamburger menu
  - [ ] Test bottom navigation
  - [ ] Test touch gestures
  - [ ] Test swipe actions
  - [ ] Test pinch zoom
  - [ ] Test responsive layouts
  - [ ] Test mobile keyboard
  - [ ] Test mobile forms
  - [ ] Test mobile search
  - [ ] Test mobile chat
  - [ ] Test mobile graph
  - [ ] Test mobile settings
  - [ ] Test mobile share
  - [ ] Test mobile notifications
  - [ ] Test offline mode
  - [ ] Test portrait mode
  - [ ] Test landscape mode
  - [ ] Test dark mode mobile
  - [ ] Test accessibility mobile

- [ ] Task: Create performance.spec.ts
  - [ ] Create `AURA-CHAT/e2e/performance.spec.ts`
  - [ ] Test page load time
  - [ ] Test first contentful paint
  - [ ] Test largest contentful paint
  - [ ] Test time to interactive
  - [ ] Test memory usage
  - [ ] Test CPU usage
  - [ ] Test graph rendering time
  - [ ] Test message send latency
  - [ ] Test search response time
  - [ ] Test navigation time

## Phase 3: Create CI/CD Workflows

- [ ] Task: Create GitHub Actions workflow
  - [ ] Create `.github/workflows/e2e-tests.yml`
  - [ ] Run on push to main
  - [ ] Run on PR
  - [ ] Matrix strategy for browsers
  - [ ] Matrix strategy for mobile
  - [ ] Upload artifacts
  - [ ] Add timeout (30 min)

- [ ] Task: Create GitLab CI configuration
  - [ ] Create `.gitlab-ci.yml`
  - [ ] Define stages
  - [ ] Configure parallel jobs
  - [ ] Add test stage
  - [ ] Add report artifacts
  - [ ] Add cache configuration

- [ ] Task: Create Jenkins pipeline
  - [ ] Create `Jenkinsfile`
  - [ ] Define stages
  - [ ] Configure parallel execution
  - [ ] Add timeout
  - [ ] Add Slack notifications
  - [ ] Add test reporting

## Phase 4: Fix Test Quality

- [ ] Task: Replace waitForTimeout calls
  - [ ] Search for `waitForTimeout` in test files
  - [ ] Replace with explicit waits
  - [ ] Add network idle waiting
  - [ ] Add element state waiting

- [ ] Task: Add proper waiting strategies
  - [ ] Add `waitForSelector`
  - [ ] Add `waitForLoadState`
  - [ ] Add `waitForResponse`
  - [ ] Add `waitForFunction`

- [ ] Task: Add retry logic
  - [ ] Add test retries in config
  - [ ] Add soft assertions
  - [ ] Add test hooks for cleanup

- [ ] Task: Run E2E test suite
  - [ ] Run on desktop
  - [ ] Run on mobile (all 3 devices)
  - [ ] Verify 135+ tests
  - [ ] Check for failures

- [ ] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)

## Summary
- Total Tasks: 4 phases, 70+ subtasks
- Expected Duration: 2-3 days
- Success Criteria: 135+ tests, mobile support, CI/CD configured
