# Roadmap: AURA v1.2 — Settings Wiring E2E

**Created:** 2026-03-23
**Phases:** 4 (Phase 14-17)
**Requirements:** 12/12 mapped

## Overview

AURA v1.2 wires SettingsStore end-to-end so every AI feature in both applications respects per-use-case model/provider configuration. Currently only chat in AURA-CHAT is fully wired — the remaining 7 consumers either bypass SettingsStore with hardcoded env vars, read the `model` field while ignoring `provider`, or are blocked by an incomplete `ALLOWED_USE_CASES` allowlist. This milestone introduces a shared `resolve_use_case_config()` utility, expands the use-case allowlist, fixes caching pitfalls, wires all 8 consumers across both apps, and validates the full settings→behavior flow with E2E tests.

## Milestones

- [x] **v1.0 M2KG Transformation** — Phases 1-7 (shipped 2026-03-08)
- [x] **v1.1 Multi-Provider LLM Architecture** — Phases 8-13 (shipped 2026-03-16)
- [ ] **v1.2 Settings Wiring E2E** — Phases 14-17 (in progress)

---

## Phases

- [x] **Phase 14: Foundation — Config Resolver + Allowlist + Cache Fixes** - Shared `resolve_use_case_config()` utility, expanded `ALLOWED_USE_CASES`, zombie-None cache fix, env-var fallback chain (completed 2026-03-23)
- [x] **Phase 15: Wire AURA-CHAT Consumers** - Gatekeeper, entity extractor, embeddings, and relationship extraction all pass explicit `provider` from SettingsStore to ModelRouter (completed 2026-03-23)
- [x] **Phase 16: Wire AURA-NOTES-MANAGER Consumers** - KG processor, entity extractor, embeddings, and summarizer all route through ModelRouter with SettingsStore config (completed 2026-03-23)
- [x] **Phase 17: Frontend + Cross-App Validation** - Settings page UI updated with new use cases, Playwright E2E tests for settings→behavior flow, cross-app config propagation verified (completed 2026-03-23)

## Phase Details

### Phase 14: Foundation — Config Resolver + Allowlist + Cache Fixes
x`x`
**Goal:** All use cases are configurable via the settings API, and a shared config resolution utility provides `{provider, model}` to every consumer with a reliable fallback chain

**Depends on:** Nothing (first phase of v1.2; v1.1 complete)

**Requirements:** API-01, API-02, FB-01, FB-02

**Success Criteria** (what must be TRUE):
  1. PUT `/api/v1/settings/defaults/gatekeeper` returns 200 instead of 400, and the configured provider/model appear on GET
  2. PUT `/api/v1/settings/defaults/relationship_extraction` returns 200 in both AURA-CHAT and AURA-NOTES-MANAGER settings routers
  3. `resolve_use_case_config("gatekeeper")` returns `{provider, model}` from SettingsStore when Redis is reachable, falling back to env vars when Redis is down, with a logged warning — never crashes
  4. When Redis recovers after a failure, SettingsStore values resume within 30 seconds (no 5-minute zombie-None cache)
  5. Unit tests cover all resolution paths: SettingsStore hit, env-var fallback, hardcoded default, Redis-down scenario

**Plans:** 2/2 plans complete

Plans:
- [ ] 14-01-PLAN.md — Sentinel cache fix + resolve_use_case_config() utility + tests
- [ ] 14-02-PLAN.md — ALLOWED_USE_CASES expansion in both routers + router tests

---

### Phase 15: Wire AURA-CHAT Consumers

**Goal:** Every LLM call in AURA-CHAT reads provider and model from SettingsStore and passes them explicitly to ModelRouter — no more hardcoded env vars or `/` heuristic provider guessing

**Depends on:** Phase 14

**Requirements:** PP-01, PP-02, PP-03, PP-04

**Success Criteria** (what must be TRUE):
  1. Entity extractor produces responses using the provider configured in SettingsStore for `entity_extraction` — not the default Vertex AI (verified by setting OpenRouter and observing the response metadata)
  2. Gatekeeper routes through ModelRouter with the configured provider, including OpenRouter — the blanket OpenRouter skip at `llm_gatekeeper.py:153-159` is removed and JSON mode works per-provider
  3. Embeddings call `router.embed(provider=cfg["provider"])` with the provider from SettingsStore, and the `VERTEX_PROJECT` check only fires when `provider == "vertex_ai"`
  4. Relationship extraction reads from SettingsStore with env var fallback, passes `{provider, model}` to ModelRouter, and logs which source it used
  5. Changing the provider for any use case in the settings page takes effect on the next LLM call without process restart

