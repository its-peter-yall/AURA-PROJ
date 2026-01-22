# Phase 4: AURA-CHAT Module Integration

**Status:** PLANNED
**Started:** 2026-01-19
**Project:** AURA-CHAT

## Overview

Phase 4 extends AURA-CHAT with module-centric functionality, enabling students to:
- Select modules for study
- Query within module context
- Discover cross-module concepts

## Task Breakdown

| Task | Description | Files |
|------|-------------|-------|
| 04-01 | Module-Aware RAG Engine | `rag_engine.py` (extend) |
| 04-02 | Student Module Endpoints | `routers/student_modules.py` (new) |
| 04-03 | Graph Manager Module Methods | `graph_manager.py` (extend) |

## Key Deliverables

1. **Module-Aware RAG** - `query()` method accepts `module_ids` parameter
2. **Cross-Module Discovery** - Find concepts appearing in 2+ modules
3. **Student Module API** - 6 endpoints for module selection and querying
4. **Graph Manager Extensions** - 6 new module-aware query methods

## Performance Targets

| Metric | Target |
|--------|--------|
| RAG query (single module) | < 2s |
| RAG query (multi-module) | < 3s |
| Module document lookup | < 100ms |

## Dependencies

- Phase 3: Module Management (completed) - provides published modules endpoint
- AURA-NOTES-MANAGER API - for fetching published modules
- Redis - session storage for module selections

## Next Steps

Execute 04-01 → 04-02 → 04-03 sequentially (04-02 depends on 04-01).
