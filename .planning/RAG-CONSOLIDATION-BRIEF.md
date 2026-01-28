# RAG Consolidation Refactoring

**One-liner**: Remove duplicate RAG/query services from AURA-NOTES-MANAGER and consolidate all query functionality in AURA-CHAT.

## Problem

AURA-NOTES-MANAGER contains RAG query services that duplicate AURA-CHAT's functionality. Both apps share the same Neo4j database, creating:

- **Code duplication** - Two separate RAG engines, answer synthesizers, query analyzers
- **Maintenance burden** - Changes must be made in two places
- **Dead code** - `query_analyzer.py` is completely unused despite documentation claiming otherwise
- **Unclear responsibilities** - Staff portal (NOTES-MANAGER) shouldn't handle student queries

## Background

Analysis revealed:

| File | Location | Status |
|------|----------|--------|
| `answer_synthesizer.py` | AURA-NOTES-MANAGER/services | Used by rag_engine |
| `query_analyzer.py` | AURA-NOTES-MANAGER/services | **DEAD CODE** - never imported |
| `rag_engine.py` | AURA-NOTES-MANAGER/api | Active, handles KG queries |
| `routers/query.py` | AURA-NOTES-MANAGER/api | HTTP endpoints for queries |
| `kg-query/` | AURA-NOTES-MANAGER/frontend | Full query UI with graph viz |

**Key insight:** AURA-CHAT already has its own RAG engine (`backend/rag_engine.py`) with no dependency on NOTES-MANAGER. The duplication is unnecessary.

## Success Criteria

How we know it worked:

- [ ] AURA-NOTES-MANAGER has no RAG query services (rag_engine.py, answer_synthesizer.py, query_analyzer.py removed)
- [ ] Graph visualization works in AURA-CHAT (EntityGraph component migrated)
- [ ] NOTES-MANAGER retains graph data API for module preview (simplified endpoint)
- [ ] Both apps share Neo4j without query duplication
- [ ] All existing tests pass after refactoring
- [ ] No broken imports or dead code remnants

## Constraints

- **Shared database** - Both apps connect to the same Neo4j instance
- **Graph visualization** - Must preserve EntityGraph component (just move it)
- **No feature regression** - Staff should still preview module KG structure
- **Incremental approach** - Changes should be atomic and reversible

## Out of Scope

What we're NOT building:

- New RAG capabilities (this is cleanup, not enhancement)
- Changes to AURA-CHAT's existing RAG engine
- Database schema changes
- Authentication/authorization changes
- New UI features beyond migration

## Current State

**Codebase analysis complete:**

```
AURA-NOTES-MANAGER/
├── api/
│   ├── rag_engine.py          # TO REMOVE
│   ├── routers/query.py       # TO REMOVE
│   ├── graph_manager.py       # KEEP
│   └── graph_visualizer.py    # KEEP
├── services/
│   ├── answer_synthesizer.py  # TO REMOVE
│   └── query_analyzer.py      # TO REMOVE (dead code)
└── frontend/src/features/
    └── kg-query/
        ├── pages/             # TO REMOVE
        ├── hooks/             # TO REMOVE  
        ├── api/               # TO REMOVE
        └── components/
            └── EntityGraph.tsx # TO MIGRATE → AURA-CHAT
```

## Architecture After Refactoring

```
AURA-NOTES-MANAGER (Staff Portal)
├── Document/Module Management ✓
├── KG Processing (chunk, embed, extract) ✓
├── Module Publishing ✓
└── Graph Preview API (simplified) ← NEW

AURA-CHAT (Student Portal)
├── Module-Aware RAG ✓ (existing)
├── Study Sessions ✓ (existing)
└── Graph Visualization ← MIGRATED

Shared: Neo4j KG Database
```
