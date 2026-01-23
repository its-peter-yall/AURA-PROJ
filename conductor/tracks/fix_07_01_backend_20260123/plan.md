# Track Implementation Plan: Fix 07-01 Backend Tests

## Phase 1: Fix Fixtures

- [ ] Task: Read current conftest.py to understand fixture structure
  - [ ] Open `AURA-CHAT/tests/conftest.py`
  - [ ] Identify mock_neo4j_driver fixture definition
  - [ ] Identify mock_redis_client fixture definition
  - [ ] Identify missing mock_chat_manager requirements

- [ ] Task: Fix mock_neo4j_driver return type
  - [ ] Change `driver.execute_query = MagicMock(return_value=([], None, None))`
  - [ ] To: `driver.execute_query = MagicMock(return_value=[])`
  - [ ] Run pytest to verify tests still pass

- [ ] Task: Add mock_chat_manager fixture
  - [ ] Create fixture with get_last_n_messages(session_id, n) method
  - [ ] Create fixture with add_message(session_id, role, content, sources) method
  - [ ] Create fixture with get_conversation_history(session_id) method
  - [ ] Create fixture with clear_conversation(session_id) method
  - [ ] Verify fixture works with existing tests

- [ ] Task: Add TTL tracking to mock_redis_client
  - [ ] Modify setex to track expiration times
  - [ ] Add storage dict to track key -> {value, ttl}
  - [ ] Add get method to retrieve stored values

## Phase 2: Add Missing Tests

- [ ] Task: Add analytics and cache tests to test_session_crud.py
  - [ ] test_get_user_session_count - Returns count for user
  - [ ] test_get_user_session_count_empty - Zero when no sessions
  - [ ] test_get_user_message_count - Returns total message count
  - [ ] test_get_user_message_count_empty - Zero when no messages
  - [ ] test_get_user_module_usage - Returns module usage statistics
  - [ ] test_get_user_module_usage_empty - Empty list when no usage
  - [ ] test_get_session_activity_timeline - Returns hourly message distribution
  - [ ] test_get_user_analytics - Returns complete user analytics dict
  - [ ] test_validate_ownership_valid - Correct owner returns True
  - [ ] test_validate_ownership_invalid - Wrong user returns False
  - [ ] test_validate_ownership_nonexistent - Non-existent session returns False
  - [ ] test_archive_session - Status changes to archived
  - [ ] test_resume_session - Status changes back to active
  - [ ] test_update_session_invalidates_cache - Cache cleared on update
  - [ ] test_add_message_invalidates_cache - Cache cleared on new message

- [ ] Task: Add query classification and thinking detection tests to test_rag_engine.py
  - [ ] test_classify_query_vector_only - "what is" patterns return vector_only
  - [ ] test_classify_query_hybrid - Complex queries return hybrid
  - [ ] test_classify_query_graph_expansion - "compare/contrast" return graph_expansion
  - [ ] test_classify_query_short - Short queries (<6 words) return vector_only
  - [ ] test_expand_query - Related terms added via graph lookup
  - [ ] test_is_thinking_text_with_markers - Thinking markers detected correctly
  - [ ] test_is_thinking_text_without_markers - Non-thinking text returns False
  - [ ] test_split_thinking_from_response - Content separated at response markers
  - [ ] test_thinking_markers_comprehensive - All `_THINKING_MARKERS` patterns tested
  - [ ] test_response_markers_comprehensive - All `_RESPONSE_MARKERS` patterns tested
  - [ ] test_hybrid_search_combines_vector_fulltext - 70% vector + 30% fulltext scores
  - [ ] test_context_window_respected - Chunks limited by MAX_CONTEXT_TOKENS
  - [ ] test_citation_relevance_threshold - Chunks below score threshold filtered

- [ ] Task: Add search_vector_with_modules to mock_graph_manager
  - [ ] Implement method for module-filtered vector search
  - [ ] Return list of dicts with similarity scores

## Phase 3: Configure Coverage and Verify

- [ ] Task: Configure pytest-cov in pyproject.toml
  - [ ] Add `[tool.pytest.ini_options]` with coverage settings
  - [ ] Add `[tool.coverage.run]` configuration
  - [ ] Add `[tool.coverage.report]` configuration

- [ ] Task: Run full test suite with coverage
  - [ ] Run `pytest tests/ -v --tb=short`
  - [ ] Run `pytest tests/ --cov=backend --cov-fail-under=85`
  - [ ] Verify session_manager.py coverage >= 90%
  - [ ] Verify rag_engine.py coverage >= 88%

- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Summary
- Total Tasks: 4 phases, 45+ subtasks
- Expected Duration: 1-2 days
- Success Criteria: 83+ tests, 90%/88% coverage, all tests pass
