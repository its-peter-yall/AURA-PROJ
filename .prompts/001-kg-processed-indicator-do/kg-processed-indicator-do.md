# KG Processed Indicator Implementation

**Generated:** 2026-01-25
**Prompt:** 001-kg-processed-indicator-do

---

## Stage 1: Research Findings

### Key Files Examined

| File | Location | Purpose |
|------|----------|---------|
| GridView.tsx | `frontend/src/components/explorer/GridView.tsx` | Renders grid items, already imports KGStatusBadge |
| KGStatusBadge.tsx | `frontend/src/features/kg/components/KGStatusBadge.tsx` | Shows status icons for pending/processing/ready/failed |
| ProcessDialog.tsx | `frontend/src/features/kg/components/ProcessDialog.tsx` | Confirmation dialog for batch KG processing |
| useExplorerStore.ts | `frontend/src/stores/useExplorerStore.ts` | Zustand store with selection mode and processDialog state |
| explorer.css | `frontend/src/styles/explorer.css` | Styles for grid items, no disabled state existed |
| kg.types.ts | `frontend/src/features/kg/types/kg.types.ts` | Type: `KGDocumentStatus = 'pending' | 'processing' | 'ready' | 'failed'` |

### Current Implementation Patterns

1. **KG Status Display**: Already uses `KGStatusBadge` component in GridView (line 384)
2. **Selection Mode**: Managed via `selectionMode` boolean in store, toggled from Header
3. **ProcessDialog**: Opens via `openProcessDialog(fileIds, moduleId)` from Header
4. **Status Source**: `item.meta?.kg_status` contains the KG processing status

---

## Stage 2: Implementation Plan

### Changes Required

1. **GridView.tsx**
   - Add `isKGReady` check for each item
   - Add `isDisabledInSelection` computed value
   - Modify `handleClick` to prevent selection of KG-ready items
   - Add visual indicators (green LED) for processed items
   - Add `kg-disabled` class when in selection mode

2. **explorer.css**
   - Add `.grid-item.kg-disabled` style (opacity, cursor)
   - Add `.kg-ready-led` for absolute positioned LED
   - Add `.kg-ready-led-inline` for selection mode LED

3. **useExplorerStore.ts**
   - Add `skippedCount` to ProcessDialogState
   - Update `openProcessDialog` signature

4. **ProcessDialog.tsx**
   - Display skipped count info banner
   - Update completion message to show skipped docs

---

## Stage 3: Code Changes

### GridView.tsx (Lines 251-268)

```typescript
const handleClick = (e: React.MouseEvent, item: FileSystemNode) => {
    e.stopPropagation();

    const itemIds = filteredItems.map(i => i.id);
    
    // Check if note is already KG-processed
    const isKGReady = item.type === 'note' && item.meta?.kg_status === 'ready';

    if (selectionMode) {
        // In selection mode, prevent selecting already-processed notes
        if (isKGReady) {
            return; // Do nothing - item is disabled
        }
        toggleSelect(item.id);
        return;
    }
    // ... rest of click handling
};
```

### GridView.tsx (Lines 326-354)

```typescript
{filteredItems.map((item) => {
    const config = typeConfig[item.type] || typeConfig.note;
    const Icon = config.icon;
    const isSelected = selectedIds.has(item.id);
    const isRenaming = item.id === renamingNodeId;
    // Check if note is already KG-processed
    const isKGReady = item.type === 'note' && item.meta?.kg_status === 'ready';
    // In selection mode, already-processed notes are disabled
    const isDisabledInSelection = selectionMode && isKGReady;

    return (
        <div
            key={item.id}
            className={`grid-item ${isSelected ? 'selected' : ''} ${isDisabledInSelection ? 'kg-disabled' : ''}`}
            onClick={(e) => handleClick(e, item)}
            onDoubleClick={() => handleDoubleClick(item)}
            onContextMenu={(e) => handleContextMenu(e, item)}
            title={isDisabledInSelection ? 'Already processed - will be skipped' : undefined}
        >
            {/* Green LED indicator for KG-ready notes */}
            {isKGReady && !selectionMode && (
                <div className="kg-ready-led" title="Already processed" />
            )}
            
            {/* Selection Checkbox */}
            {selectionMode && (
                <div className="absolute top-2 right-2 text-primary z-10">
                    {isDisabledInSelection ? (
                        <div className="kg-ready-led-inline" title="Already processed - will be skipped" />
                    ) : isSelected ? (
                        <CheckSquare className="h-5 w-5 fill-background" />
                    ) : (
                        <Square className="h-5 w-5 text-zinc-300 dark:text-zinc-600" />
                    )}
                </div>
            )}
            // ...
        </div>
    );
})}
```

