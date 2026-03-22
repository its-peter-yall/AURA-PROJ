# Requirements: AURA v1.2 — Settings Wiring E2E

**Defined:** 2026-03-23
**Core Value:** Transform from document-centric to module-centric learning, enabling contextual study sessions with persistent history and cross-module concept discovery.

## v1.2 Requirements

### API Configuration

- [ ] **API-01**: Admin can configure gatekeeper model/provider via settings page (add `"gatekeeper"` to `ALLOWED_USE_CASES` in both settings routers + frontend type + UI)
- [ ] **API-02**: Admin can configure relationship extraction model/provider via settings page (add `"relationship_extraction"` to `ALLOWED_USE_CASES` in both settings routers + frontend type + UI)

### Provider Passthrough — AURA-CHAT

- [ ] **PP-01**: Entity extractor passes explicit `provider` from SettingsStore to `GenerateRequest` (remove reliance on `/` heuristic in `AURA-CHAT/backend/llm_entity_extractor.py`)
- [ ] **PP-02**: Gatekeeper routes through ModelRouter with explicit provider (remove OpenRouter blanket skip in `AURA-CHAT/backend/llm_gatekeeper.py:153-159`, handle JSON mode per-provider)
- [ ] **PP-03**: Embeddings passes `provider` from SettingsStore to `router.embed()` consistently (`AURA-CHAT/backend/utils/embeddings.py`)
- [ ] **PP-04**: Relationship extraction reads from SettingsStore with env var fallback, passes `provider` to ModelRouter (`AURA-CHAT/backend/`)

### Provider Passthrough — AURA-NOTES-MANAGER

- [ ] **PP-05**: KG processor reads from SettingsStore at runtime (replace `LLM_ENTITY_EXTRACTION_MODEL` env var constant with `resolve_use_case_config("entity_extraction")` in `AURA-NOTES-MANAGER/api/kg_processor.py`)
- [ ] **PP-06**: Entity extractor passes explicit `provider` from SettingsStore (`AURA-NOTES-MANAGER/services/llm_entity_extractor.py`)
- [ ] **PP-07**: Embeddings passes `provider` from SettingsStore to `router.embed()` (`AURA-NOTES-MANAGER/services/embeddings.py`)
- [ ] **PP-08**: Summarizer routes through ModelRouter instead of direct Vertex SDK calls (`AURA-NOTES-MANAGER/services/summarizer.py`)

### Fallback Behavior

- [ ] **FB-01**: SettingsStore value is authoritative over env vars when SettingsStore is reachable (fix `AURA-NOTES-MANAGER/api/config.py` env var shadowing in `kg_processor.py`)
- [ ] **FB-02**: Graceful degradation documented and verified — log warning on Redis down, fall back to env vars, never crash (verify `get_default_sync` exception handling across all consumers)

## Future Requirements

Deferred to future milestones:

- **FUT-01**: Dynamic thinking mode model list from provider capabilities metadata
- **FUT-02**: Multi-provider chat config fallback (include OpenRouter models when Redis is down)
- **FUT-03**: SettingsStore health indicator in settings page UI

## Out of Scope

| Feature | Reason |
|---------|--------|
| Add new LLM providers | Wiring milestone, not provider milestone |
| Refactor SettingsStore to async-only | Sync consumers need `get_default_sync()` |
| Change Redis schema | Current hash at `aura:model_router:settings` is adequate |
| Unified config migration | Each consumer reads SettingsStore first, env vars second |
| Provider-specific logic in SettingsStore | SettingsStore stays provider-agnostic |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| API-01 | Phase 14 | Pending |
| API-02 | Phase 14 | Pending |
| PP-01 | Phase 15 | Pending |
| PP-02 | Phase 15 | Pending |
| PP-03 | Phase 15 | Pending |
| PP-04 | Phase 15 | Pending |
| PP-05 | Phase 16 | Pending |
| PP-06 | Phase 16 | Pending |
| PP-07 | Phase 16 | Pending |
| PP-08 | Phase 16 | Pending |
| FB-01 | Phase 14 | Pending |
| FB-02 | Phase 14 | Pending |

**Coverage:**
- v1.2 requirements: 12 total
- Mapped to phases: 12 ✓
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-23*
*Last updated: 2026-03-23 after roadmap creation (12/12 mapped)*
