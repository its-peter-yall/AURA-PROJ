# Project Retrospective

## Milestone: v1.0 — M2KG Transformation

**Shipped:** 2026-03-08
**Phases:** 7 | **Plans:** 28 | **Tasks:** 67 summaries

---

### What Was Built

Module-centric learning platform with knowledge graphs, transforming AURA from document-centric to module-centric architecture. Delivered two integrated applications (AURA-NOTES-MANAGER for staff, AURA-CHAT for students) with persistent study sessions, module-aware RAG, and full testing infrastructure.

**Key Deliverables:**
- Neo4j-based knowledge graph with HNSW vector search
- Celery async KG processing pipeline
- 4-level module hierarchy (Dept → Semester → Subject → Module)
- Session-based chat with persistent history
- Module-aware RAG with cross-module discovery
- Feature-based React frontend architecture
- 210+ unit tests, 65+ E2E tests
- Docker Compose deployment (8 services)

---

### What Worked

**1. Feature-based frontend architecture**
- Organizing by feature (`features/modules/`, `features/study-sessions/`) made code discoverable
- Shared components in `components/` for reuse across features
- Clear separation of concerns

**2. Dual-database strategy**
- Neo4j for graph + vector search worked well
- Redis for caching and Celery broker
- No need for separate vector DB

**3. Session-based chat design**
- Moving from stateless to persistent sessions improved UX significantly
- Message history with pagination works smoothly
- Session context preserved across browser refreshes

**4. Plan-driven development**
- Having detailed PLAN.md files with verification steps caught issues early
- SUMMARY.md files served as both documentation and completion markers

**5. Component extraction pattern**
- Extracting MessageBubble and CitationPanel from ChatPage.tsx improved testability
- Reusable components reduced duplication

---

### What Was Inefficient

**1. Split backend in AURA-CHAT**
- Maintaining `server/` and `backend/` directories caused confusion
- Unclear which to use for new features
- Should have migrated fully to `server/` earlier

**2. Dual frontend versions**
- AURA-CHAT on React 19, AURA-NOTES-MANAGER on React 18
- Added complexity for shared components
- Should have aligned versions sooner

**3. Manual verification overhead**
- Some plans required extensive manual testing
- Could have automated more verification steps

**4. Documentation drift**
- AGENTS.md, CLAUDE.md, GEMINI.md needed periodic refreshes
- Quick task 7 addressed this but shouldn't have been necessary

---

### Patterns Established

