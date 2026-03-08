```
<objective>
Add HTTP endpoints to AURA-NOTES-MANAGER for hierarchy navigation (departments → semesters → subjects → modules) and update AURA-CHAT to proxy these endpoints with single-module selection. Frontend needs hierarchical drill-down; backend must expose the hierarchy as REST APIs.
</objective>

<context>
@.planning/ROADMAP.md - Phase 6 (Frontend Implementation)
@AURA-NOTES-MANAGER/api/hierarchy.py - Existing read-only hierarchy functions (Firestore)
@AURA-NOTES-MANAGER/api/modules/router.py - Existing module endpoints
@AURA-CHAT/backend/routers/student_modules.py - Current flat module selection API
@AURA-CHAT/client/src/types/api.ts - Frontend types to extend
@AURA-CHAT/client/src/lib/api.ts - Frontend API functions to extend

Previous: 06-02 AURA-CHAT Module Selector UI (hierarchical) planned
Current: Backend endpoints to support hierarchical module selection
</context>

<requirements>
1. AURA-NOTES-MANAGER: Expose hierarchy as HTTP endpoints
2. AURA-CHAT: Proxy hierarchy endpoints from AURA-NOTES-MANAGER
3. Single module selection only (no multi-select, no Redis for selection state)
4. Frontend will call AURA-CHAT endpoints which proxy to AURA-NOTES-MANAGER
5. Endpoints must support filtering: semesters by department, subjects by semester, modules by subject

Data Flow:
```
Frontend                    AURA-CHAT                   AURA-NOTES-MANAGER
   │                           │                              │
   ├─ GET /departments ────────┼── GET /hierarchy/departments ─┼──► Firestore
   │                           │                              │
   ├─ GET /semesters?dept=xxx ─┼── GET /hierarchy/semesters? ──┼──► Firestore
   │                           │    department_id=xxx          │
   │                           │                              │
   ├─ GET /subjects?sem=xxx ───┼── GET /hierarchy/subjects? ───┼──► Firestore
   │                           │    semester_id=xxx            │
   │                           │                              │
   ├─ GET /modules?subj=xxx ───┼── GET /hierarchy/modules? ────┼──► Firestore
   │                           │    subject_id=xxx             │
   │                           │                              │
   └─ POST /query ─────────────┼── query with module_id ───────┼──► Neo4j
