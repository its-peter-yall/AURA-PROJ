---
phase: rc-02-graph-api
type: execute
plan: RC-02-01
---

<objective>
Create minimal graph preview API for staff module review in AURA-NOTES-MANAGER.

Purpose: Retain graph data access for module preview after RAG removal, using existing graph_manager.py and graph_visualizer.py.
Output: New `api/routers/graph_preview.py` with lightweight endpoints for graph visualization.
</objective>

<execution_context>
@~/.config/opencode/skills/create-plans/workflows/execute-phase.md
@~/.config/opencode/skills/create-plans/templates/summary.md
</execution_context>

<context>
@.planning/RAG-CONSOLIDATION-BRIEF.md
@.planning/RAG-CONSOLIDATION-ROADMAP.md
@.planning/phases/rc-01-dependency-mapping/BACKEND-DEPENDENCIES.md
@AURA-NOTES-MANAGER/api/graph_manager.py
@AURA-NOTES-MANAGER/api/graph_visualizer.py
@AURA-NOTES-MANAGER/api/main.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Analyze existing graph_manager.py capabilities</name>
  <files>AURA-NOTES-MANAGER/api/graph_manager.py</files>
  <action>
    Read graph_manager.py to understand available methods:
    1. What graph data retrieval methods exist?
    2. What parameters do they accept (module_id, entity_types, limit)?
    3. What is the return format (nodes, edges, counts)?
    
    Document the methods that will be exposed via the new API.
    Do NOT modify graph_manager.py - just document what's available.
  </action>
  <verify>List of methods with signatures documented</verify>
  <done>Clear understanding of graph_manager capabilities for API design</done>
</task>

<task type="auto">
  <name>Task 2: Create Pydantic response schemas</name>
  <files>AURA-NOTES-MANAGER/api/schemas/graph_preview.py</files>
  <action>
    Create new schema file with response models matching FRONTEND-DEPENDENCIES.md types:
    
    ```python
    # graph_preview.py
    # Response schemas for graph preview API endpoints
    
    from pydantic import BaseModel, Field
    from typing import List, Dict, Any, Optional
    
    class GraphNode(BaseModel):
        """Single node in the knowledge graph."""
        id: str
        label: str
        name: str
        type: str
        properties: Dict[str, Any] = Field(default_factory=dict)
    
    class GraphEdge(BaseModel):
        """Single edge/relationship in the knowledge graph."""
        id: str
        source: str
        target: str
        type: str
        properties: Dict[str, Any] = Field(default_factory=dict)
    
    class GraphPreviewResponse(BaseModel):
        """Complete graph data for visualization."""
        nodes: List[GraphNode]
        edges: List[GraphEdge]
        node_count: int
        edge_count: int
        module_id: Optional[str] = None
    
    class GraphStatsResponse(BaseModel):
        """Statistics about a module's knowledge graph."""
        node_count: int
        edge_count: int
        entity_types: Dict[str, int]  # type -> count
        relationship_types: Dict[str, int]  # type -> count
    ```
    
    Ensure schemas match the types in FRONTEND-DEPENDENCIES.md (lines 130-156).
  </action>
  <verify>File exists, Pydantic models validate with sample data</verify>
  <done>api/schemas/graph_preview.py created with GraphNode, GraphEdge, GraphPreviewResponse, GraphStatsResponse</done>
</task>

