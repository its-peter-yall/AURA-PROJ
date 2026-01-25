<!--
META-PROMPT: 001-kg-processed-indicator-do
PURPOSE: Implement "already processed" green LED indicator for KG-processed files
TYPE: Multi-stage Do prompt (Research → Plan → Execute)
OUTPUT: .prompts/001-kg-processed-indicator-do/kg-processed-indicator-do.md
-->

<workflow>
<stage_1_research>
Research the current explorer UI implementation to understand:
1. How GridView.tsx renders file items and displays metadata
2. How kg_status is currently displayed (look for KGStatusBadge component)
3. How selection mode works in the explorer
4. How useExplorerStore manages selection state
5. How ProcessDialog.tsx gets file_ids for processing

Key files to examine:
- frontend/src/components/explorer/GridView.tsx
- frontend/src/features/kg/components/ProcessDialog.tsx
- frontend/src/stores/useExplorerStore.ts
- frontend/src/features/kg/hooks/useKGProcessing.ts
- frontend/src/api/explorerApi.ts

Deliverable for this stage: Document current implementation patterns and identify exact locations for changes.
</stage_1_research>

<stage_2_plan>
Create a detailed implementation plan:
1. Add green LED icon component for "ready" status
2. Modify GridView.tsx to:
   - Show green LED on notes with kg_status === "ready"
   - Apply visual disabled state (greyed out) for ready notes in selection mode
3. Modify selection logic in useExplorerStore or GridView to:
   - Filter out already-processed docs from selection when entering selection mode
   - Keep track of filtered vs available selections
4. Update ProcessDialog.tsx to:
   - Show accurate count of documents being queued
   - Display info about skipped already-processed docs
5. Add tooltip explaining why items are disabled

Consider edge cases:
- What if user manually deselects an already-processed doc?
- Should there be a "Force include" checkbox?
- How to handle failed docs (yellow LED)?

Deliverable: Implementation plan with file paths and line numbers for changes.
</stage_2_plan>

<stage_3_execute>
Implement the changes according to the plan:

1. Create/reuse a status indicator component:
   - Location: frontend/src/features/kg/components/KGStatusBadge.tsx (if exists) or GridView.tsx
   - Show green LED for kg_status === "ready"
   - Style: small circular indicator (~8px), green color, subtle glow effect

2. Update GridView.tsx:
   - Add status indicator for each note item
   - When in selection mode, apply disabled styling to ready docs
   - Prevent click selection for ready docs (or allow with visual feedback)

3. Update ProcessDialog.tsx:
   - Count only non-ready docs for processing
   - Display message like "3 documents ready to process, 2 already processed"

4. Add tooltip component for disabled items:
   - "Already processed - click to force reprocess" (if implementing force option)

Deliverable: All code changes implemented and tested.
</stage_3_execute>

<verification>
Run these checks:
1. ESLint passes: cd frontend && npm run lint
2. TypeScript compiles: cd frontend && npm run typecheck (if available)
3. Visual check: Verify green LED appears on ready docs
4. Selection check: Verify ready docs are visually disabled in selection mode
5. ProcessDialog check: Verify accurate counts shown

Document any issues found.
</verification>

<success_criteria>
- Green LED indicator appears on already-processed notes
- Already-processed notes are visually greyed out in selection mode
- ProcessDialog shows accurate counts (queued vs skipped)
- ESLint passes with no new warnings
- No breaking changes to existing functionality
</success_criteria>

<output_location>
Save final output to: .prompts/001-kg-processed-indicator-do/kg-processed-indicator-do.md

The output must include:
1. Research findings with file references
2. Implementation plan with line numbers
3. All code changes (full file contents for modified files)
4. Verification results
5. SUMMARY.md with:
   - One-liner: "Added green LED indicator and disabled selection for already-processed KG files"
   - Files modified: List of files changed
   - Key decisions: Any UX choices made
   - Next steps: Optional improvements
</output_location>