```

AURA-NOTES-MANAGER Endpoints (NEW):
- GET /api/v1/hierarchy/departments
- GET /api/v1/hierarchy/semesters?department_id=xxx
- GET /api/v1/hierarchy/subjects?department_id=xxx&semester_id=xxx
- GET /api/v1/hierarchy/modules?department_id=xxx&semester_id=xxx&subject_id=xxx

AURA-CHAT Proxy Endpoints (NEW):
- GET /api/student/hierarchy/departments
- GET /api/student/hierarchy/semesters?department_id=xxx
- GET /api/student/hierarchy/subjects?department_id=xxx&semester_id=xxx
- GET /api/student/hierarchy/modules?department_id=xxx&semester_id=xxx&subject_id=xxx

Removed Endpoints (no longer needed):
- GET /api/student/modules/available (replaced by hierarchy endpoints)
- POST /api/student/modules/select (single module, no Redis needed)
- POST /api/student/modules/deselect (not needed)
- POST /api/student/modules/clear (not needed)
</requirements>

<tasks>
<task>
<type>create</type>
<file>AURA-NOTES-MANAGER/api/hierarchy/models.py</file>
<action>
Create Pydantic models for hierarchy responses.

Purpose:
- Define response schemas for departments, semesters, subjects, modules
- Ensure consistent response format across all hierarchy endpoints

Models to Create:
1. DepartmentResponse: id, code, name
2. SemesterResponse: id, name, year, semester_number
3. SubjectResponse: id, code, name, module_count
4. ModuleHierarchyResponse: id, code, name, description, document_count
5. DepartmentListResponse, SemesterListResponse, SubjectListResponse, ModuleListResponse

Use existing hierarchy.py return format as reference (returns dict with id, label, type, etc.).
</action>
<verify>
1. Check syntax: `python -m py_compile AURA-NOTES-MANAGER/api/hierarchy/models.py`
2. Verify all Pydantic models validate correctly
</verify>
<done>
Hierarchy Pydantic models created
</done>
</task>

<task>
<type>create</type>
<file>AURA-NOTES-MANAGER/api/hierarchy/router.py</file>
<action>
Create FastAPI router with hierarchy HTTP endpoints.

Purpose:
- Expose hierarchy navigation as REST APIs for AURA-CHAT proxy
- Use existing hierarchy.py functions for data fetching

Endpoints to Add:
1. GET /hierarchy/departments - List all departments
2. GET /hierarchy/semesters?department_id=xxx - Get semesters for department
3. GET /hierarchy/subjects?department_id=xxx&semester_id=xxx - Get subjects for semester
4. GET /hierarchy/modules?department_id=xxx&semester_id=xxx&subject_id=xxx - Get modules for subject

Implementation:
- Import get_all_departments, get_semesters_by_department, get_subjects_by_semester, get_modules_by_subject from hierarchy.py
- Add query parameters for filtering
- Return typed responses using hierarchy models
- Handle errors (department not found, etc.)

Response Format:
```json
{
  "items": [...],
  "total": 5
}
```

Mount at /api/v1 prefix when included in main.py.
</action>
<verify>
1. Check syntax: `python -m py_compile AURA-NOTES-MANAGER/api/hierarchy/router.py`
2. Verify endpoints have proper query parameters
3. Test response format matches frontend expectations
</verify>
<done>
Hierarchy HTTP router created with 4 endpoints
</done>
</task>

<task>
<type>update</type>
<file>AURA-NOTES-MANAGER/api/main.py</file>
<action>
Add hierarchy router to main.py.

Action:
- Import hierarchy_router from api.hierarchy.router
- Include router with prefix "/api/v1"

Existing imports pattern:
```python
from api.modules import modules_router
app.include_router(modules_router, prefix="/api/v1")
```

Add similarly for hierarchy_router.
</action>
<verify>
1. Check syntax: `python -m py_compile AURA-NOTES-MANAGER/api/main.py`
2. Verify router is included
</verify>
<done>
Main app updated with hierarchy router
</done>
</task>

<task>
<type>update</type>
<file>AURA-CHAT/backend/routers/student_modules.py</file>
<action>
Update student_modules.py to add hierarchy proxy endpoints and simplify for single-module selection.

Purpose:
- Proxy hierarchy calls from AURA-NOTES-MANAGER
- Single module selection (no multi-select, no Redis storage)

Changes:

1. ADD new proxy endpoints:
```python
# Proxy to AURA-NOTES-MANAGER hierarchy endpoints
HIERARCHY_BASE_URL = "http://127.0.0.1:8001/api/v1/hierarchy"

@router.get("/hierarchy/departments")
async def get_departments() -> Dict[str, Any]:
    """Proxy: Get all departments from AURA-NOTES-MANAGER."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{HIERARCHY_BASE_URL}/departments", timeout=10.0)
        return response.json()

@router.get("/hierarchy/semesters")
async def get_semesters(department_id: str) -> Dict[str, Any]:
    """Proxy: Get semesters for department."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{HIERARCHY_BASE_URL}/semesters",
            params={"department_id": department_id},
            timeout=10.0
        )
        return response.json()

@router.get("/hierarchy/subjects")
async def get_subjects(
    department_id: str,
    semester_id: str
) -> Dict[str, Any]:
    """Proxy: Get subjects for semester."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{HIERARCHY_BASE_URL}/subjects",
            params={"department_id": department_id, "semester_id": semester_id},
            timeout=10.0
        )
        return response.json()

@router.get("/hierarchy/modules")
async def get_modules(
    department_id: str,
    semester_id: str,
    subject_id: str
) -> Dict[str, Any]:
    """Proxy: Get modules for subject."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{HIERARCHY_BASE_URL}/modules",
            params={
                "department_id": department_id,
                "semester_id": semester_id,
                "subject_id": subject_id
            },
            timeout=10.0
        )
        return response.json()
