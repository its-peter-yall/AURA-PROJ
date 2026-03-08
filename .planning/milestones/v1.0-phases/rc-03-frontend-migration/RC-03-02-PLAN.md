---
phase: rc-03-frontend-verification
type: execute
plan: RC-03-02
---

<objective>
Assess whether module filtering is needed for AURA-CHAT graph visualization.

Purpose: Determine if AURA-CHAT's graph should filter by selected module(s) for focused study sessions.
Output: Decision document on module filtering and implementation if needed.
</objective>

<execution_context>
@~/.config/opencode/skills/create-plans/workflows/execute-phase.md
@~/.config/opencode/skills/create-plans/templates/summary.md
</execution_context>

<context>
@.planning/RAG-CONSOLIDATION-BRIEF.md
@.planning/RAG-CONSOLIDATION-ROADMAP.md
@.planning/phases/rc-03-frontend-verification/RC-03-01-SUMMARY.md
@AURA-CHAT/client/src/features/graph/GraphPage.tsx
@AURA-CHAT/client/src/hooks/useGraphQuery.ts
@AURA-CHAT/client/src/types/index.ts
</context>

<tasks>

<task type="auto">
  <name>Task 1: Analyze current GraphQueryParams</name>
  <files>AURA-CHAT/client/src/types/index.ts, AURA-CHAT/client/src/types/api.ts</files>
  <action>
    Check if GraphQueryParams already supports module filtering:
    
    1. Find GraphQueryParams type definition
    2. Check for module_id or module_ids parameter
    3. Check if backend /graph/data endpoint accepts module filter
    
    Document current state:
    - Does module filtering exist? (yes/no)
    - If yes, how is it used?
    - If no, is it needed for the module-centric architecture?
  </action>
  <verify>GraphQueryParams definition found and analyzed</verify>
  <done>Module filtering capability documented</done>
</task>

<task type="auto">
  <name>Task 2: Check module selection context in AURA-CHAT</name>
  <files>AURA-CHAT/client/src/features/modules/, AURA-CHAT/client/src/features/chat/</files>
  <action>
    Understand how modules are selected in AURA-CHAT:
    
    1. Find module selector component
    2. Check if selected modules are stored in context/state
    3. Determine if chat queries filter by module
    4. Assess if graph should also filter by selected module
    
    The BRIEF describes a module-centric architecture where students select modules for study.
    Graph visualization may need to respect this selection.
  </action>
  <verify>Module selection mechanism documented</verify>
  <done>Module context usage understood</done>
</task>

<task type="checkpoint:decision" gate="blocking">
  <decision>Should module filtering be added to AURA-CHAT graph visualization?</decision>
  <context>
    AURA-CHAT's graph currently shows all documents/entities.
    The module-centric architecture suggests users study within module boundaries.
    Adding module filtering would focus the graph on selected module(s).
  </context>
  <options>
    <option id="add-filtering">
      <name>Add module filtering</name>
      <pros>Consistent with module-centric architecture; focused study experience; matches chat behavior</pros>
      <cons>Additional development work; may limit cross-module discovery</cons>
    </option>
    <option id="skip-filtering">
      <name>Skip module filtering</name>
      <pros>Less work; allows seeing full knowledge graph; cross-module discovery</pros>
      <cons>May be overwhelming; inconsistent with chat's module focus</cons>
    </option>
    <option id="defer-filtering">
      <name>Defer to future phase</name>
      <pros>Keeps RAG consolidation focused; can add later based on user feedback</pros>
      <cons>Technical debt; may need to revisit this decision</cons>
    </option>
  </options>
  <resume-signal>Select: add-filtering, skip-filtering, or defer-filtering</resume-signal>
</task>

<task type="auto">
  <name>Task 3: Document decision and rationale</name>
  <files>.planning/phases/rc-03-frontend-verification/MODULE-FILTERING-DECISION.md</files>
  <action>
    Based on checkpoint decision, document:
    
    1. Decision made (add/skip/defer)
    2. Rationale for the decision
    3. If "add-filtering":
       - Implementation approach
       - Files to modify
       - Effort estimate
    4. If "skip-filtering" or "defer-filtering":
       - Why this is acceptable
       - Conditions that would trigger revisiting
    5. Impact on Phase 4 (RAG Removal)
  </action>
  <verify>Decision document created</verify>
  <done>MODULE-FILTERING-DECISION.md created with clear rationale</done>
</task>

<task type="auto">
  <name>Task 4: Update roadmap if implementation needed</name>
  <files>.planning/RAG-CONSOLIDATION-ROADMAP.md</files>
  <action>
    If decision was "add-filtering":
    - Add implementation tasks to Phase 3 or create Phase 3.5
    - Update plan count in progress table
    
    If decision was "skip-filtering" or "defer-filtering":
    - Note decision in roadmap
    - Proceed to Phase 4
    
    Ensure roadmap reflects current state accurately.
  </action>
  <verify>Roadmap updated if needed</verify>
  <done>Roadmap reflects decision</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] GraphQueryParams analyzed for module support
- [ ] Module selection context understood
- [ ] Decision made on module filtering
- [ ] Decision documented with rationale
- [ ] Roadmap updated if needed
</verification>

<success_criteria>
- All tasks completed
- Clear decision on module filtering (add/skip/defer)
- Decision documented for future reference
- Ready to proceed to Phase 4 (RAG Removal)
</success_criteria>

<output>
After completion, create `.planning/phases/rc-03-frontend-verification/RC-03-02-SUMMARY.md`
</output>