**Plans:** 3 plans in 2 waves

Plans:
- [x] 15-01-PLAN.md — Shared infrastructure: provider propagation in VertexCompatModel + get_model() + OpenRouter JSON mode (Wave 1)
- [x] 15-02-PLAN.md — Wire entity extraction + relationship extraction to resolve_use_case_config() (Wave 2) ✅
- [x] 15-03-PLAN.md — Wire gatekeeper + fix embeddings VERTEX_PROJECT check (Wave 2) ✅

---

### Phase 16: Wire AURA-NOTES-MANAGER Consumers

**Goal:** Every LLM call in AURA-NOTES-MANAGER reads provider and model from SettingsStore and routes through ModelRouter — no more direct SDK calls or import-time config reads

**Depends on:** Phase 14

**Requirements:** PP-05, PP-06, PP-07, PP-08

**Success Criteria** (what must be TRUE):
  1. KG processor reads `resolve_use_case_config("entity_extraction")` at runtime instead of the module-level `LLM_ENTITY_EXTRACTION_MODEL` constant — changing the setting takes effect without restart
  2. Entity extractor passes explicit `provider` from SettingsStore to `GenerateRequest` — no import-time reads
  3. Embeddings passes `provider` from SettingsStore to `router.embed()` consistently
  4. Summarizer routes through ModelRouter instead of direct Vertex SDK calls, and bare `except: pass` blocks are replaced with logged error handling
  5. Integration tests verify each consumer falls back to env vars gracefully when Redis is unreachable

**Plans:** 3/3 plans complete

Plans:
- [x] 16-03-PLAN.md — Create integration test file for consumer wiring (PP-05 through PP-08) (Wave 1) ✅
- [ ] 16-01-PLAN.md — Wire KG processor + entity extractor (PP-05, PP-06) (Wave 2)
- [x] 16-02-PLAN.md — Wire embeddings + summarizer (PP-07, PP-08) (Wave 2) ✅

---

### Phase 17: Frontend + Cross-App Validation

**Goal:** Settings page UI reflects all configurable use cases, and E2E tests prove that changing a setting in the admin UI propagates to actual LLM behavior across both applications

**Depends on:** Phases 15, 16

**Requirements:** (cross-cutting validation — no new requirements; validates API-01, API-02, PP-01 through PP-08, FB-01, FB-02)

**Success Criteria** (what must be TRUE):
  1. AURA-NOTES-MANAGER settings page shows `gatekeeper` and `relationship_extraction` rows in the default model section, and the `UseCase` type union includes both
  2. Playwright E2E test: admin sets entity_extraction provider to OpenRouter in settings page → triggers a KG processing run → response metadata confirms OpenRouter was used
  3. Playwright E2E test: Redis is stopped → consumers log warnings and fall back to env vars → Redis is restarted → SettingsStore values resume within 30 seconds
  4. Both applications pass their full test suites (unit + E2E) with SettingsStore wiring active
  5. No direct imports of `vertexai`, `google.generativeai`, or `openai` SDK exist outside `shared/model_router/` in either application (AST audit)

**Plans:** 3/3 plans complete

Plans:
- [ ] 17-01-PLAN.md — NOTES-MANAGER use case expansion (UseCase type + USE_CASES + USE_CASE_MODEL_TYPES) (Wave 1)
- [ ] 17-02-PLAN.md — AURA-CHAT settings page (types, API, hooks, components, page, route) (Wave 1)
- [ ] 17-03-PLAN.md — E2E tests (both apps) + AST audit + full test suite validation (Wave 2)

---

## Progress

**Execution Order:** 14 → {15, 16 (parallel)} → 17

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 14. Foundation: Config + Allowlist + Cache | 2/2 | Complete    | 2026-03-23 |
| 15. Wire AURA-CHAT Consumers | 3/3 | Complete    | 2026-03-23 |
| 16. Wire AURA-NOTES-MANAGER Consumers | 3/3 | Complete    | 2026-03-23 |
| 17. Frontend + Cross-App Validation | 2/3 | Complete    | 2026-03-23 |

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
- [research/SUMMARY.md](./research/SUMMARY.md) - v1.2 research findings
- [REQUIREMENTS.md](./REQUIREMENTS.md) - Scoped requirements

---

*Roadmap created: 2026-03-23*
*Last updated: 2026-03-23*