1. **Plan structure:** Objective → Context → Requirements → Tasks → Verify → Done
2. **File headers:** Mandatory for all .ts, .tsx, .py files
3. **API pattern:** Extend `types/api.ts` and `lib/api.ts` rather than new files
4. **Hook pattern:** TanStack Query for server state, Zustand for UI state
5. **Test location:** Co-located tests (`*.test.ts`, `*.test.tsx`) and dedicated `e2e/` folders
6. **Path alias:** `@/*` → `./src/*` consistently across projects
7. **Color scheme:** Cyber Yellow (#FFD400) as primary accent

---

### Key Lessons

1. **Research-first principle saved time** — Web searching unfamiliar libraries before implementing prevented wrong approaches

2. **Component extraction improves maintainability** — Large files like ChatPage.tsx became manageable after extraction

3. **Feature-based structure scales** — Adding new features (study-sessions, modules) was straightforward

4. **Testing early prevents regression** — E2E tests caught integration issues unit tests missed

5. **Documentation must be maintained** — CLAUDE.md, AGENTS.md need regular updates as codebase evolves

6. **Dual version strategy has costs** — React 18/19 split added complexity without clear benefit

---

### Cost Observations

- **Timeline:** 46 days (Jan 19 → Mar 8)
- **Commits:** ~200+
- **Files changed:** 310 files, 144K+ lines added
- **LOC:** ~121K (Python + TypeScript)
- **Test coverage:** >85% backend, >80% frontend

**Efficiency notes:**
- 7 phases in 46 days = ~6.5 days/phase average
- Quick tasks (1, 7) were small maintenance items
- RAG consolidation (RC phases) was refactoring overhead

---

## Milestone: v1.1 — Multi-Provider LLM Architecture

**Shipped:** 2026-03-15
**Phases:** 6 | **Plans:** 23 | **Timeline:** 6 days (Mar 10 → Mar 15)

---

### What Was Built

Provider-agnostic LLM architecture enabling both AURA applications to access Vertex AI, OpenRouter (200+ models), and local Ollama through a unified interface. Delivered shared model_router package, cross-app migration, admin settings UI, and usage tracking with cost dashboard.

**Key Deliverables:**
- `shared/model_router/` package with Provider ABC and unified error hierarchy
- VertexAI provider wrapping existing code (backward compatible)
- OpenRouter provider with 200+ models and normalized streaming
- Cross-app migration with compatibility shims and import-compliance audit
- Admin settings pages (provider config, API key management, default models)
- Hierarchical model picker (2-level Vertex AI, 3-level OpenRouter)
- Usage tracking with Redis persistence and cost dashboard
- 1100+ tests passing across shared, backend, and frontend suites

---

### What Worked

**1. Strangler Fig migration pattern**
- Compatibility shims allowed gradual migration without breaking existing code
- Legacy imports preserved while delegating to new router internally
- Zero-regression migration verified by existing test suite

**2. Shared package at project root**
- Single `shared/model_router/` package served both AURA apps
- Workspace-local pytest avoided monorepo discovery conflicts
- Clean separation from app-specific code

**3. Late-binding for Redis dependencies**
- UsageTracker and CostCalculator bound after ModelRouter construction
- Avoided startup failures when Redis unavailable in test mode
- Swallowed telemetry failures for resilience

**4. Provider normalization**
- Unified SSE streaming format across Vertex AI and OpenRouter
- Thinking parameter translation for Gemini/Claude/DeepSeek
- Single `enable_thinking` interface across all providers

**5. AST-based import compliance**
- Automated audit caught direct SDK imports after migration
- Worker-context verification for Celery/ARQ background tasks
- Prevented quiet regressions in background jobs

---

### What Was Inefficient

**1. Quick tasks during phases**
- Multiple quick tasks (13-19) interrupted phase flow
- Context switching between planned work and ad-hoc issues
- Could have batched quick tasks between phases

**2. Dual frontend React versions**
- AURA-CHAT (React 19) vs AURA-NOTES-MANAGER (React 18)
- Required copying components rather than shared package
- Tailwind v3 vs v4 config differences

**3. State drift between sessions**
- Multiple STATE.md updates across sessions
- Some pending todos carried through multiple phases
- Quick task documentation needed manual sync

---

### Patterns Established

1. **Lazy provider registration:** OpenRouter registers on-demand when API key configured
2. **Fernet encryption:** KeyManager uses Fernet symmetric encryption for API keys
3. **TTL guardrails:** Model cache with configurable 5-60 minute TTL
4. **Hierarchical config:** pydantic-settings for layering provider defaults
5. **Usage hooks:** Router automatically tracks tokens/cost without caller intervention
6. **Cost badge pattern:** Inline per-session cost display in chat UI

---

### Key Lessons

1. **Plan phases with dependency analysis** — Phase 8's Strangler Fig pattern enabled zero-regression migration across 35+ files

2. **Test environment isolation matters** — `AURA_TEST_MODE` and workspace-local runners prevented environment conflicts

3. **Provider abstraction overhead is minimal** — Benchmark proved <10ms router overhead, acceptable for LLM calls (seconds)

4. **Compatibility shims enable gradual migration** — Legacy imports preserved while delegating to new router

5. **Automated compliance checking prevents regressions** — AST-based import audit caught edge cases manual review missed

---

### Cost Observations

- **Timeline:** 6 days (Mar 10 → Mar 15)
- **Commits:** 112 commits from v1.0 to v1.1
- **LOC added:** ~14K (Python + TypeScript)
- **Test coverage:** 1100+ tests maintained

**Efficiency notes:**
- 6 phases in 6 days = 1 phase/day average
- Phase 10 (migration) was longest at ~70 min
- Phase 9 (OpenRouter) was fastest at ~10 min
- 9 quick tasks during v1.1 development interrupted flow

---

## Milestone: v1.2 — Settings Wiring E2E

**Shipped:** 2026-03-23
**Phases:** 4 | **Plans:** 11 | **Timeline:** 1 day

---

### What Was Built

End-to-end SettingsStore wiring so every AI feature in both applications respects per-use-case model/provider configuration. Delivered shared `resolve_use_case_config()` utility, wired all 8 LLM consumers across both apps, expanded frontend settings UI, and validated with Playwright E2E tests.

**Key Deliverables:**
- `resolve_use_case_config()` — 3-step resolution (SettingsStore → env var → hardcoded default)
- Zombie-None cache fix — 30s error TTL for rapid Redis recovery
- `ALLOWED_USE_CASES` expansion — gatekeeper + relationship_extraction in both apps
- AURA-CHAT consumer wiring — entity extractor, gatekeeper, embeddings, relationship extraction
- AURA-NOTES-MANAGER consumer wiring — KG processor, entity extractor, embeddings, summarizer
- Frontend settings pages — 5 use case rows, admin guards, E2E test specs
- AST import audit — no direct SDK imports outside `shared/model_router/`

---

### What Worked

**1. Single-day milestone execution**
- 4 phases completed in 1 day (29 commits)
- Phases 15 and 16 ran in parallel (independent consumers)
- Tight scope kept momentum without scope creep

**2. Utility-first architecture**
- `resolve_use_case_config()` centralised 3-step resolution in one function
- All 8 consumers reused the same utility — no per-consumer logic
- Consistent fallback behavior across entire codebase

**3. Sentinel cache pattern**
- `_SENTINEL_ERROR` cached on Redis failure with 30s TTL
- Differentiated TTL for errors (30s) vs misses (300s)
- 5-minute zombie-None problem eliminated

**4. Retroactive verification workflow**
- Phase 15 VERIFICATION.md created from SUMMARY.md evidence
- Integration checker spawned for cross-phase wiring verification
- Audit passed with 12/12 requirements satisfied

---

### What Was Inefficient

**1. Documentation lag**
- Phase 15 VERIFICATION.md never written during execution
- Required retroactive creation from SUMMARY.md files
- VALIDATION.md files remain in draft status (3 of 4 phases)

**2. Dead code left behind**
- `llm_entity_extractor.py` `_extract_partial_json` has unreachable code after `return {}`
- Typical of rapid execution — no cleanup pass

---

### Patterns Established

1. **Retroactive verification from SUMMARY.md:** When execution is fast, verification docs can be created from SUMMARY evidence
2. **Parallel phase execution:** Phases 15 and 16 ran independently with no conflicts
3. **Config resolution abstraction:** Single utility replaces 8 separate consumer implementations
4. **Graceful Redis degradation:** 30s error TTL + fallback chain prevents crashes

---

### Key Lessons

1. **Utility functions pay off at scale** — One `resolve_use_case_config()` replaced 8 different consumer implementations with consistent behavior

2. **Cache TTL matters for resilience** — 30s error TTL vs 5-minute default made Redis recovery 10x faster

3. **Parallel phases work when consumers are independent** — Phases 15 (CHAT) and 16 (NOTES) had no shared dependencies

4. **Documentation lags execution in rapid milestones** — Verification files should be written during execution, not retroactively

---

### Cost Observations

- **Timeline:** 1 day (Mar 23)
- **Commits:** 29 commits
- **LOC added:** ~6K (43 files changed)
- **Files modified:** 43

**Efficiency notes:**
- 4 phases in 1 day = 1 phase/hour average
- Phase 14 (foundation) was 2 hours
- Phase 17 (validation) was 1 hour
- No quick tasks — focused execution

---

## Cross-Milestone Trends

### Code Growth

| Milestone | LOC | Files | Phases | Days |
|-----------|-----|-------|--------|------|
| v1.0 | 121K | 310 | 7 | 46 |
| v1.1 | 135K | +80 | 6 | 6 |
| v1.2 | 141K | +43 | 4 | 1 |

### Test Coverage

| Milestone | Unit Tests | E2E Tests | Coverage |
|-----------|------------|-----------|----------|
| v1.0 | 210+ | 65+ | 85% backend, 80% frontend |
| v1.1 | 1100+ | 65+ | 85% backend, 80% frontend |
| v1.2 | 1100+ | 6+ (settings) | 85% backend, 80% frontend |

### Technical Debt Status

| Item | v1.0 | v1.1 | v1.2 |
|------|------|------|------|
| Split backend directories | Open | Open | Open |
| React version alignment | Open | Still aligned wrong | Still aligned wrong |
| Hardcoded workflow paths | Open | Open | Open |
| Documentation sync | Manual | Manual | Manual |
| Direct SDK imports | N/A | ✓ Closed (AST audit) | ✓ Closed |
| Settings wiring | Not started | Partial | ✓ Complete |

### What's Next

Define v1.3 scope via `/gsd-new-milestone`

Potential areas:
- Dynamic thinking mode model list from provider metadata
- Provider fallback (auto-switch on rate limits)
- Settings health indicator in UI
- Ollama local models (full implementation)
- Production monitoring (Prometheus/Grafana)
- Cost alerts and budget management

---

*Retrospective updated: 2026-03-23 after v1.2 milestone*
