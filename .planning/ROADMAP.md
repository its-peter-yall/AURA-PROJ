# Roadmap: AURA

## Milestones

- [x] **v1.0 M2KG Transformation** — Phases 1-7 (shipped 2026-03-08)
- [x] **v1.1 Multi-Provider LLM Architecture** — Phases 8-13 (shipped 2026-03-16)
- [x] **v1.2 Settings Wiring E2E** — Phases 14-17 (shipped 2026-03-23)

## Phases

<details>
<summary>v1.0 M2KG Transformation (Phases 1-7) — SHIPPED 2026-03-08</summary>

- [x] Phase 1: Database Schema Extension — Neo4j module-centric schema
- [x] Phase 2: Knowledge Graph Processor — Celery async pipeline
- [x] Phase 3: Module Management — CRUD API with hierarchy
- [x] Phase 4: AURA-CHAT Integration — Module filtering, session-based chat
- [x] Phase 5: Study Session System — Session CRUD, message history
- [x] Phase 6: Frontend Implementation — KG processing UI, module selector
- [x] Phase 7: Testing & Optimization — Unit, E2E, performance, load tests

</details>

<details>
<summary>v1.1 Multi-Provider LLM Architecture (Phases 8-13) — SHIPPED 2026-03-16</summary>

- [x] Phase 8: Shared Package Foundation — model_router with Vertex AI provider
- [x] Phase 9: OpenRouter + Streaming — 200+ models, thinking mode
- [x] Phase 10: Cross-App Migration — Façade pattern, AST audit
- [x] Phase 11: Frontend Settings UI — Hierarchical model picker
- [x] Phase 12: Usage & Cost Tracking — Token/cost per request, Recharts dashboard
- [x] Phase 13: Integration & Polish — Cross-provider tests, router overhead benchmark

</details>

<details>
<summary>v1.2 Settings Wiring E2E (Phases 14-17) — SHIPPED 2026-03-23</summary>

- [x] Phase 14: Foundation — resolve_use_case_config(), cache fix, ALLOWED_USE_CASES expansion
- [x] Phase 15: Wire AURA-CHAT Consumers — All 4 consumers route through SettingsStore
- [x] Phase 16: Wire AURA-NOTES-MANAGER Consumers — All 4 consumers route through SettingsStore
- [x] Phase 17: Frontend + Cross-App Validation — Settings pages, E2E tests, AST audit

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-7 | v1.0 | 28/28 | Complete | 2026-03-08 |
| 8-13 | v1.1 | 23/23 | Complete | 2026-03-16 |
| 14-17 | v1.2 | 11/11 | Complete | 2026-03-23 |
| 9 | v1.3 | 4/4 | Complete | 2026-05-23 |

---

## Next

*No active milestone — run `/gsd-new-milestone` to start next cycle*

Available roadmaps for future work:
- RAG Consolidation (Phase 5: Verification remaining)
- KG Enhancement
- AI Enablement

---

## Technology Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.11+ | Backend runtime |
| **FastAPI** | 0.109.0 | API framework |
| **Redis** | 7+ | SettingsStore, caching |
| **React** | 18/19 | Frontend (NOTES/CHAT) |
| **TypeScript** | 5.3+ | Type safety |
| **Playwright** | 1.49+ | E2E testing |
| **shared/model_router** | local | Config resolution + routing |

---

## References

- [PROJECT.md](./PROJECT.md) - Current project state
- [MILESTONES.md](./MILESTONES.md) - Milestone history
- [milestones/](./milestones/) - Archived roadmaps and requirements

### Phase 1: Multi-model chat configuration - allow 1-5 models with default selection in settings, and update chat page to use default

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 0
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 1 to break down)

### Phase 9: I want to add another provider in the settings page along with openrouter. https://docs.generalcompute.com/quickstart 'General Compute' will be the name of the provider. I need to create support for general compute provider in the existing project

**Goal:** Support General Compute provider in shared model_router and settings backend/frontends alongside OpenRouter.
**Requirements**: P9-01, P9-02, P9-03, P9-04, P9-05, P9-06, P9-07, P9-08, P9-09
**Depends on:** Phase 8
**Plans:** 4 plans

Plans:
- [x] Plan 09-01a: General Compute Provider — Core Implementation (shipped 2026-05-23)
- [x] Plan 09-01b: General Compute Provider — Pricing, Exports & Tests (shipped 2026-05-23)
- [x] Plan 09-02: General Compute Key Validation — Both Settings Routers (shipped 2026-05-23)
- [x] Plan 09-03: General Compute Provider — Frontend Settings UI (Both Apps) (shipped 2026-05-23)

---

*Last updated: 2026-05-23 after Phase 9 completion*
