# Project Research Summary

**Project:** AURA v1.2 — SettingsStore E2E Wiring
**Domain:** Multi-provider LLM configuration consistency across dual-app platform
**Researched:** 2026-03-23
**Confidence:** HIGH

## Executive Summary

AURA is a dual-application monorepo (AURA-CHAT for student-facing RAG chat, AURA-NOTES-MANAGER for staff document management) that shares a `model_router` package with a Redis-backed `SettingsStore` for per-use-case LLM configuration (`{provider, model}` pairs). The core problem is that **only chat in AURA-CHAT is fully wired end-to-end** — the remaining 7 consumers either bypass SettingsStore with hardcoded env vars, read the `model` field while ignoring `provider`, or are blocked from configuration by an incomplete `ALLOWED_USE_CASES` allowlist. The settings UI promises per-use-case defaults, but selecting OpenRouter as provider has no effect for most consumers.

The recommended approach is to introduce a shared `resolve_use_case_config()` utility in `shared/model_router/` that enforces a 3-step resolution chain (SettingsStore → env var → hardcoded default) and returns `{provider, model}` to every consumer. This eliminates 7+ duplicated resolution patterns, ensures `provider` is always passed to ModelRouter, and makes the fallback chain explicit and testable. Two missing use cases (`gatekeeper`, `relationship_extraction`) must be added to `ALLOWED_USE_CASES` across both settings routers before any wiring work proceeds.

The key risks are: (1) **zombie-None caching** — when Redis goes down, the 5-minute cache stores the error as a legitimate "no config" entry, masking Redis recovery for up to 5 minutes; (2) **multi-worker cache inconsistency** — each uvicorn worker has its own in-process cache that isn't invalidated when another worker writes to SettingsStore; and (3) **module-level config reads** — several consumers read SettingsStore at import time, making runtime settings changes impossible without process restart.

## Key Findings

### Recommended Stack

No new dependencies. The wiring uses only existing shared packages (`model_router.settings_store`, `model_router.router`). The `resolve_use_case_config()` utility adds ~20 lines to `settings_store.py` and eliminates 42 potential failure points across 7 consumers.

**Core utilities:**
- `resolve_use_case_config(use_case)`: Central resolution function — SettingsStore → env var → hardcoded default
- `get_default_sync()`: Existing 5-minute cached Redis read (keep as-is)
- `ModelRouter.generate(GenerateRequest(provider=..., model=...))`: Existing router — already supports `provider` field, callers just never pass it
- `ModelRouter.embed(provider=...)`: Existing embedding router — same gap

### Expected Features

**Must have (table stakes):**
1. **All 6 use cases configurable via Settings API** — `gatekeeper` and `relationship_extraction` added to `ALLOWED_USE_CASES` + UI
2. **Provider field respected everywhere** — explicit `provider` passed to `GenerateRequest` in all 8 consumer locations
3. **No silent env-var fallbacks when SettingsStore has a value** — admin-configured settings must be authoritative
4. **Graceful degradation when Redis is down** — log warning, use env defaults, never crash

**Should have (competitive):**
5. **Gatekeeper works with OpenRouter** — remove blanket skip, verify JSON mode support
6. **Summarizer routes through ModelRouter** — replace direct Vertex SDK calls

**Defer (v2+):**
7. Dynamic thinking mode model list from provider capabilities
8. Multi-provider chat config fallback (Redis-down model list)
9. SettingsStore health indicator in UI

**Anti-features (explicitly do NOT build):**
- Add new providers (this is a wiring milestone, not a provider milestone)
- Refactor SettingsStore to async-only (sync consumers need `get_default_sync()`)
- Change the Redis schema (current hash is adequate)
- Build a unified config migration system (each consumer reads SettingsStore first, env vars second)
- Add provider-specific logic to SettingsStore (keep it provider-agnostic)

### Architecture Approach

