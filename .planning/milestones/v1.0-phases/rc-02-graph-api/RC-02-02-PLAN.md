---
phase: rc-02-graph-api
type: execute
plan: RC-02-02
---

<objective>
Add tests for the new graph preview API endpoints.

Purpose: Ensure graph preview API is reliable before removing RAG services that it replaces.
Output: Test file `tests/test_graph_preview.py` with unit and integration tests.
</objective>

<execution_context>
@~/.config/opencode/skills/create-plans/workflows/execute-phase.md
@~/.config/opencode/skills/create-plans/templates/summary.md
</execution_context>

<context>
@.planning/RAG-CONSOLIDATION-BRIEF.md
@.planning/RAG-CONSOLIDATION-ROADMAP.md
@.planning/phases/rc-02-graph-api/RC-02-01-SUMMARY.md
@AURA-NOTES-MANAGER/api/routers/graph_preview.py
@AURA-NOTES-MANAGER/api/schemas/graph_preview.py
@AURA-NOTES-MANAGER/tests/
</context>

<tasks>

<task type="auto">
  <name>Task 1: Analyze existing test patterns</name>
  <files>AURA-NOTES-MANAGER/tests/</files>
  <action>
    Examine existing tests to understand:
    1. Test framework used (pytest, unittest)
    2. How FastAPI TestClient is configured
    3. How database/Neo4j is mocked or handled
    4. Fixture patterns used
    5. Naming conventions
    
    Document the patterns to follow for consistency.
  </action>
  <verify>List test patterns documented</verify>
  <done>Test patterns understood, ready to create consistent tests</done>
</task>

<task type="auto">
  <name>Task 2: Create test file with fixtures</name>
  <files>AURA-NOTES-MANAGER/tests/test_graph_preview.py</files>
  <action>
    Create test file with:
    
    ```python
    # test_graph_preview.py
    # Tests for graph preview API endpoints
    #
    # Verifies the lightweight graph preview API returns correct
    # data structure for module visualization.
    #
    # @see: api/routers/graph_preview.py - Endpoints under test
    # @see: api/schemas/graph_preview.py - Response schemas
    
    import pytest
    from fastapi.testclient import TestClient
    from unittest.mock import Mock, patch
    
    from api.main import app
    from api.schemas.graph_preview import (
        GraphNode,
        GraphEdge,
        GraphPreviewResponse,
        GraphStatsResponse
    )
    
    client = TestClient(app)
    
    @pytest.fixture
    def mock_graph_data():
        """Sample graph data for testing."""
        return {
            "nodes": [
                {"id": "n1", "label": "Machine Learning", "name": "Machine Learning", "type": "Topic", "properties": {}},
                {"id": "n2", "label": "Neural Networks", "name": "Neural Networks", "type": "Concept", "properties": {}},
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2", "type": "CONTAINS", "properties": {}},
            ],
            "node_count": 2,
            "edge_count": 1,
            "module_id": "test-module"
        }
    
    @pytest.fixture
    def mock_stats_data():
        """Sample stats data for testing."""
        return {
            "node_count": 50,
            "edge_count": 75,
            "entity_types": {"Topic": 10, "Concept": 30, "Finding": 10},
            "relationship_types": {"CONTAINS": 40, "RELATES_TO": 35}
        }
    ```
    
    Add fixtures following existing patterns from Task 1.
  </action>
  <verify>File exists with imports and fixtures</verify>
  <done>test_graph_preview.py created with fixtures</done>
</task>

<task type="auto">
  <name>Task 3: Add endpoint response tests</name>
  <files>AURA-NOTES-MANAGER/tests/test_graph_preview.py</files>
  <action>
    Add tests for successful responses:
    
    ```python
    class TestGraphPreviewEndpoints:
        """Tests for /api/v1/graph-preview endpoints."""
        
        def test_get_module_graph_success(self, mock_graph_data):
            """GET /modules/{module_id} returns graph data."""
            with patch('api.routers.graph_preview.get_graph_manager') as mock:
                mock_manager = Mock()
                mock_manager.get_module_graph.return_value = mock_graph_data
                mock.return_value = mock_manager
                
                response = client.get("/api/v1/graph-preview/modules/test-module")
                
                assert response.status_code == 200
                data = response.json()
                assert "nodes" in data
                assert "edges" in data
                assert data["node_count"] == 2
                assert data["edge_count"] == 1
        
        def test_get_module_graph_with_filters(self, mock_graph_data):
            """GET /modules/{module_id} accepts query parameters."""
            with patch('api.routers.graph_preview.get_graph_manager') as mock:
                mock_manager = Mock()
                mock_manager.get_module_graph.return_value = mock_graph_data
                mock.return_value = mock_manager
                
                response = client.get(
                    "/api/v1/graph-preview/modules/test-module",
                    params={"entity_types": ["Topic", "Concept"], "limit": 50}
                )
                
                assert response.status_code == 200
        
        def test_get_module_graph_stats_success(self, mock_stats_data):
            """GET /modules/{module_id}/stats returns statistics."""
            with patch('api.routers.graph_preview.get_graph_manager') as mock:
                mock_manager = Mock()
                mock_manager.get_module_stats.return_value = mock_stats_data
                mock.return_value = mock_manager
                
                response = client.get("/api/v1/graph-preview/modules/test-module/stats")
                
                assert response.status_code == 200
                data = response.json()
                assert "node_count" in data
                assert "edge_count" in data
                assert "entity_types" in data
    ```
  </action>
  <verify>Tests added to file</verify>
  <done>Success case tests added</done>
