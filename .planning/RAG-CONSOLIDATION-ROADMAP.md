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

- [ ] **Phase 1: Dependency Mapping** - Map all dependencies, verify removal safety
- [ ] **Phase 2: Graph API Consolidation** - Create simplified graph preview API in NOTES-MANAGER
- [ ] **Phase 3: Frontend Migration** - Move EntityGraph to AURA-CHAT
- [ ] **Phase 4: RAG Removal** - Remove dead RAG code from NOTES-MANAGER
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

### Phase 3: Frontend Migration
**Goal**: Move EntityGraph visualization component to AURA-CHAT
**Depends on**: Phase 2
**Project**: AURA-CHAT, AURA-NOTES-MANAGER
**Plans**: 3 plans

Migrates the graph visualization from NOTES-MANAGER to CHAT, adapting it for student use.

Plans:
- [ ] RC-03-01: Copy EntityGraph component to AURA-CHAT
- [ ] RC-03-02: Create graph feature in AURA-CHAT (`client/src/features/graph/`)
- [ ] RC-03-03: Integrate graph visualization with CHAT's study session UI

**Files to migrate:**
```
FROM: AURA-NOTES-MANAGER/frontend/src/features/kg-query/components/EntityGraph.tsx
TO:   AURA-CHAT/client/src/features/graph/components/EntityGraph.tsx
```

**Adaptations needed:**
- Connect to CHAT's API endpoints
- Style to match CHAT's Cyber Yellow theme
- Integrate with module selection context

---

### Phase 4: RAG Removal
**Goal**: Remove duplicate RAG services from NOTES-MANAGER
**Depends on**: Phase 3
**Project**: AURA-NOTES-MANAGER
**Plans**: 3 plans

Safely removes all RAG-related code now that graph visualization is migrated.

Plans:
- [ ] RC-04-01: Remove backend RAG services
- [ ] RC-04-02: Remove frontend kg-query feature
- [ ] RC-04-03: Update main.py router registration, clean imports

**Files to remove:**
```
# Backend
api/rag_engine.py              # DELETE
api/routers/query.py           # DELETE
services/answer_synthesizer.py # DELETE
services/query_analyzer.py     # DELETE

# Frontend
frontend/src/features/kg-query/pages/        # DELETE
frontend/src/features/kg-query/hooks/        # DELETE
frontend/src/features/kg-query/api/          # DELETE
frontend/src/features/kg-query/components/   # DELETE (after migration)
```

**Keep:**
```
api/graph_manager.py      # Used by graph preview
api/graph_visualizer.py   # Used by graph preview
api/routers/graph_preview.py  # New minimal API
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
| 2. Graph API Consolidation | 1/2 | In progress | - |
| 3. Frontend Migration | 0/3 | Not started | - |
| 4. RAG Removal | 0/3 | Not started | - |
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
api/routers/graph_preview.py  (NEW)
```

### To Create (AURA-CHAT)
```
client/src/features/graph/
  ├── components/EntityGraph.tsx  (migrated)
  ├── hooks/useGraphData.ts
  ├── api/graph.api.ts
  └── index.ts
```

---

## Next Action

Start with **Phase 1: Dependency Mapping** to verify the removal scope is accurate and identify any unexpected dependencies before making changes.

Execute: `.planning/phases/rc-01-dependency-mapping/RC-01-01-PLAN.md`
