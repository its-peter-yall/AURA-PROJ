<!--
META-PROMPT: 002-kg-delete-processed-do
PURPOSE: Implement "Delete from KG" feature for already-processed documents
TYPE: Multi-stage Do prompt (Research → Plan → Execute)
OUTPUT: .prompts/002-kg-delete-processed-do/kg-delete-processed-do.md
CHAIN: References 001-kg-processed-indicator-do implementation
-->

# Delete Processed Documents from Knowledge Graph

## Objective

Implement a feature that allows users to select already-processed documents (those with `kg_status === "ready"`) and remove ALL their traces from the Knowledge Graph, effectively "un-processing" them.

This is the inverse of the KG processing feature - instead of adding documents to the graph, we're removing them completely.

## Context

### Prior Implementation
@.prompts/001-kg-processed-indicator-do/kg-processed-indicator-do.md

### Reference Files - AURA-NOTES-MANAGER
- @AURA-NOTES-MANAGER/frontend/src/components/explorer/GridView.tsx - Current grid with KG-ready indicators
- @AURA-NOTES-MANAGER/frontend/src/stores/useExplorerStore.ts - Selection and dialog state
- @AURA-NOTES-MANAGER/frontend/src/features/kg/components/ProcessDialog.tsx - Existing process dialog pattern
- @AURA-NOTES-MANAGER/frontend/src/features/kg/hooks/useKGProcessing.ts - KG processing hooks

### Reference Files - AURA-CHAT Backend (Graph Operations)
- @AURA-CHAT/backend/graph_manager.py - Contains `delete_document` method (lines 1151-1244) showing comprehensive KG cleanup pattern

### Current Behavior
From 001-kg-processed-indicator-do:
- Notes with `kg_status === "ready"` show a green LED indicator
- In selection mode, these notes are greyed out and cannot be selected for processing
- Users cannot currently remove documents from the KG

## Requirements

### 1. New Selection Mode: "Select Processed Only"
Add a mode where users can ONLY select already-processed documents (opposite of current behavior):
- Toggle between "Select for Processing" (current) and "Select for Removal"
- When in "removal mode", only `kg_status === "ready"` notes are selectable
- Non-processed notes should be greyed out in removal mode

### 2. Delete Confirmation Dialog
Create `DeleteFromKGDialog.tsx` similar to `ProcessDialog.tsx`:
- Warning message explaining what will be deleted:
  - Document node and all relationships
  - All Chunk nodes connected to document
  - Parent chunks if any
  - Orphaned entities (Topic, Concept, Methodology, Finding not connected to other docs)
- Show count of selected documents
- Require explicit confirmation (e.g., type "DELETE" or checkbox)
- Show progress during deletion

### 3. Backend Endpoint
Create new API endpoint for batch KG deletion:
```
POST /v1/kg/delete-batch
Body: { file_ids: string[], module_id: string }
Response: { deleted_count: number, failed: string[], message: string }
```

Reference the deletion pattern from `AURA-CHAT/backend/graph_manager.py:delete_document`:
1. Delete parent chunks (`DETACH DELETE p`)
2. Delete child chunks (`DETACH DELETE c`)
3. Delete document node (`DETACH DELETE d`)
4. Clean up orphaned entities (Topic, Concept, Methodology, Finding not connected to any Document or Chunk)

### 4. Update Note Status After Deletion
After successful deletion:
- Update Firestore `kg_status` from "ready" back to "pending" (or null)
- Clear `kg_processed_at` timestamp
- Note should no longer show green LED indicator

### 5. UI State Updates
- Remove deleted notes from "ready" state in UI
- Show success toast with count
- Optionally refresh explorer tree to reflect updated status

## Deliverables

### Frontend Changes
1. **Header.tsx**: Add toggle between "Process Mode" and "Delete Mode" for selection
2. **GridView.tsx**: Invert selection logic when in delete mode
3. **DeleteFromKGDialog.tsx**: New confirmation dialog component
4. **useKGProcessing.ts**: Add `deleteFromKG` mutation hook
5. **explorerApi.ts**: Add `deleteKGBatch` API function
6. **useExplorerStore.ts**: Add `deleteDialog` state similar to `processDialog`

