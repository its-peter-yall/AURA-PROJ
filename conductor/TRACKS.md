# Project Tracks

This file tracks all major tracks for the project. Each track has its own detailed plan in its respective folder.

---

## Phase 7 Testing Fixes (2026-01-23)

- [~] **Track: Fix 07-01 Backend Tests**
  *Link: [./tracks/fix_07_01_backend_20260123/](./tracks/fix_07_01_backend_20260123/)*
  Fix mock_neo4j_driver return type, add mock_chat_manager fixture, add 37 missing tests, achieve 90% coverage on session_manager.py and 88% on rag_engine.py

- [~] **Track: Fix 07-02 Frontend Tests**
  *Link: [./tracks/fix_07_02_frontend_20260123/](./tracks/fix_07_02_frontend_20260123/)*
  Install MSW package, create handlers.ts file, add 53 missing tests to reach 140+ tests, fix placeholder files

- [x] **Track: Fix 07-03 AURA-NOTES Tests**
  *Link: [./tracks/fix_07_03_auranotes_20260123/](./tracks/fix_07_03_auranotes_20260123/)*
  Create useKGProcessing.test.ts with 16 tests, add 23 missing store tests, fix FileSelectionBar verification, add warningTimeoutId clearing tests

- [x] **Track: Fix 07-04 E2E Tests**
  *Link: [./tracks/fix_07_04_e2e_20260123/](./tracks/fix_07_04_e2e_20260123/)*
  Add mobile browser projects (iPhone 12, Pixel 5, iPad), create mobile.spec.ts and performance.spec.ts, add GitHub Actions/GitLab CI/Jenkins workflows

- [~] **Track: Fix 07-05 Performance Tests**
  *Link: [./tracks/fix_07_05_performance_20260123/](./tracks/fix_07_05_performance_20260123/)*
  Create AURA-NOTES benchmark/security tests, add prometheus.yml, Grafana provisioning, redis-exporter and neo4j-exporter configs, configure Trivy in CI/CD
