---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - AURA-NOTES-MANAGER/frontend/AGENTS.md
  - AURA-NOTES-MANAGER/frontend/CLAUDE.md
  - AURA-NOTES-MANAGER/frontend/GEMINI.md
autonomous: true
requirements:
  - QUICK-01
must_haves:
  truths:
    - AGENTS.md accurately reflects frontend structure and conventions
    - CLAUDE.md accurately reflects architecture and coding rules
    - GEMINI.md accurately reflects AI integration and development workflow
    - All three files have consistent information
  artifacts:
    - path: AURA-NOTES-MANAGER/frontend/AGENTS.md
      provides: Frontend agent documentation
      min_lines: 150
    - path: AURA-NOTES-MANAGER/frontend/CLAUDE.md
      provides: Claude-specific frontend guide
      min_lines: 150
    - path: AURA-NOTES-MANAGER/frontend/GEMINI.md
      provides: Gemini-specific frontend guide
      min_lines: 150
  key_links:
    - from: AGENTS.md
      to: src/features/kg/
      via: Knowledge Graph feature documentation
    - from: CLAUDE.md
      to: api/client.ts
      via: API layer patterns
    - from: GEMINI.md
      to: services/
      via: AI integration documentation
---

<objective>
Update AGENTS.md, CLAUDE.md, and GEMINI.md in AURA-NOTES-MANAGER/frontend to accurately reflect the current codebase structure, conventions, and development workflow.

Purpose: Ensure AI agents have accurate, up-to-date documentation for the frontend codebase
Output: Three synchronized documentation files with current architecture, file locations, and conventions
</objective>

<execution_context>
@C:/Users/Peter/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/Peter/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@AURA-NOTES-MANAGER/frontend/AGENTS.md
@AURA-NOTES-MANAGER/frontend/CLAUDE.md
@AURA-NOTES-MANAGER/frontend/GEMINI.md
@AURA-NOTES-MANAGER/frontend/src/features/kg/
@AURA-NOTES-MANAGER/frontend/src/api/
@AURA-NOTES-MANAGER/frontend/src/stores/

Current state: All three files were recently updated (2026-03-06) but need verification against actual codebase:
- AGENTS.md: Structure, conventions, agent behavior
- CLAUDE.md: Architecture, Claude-specific rules
- GEMINI.md: AI integration, Gemini-specific notes

Key areas to verify:
1. Knowledge Graph feature in src/features/kg/ (components, hooks, types)
2. API layer in src/api/ (client.ts, explorerApi.ts, audioApi.ts, userApi.ts)
3. State management (useExplorerStore, useAuthStore)
4. Port configuration (5174, not 5173)
5. Testing setup (Vitest + Playwright + Jest for Firestore rules)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Verify and update AGENTS.md</name>
  <files>AURA-NOTES-MANAGER/frontend/AGENTS.md</files>
  <action>
Verify AGENTS.md accurately reflects the current frontend codebase:

1. Check src/features/kg/ exists with components/, hooks/, types/
2. Verify src/api/ structure (client.ts, explorerApi.ts, audioApi.ts, userApi.ts, firebaseClient.ts)
3. Confirm src/stores/ has useExplorerStore.ts and useAuthStore.ts
4. Verify port is 5174 (not 5173) in vite.config.ts
5. Check testing setup: Vitest (unit), Playwright (E2E), Jest (Firestore rules)
6. Verify file header format matches current standard

Update AGENTS.md if any discrepancies found:
- Update "WHERE TO LOOK" table with accurate file paths
- Verify "STRUCTURE" section matches actual directory layout
- Ensure "CONVENTIONS" section reflects current patterns
- Update "File Header Requirements" with correct format

Reference root AGENTS.md for consistent style but keep frontend-specific.
  </action>
  <verify>
    <automated>cat AURA-NOTES-MANAGER/frontend/AGENTS.md | head -50</automated>
  </verify>
  <done>AGENTS.md verified against actual codebase, any discrepancies corrected</done>
</task>

<task type="auto">
  <name>Task 2: Verify and update CLAUDE.md</name>
  <files>AURA-NOTES-MANAGER/frontend/CLAUDE.md</files>
  <action>
Verify CLAUDE.md accurately reflects the current frontend codebase:

1. Verify "ARCHITECTURE" section matches actual src/ structure
2. Check "State Management" section accurately describes Zustand + TanStack Query separation
3. Verify "API Layer" section describes DuplicateError and typed fetch wrappers correctly
4. Confirm "Knowledge Graph Feature" section matches src/features/kg/ contents
5. Check "KEY FILES" table has correct paths
6. Verify port 5174 in DEVELOPMENT section
7. Ensure "CLAUDE CODE RULES" are accurate and complete

Update CLAUDE.md if any discrepancies found:
- Fix any incorrect file paths
- Update architecture description if structure changed
- Ensure port numbers are correct (5174)
- Verify testing commands match package.json scripts

Maintain consistency with AGENTS.md but keep Claude-specific focus.
  </action>
  <verify>
    <automated>cat AURA-NOTES-MANAGER/frontend/CLAUDE.md | head -50</automated>
  </verify>
  <done>CLAUDE.md verified against actual codebase, any discrepancies corrected</done>
</task>

<task type="auto">
  <name>Task 3: Verify and update GEMINI.md</name>
  <files>AURA-NOTES-MANAGER/frontend/GEMINI.md</files>
  <action>
Verify GEMINI.md accurately reflects the current frontend codebase:

1. Verify "ARCHITECTURE" section matches actual src/ structure
2. Check "AI Services Integration" accurately describes backend services integration
3. Verify "API Integration" section matches actual patterns
4. Confirm "Knowledge Graph Feature" section is accurate
5. Check "AUDIO PIPELINE" section describes correct flow
6. Verify "KEY FILES" table has correct paths
7. Ensure port 5174 in DEVELOPMENT section

Update GEMINI.md if any discrepancies found:
- Fix any incorrect file paths
- Update AI service references if changed
- Ensure port numbers are correct (5174)
- Verify backend service paths are correct

Maintain consistency with AGENTS.md and CLAUDE.md but keep Gemini-specific focus.
  </action>
  <verify>
    <automated>cat AURA-NOTES-MANAGER/frontend/GEMINI.md | head -50</automated>
  </verify>
  <done>GEMINI.md verified against actual codebase, any discrepancies corrected</done>
</task>

</tasks>

<verification>
After all tasks complete:
1. All three files have consistent information about:
   - Port number (5174)
   - Directory structure
   - File paths
   - Testing setup
2. Each file maintains its specific focus:
   - AGENTS.md: General agent guidance
   - CLAUDE.md: Claude-specific rules and patterns
   - GEMINI.md: Gemini-specific notes and AI integration
3. File headers and formatting are consistent across all three
</verification>

<success_criteria>
- All three documentation files verified against actual codebase
- Any discrepancies between docs and code corrected
- Port numbers consistent (5174)
- File paths accurate in all "WHERE TO LOOK" / "KEY FILES" sections
- Knowledge Graph feature accurately documented
- Testing setup (Vitest/Playwright/Jest) correctly described
</success_criteria>

<output>
After completion, create `.planning/quick/1-update-agents-md-claude-md-and-gemini-md/quick-1-SUMMARY.md`
</output>