```

2. REMOVE endpoints no longer needed:
- GET /modules/available (replaced by hierarchy endpoints)
- POST /modules/select (single module, no Redis needed)
- POST /modules/deselect (not needed)
- POST /modules/clear (not needed)

3. UPDATE query endpoint:
- Change from module_ids (list) to single module_id
- Remove enable_cross_module parameter (not applicable for single module)
- RAG query uses single module_id for filtering

Preserve:
- StudentQueryRequest with single module_id
- QueryResponse
- _get_selected_modules (may be used elsewhere, can deprecate later)
</action>
<verify>
1. Check syntax: `python -m py_compile AURA-CHAT/backend/routers/student_modules.py`
2. Verify new endpoints have proper query parameters
3. Verify removed endpoints are cleanly deleted
4. Test proxy endpoints return correct data
</verify>
<done>
student_modules.py updated with hierarchy proxies and single-module support
</done>
</task>

<task>
<type>update</type>
<file>AURA-CHAT/client/src/types/api.ts</file>
<action>
Extend types/api.ts with hierarchy types for frontend.

Types to Add:
1. Department: id, code, name
2. Semester: id, name, year, semester_number
3. Subject: id, code, name, module_count
4. Module: id, code, name, description, document_count
5. Hierarchy responses (DepartmentList, SemesterList, etc.)

Preserve existing types (APIResponse, Document types, Chat types, Graph types).

Export types for use in ModuleSelector and hooks.
</action>
<verify>
1. Check syntax: Verify TypeScript compilation
2. Verify all type interfaces are complete
</verify>
<done>
types/api.ts extended with hierarchy types
</done>
</task>

<task>
<type>update</type>
<file>AURA-CHAT/client/src/lib/api.ts</file>
<action>
Extend lib/api.ts with hierarchy API functions for frontend.

Functions to Add:
1. getDepartments() - GET /api/student/hierarchy/departments
2. getSemesters(department_id) - GET /api/student/hierarchy/semesters?department_id=xxx
3. getSubjects(department_id, semester_id) - GET /api/student/hierarchy/subjects?dept=xxx&sem=xxx
4. getModules(department_id, semester_id, subject_id) - GET /api/student/hierarchy/modules?...

Remove functions no longer needed:
- getAvailableModules() (replaced by hierarchy functions)
- selectModules() (not needed for single module)
- deselectModules() (not needed)
- clearModules() (not needed)

Use existing axios instance and error handling patterns.
</action>
<verify>
1. Check syntax: Verify TypeScript compilation
2. Verify all API functions are exported
</verify>
<done>
lib/api.ts extended with hierarchy API functions
</done>
</task>
</tasks>

<output>
SUMMARY.md in `.planning/phases/06-frontend/06-02b-BACKEND-SUMMARY.md`
</output>

<success_criteria>
- [ ] AURA-NOTES-MANAGER: 4 new hierarchy HTTP endpoints
- [ ] AURA-CHAT: 4 new proxy endpoints for hierarchy
- [ ] AURA-CHAT: Query endpoint supports single module_id
- [ ] AURA-CHAT: Removed multi-select Redis logic
- [ ] Frontend types: types/api.ts extended with hierarchy types
- [ ] Frontend API: lib/api.ts extended with hierarchy functions
- [ ] Endpoints return consistent response format
- [ ] All Python files pass py_compile
- [ ] TypeScript compiles without errors
</success_criteria>

<checkpoint:human-verify>
Test via curl/Postman:
1. GET http://127.0.0.1:8001/api/v1/hierarchy/departments
2. GET http://127.0.0.1:8000/api/student/hierarchy/departments (proxy)
3. GET http://127.0.0.1:8000/api/student/hierarchy/semesters?department_id=xxx
4. GET http://127.0.0.1:8000/api/student/hierarchy/subjects?dept=xxx&sem=xxx
5. GET http://127.0.0.1:8000/api/student/hierarchy/modules?dept=xxx&sem=xxx&subj=xxx
6. POST /api/student/query with single module_id
</checkpoint:human-verify>
