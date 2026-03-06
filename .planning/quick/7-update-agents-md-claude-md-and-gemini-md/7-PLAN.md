---
phase: quick
plan: 7
type: execute
wave: 1
depends_on: []
files_modified:
  - ./AGENTS.md
  - ./CLAUDE.md
  - ./GEMINI.md
autonomous: true
requirements:
  - QUICK-07
must_haves:
  truths:
    - All three documentation files have updated generation dates
    - Documentation accurately reflects current codebase structure
    - Cross-references between files are consistent
  artifacts:
    - path: "./AGENTS.md"
      provides: "Project knowledge base for AI agents"
      min_lines: 500
    - path: "./CLAUDE.md"
      provides: "Claude Code specific instructions"
      min_lines: 500
    - path: "./GEMINI.md"
      provides: "Google Cloud/Gemini context"
      min_lines: 800
  key_links:
    - from: "AGENTS.md"
      to: "CLAUDE.md"
      via: "Reference to root coding standards"
    - from: "GEMINI.md"
      to: "CLAUDE.md"
      via: "Reference to coding standards section"
---

<objective>
Update AGENTS.md, CLAUDE.md, and GEMINI.md to reflect the current codebase state as of March 2026.

Purpose: Ensure AI assistants have accurate, up-to-date context when working with the AURA project.
Output: Three synchronized documentation files with updated timestamps, consistent structure, and accurate codebase references.
</objective>

<execution_context>
@C:/Users/Peter/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/Peter/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md
@./AGENTS.md
@./GEMINI.md

## Current State Analysis

All three files were generated on 2026-02-02. The codebase has evolved since then:
- Quick task 1 completed on 2026-02-23 (DOM confirm dialog replacement)
- Phase 5 (Study Session System) marked as COMPLETED
- Current date is 2026-03-06

## Synchronization Requirements

1. **AGENTS.md** - Project knowledge base (general AI context)
2. **CLAUDE.md** - Claude Code specific instructions (nearly identical to AGENTS.md)
3. **GEMINI.md** - Google Cloud/Gemini specific context (additional Vertex AI content)

## Key Updates Needed

- Update generation date to 2026-03-06
- Verify Phase 5 is marked COMPLETED in all files
- Ensure consistency across all three files for shared sections
- Update STATE.md reference to include recent quick task
</context>

<tasks>

<task type="auto">
  <name>Task 1: Update AGENTS.md with current state</name>
  <files>./AGENTS.md</files>
  <action>
Update the AGENTS.md file to reflect the current codebase state:

1. Update generation date from "2026-02-02" to "2026-03-06"
2. In ROADMAP.md reference section, verify Phase 5 (Study Session System) shows as "COMPLETED ✓" (already correct)
3. Add a note about the recent quick task completion (2026-02-23) in the Recent Changes section
4. Ensure all file paths and references are still accurate
5. Verify the "Recent Architectural Changes" section is up to date

The file should maintain its current structure but reflect the most current project state.
  </action>
  <verify>
    <automated>grep -n "Generated:" ./AGENTS.md | head -1</automated>
  </verify>
  <done>AGENTS.md shows generation date of 2026-03-06 and accurately reflects current project state</done>
</task>

<task type="auto">
  <name>Task 2: Update CLAUDE.md with current state</name>
  <files>./CLAUDE.md</files>
  <action>
Update the CLAUDE.md file to reflect the current codebase state:

1. Update generation date from "2026-02-02" to "2026-03-06"
2. Ensure consistency with AGENTS.md for shared sections
3. Verify all conductor documentation references are current
4. Confirm the "Recent Architectural Changes" section matches AGENTS.md
5. Ensure the file header requirements section is identical across both files

CLAUDE.md serves as the primary instruction file for Claude Code, so it should be the most accurate and comprehensive.
  </action>
  <verify>
    <automated>grep -n "Generated:" ./CLAUDE.md | head -1</automated>
  </verify>
  <done>CLAUDE.md shows generation date of 2026-03-06 and is synchronized with AGENTS.md</done>
</task>

<task type="auto">
  <name>Task 3: Update GEMINI.md with current state</name>
  <files>./GEMINI.md</files>
  <action>
Update the GEMINI.md file to reflect the current codebase state:

1. Update generation date from "2026-02-02" to "2026-03-06"
2. Synchronize the shared sections (Structure, Where to Look, Conventions, Commands, Notes, Environment Variables, Testing Strategy) with AGENTS.md and CLAUDE.md
3. Keep the Google Cloud-specific sections intact:
   - Google Cloud Integration
   - Dual SDK Architecture
   - AURA-CHAT Specifics (Thinking Mode, RAG Engine)
   - AURA-NOTES-MANAGER Specifics (Deepgram, Audio Pipeline, KG Processing)
4. Ensure the Agent Behaviour section matches the other files
5. Verify all Gemini model specifications are current

GEMINI.md has additional Vertex AI and Google Cloud content that should be preserved while updating the common sections.
  </action>
  <verify>
    <automated>grep -n "Generated:" ./GEMINI.md | head -1</automated>
  </verify>
  <done>GEMINI.md shows generation date of 2026-03-06, synchronized common sections, and preserved Google Cloud-specific content</done>
</task>

</tasks>

<verification>
- All three files have generation date of 2026-03-06
- Shared sections (Structure, Conventions, Commands, Testing) are consistent across files
- GEMINI.md retains its unique Google Cloud and Vertex AI content
- All files accurately reflect Phase 5 as COMPLETED
- Recent quick task (2026-02-23) is referenced
</verification>

<success_criteria>
- AGENTS.md, CLAUDE.md, and GEMINI.md all updated with current generation date
- Cross-file consistency verified for shared sections
- Google Cloud-specific content in GEMINI.md preserved
- All internal references and links are accurate
</success_criteria>

<output>
After completion, create `.planning/quick/7-update-agents-md-claude-md-and-gemini-md/7-SUMMARY.md`
</output>
