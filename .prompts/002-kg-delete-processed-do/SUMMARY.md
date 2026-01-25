# SUMMARY: Delete from KG Feature

## One-liner
Added "Delete from KG" feature enabling users to remove processed documents and their graph data from the Knowledge Graph.

## Files Modified

### Backend
- `api/modules/models.py` - Added `BatchDeleteRequest`, `BatchDeleteResponse` models
- `api/graph_manager.py` - Added `delete_document()` method for Neo4j cleanup
- `api/kg/router.py` - Added `POST /kg/delete-batch` endpoint

### Frontend
- `frontend/src/features/kg/types/kg.types.ts` - Added delete type interfaces
- `frontend/src/api/explorerApi.ts` - Added `deleteKGBatch()` API function
- `frontend/src/features/kg/hooks/useKGProcessing.ts` - Added `deleteFiles` mutation
- `frontend/src/stores/useExplorerStore.ts` - Added delete mode and dialog state
- `frontend/src/components/explorer/GridView.tsx` - Updated selection logic
- `frontend/src/components/layout/Header.tsx` - Added mode toggle UI
- `frontend/src/pages/ExplorerPage.tsx` - Added DeleteFromKGDialog render

### Files Created
- `frontend/src/features/kg/components/DeleteFromKGDialog.tsx` - Confirmation dialog

## Key Decisions

1. **Mode toggle pattern**: Reused selection mode but inverted logic rather than adding separate selection system
2. **Same dialog pattern**: DeleteFromKGDialog matches ProcessDialog styling for consistency
3. **Firestore reset**: Set `kg_status` to "pending" (not null) to maintain schema consistency
4. **Orphan cleanup**: Delete entities with no remaining connections to prevent graph pollution
5. **Preserve files**: Original PDFs are NOT deleted - only graph data

## Edge Cases Handled

- Documents not found → skipped, added to failed list
- Wrong module ownership → rejected
- Non-KG-ready documents → rejected (nothing to delete)
- Neo4j failures → caught, logged, reported
- Partial batch failures → success count + failed list returned

## Verification

- ✅ ESLint: No new errors
- ✅ TypeScript build: Successful
- ✅ All success criteria met

## Next Steps (Optional)

1. Add "Select all KG-ready" bulk selection helper
2. Implement soft-delete with recovery window
3. Add per-document progress for large batches
4. Require typing "DELETE" for extra confirmation