<task type="auto">
  <name>Task 3: Create graph preview router</name>
  <files>AURA-NOTES-MANAGER/api/routers/graph_preview.py</files>
  <action>
    Create new router with two endpoints:
    
    ```python
    # graph_preview.py
    # Lightweight graph preview API for module visualization
    # 
    # Provides graph data for staff module preview without full RAG capabilities.
    # Uses graph_manager.py directly, does NOT depend on rag_engine.py.
    #
    # @see: api/graph_manager.py - Graph data operations
    # @see: api/schemas/graph_preview.py - Response schemas
    
    from fastapi import APIRouter, Depends, Query, HTTPException
    from typing import Optional, List
    
    from api.graph_manager import GraphManager
    from api.schemas.graph_preview import (
        GraphPreviewResponse,
        GraphStatsResponse,
        GraphNode,
        GraphEdge
    )
    
    router = APIRouter(
        prefix="/api/v1/graph-preview",
        tags=["Graph Preview"]
    )
    
    def get_graph_manager() -> GraphManager:
        """Dependency injection for GraphManager."""
        return GraphManager()
    
    @router.get(
        "/modules/{module_id}",
        response_model=GraphPreviewResponse,
        summary="Get graph data for module preview"
    )
    async def get_module_graph(
        module_id: str,
        entity_types: Optional[List[str]] = Query(None),
        limit: int = Query(100, ge=1, le=500),
        graph_manager: GraphManager = Depends(get_graph_manager)
    ):
        """
        Retrieve graph nodes and edges for a module.
        
        Used by staff to preview module knowledge graph before publishing.
        Returns nodes, edges, and counts for visualization.
        """
        # Implementation uses graph_manager methods
        pass
    
    @router.get(
        "/modules/{module_id}/stats",
        response_model=GraphStatsResponse,
        summary="Get graph statistics for module"
    )
    async def get_module_graph_stats(
        module_id: str,
        graph_manager: GraphManager = Depends(get_graph_manager)
    ):
        """
        Retrieve statistics about a module's knowledge graph.
        
        Returns counts by entity type and relationship type.
        """
        # Implementation uses graph_manager methods
        pass
    ```
    
    Implement the endpoint bodies using graph_manager methods identified in Task 1.
    Follow Google Python Style Guide (from AGENTS.md).
  </action>
  <verify>python -c "from api.routers.graph_preview import router; print(router.routes)"</verify>
  <done>graph_preview.py router created with /modules/{module_id} and /modules/{module_id}/stats endpoints</done>
</task>

<task type="auto">
  <name>Task 4: Register router in main.py</name>
  <files>AURA-NOTES-MANAGER/api/main.py</files>
  <action>
    Add the new graph_preview router to main.py:
    
    1. Add import near other router imports:
       ```python
       from api.routers.graph_preview import router as graph_preview_router
       ```
    
    2. Add router registration after existing routers:
       ```python
       app.include_router(graph_preview_router)  # Graph Preview API (RC-02)
       ```
    
    Do NOT remove the query_router yet - that happens in Phase RC-04.
  </action>
  <verify>Start server, visit /docs to see new endpoints in Swagger UI</verify>
  <done>graph_preview_router registered in main.py, visible in API docs</done>
</task>

<task type="auto">
  <name>Task 5: Export router from __init__.py</name>
  <files>AURA-NOTES-MANAGER/api/routers/__init__.py</files>
  <action>
    Add export for the new router:
    
    ```python
    from api.routers.graph_preview import router as graph_preview_router
    ```
    
    Add to __all__ if present.
  </action>
  <verify>python -c "from api.routers import graph_preview_router"</verify>
  <done>graph_preview_router exported from api.routers</done>
</task>

<task type="auto">
  <name>Task 6: Manual API test</name>
  <files>N/A</files>
  <action>
    Test the new endpoints manually:
    
    1. Start the API server:
       ```bash
       cd AURA-NOTES-MANAGER/api && python main.py
       ```
    
    2. Test graph preview endpoint:
       ```bash
       curl http://127.0.0.1:8001/api/v1/graph-preview/modules/test-module
       ```
    
    3. Test stats endpoint:
       ```bash
       curl http://127.0.0.1:8001/api/v1/graph-preview/modules/test-module/stats
       ```
    
    4. Check Swagger docs at http://127.0.0.1:8001/docs
    
    Document any errors for fixing.
  </action>
  <verify>Both endpoints return valid JSON (even if empty data)</verify>
  <done>API endpoints respond correctly, no import or runtime errors</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] api/schemas/graph_preview.py exists with all models
- [ ] api/routers/graph_preview.py exists with both endpoints
- [ ] Router registered in main.py
- [ ] Server starts without import errors
- [ ] Endpoints visible in /docs
- [ ] Both endpoints return valid responses
</verification>

<success_criteria>
- All tasks completed
- New graph preview API functional
- Does NOT depend on rag_engine.py or answer_synthesizer.py
- Uses only graph_manager.py (which is being kept)
- API design matches frontend expectations from FRONTEND-DEPENDENCIES.md
</success_criteria>

<output>
After completion, create `.planning/phases/rc-02-graph-api/RC-02-01-SUMMARY.md`
</output>
