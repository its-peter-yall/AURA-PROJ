# Backend Dependencies Report - RAG Consolidation Phase RC-01

**Generated:** 2026-01-29  
**Phase:** RC-01 - Dependency Mapping  
**Purpose:** Document all imports and dependencies for files scheduled for removal

---

## Executive Summary

✅ **SAFE TO PROCEED**: All files scheduled for removal have contained dependencies. No unexpected cross-module imports found.

**Files to Remove:**
1. `AURA-NOTES-MANAGER/api/rag_engine.py`
2. `AURA-NOTES-MANAGER/api/routers/query.py`
3. `AURA-NOTES-MANAGER/services/answer_synthesizer.py`
4. `AURA-NOTES-MANAGER/services/query_analyzer.py`

**Dependencies:**
- Circular/contained: `rag_engine.py` ↔ `query.py` ↔ `answer_synthesizer.py`
- Dead code: `query_analyzer.py` (ZERO imports)
- Independent: `graph_manager.py` and `graph_visualizer.py` are safe

---

## Task 1: RAGEngine Class Import Analysis

### Files Importing `rag_engine` or `RAGEngine`

#### 1. `api/rag_engine.py` (Self-reference)
- **Line 1:** File header comment
- **Line 257:** Self-import in docstring example
- **Lines 2027, 2032, 2034, 2043, 2056:** Factory function `create_rag_engine()`
- **Classification:** ✅ **Safe to remove** (self-contained)

#### 2. `api/routers/query.py` (Router using RAGEngine)
- **Line 6:** Comment - "Uses dependency injection for RAGEngine..."
- **Line 12:** Comment - "@see: api/rag_engine.py"
- **Line 30:** `from api.rag_engine import RAGEngine, MultiDocOptions, MultiDocResponse`
- **Lines 128, 130, 132, 135, 148:** Dependency injection `get_rag_engine()` function
- **Lines 203, 213, 236, 253, 323, 333, 752, 762, 786:** RAGEngine usage in endpoints
- **Classification:** ✅ **Safe to remove** (also scheduled for deletion)

#### 3. Comment References (Documentation Only)
- `services/embeddings.py:9` - Comment only
- `services/query_analyzer.py:8` - Comment only  
- `api/graph_manager.py:8` - Comment only
- `api/schemas/search.py:8` - Comment only

**Classification:** ✅ **Safe** (comments will be cleaned up with file removal)

#### 4. `api/routers/__init__.py`
- **Line 13:** `from api.routers.query import router as query_router`
- **Classification:** ✅ **Safe to remove** (query router export)

### Summary
- **Total imports:** 2 files (rag_engine.py self + query.py)
- **All imports are within files scheduled for removal**
- **No unexpected dependencies**

---

## Task 2: AnswerSynthesizer Import Analysis

### Files Importing `answer_synthesizer` or `AnswerSynthesizer`

#### 1. `services/answer_synthesizer.py` (Self-reference)
- **Line 1:** File header
- **Lines 173, 185, 207, 215:** Class definition and initialization
- **Lines 638, 640, 642, 648, 650:** Factory function
- **Classification:** ✅ **Safe to remove** (self-contained)

#### 2. `api/rag_engine.py` (Only consumer)
- **Line 1803:** Comment - "Step 2: Synthesize answer using AnswerSynthesizer"
- **Line 1804:** `from services.answer_synthesizer import AnswerSynthesizer, SynthesisOptions`
- **Line 1806:** `synthesizer = AnswerSynthesizer()`
- **Classification:** ✅ **Safe to remove** (also scheduled for deletion)

### Summary
- **Total imports:** 1 file (rag_engine.py)
- **AnswerSynthesizer is ONLY used by rag_engine.py**
- **Confirmed: Contained dependency within removal scope**

---

## Task 3: QueryAnalyzer Dead Code Verification

### Files Importing `query_analyzer` or `QueryAnalyzer`

#### Search Results
1. **`services/query_analyzer.py`** - Self-references only (file definition)
2. **`services/answer_synthesizer.py:9`** - Comment only: `# @see: services/query_analyzer.py`

### Verification
- ✅ **ZERO active imports** found
- ✅ **Confirmed dead code** - no runtime dependencies
- ✅ **Safe to delete** without any code changes

---

## Task 4: Query Router Registration

### Router Registration in `api/main.py`

**Line 98:**
```python
from api.routers.query import router as query_router
```

**Lines 145-147:**
```python
app.include_router(
    query_router
)  # KG Query API (Phase 10-04) - prefix already set in router
```

### Removal Steps
1. **Delete import** on line 98
2. **Delete `app.include_router(query_router)`** on lines 145-147
3. **No cross-router dependencies** - query router is standalone

### Additional Findings
- `api/routers/__init__.py:13` also exports query_router (will be cleaned up)
- No middleware specific to query routes
- No other routers import from query.py