The fix introduces a **shared config resolution layer** between SettingsStore and consumers. Currently each of 7+ consumers independently calls `get_default_sync()`, manually builds a Redis URL, handles None returns, extracts fields, and decides fallback behavior — duplicated with slight variations. The proposed `resolve_use_case_config()` utility centralizes this into a single ~20-line function, reducing per-consumer calls to 3 lines each.

**Major components (post-wiring):**
1. **`resolve_use_case_config()`** — resolution + fallback, sole SettingsStore reader for sync consumers
2. **`ModelRouter.generate()`** — provider-aware routing (already works, needs callers to pass `provider`)
3. **Settings routers (both apps)** — expanded `ALLOWED_USE_CASES` to include all 6 use cases
4. **7 consumers** — each reduced to `cfg = resolve_use_case_config("use_case")` → `router.generate(provider=cfg["provider"], model=cfg["model"])`

**Build order:** Foundation (resolver + allowlist) → AURA-CHAT consumers → AURA-NOTES-MANAGER consumers → Frontend + cross-app validation. Phases 2 and 3 can run in parallel.

**Key patterns to follow:**
- Resolution chain: SettingsStore → env var → hardcoded default (never None)
- Provider always passed explicitly to `GenerateRequest` or `router.embed()`
- Instance-level reads (not module-level) so settings changes take effect without restart
- 5-minute cache handles performance; shorter TTL for error-sourced entries

### Critical Pitfalls

1. **Zombie-None caching (CRITICAL, silent)** — `get_default_sync()` caches Redis failures as `None` for 5 minutes. Fix: use sentinel objects for error entries with shorter TTL (30-60s). *Address in Phase 1.*
2. **Multi-worker cache inconsistency (CRITICAL, silent)** — module-level `_defaults_cache` isn't shared across uvicorn workers. Fix: reduce TTL to 15-30s or add Redis pub/sub invalidation. *Address in Phase 1.*
3. **Provider field silently ignored (CRITICAL, silent)** — consumers read `model` but ignore `provider`, relying on fragile `/` heuristic. Fix: always pass `provider` to `GenerateRequest`. *Address in Phase 2-3.*
4. **kg_processor bypasses SettingsStore entirely (CRITICAL, silent)** — uses module-level env var constant, never reads SettingsStore. Fix: replace with runtime `resolve_use_case_config()` call. *Address in Phase 3.*
5. **ALLOWED_USE_CASES blocks real use cases (MODERATE)** — `gatekeeper` and `relationship_extraction` return 400 on PUT. Fix: add to allowlist in both routers. *Address in Phase 1.*
6. **Gatekeeper blanket OpenRouter skip (MODERATE, silent)** — ignores configured provider even if set. Fix: verify JSON mode support, remove skip. *Address in Phase 2.*
7. **Summarizer silent exception swallowing (MODERATE, silent)** — bare `except: pass` hides Redis errors. Fix: add logging or remove redundant try/except. *Address in Phase 3.*
8. **Import-time SettingsStore reads (MODERATE, silent)** — module-level constants never update. Fix: move to lazy resolution at call time. *Address in Phase 3.*

## Implications for Roadmap

Based on combined research, suggested phase structure:

### Phase 1: Foundation — Config Resolver + ALLOWED_USE_CASES
**Rationale:** Everything else depends on these two things existing. Zero behavioral change — purely additive. Must also fix zombie-None caching and multi-worker inconsistency before any consumer reads from SettingsStore, or the wiring will propagate stale data.
**Delivers:**
- `resolve_use_case_config()` utility in `shared/model_router/src/model_router/settings_store.py`
- `gatekeeper` + `relationship_extraction` added to `ALLOWED_USE_CASES` in both settings routers
- Zombie-None cache fix (sentinel objects or shorter error TTL)
- Redis URL consolidation (use `config.REDIS_URL` everywhere)
- Unit tests for resolution order and fallback chain
**Addresses:** Feature 1 (all use cases configurable), Pitfall 7 (ALLOWED_USE_CASES gate), Pitfall 1 (zombie-None), Pitfall 2 (multi-worker), Pitfall 11 (Redis URL fragility)
**Avoids:** Wiring any consumer before the foundation exists

