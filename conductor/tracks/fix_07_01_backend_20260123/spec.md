# Track Specification: Fix 07-01 Backend Tests

## Overview
Fix critical issues in Phase 7-01 AURA-CHAT backend unit tests to achieve 83+ tests, 90% coverage on session_manager.py, and 88% coverage on rag_engine.py.

## Current State (from Review)
- Test count: 75/83+ (8 short)
- Coverage: 0% on actual code (tests only validate mocks)
- Fixtures: 3/4 properly implemented

## Critical Issues to Fix

### 1. mock_neo4j_driver Return Type
**File:** `AURA-CHAT/tests/conftest.py` line 80
- **Current:** `return_value=([], None, None)` (tuple)
- **Required:** `return_value=[]` (list of dicts per graph_manager.py)
- **Impact:** Tests pass but mock doesn't match actual code behavior

### 2. Missing mock_chat_manager Fixture
Required by RAGEngine for:
- `chat_manager.get_last_n_messages()`
- `chat_manager.add_message()`
- `chat_manager.get_conversation_history()`

### 3. mock_redis_client Missing TTL Tracking
- `setex` should track expiration times for test assertions
- Plan specifies: session_manager uses `self.redis.setex(key, 86400, json.dumps(session))`

### 4. Tests Only Validate Mocks, Not Actual Code
- All unit tests use mock_session_manager and mock_graph_manager fixtures
- Actual SessionManager and RAGEngine classes are never instantiated
- Coverage shows 0% for all backend modules

## Functional Requirements

### 1. Fix Fixtures (Day 1)
- [ ] Fix mock_neo4j_driver.execute_query return type to list of dicts
- [ ] Add mock_chat_manager fixture with all required methods
- [ ] Add TTL tracking to mock_redis_client.setex
- [ ] Add mock_graph_manager.search_vector_with_modules method

### 2. Add Missing Tests (Day 2-3)
- [ ] Add 15 analytics/cache tests to test_session_crud.py
- [ ] Add 22 query classification/thinking tests to test_rag_engine.py

### 3. Integrate Real Classes (Day 3-4)
- [ ] Create integration-style tests that instantiate real SessionManager
- [ ] Create integration-style tests that instantiate real RAGEngine
- [ ] Configure pytest-cov in pyproject.toml

## Non-Functional Requirements
- All tests must pass (pytest -v)
- Coverage must meet targets (90%/88%)
- No placeholder tests allowed
- Test execution time < 60 seconds

## Acceptance Criteria
- [ ] 83+ unit tests implemented
- [ ] session_manager.py coverage >= 90%
- [ ] rag_engine.py coverage >= 88%
- [ ] All pytest tests pass
- [ ] Fixtures correctly mock actual return types
- [ ] mock_chat_manager fixture fully implemented

## Out of Scope
- Frontend tests (07-02)
- E2E tests (07-04)
- Performance benchmarks (07-05)