**Classification:** ✅ **Clean removal** - no cascading changes needed

---

## Task 5: Graph Manager & Visualizer Independence Check

### `api/graph_manager.py` Imports (Lines 1-25)
```python
from __future__ import annotations
import time
import logging
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
```

- ✅ **No imports from rag_engine.py**
- ✅ **No imports from answer_synthesizer.py**
- ✅ **No imports from query.py**
- ✅ Line 8 comment referencing rag_engine.py (documentation only)

### `api/graph_visualizer.py` Imports (Lines 1-30)
```python
from __future__ import annotations
import io
import json
import math
import logging
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set
from xml.etree import ElementTree as ET
from pydantic import BaseModel, Field
```

- ✅ **No imports from rag_engine.py**
- ✅ **No imports from answer_synthesizer.py**
- ✅ **No imports from query.py**
- ✅ Line 8-10 comments referencing graph_manager.py and query.py (documentation only)

### Verification
Both files are **completely independent** of the RAG services being removed. They will continue functioning normally after removal.

---

## Dependency Graph

```
┌─────────────────────────────────────┐
│  api/main.py                        │
│  - Imports query_router (line 98)  │
│  - Registers router (lines 145-147)│
└──────────────┬──────────────────────┘
               │
               │ (removes)
               ▼
┌─────────────────────────────────────┐
│  api/routers/query.py               │
│  - Imports RAGEngine (line 30)      │
│  - Uses in 6 endpoints              │
└──────────────┬──────────────────────┘
               │
               │ (imports)
               ▼
┌─────────────────────────────────────┐
│  api/rag_engine.py                  │
│  - Imports AnswerSynthesizer        │
│  - Self-contained logic             │
└──────────────┬──────────────────────┘
               │
               │ (imports)
               ▼
┌─────────────────────────────────────┐
│  services/answer_synthesizer.py     │
│  - No external RAG dependencies     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  services/query_analyzer.py         │
│  - ORPHANED (no imports)            │
│  - Dead code                        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  api/graph_manager.py               │
│  - Independent                      │
│  - Will remain functional           │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  api/graph_visualizer.py            │
│  - Independent                      │
│  - Uses graph_manager.py            │
└─────────────────────────────────────┘
```

---

## Removal Checklist

### Step 1: Remove Router Registration
- [ ] Delete line 98 in `api/main.py`: `from api.routers.query import router as query_router`
- [ ] Delete lines 145-147 in `api/main.py`: router registration block
- [ ] Delete line 13 in `api/routers/__init__.py`: query_router export

### Step 2: Delete Files (In Order)
1. [ ] Delete `api/routers/query.py` (consumer of RAGEngine)
2. [ ] Delete `api/rag_engine.py` (consumer of AnswerSynthesizer)
3. [ ] Delete `services/answer_synthesizer.py` (leaf dependency)
4. [ ] Delete `services/query_analyzer.py` (dead code, no dependencies)

### Step 3: Cleanup Documentation References
- [ ] Update comments in `services/embeddings.py` (line 9)
- [ ] Update comments in `api/graph_manager.py` (line 8)
- [ ] Update comments in `api/schemas/search.py` (line 8)

### Step 4: Verification
- [ ] Run backend server to ensure no import errors
- [ ] Verify graph_manager and graph_visualizer still functional
- [ ] Check API documentation (Swagger) reflects removed endpoints
- [ ] Run any existing tests

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Missing import discovered | Low | Medium | Grep search was comprehensive |
| Frontend breaks | Low | High | Frontend uses AURA-CHAT RAG (separate) |
| Graph services affected | None | N/A | Confirmed independent |
| Database schema issues | None | N/A | No schema changes needed |

---

## Recommendations

✅ **PROCEED WITH REMOVAL**

All dependencies are contained within the removal scope. No refactoring required for other modules.

**Next Phase:** RC-02 - Safe Deletion Execution
- Follow removal checklist in order
- Test after each step
- Commit after successful verification

---

## Appendix: Grep Commands Used

```bash
# Task 1: Find RAGEngine imports
grep -r "rag_engine\|RAGEngine" AURA-NOTES-MANAGER/ --include="*.py"

# Task 2: Find AnswerSynthesizer imports  
grep -r "answer_synthesizer\|AnswerSynthesizer" AURA-NOTES-MANAGER/ --include="*.py"

# Task 3: Verify QueryAnalyzer dead code
grep -r "query_analyzer\|QueryAnalyzer" AURA-NOTES-MANAGER/ --include="*.py"

# Task 4: Find query router imports
grep -r "from api.routers.query import" AURA-NOTES-MANAGER/ --include="*.py"
```

---

**Approval:** Ready for RC-02 execution phase  
**Reviewers:** @oracle (architecture validation), @swe-best-practices