### Backend Changes
1. **routers/kg.py**: Add `DELETE /v1/kg/delete-batch` endpoint
2. **kg_processor.py** or **graph_manager.py**: Add `delete_documents_from_kg` method

### Type Changes
1. **kg.types.ts**: Add `DeleteBatchRequest`, `DeleteBatchResponse` types

## Workflow

<stage_1_research>
Research the current implementation:
1. How does AURA-NOTES-MANAGER's KG processing store data in Neo4j?
2. What is the relationship structure between Notes in Firestore and Documents in Neo4j?
3. How are Chunks linked to Documents?
4. What entity types exist and how are they connected?
5. How does the backend identify documents to delete?

Key files to examine:
- `AURA-NOTES-MANAGER/api/kg_processor.py` - How documents are stored
- `AURA-NOTES-MANAGER/api/graph_manager.py` - Graph operations
- `AURA-NOTES-MANAGER/api/tasks/document_processing_tasks.py` - How `kg_status` is updated
- `AURA-CHAT/backend/graph_manager.py` - Delete pattern reference

Deliverable: Document the data model and deletion requirements.
</stage_1_research>

<stage_2_plan>
Create implementation plan:
1. Backend: Endpoint and deletion logic
2. Frontend: Dialog, hooks, API calls
3. Store: State management for delete mode
4. Integration: Connect all pieces

Include:
- File paths and approximate line numbers
- Function signatures
- Edge cases (partial failures, concurrent operations)
- Rollback considerations

Deliverable: Detailed implementation plan with file locations.
</stage_2_plan>

<stage_3_execute>
Implement changes following the plan:

1. **Backend first** (enables testing):
   - Add `/v1/kg/delete-batch` endpoint
   - Implement `delete_documents_from_kg` method
   - Update Firestore `kg_status` after deletion

2. **Frontend types and API**:
   - Add types to `kg.types.ts`
   - Add API function to `explorerApi.ts`

3. **Frontend hooks and store**:
   - Add `deleteFromKG` mutation to `useKGProcessing.ts`
   - Add `deleteDialog` and `deleteMode` state to store

4. **Frontend UI**:
   - Create `DeleteFromKGDialog.tsx`
   - Update `Header.tsx` with mode toggle
   - Update `GridView.tsx` for delete mode selection logic

Deliverable: All code changes implemented.
</stage_3_execute>

<verification>
Run these checks:
1. Backend: API returns 200 for valid request, 400 for invalid
2. ESLint: `cd AURA-NOTES-MANAGER/frontend && npm run lint`
3. TypeScript: `cd AURA-NOTES-MANAGER/frontend && npm run build`
4. Manual test scenarios:
   - Select 2+ processed documents
   - Confirm deletion
   - Verify Neo4j no longer contains document/chunks/entities
   - Verify Firestore `kg_status` is reset
   - Verify UI updates (green LED removed)

Document any issues found.
</verification>

<success_criteria>
- [ ] Users can toggle to "Delete Mode" in selection mode
- [ ] Only KG-ready documents are selectable in delete mode
- [ ] Confirmation dialog warns about data loss
- [ ] Backend deletes all related nodes and relationships
- [ ] Orphaned entities are cleaned up
- [ ] Firestore status is reset to "pending"
- [ ] UI reflects updated status (no green LED)
- [ ] ESLint and TypeScript pass
- [ ] No breaking changes to existing functionality
</success_criteria>

<output_location>
Save output to: `.prompts/002-kg-delete-processed-do/kg-delete-processed-do.md`

Include in output:
1. Research findings with file references
2. Implementation plan with line numbers
3. All code changes (full file contents for new files, diffs for modified)
4. Verification results
5. SUMMARY.md with:
   - One-liner: "Added Delete from KG feature for removing processed documents and their graph data"
   - Files modified: List all changed/created files
   - Key decisions: Any UX/architecture choices
   - Edge cases handled
   - Next steps: Optional improvements
</output_location>
