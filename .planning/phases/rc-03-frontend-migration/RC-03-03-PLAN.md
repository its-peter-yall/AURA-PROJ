---
phase: rc-03-frontend-migration
type: execute
plan: RC-03-03
---

<objective>
Add module_id filtering parameter to AURA-CHAT graph API endpoint.

Purpose: Enable graph visualization to filter by selected module, ensuring consistency with chat feature's module-centric architecture.
Output: Updated `server/routers/graph.py` with module_id filter support and backend tests.
</objective>

<execution_context>
@~/.config/opencode/skills/create-plans/workflows/execute-phase.md
@~/.config/opencode/skills/create-plans/templates/summary.md
</execution_context>

<context>
@.planning/phases/rc-03-frontend-migration/MODULE-FILTERING-DECISION.md
@AURA-CHAT/server/routers/graph.py
@AURA-CHAT/server/schemas/graph.py
@AURA-CHAT/backend/graph_manager.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Analyze current graph.py endpoint structure</name>
  <files>AURA-CHAT/server/routers/graph.py</files>
  <action>
    Read and understand the current `/graph/data` endpoint:
    1. Current query parameters: document_id, node_types, depth, limit
    2. How filtering is implemented (Cypher queries)
    3. How results are processed (node/edge extraction)
    
    Document the insertion point for module_id filter logic.
  </action>
  <verify>Documented where module_id filter will be added</verify>
  <done>Clear understanding of endpoint structure and filter insertion point</done>
</task>

<task type="auto">
  <name>Task 2: Analyze Neo4j schema for Module relationships</name>
  <files>AURA-CHAT/backend/graph_manager.py</files>
  <action>
    Determine how Modules connect to Documents in Neo4j:
    1. Look for Module node type and its relationships
    2. Find the relationship type connecting Module → Document
       (likely: HAS_DOCUMENT, CONTAINS, or similar)
    3. Verify the schema supports module_id filtering
    
    If Module → Document relationship doesn't exist, document what 
    relationship IS available (e.g., Document has module_id property).
  </action>
  <verify>Documented Module-Document relationship pattern</verify>
  <done>Know how to filter graph by module (relationship or property)</done>
</task>

<task type="auto">
  <name>Task 3: Add module_id query parameter to endpoint</name>
  <files>AURA-CHAT/server/routers/graph.py</files>
  <action>
    Update the `/graph/data` endpoint signature:
    
    ```python
    @router.get("/data", response_model=GraphData)
    async def get_graph_data(
        document_id: Optional[str] = Query(None, description="Filter by document ID"),
        module_id: Optional[str] = Query(None, description="Filter by module ID"),  # NEW
        node_types: Optional[List[str]] = Query(None, description="Filter by node types"),
        depth: int = Query(2, ge=1, le=5, description="Traversal depth"),
        limit: int = Query(500, ge=1, le=1000, description="Maximum nodes to return"),
        graph_manager: GraphManager = Depends(get_graph_manager),
    ) -> GraphData:
    ```
    
    Add the module_id parameter after document_id.
  </action>
  <verify>Endpoint signature updated with module_id parameter</verify>
  <done>module_id query parameter added to /graph/data</done>
</task>

<task type="auto">
  <name>Task 4: Implement module filtering logic</name>
  <files>AURA-CHAT/server/routers/graph.py</files>
  <action>
    Add module_id filtering logic to the endpoint:
    
    OPTION A - If Module → Document relationship exists:
    ```python
    if module_id:
        # Get graph filtered by module
        query = """
        MATCH (m:Module {id: $module_id})-[:HAS_DOCUMENT]->(doc:Document)
        WITH doc
        MATCH (doc)-[r*1..$depth]->(entity)
        WITH doc, r, entity LIMIT $limit
        RETURN doc as n, labels(doc) as node_labels, r, entity as m, labels(entity) as target_labels
        """
        result = await graph_manager.execute_query(query, {
            "module_id": module_id,
            "depth": depth,
            "limit": limit
        })
    ```
    
    OPTION B - If Documents have module_id property:
    ```python
    if module_id:
        query = """
        MATCH (doc:Document {module_id: $module_id})
        WITH doc LIMIT $limit
        MATCH (doc)-[r]->(entity)
        RETURN doc as n, labels(doc) as node_labels, r, entity as m, labels(entity) as target_labels
        """
        result = await graph_manager.execute_query(query, {
            "module_id": module_id,
            "limit": limit
        })
    ```
    
    Integrate this new conditional branch alongside existing document_id filter.
    Priority order: document_id (most specific) > module_id > global graph
  </action>
  <verify>Module filtering logic implemented and compiles</verify>
  <done>module_id filter applied to Cypher query when provided</done>