</task>

<task type="auto">
  <name>Task 4: Add error handling tests</name>
  <files>AURA-NOTES-MANAGER/tests/test_graph_preview.py</files>
  <action>
    Add tests for error cases:
    
    ```python
        def test_get_module_graph_not_found(self):
            """GET /modules/{module_id} returns 404 for unknown module."""
            with patch('api.routers.graph_preview.get_graph_manager') as mock:
                mock_manager = Mock()
                mock_manager.get_module_graph.return_value = None
                mock.return_value = mock_manager
                
                response = client.get("/api/v1/graph-preview/modules/nonexistent")
                
                assert response.status_code == 404
        
        def test_get_module_graph_invalid_limit(self):
            """GET /modules/{module_id} validates limit parameter."""
            response = client.get(
                "/api/v1/graph-preview/modules/test-module",
                params={"limit": 1000}  # Exceeds max of 500
            )
            
            assert response.status_code == 422  # Validation error
        
        def test_get_module_graph_stats_not_found(self):
            """GET /modules/{module_id}/stats returns 404 for unknown module."""
            with patch('api.routers.graph_preview.get_graph_manager') as mock:
                mock_manager = Mock()
                mock_manager.get_module_stats.return_value = None
                mock.return_value = mock_manager
                
                response = client.get("/api/v1/graph-preview/modules/nonexistent/stats")
                
                assert response.status_code == 404
    ```
  </action>
  <verify>Error tests added</verify>
  <done>Error handling tests added</done>
</task>

<task type="auto">
  <name>Task 5: Add schema validation tests</name>
  <files>AURA-NOTES-MANAGER/tests/test_graph_preview.py</files>
  <action>
    Add tests for Pydantic schema validation:
    
    ```python
    class TestGraphPreviewSchemas:
        """Tests for graph preview Pydantic schemas."""
        
        def test_graph_node_schema(self):
            """GraphNode validates correctly."""
            node = GraphNode(
                id="n1",
                label="Test Node",
                name="Test Node",
                type="Topic",
                properties={"key": "value"}
            )
            assert node.id == "n1"
            assert node.type == "Topic"
        
        def test_graph_edge_schema(self):
            """GraphEdge validates correctly."""
            edge = GraphEdge(
                id="e1",
                source="n1",
                target="n2",
                type="RELATES_TO",
                properties={}
            )
            assert edge.source == "n1"
            assert edge.target == "n2"
        
        def test_graph_preview_response_schema(self, mock_graph_data):
            """GraphPreviewResponse validates complete response."""
            response = GraphPreviewResponse(**mock_graph_data)
            assert len(response.nodes) == 2
            assert len(response.edges) == 1
            assert response.node_count == 2
        
        def test_graph_stats_response_schema(self, mock_stats_data):
            """GraphStatsResponse validates statistics."""
            response = GraphStatsResponse(**mock_stats_data)
            assert response.node_count == 50
            assert response.entity_types["Topic"] == 10
    ```
  </action>
  <verify>Schema tests added</verify>
  <done>Schema validation tests added</done>
</task>

<task type="auto">
  <name>Task 6: Run tests and verify</name>
  <files>AURA-NOTES-MANAGER/tests/test_graph_preview.py</files>
  <action>
    Run the tests and ensure they pass:
    
    ```bash
    cd AURA-NOTES-MANAGER
    # Use root venv per AGENTS.md
    ../.venv/Scripts/python -m pytest tests/test_graph_preview.py -v
    ```
    
    Fix any failures before completing.
    
    Expected output:
    - All tests pass
    - No import errors
    - Mocking works correctly
  </action>
  <verify>pytest output shows all tests passing</verify>
  <done>All tests pass, graph preview API fully tested</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] tests/test_graph_preview.py exists
- [ ] All tests pass with pytest
- [ ] Tests cover success cases for both endpoints
- [ ] Tests cover error cases (404, validation)
- [ ] Tests cover schema validation
- [ ] No mocking issues or import errors
</verification>

<success_criteria>
- All tasks completed
- 100% of new endpoints have test coverage
- Tests follow existing project patterns
- Tests mock graph_manager to avoid Neo4j dependency
- All tests pass
</success_criteria>

<output>
After completion, create `.planning/phases/rc-02-graph-api/RC-02-02-SUMMARY.md`
</output>