### explorer.css (Lines 290-330)

```css
/* KG-processed disabled state in selection mode */
.grid-item.kg-disabled {
    opacity: 0.5;
    cursor: not-allowed;
    position: relative;
}

.grid-item.kg-disabled:hover {
    background: transparent;
}

/* Green LED indicator for KG-ready notes (non-selection mode) */
.kg-ready-led {
    position: absolute;
    top: 8px;
    right: 8px;
    width: 10px;
    height: 10px;
    background: #22c55e;
    border-radius: 50%;
    box-shadow: 0 0 6px rgba(34, 197, 94, 0.6);
}

/* Green LED inline for selection mode (replaces checkbox) */
.kg-ready-led-inline {
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}

.kg-ready-led-inline::before {
    content: '';
    width: 10px;
    height: 10px;
    background: #22c55e;
    border-radius: 50%;
    box-shadow: 0 0 6px rgba(34, 197, 94, 0.6);
}
```

### useExplorerStore.ts

```typescript
interface ProcessDialogState {
    open: boolean;
    fileIds: string[];
    moduleId: string;
    skippedCount: number;  // Count of already-processed docs that were filtered out
}

// Updated function signature
openProcessDialog: (fileIds: string[], moduleId: string, skippedCount?: number) => void;
```

### ProcessDialog.tsx

```typescript
{processDialog.skippedCount > 0 && (
    <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--spacing-sm)',
        padding: 'var(--spacing-sm) var(--spacing-md)',
        background: 'rgba(34, 197, 94, 0.1)',
        border: '1px solid rgba(34, 197, 94, 0.3)',
        borderRadius: 'var(--radius-sm)',
        marginBottom: 'var(--spacing-md)',
        fontSize: '13px',
        color: '#22c55e'
    }}>
        <Info size={16} />
        {processDialog.skippedCount} document(s) already processed — will be skipped
    </div>
)}
```

---

## Verification Results

### ESLint
- **Status**: Passed (no new errors)
- Pre-existing errors in `useKGProcessing.test.tsx` and `UnifiedGraphView.tsx` (unrelated)

### TypeScript Build
- **Status**: ✅ Success
- Build output: `dist/index-D6V8IasK.js` (509.95 kB)
- No type errors in modified files

### Visual Checks (Manual Required)
- [ ] Green LED appears on notes with `kg_status === 'ready'` in normal mode
- [ ] Green LED replaces checkbox for ready notes in selection mode
- [ ] Ready notes are greyed out (50% opacity) in selection mode
- [ ] Clicking ready notes in selection mode does nothing
- [ ] ProcessDialog shows skipped count when `skippedCount > 0`

---

## Files Modified

| File | Type | Changes |
|------|------|---------|
| `frontend/src/components/explorer/GridView.tsx` | Modified | Added isKGReady check, disabled selection, LED indicators |
| `frontend/src/styles/explorer.css` | Modified | Added .kg-disabled, .kg-ready-led styles |
| `frontend/src/stores/useExplorerStore.ts` | Modified | Added skippedCount to ProcessDialogState |
| `frontend/src/features/kg/components/ProcessDialog.tsx` | Modified | Added skipped docs info banner |

---

## Edge Cases Handled

1. **Already-processed docs cannot be selected** - Click handler returns early
2. **Visual feedback** - Greyed out appearance + green LED indicates why item is disabled
3. **Tooltip** - Hover shows "Already processed - will be skipped"
4. **ProcessDialog** - Shows accurate counts including skipped docs

---

## Next Steps (Optional Improvements)

1. **"Select All" with skip notification** - Add select-all button that auto-skips processed and shows count
2. **"Force reprocess" option** - Checkbox in ProcessDialog to include already-processed docs
3. **Failed docs (yellow LED)** - Could add amber LED for `kg_status === 'failed'` with "Retry" option
4. **Batch status refresh** - Polling to update LED states after processing completes
