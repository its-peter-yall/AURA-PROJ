# Roadmap: RAG Consolidation Refactoring

> **Version:** 1.0
> **Created:** January 29, 2026
> **Brief:** `@.planning/RAG-CONSOLIDATION-BRIEF.md`
> **Reference:** `@AGENTS.md`

---

## Overview

This roadmap consolidates RAG/query functionality by removing duplicate services from AURA-NOTES-MANAGER and migrating graph visualization to AURA-CHAT. The refactoring ensures clear separation of concerns: NOTES-MANAGER handles document management/KG processing, CHAT handles student queries with optional graph visualization.

---

## Phases

- [x] **Phase 1: Dependency Mapping** - Map all dependencies, verify removal safety
- [x] **Phase 2: Graph API Consolidation** - Create simplified graph preview API in NOTES-MANAGER
- [x] **Phase 3: Frontend Verification + Module Filtering** - Verify AURA-CHAT graph, add module filtering
- [x] **Phase 4: RAG Removal** - Remove dead RAG code from NOTES-MANAGER
- [ ] **Phase 5: Verification** - Integration testing, cleanup

---

## Phase Details

### Phase 1: Dependency Mapping
**Goal**: Complete dependency analysis to ensure safe removal
**Depends on**: Nothing (first phase)
**Project**: AURA-NOTES-MANAGER
**Plans**: 2 plans

This phase maps all imports and usages of the files to be removed, identifying any unexpected dependencies.

Plans:
- [ ] RC-01-01: Backend dependency mapping (rag_engine, answer_synthesizer, query.py)
- [x] RC-01-02: Frontend dependency mapping (kg-query feature)

**Files to analyze:**
```python
# Backend
api/rag_engine.py           # Find: who imports RAGEngine
api/routers/query.py        # Find: router registration in main.py
services/answer_synthesizer.py  # Find: imports
services/query_analyzer.py      # Verify: truly dead code

# Frontend  
frontend/src/features/kg-query/  # Find: route registration, navigation
```

**Output**: Dependency report listing all imports and their resolution

---

### Phase 2: Graph API Consolidation
**Goal**: Create minimal graph preview API for staff module review
**Depends on**: Phase 1
**Project**: AURA-NOTES-MANAGER
**Plans**: 2 plans

Extracts the graph visualization logic into a standalone, lightweight API that doesn't require the full RAG engine.

Plans:
- [x] RC-02-01: Create graph preview router (`api/routers/graph_preview.py`)
- [ ] RC-02-02: Add tests for graph preview endpoints

**New API Endpoints:**
```python
# GET /api/v1/graph/modules/{module_id}/preview
# Returns: entities, relationships for module visualization

# GET /api/v1/graph/modules/{module_id}/stats
# Returns: entity counts, relationship counts for module
```

**Dependencies**: Uses existing `graph_manager.py` and `graph_visualizer.py`

---

### Phase 3: Frontend Verification (REVISED + EXTENDED)
**Goal**: Verify AURA-CHAT's existing graph visualization and add module filtering
**Depends on**: Phase 2
**Project**: AURA-CHAT
**Plans**: 4 plans (extended from 2 after decision)

**Discovery:** AURA-CHAT already has a complete 3D graph visualization (`features/graph/GraphPage.tsx`, 712 lines) using Reagraph with multiple layouts, filters, and node details. EntityGraph migration is **NOT NEEDED**.

Plans:
- [x] RC-03-01: Verify AURA-CHAT graph visualization works with current backend
- [x] RC-03-02: Assess module filtering necessity (decision: ADD module filtering)
- [x] RC-03-03: Backend module filtering (server/routers/graph.py)
- [x] RC-03-04: Frontend module filtering (GraphPage.tsx integration)

**AURA-CHAT GraphPage Features (already implemented):**
```
- 5 layout options (radial, hierarchical, circular, force-directed)
- Filter sidebar with node type toggles
- Node detail panel with properties
- WebGL error boundary
- Depth and limit controls
- Full test coverage (GraphPage.test.tsx)
```

**Decision 1:** Skip EntityGraph migration - AURA-CHAT's Reagraph solution is superior to the SVG-based EntityGraph in NOTES-MANAGER. EntityGraph will be deleted with the kg-query feature in Phase 4.

**Decision 2 (MODULE-FILTERING-DECISION.md):** **Add module filtering** to AURA-CHAT graph visualization for architectural consistency. Graph will respect module selection, matching chat behavior. Implementation split into backend (RC-03-03) and frontend (RC-03-04) plans.

**New Plans:**

**RC-03-03: Backend module filtering**
- Add `module_id` parameter to `/graph/data` endpoint (server/routers/graph.py)
- Update Cypher query to filter by module: `MATCH (:Module {id: $module_id})-[:HAS_DOCUMENT]->(doc)-[*1..depth]->(entity)`
- Add tests for module filtering logic
- Estimated effort: 2-3 hours

