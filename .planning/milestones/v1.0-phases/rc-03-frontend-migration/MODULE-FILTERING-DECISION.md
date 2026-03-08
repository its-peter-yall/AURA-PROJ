# Module Filtering Decision for AURA-CHAT Graph Visualization

**Decision Date:** 2026-01-29  
**Phase:** RC-03 (Frontend Verification)  
**Plan:** RC-03-02  
**Decision:** **Add module filtering to AURA-CHAT graph visualization**

---

## Executive Summary

AURA-CHAT graph visualization will be enhanced to respect module selection, filtering the graph to show only entities and relationships within the selected module. This ensures consistency with the chat feature's module-centric architecture.

---

## Context

**Current State:**
- **Chat feature:** Filters queries by selected module (`module_ids` parameter)
- **Graph feature:** Shows ALL documents/entities regardless of module selection
- **Module selection:** 4-level hierarchy (Department → Semester → Subject → Module) via `ModuleSelectorModal`
- **Storage:** Selected module ID persisted in `localStorage` and ChatPage state

**Architectural inconsistency:**
```
ChatPage (module-aware):
  User selects Module A
  → Chat queries: Only search Module A's documents ✓
  → Graph view: Shows ALL modules' documents ✗
```

---

## Decision Rationale

**Why "Add module filtering" was chosen over alternatives:**

### ✅ Pros
1. **Architectural consistency:** Graph behavior matches chat behavior (both module-aware)
2. **Focused study experience:** Students see knowledge graph for their current module only
3. **Cognitive load reduction:** Smaller, relevant graph instead of overwhelming full graph
4. **Educational alignment:** Matches how students think about coursework (module by module)
5. **UI/UX improvement:** Graph becomes a companion to chat, not a separate exploration tool

### ⚠️ Cons (Acceptable tradeoffs)
1. **Development effort:** Requires backend + frontend changes (~1 day work)
2. **Cross-module discovery limitation:** Users won't see relationships between modules
   - *Mitigation:* Can add "All Modules" option in future if needed
3. **Testing complexity:** Need to verify filtering logic works correctly

---

## Implementation Plan

### Phase 1: Backend Changes (server/)

**File:** `server/routers/graph.py`

**Modification:** Add `module_id` query parameter to `/graph/data` endpoint

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

**Cypher Query Change:**

When `module_id` is provided, modify the graph query to:
1. Start from `(:Module {id: $module_id})`
2. Traverse to related documents: `MATCH (module)-[:HAS_DOCUMENT]->(doc:Document)`
3. Expand from documents: `MATCH (doc)-[*1..depth]->(entity)`
4. Return filtered subgraph

**Estimated LOC:** ~30 lines (query logic + parameter handling)

---

### Phase 2: Frontend Changes (client/)

**File 1:** `client/src/types/api.ts`

Add `module_id` to GraphQueryParams:

```typescript
export interface GraphQueryParams {
    document_id?: string;
    module_id?: string;     // NEW
    node_types?: string[];
    depth?: number;
    limit?: number;
}
```

**File 2:** `client/src/lib/api.ts`

Update `getGraphData` to pass `module_id`:

```typescript
export async function getGraphData(params: GraphQueryParams): Promise<GraphData> {
    const response = await api.get<GraphData>('/graph/data', { params });
    return response.data;
}
```

**File 3:** `client/src/features/graph/GraphPage.tsx`

1. Import module selection utilities
2. Read selected module from localStorage
3. Pass `module_id` to filters state
4. Display selected module in header (e.g., "Knowledge Graph • Module: CS101")
5. Add "Clear Module Filter" button to show full graph if needed

```typescript
// GraphPage.tsx changes
const [filters, setFilters] = useState<GraphQueryParams>({
    limit: 500,
    depth: 2,
    module_id: loadSelectedModuleId(), // NEW - read from localStorage
});

// Display module name in header
{selectedModule && (
    <div className="text-xs text-muted-foreground">
        Filtered by: {selectedModule.name}
    </div>
)}
```

**Estimated LOC:** ~50 lines (type changes + UI additions)

---

### Phase 3: Testing

**Test cases:**
1. ✅ Graph filters to module when module selected
2. ✅ Graph shows full graph when no module selected
3. ✅ Switching modules updates graph
4. ✅ Graph and chat share same module selection
5. ✅ Edge cases: Module with no documents, empty graph

**Test files to update:**
- `client/src/features/graph/GraphPage.test.tsx` - Add module filtering tests
- `server/tests/test_graph_router.py` - Add module parameter tests

**Estimated effort:** ~2 hours

---

## Effort Estimate

| Phase | Work | Time |
|-------|------|------|
| Backend (graph.py) | Add module_id param, update Cypher query | 2-3 hours |
| Frontend (types, api, GraphPage) | Add parameter, update UI | 2-3 hours |
| Testing | Write + run tests | 2 hours |
| **Total** | **Full implementation** | **6-8 hours (~1 day)** |

---

## Files to Modify

### Backend
- `server/routers/graph.py` - Add module_id parameter, update query logic
- `server/schemas/graph.py` - No changes needed (GraphQueryParams in client only)
- `server/tests/test_graph_router.py` - Add module filtering tests

### Frontend
- `client/src/types/api.ts` - Add module_id to GraphQueryParams
- `client/src/lib/api.ts` - Pass module_id in request (no code changes, just parameter passthrough)
- `client/src/features/graph/GraphPage.tsx` - Read module from storage, display in UI
- `client/src/features/graph/GraphPage.test.tsx` - Add module filtering test cases

**Total:** 6 files modified, ~80 lines of code added

---

## Impact on Phase 4 (RAG Removal)

**No impact** - This decision is orthogonal to RAG removal:

1. **Module filtering uses existing graph structure** - No dependency on NOTES-MANAGER RAG
2. **Backend graph endpoint already exists** - Just adding a filter parameter
3. **EntityGraph migration already skipped** - This work is independent of that decision
4. **Phase 4 can proceed as planned** - Remove NOTES-MANAGER RAG services without conflicts

---

## Alternatives Considered

### Option 2: Skip module filtering (REJECTED)

**Why rejected:**
- Creates UI/UX inconsistency (chat is module-aware, graph is not)
- Overwhelming for students (seeing all modules' entities at once)
- Doesn't align with educational use case (focused study sessions)
- Harder to justify later (technical debt)

### Option 3: Defer to future phase (REJECTED)

**Why rejected:**
- Low implementation cost (~1 day) doesn't justify deferral
- Would create temporary inconsistency through Phase 4
- Better to have consistent architecture before RAG removal
- User feedback would likely request this feature anyway

---

## Success Criteria

Module filtering is complete when:

- [ ] Backend `/graph/data` accepts `module_id` parameter
- [ ] Graph filters to selected module's documents and entities
- [ ] Graph header displays selected module name
- [ ] No module selected → full graph displayed (current behavior)
- [ ] Tests pass for module filtering logic
- [ ] Graph and chat share same module selection (consistent UX)

---

## Next Steps

1. **Create Phase 3.5 (Module Filtering Implementation)** - New phase after RC-03-02
2. **Update RAG-CONSOLIDATION-ROADMAP.md** - Add Phase 3.5 with 2 plans:
   - RC-03-03: Backend module filtering (server/routers/graph.py)
   - RC-03-04: Frontend module filtering (GraphPage.tsx integration)
3. **Proceed to Phase 4 (RAG Removal)** - After Phase 3.5 complete

---

**Decision Owner:** AI Agent (OpenCode)  
**Approved By:** User (plan executor)  
**Status:** ✅ **Approved for Implementation**
