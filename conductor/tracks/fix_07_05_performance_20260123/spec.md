# Track Specification: Fix 07-05 Performance Tests

## Overview
Fix issues in Phase 7-05 performance and Docker tests to achieve 28+ tests with proper monitoring and security scanning.

## Current State (from Review)
- Test count: 17/28 (11 short)
- AURA-NOTES-MANAGER has **zero** benchmark/security tests
- Missing prometheus.yml and Grafana provisioning
- Missing redis-exporter, neo4j-exporter, node-exporter
- No CI/CD for Trivy or performance gates
- Only 2 of 8 security tests implemented

## Critical Issues to Fix

### 1. Missing AURA-NOTES Benchmark Tests
- Zero benchmark tests for AURA-NOTES-MANAGER
- Need tests for Firestore operations
- Need tests for Deepgram processing

### 2. Missing Security Tests
- Only 2 of 8 security tests implemented
- Need: Input validation tests
- Need: Authentication tests
- Need: Authorization tests
- Need: Rate limiting tests

### 3. Missing Monitoring Configuration
- prometheus.yml not created
- Grafana provisioning not configured
- redis-exporter not configured
- neo4j-exporter not configured

### 4. Missing CI/CD Integration
- Trivy not configured in CI
- Performance gates not configured
- No benchmark thresholds

## Functional Requirements

### 1. Create AURA-NOTES Benchmark Tests (Day 1)
- [ ] Test Firestore query performance
- [ ] Test document creation time
- [ ] Test batch operations
- [ ] Test Deepgram API calls
- [ ] Test audio processing time
- [ ] Test note transcription

### 2. Add Security Tests (Day 2)
- [ ] Input validation tests (4 tests)
- [ ] Authentication middleware tests (2 tests)
- [ ] Authorization tests (2 tests)
- [ ] Rate limiting tests (2 tests)

### 3. Configure Monitoring (Day 2-3)
- [ ] Create prometheus.yml
- [ ] Configure Prometheus scrape targets
- [ ] Configure Grafana provisioning
- [ ] Create Grafana dashboards
- [ ] Configure redis-exporter (port 9121)
- [ ] Configure neo4j-exporter (port 2004)
- [ ] Configure node-exporter (port 9100)

### 4. Configure CI/CD (Day 3)
- [ ] Add Trivy to GitHub Actions
- [ ] Add Trivy to GitLab CI
- [ ] Add Trivy to Jenkins
- [ ] Add performance gates
- [ ] Add benchmark thresholds

## Non-Functional Requirements
- All benchmark tests must pass (pytest-benchmark)
- All security tests must pass
- Docker Compose must start successfully
- All exporters must be accessible
- CI/CD must complete in < 30 minutes

## Acceptance Criteria
- [ ] 28+ benchmark/security tests
- [ ] AURA-NOTES benchmark tests created (10+ tests)
- [ ] All security tests implemented (8 tests)
- [ ] prometheus.yml configured
- [ ] Grafana provisioned
- [ ] redis-exporter (9121) configured
- [ ] neo4j-exporter (2004) configured
- [ ] Trivy in CI/CD

## Out of Scope
- Unit tests (07-01, 07-02, 07-03)
- E2E tests (07-04)