**RC-03-04: Frontend module filtering**
- Update `GraphQueryParams` to include `module_id` (client/src/types/api.ts)
- Read selected module from localStorage in GraphPage
- Display module name in header, add "Clear Module Filter" option
- Update tests for module-aware graph behavior
- Estimated effort: 2-3 hours

---

### Phase 4: RAG Removal
**Goal**: Remove duplicate RAG services from NOTES-MANAGER
**Depends on**: Phase 3 (Complete)
**Project**: AURA-NOTES-MANAGER
**Plans**: 3 plans

Safely removes all RAG-related code. EntityGraph migration was SKIPPED because AURA-CHAT already has a superior Reagraph-based implementation.

Plans:
- [x] RC-04-01: Remove backend RAG services (rag_engine.py, query.py, answer_synthesizer.py, query_analyzer.py)
- [x] RC-04-02: Remove frontend kg-query feature (entire directory, 9 files, ~3,751 lines)
- [x] RC-04-03: Update main.py router registration, clean imports, final verification

**Execution Order:** RC-04-01 → RC-04-02 → RC-04-03 (sequential, dependencies between plans)

**Files to remove:**
```
# Backend (4 files)
api/rag_engine.py              # DELETE - RAG engine core
api/routers/query.py           # DELETE - Query router
services/answer_synthesizer.py # DELETE - Response generation
services/query_analyzer.py     # DELETE - Dead code (zero imports)

# Frontend (9 files, ~3,751 lines)
frontend/src/features/kg-query/api/kg-query.api.ts
frontend/src/features/kg-query/components/EntityGraph.tsx
frontend/src/features/kg-query/components/GraphFilterPanel.tsx
frontend/src/features/kg-query/components/KGSearchBar.tsx
frontend/src/features/kg-query/components/SearchResultsList.tsx
frontend/src/features/kg-query/components/UnifiedGraphView.tsx
frontend/src/features/kg-query/hooks/useKGQuery.ts
frontend/src/features/kg-query/pages/KGQueryPage.tsx
frontend/src/features/kg-query/types/kg-query.types.ts
```

**Keep:**
```
api/graph_manager.py           # Used by graph preview
api/graph_visualizer.py        # Used by graph preview
api/routers/graph_preview.py   # New minimal API (RC-02)
api/schemas/graph_preview.py   # Response schemas (RC-02)
```

---

### Phase 5: Verification
**Goal**: Ensure both applications work correctly after refactoring
**Depends on**: Phase 4
**Project**: Both
**Plans**: 2 plans

Final verification that the refactoring is complete and both apps function correctly.

Plans:
- [ ] RC-05-01: Run all existing tests, fix any failures
- [ ] RC-05-02: Integration test: module creation → KG processing → graph visualization

**Verification checklist:**
- [ ] NOTES-MANAGER: Module CRUD works
- [ ] NOTES-MANAGER: KG processing works
- [ ] NOTES-MANAGER: Graph preview API returns data
- [ ] CHAT: RAG queries work (unchanged)
- [ ] CHAT: Graph visualization displays module entities
- [ ] No broken imports in either codebase
- [ ] No dead code remnants

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Dependency Mapping | 2/2 | Complete | 2026-01-29 |
| 2. Graph API Consolidation | 2/2 | Complete | 2026-01-29 |
| 3. Frontend Verification | 4/4 | Complete | 2026-01-29 |
| 4. RAG Removal | 3/3 | Complete | 2026-01-29 |
| 5. Verification | 0/2 | Not started | - |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Hidden dependencies | Phase 1 explicitly maps all imports before removal |
| Graph viz regression | Phase 3 migrates before Phase 4 removes |
| Test failures | Phase 5 runs full test suite before completion |
| Rollback needed | Git commits are atomic per-plan, easy revert |

---

## Files Quick Reference

### To Remove (AURA-NOTES-MANAGER)
```
api/rag_engine.py
api/routers/query.py
services/answer_synthesizer.py
services/query_analyzer.py
frontend/src/features/kg-query/
```

### To Keep (AURA-NOTES-MANAGER)
```
api/graph_manager.py
api/graph_visualizer.py
api/routers/graph_preview.py  (NEW - RC-02)
api/schemas/graph_preview.py  (NEW - RC-02)
```

### Already Complete (AURA-CHAT)
```
# Graph visualization already exists - no migration needed
client/src/features/graph/GraphPage.tsx  (712 lines, Reagraph 3D)
client/src/hooks/useGraphQuery.ts

# Module filtering added in RC-03
server/routers/graph.py  (module_id parameter added)
client/src/types/api.ts  (GraphQueryParams.module_id)
```

---

## Next Action

Start **Phase 4: RAG Removal** - Delete duplicate RAG services from AURA-NOTES-MANAGER.

Execute plans in order:

1. `.planning/phases/rc-04-rag-removal/RC-04-01-PLAN.md` (Backend: delete 4 files)
2. `.planning/phases/rc-04-rag-removal/RC-04-02-PLAN.md` (Frontend: delete 9 files)
3. `.planning/phases/rc-04-rag-removal/RC-04-03-PLAN.md` (main.py cleanup, verification)