### Phase 2: Wire AURA-CHAT Consumers
**Rationale:** AURA-CHAT is the student-facing app with established test coverage. Wire all consumers in one app for end-to-end validation before touching NOTES.
**Delivers:**
- Gatekeeper: remove OpenRouter skip, route through ModelRouter with explicit provider
- Entity extractor: return `(provider, model)` from resolver, pass to `GenerateRequest`
- Embeddings: make `VERTEX_PROJECT` check provider-conditional (only enforce when `provider == "vertex_ai"`)
- Relationship extraction: wire `get_default_sync("relationship_extraction")` with env var fallback
- Chat config endpoint: improve fallback to include OpenRouter models when key exists
- Thinking model list: extend `CHAT_MODELS_WITH_THINKING` with known OpenRouter thinking models
- Integration tests for each consumer with mocked SettingsStore
**Addresses:** Feature 2 (provider field respected), Feature 3 (no silent fallbacks), Feature 5 (gatekeeper OpenRouter), Pitfall 3 (provider ignored), Pitfall 5 (gatekeeper skip), Pitfall 6 (embedding project check)
**Avoids:** Silent provider routing, hardcoded Vertex-only lists

### Phase 3: Wire AURA-NOTES-MANAGER Consumers
**Rationale:** NOTES has separate concerns (KG processing, summarization). Lower risk when CHAT is already verified. Same wiring pattern as Phase 2.
**Delivers:**
- kg_processor: replace `LLM_ENTITY_EXTRACTION_MODEL` module-level constant with runtime `resolve_use_case_config("entity_extraction")`
- Entity extractor: use resolver, pass provider to ModelRouter
- Embeddings: pass `provider` from `_embedding_default` to `router.embed()`
- Summarizer: route through ModelRouter instead of direct Vertex SDK; remove bare `except: pass`
- Integration tests for each consumer
**Addresses:** Feature 6 (summarizer routing), Pitfall 4 (kg_processor bypass), Pitfall 8 (summarizer silent swallow), Pitfall 12 (import-time stale globals)
**Avoids:** Module-level SettingsStore reads, direct Vertex SDK calls bypassing ModelRouter

### Phase 4: Frontend + Cross-App Validation
**Rationale:** Only after both apps are wired can we validate that settings changes propagate correctly across the platform.
**Delivers:**
- Settings page UI updated with `gatekeeper` + `relationship_extraction` rows in AURA-NOTES-MANAGER
- `UseCase` type union updated in frontend types
- Playwright E2E tests for settings → behavior flow
- Cross-app validation: changing a setting in one app affects both apps
**Addresses:** Feature 4 (graceful degradation verification), UI completeness
**Avoids:** UI showing use cases that aren't actually configurable

### Phase Ordering Rationale

- **Phase 1 first** because all other phases depend on `resolve_use_case_config()` existing and `ALLOWED_USE_CASES` being complete. Also must fix caching pitfalls before wiring consumers.
- **Phases 2 and 3 run in parallel** (separate apps, independent consumers, same pattern).
- **Phase 4 last** because cross-app validation requires both apps wired.
- Each phase is independently testable and deployable.
- The dependency graph is: Phase 1 → {Phase 2, Phase 3 (parallel)} → Phase 4.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (gatekeeper):** Verify OpenRouter `response_mime_type` / JSON mode support per-model. The blanket skip at `llm_gatekeeper.py:153-159` may be unnecessary now — but needs live API verification.
- **Phase 2 (thinking models):** Confirm which OpenRouter models support thinking mode. May need a static extension to `CHAT_MODELS_WITH_THINKING` or a capability flag.