</task>

<task type="auto">
  <name>Task 5: Update docstring with module_id documentation</name>
  <files>AURA-CHAT/server/routers/graph.py</files>
  <action>
    Update the module docstring (lines 1-70) to include module_id:
    
    ```python
    """
    GET /graph/data
        Get graph data for visualization.
        Query params:
        - document_id: Filter to single document's subgraph
        - module_id: Filter to module's documents and entities (NEW)
        - node_types: Filter by node types (e.g., ["Document", "Concept"])
        ...
    """
    ```
    
    Also update the endpoint docstring:
    ```python
    """
    Get graph data for visualization.
    Returns nodes and edges filtered by parameters.
    
    Filter priority:
    1. document_id - Show single document's subgraph
    2. module_id - Show all documents in a module
    3. None - Show global graph (limited)
    """
    ```
  </action>
  <verify>Docstrings updated with module_id documentation</verify>
  <done>Documentation reflects new module_id parameter</done>
</task>

<task type="auto">
  <name>Task 6: Create backend tests for module filtering</name>
  <files>AURA-CHAT/server/tests/test_graph_router.py</files>
  <action>
    Add or update tests for the module_id parameter:
    
    ```python
    @pytest.mark.asyncio
    async def test_get_graph_data_with_module_filter():
        """Test graph data filtered by module_id."""
        response = await client.get("/graph/data", params={"module_id": "test-module-1"})
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
    
    @pytest.mark.asyncio
    async def test_module_filter_with_nonexistent_module():
        """Test graph data with non-existent module returns empty."""
        response = await client.get("/graph/data", params={"module_id": "nonexistent"})
        assert response.status_code == 200
        data = response.json()
        assert data["nodes"] == []
    
    @pytest.mark.asyncio
    async def test_document_filter_takes_priority_over_module():
        """Test that document_id filter takes priority over module_id."""
        response = await client.get("/graph/data", params={
            "document_id": "doc-1",
            "module_id": "module-1"
        })
        assert response.status_code == 200
        # Should only show doc-1's subgraph, not entire module
    ```
    
    Create test file if it doesn't exist.
  </action>
  <verify>pytest runs tests successfully (even with mocked Neo4j)</verify>
  <done>Backend tests created for module_id filtering</done>
</task>

<task type="auto">
  <name>Task 7: Manual API verification</name>
  <files>N/A</files>
  <action>
    Test the updated endpoint manually:
    
    1. Start the API server:
       ```bash
       cd AURA-CHAT/server && python main.py
       ```
    
    2. Test module filter endpoint:
       ```bash
       curl "http://127.0.0.1:8000/graph/data?module_id=test-module"
       ```
    
    3. Verify Swagger docs show new parameter:
       Visit http://127.0.0.1:8000/docs and check /graph/data endpoint
    
    4. Test filter priority (document_id + module_id):
       ```bash
       curl "http://127.0.0.1:8000/graph/data?document_id=doc-1&module_id=mod-1"
       ```
    
    Document any errors for fixing.
  </action>
  <verify>API endpoint accepts module_id and returns valid response</verify>
  <done>Manual verification confirms module_id filter works</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] module_id parameter added to /graph/data endpoint
- [ ] Cypher query modified to filter by module
- [ ] Filter priority: document_id > module_id > global
- [ ] Docstrings updated
- [ ] Server starts without errors
- [ ] Swagger UI shows module_id parameter
- [ ] Backend tests pass
</verification>

<success_criteria>
- All tasks completed
- GET /graph/data?module_id=X returns filtered graph
- Existing functionality (document_id filter, global graph) unaffected
- Tests verify module filtering behavior
- API documentation updated
</success_criteria>

<output>
After completion, create `.planning/phases/rc-03-frontend-migration/RC-03-03-SUMMARY.md`
</output>
