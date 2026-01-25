# SUMMARY

**One-liner:** Added green LED indicator and disabled selection for already-processed KG files

## Files Modified

- `AURA-NOTES-MANAGER/frontend/src/components/explorer/GridView.tsx` - Added KG-ready detection, disabled selection, LED indicators
- `AURA-NOTES-MANAGER/frontend/src/styles/explorer.css` - Added .kg-disabled, .kg-ready-led, .kg-ready-led-inline styles
- `AURA-NOTES-MANAGER/frontend/src/stores/useExplorerStore.ts` - Added skippedCount to ProcessDialogState
- `AURA-NOTES-MANAGER/frontend/src/features/kg/components/ProcessDialog.tsx` - Added skipped docs info banner

## Key Decisions

1. **Green LED placement**: Top-right corner (8px from edges), 10px diameter with green glow
2. **Disabled state**: 50% opacity + cursor: not-allowed (greyed out appearance)
3. **Selection prevention**: Click handler returns early for KG-ready items - no toggle allowed
4. **LED in selection mode**: Replaces checkbox with inline LED indicator for processed items
5. **Info banner color**: Green (#22c55e) to match LED and indicate positive "already done" status

## Next Steps

- Add "Select All" button that shows skipped count
- Consider "Force reprocess" checkbox for edge cases
- Add amber LED for failed docs with retry option