Phases with standard patterns (skip research-phase):
- **Phase 1:** Well-defined — add function + expand constant set. Standard utility pattern.
- **Phase 3:** Follows same wiring pattern as Phase 2. No novel integration.
- **Phase 4:** Standard React settings UI update. Well-understood.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | No new dependencies needed — wiring uses existing shared packages only |
| Features | HIGH | All 9 features verified by reading source code; dependency graph clear |
| Architecture | HIGH | All 7 integration points verified; resolver design follows existing patterns |
| Pitfalls | HIGH | All 12 pitfalls verified from source code analysis; community patterns corroborate |

**Overall confidence:** HIGH

### Gaps to Address

- **OpenRouter JSON mode support:** Whether OpenRouter supports `response_mime_type` for Gemini models needs live API verification during Phase 2 planning. If not supported, gatekeeper needs provider-specific prompt injection as fallback. *Handle during Phase 2 research.*
- **Thinking-capable OpenRouter models:** Which models support thinking is undocumented. Phase 2f may need a manual mapping or `ModelInfo` capability flag — defer dynamic resolution. *Start with static list extension, plan dynamic for v1.3.*
- **Cache invalidation strategy choice:** Pitfall 1 and 2 prevention requires a design decision (sentinel objects vs. shorter TTL vs. Redis pub/sub). Recommend starting with shorter TTL (30s) and adding pub/sub if inconsistency is observed in production. *Decide during Phase 1 implementation.*

## Sources

### Primary (HIGH confidence)
- `shared/model_router/src/model_router/settings_store.py` — SettingsStore implementation, cache behavior, exception handling, TTL logic
- `shared/model_router/src/model_router/router.py` — Provider routing, `_determine_provider_type()`, `GenerateRequest.provider`
- `shared/model_router/src/model_router/types.py:41` — `GenerateRequest` provider field
- `AURA-CHAT/server/routers/settings.py:55` — `ALLOWED_USE_CASES` definition
- `AURA-CHAT/server/routers/chat.py:368-379` — Chat SettingsStore wiring (working reference)
- `AURA-CHAT/backend/llm_gatekeeper.py:138-166` — Gatekeeper provider resolution, OpenRouter skip
- `AURA-CHAT/backend/llm_entity_extractor.py:301-320` — Entity extractor provider handling
- `AURA-CHAT/backend/utils/embeddings.py:56-77, 154-161, 228-232` — Embeddings SettingsStore read, provider passthrough, project check
- `AURA-CHAT/backend/utils/config.py:59-63, 87-88, 199-206` — Hardcoded model lists, env var fallbacks
- `AURA-NOTES-MANAGER/api/kg_processor.py:465` — KG processor bypass (GeminiClient init)
- `AURA-NOTES-MANAGER/api/config.py:62-73` — Module-level env var constants
- `AURA-NOTES-MANAGER/api/routers/settings.py:55` — NOTES ALLOWED_USE_CASES
- `AURA-NOTES-MANAGER/services/llm_entity_extractor.py:204-222` — Import-time SettingsStore read
- `AURA-NOTES-MANAGER/services/embeddings.py:84-107` — Embeddings provider handling
- `AURA-NOTES-MANAGER/services/summarizer.py:63-72` — Summarizer direct Vertex SDK
- `AURA-NOTES-MANAGER/frontend/src/types/settings.ts:32` — `UseCase` type union
- `AURA-NOTES-MANAGER/frontend/src/features/settings/components/DefaultModelSection.tsx:44-48` — UI use case list
- `.planning/issues/SETTINGS-WIRING-E2E.md` — Detailed problem specification
- OpenRouter API docs (verified 2026-03) — `response_mime_type` support for Gemini models

### Secondary (MEDIUM confidence)
- Community patterns: Redis two-level cache with circuit breaker (2026)
- Community patterns: Dynamic config race conditions in distributed systems (2026)
- Production postmortems: Redis failover cascading failures (2026)
- Config-as-dependency anti-patterns (2026)

### Tertiary (LOW confidence)
- OpenRouter JSON mode support for all model families — needs per-model verification
- Thinking-capable model mapping for non-Gemini OpenRouter models — undocumented

---
*Research completed: 2026-03-23*
*Ready for roadmap: yes*
