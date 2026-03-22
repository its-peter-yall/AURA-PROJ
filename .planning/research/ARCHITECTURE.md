# Architecture: SettingsStore E2E Wiring

**Domain:** Settings configuration propagation across dual-app monorepo
**Researched:** 2026-03-23
**Overall confidence:** HIGH

## Executive Summary

The shared `model_router` SettingsStore (Redis hash `aura:model_router:settings`) stores
`{provider, model}` per use case. The settings API and UI in both apps expose configuration
for `chat`, `embeddings`, `entity_extraction`, `summarization`. But **7 integration points
bypass or partially use** SettingsStore. Only `chat` in AURA-CHAT is fully wired end-to-end.

The core problem is architectural: SettingsStore was built as a **data store** but consumed
without a **config resolution layer**. Each consumer independently calls `get_default_sync()`,
sometimes reads the `provider` field, sometimes ignores it, and sometimes bypasses
SettingsStore entirely with hardcoded env vars. There is no shared pattern, no fallback
chain, and no provider-passthrough contract.

The fix requires: (1) expanding `ALLOWED_USE_CASES` to include `gatekeeper` and
`relationship_extraction`, (2) standardizing a config resolution pattern across all 7
consumers, (3) ensuring `provider` is always passed through to ModelRouter, and (4)
replacing hardcoded lists with dynamic resolution where possible.

## Integration Map

### Current State: 7 Broken Wiring Points

```
                    SettingsStore (Redis)
                    ┌─────────────────┐
                    │ chat: {p, m}    │
                    │ embeddings: {p,m}│
                    │ entity_ext: {p,m}│
                    │ summarization   │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    AURA-CHAT          SHARED           AURA-NOTES-MANAGER
    ─────────          ──────           ──────────────────
          │                                     │
   ┌──────┴──────┐                      ┌───────┴───────┐
   │             │                      │               │
   │  ✅ Chat    │                      │ ❌ kg_processor│
   │  (wired)    │                      │ (bypasses)    │
   │             │                      │               │
   │ ❌ Gatekpr  │                      │ ⚠️ entity_ext  │
   │ (partial)   │                      │ (model only)  │
   │             │                      │               │
   │ ⚠️ Entity   │                      │ ⚠️ embeddings  │
   │ (model only)│                      │ (model only)  │
   │             │                      │               │
   │ ⚠️ Embed    │                      │ ⚠️ summarizer  │
   │ (model+prov)│                      │ (model only)  │
   │             │                      │               │
   │ ❌ Relation │                      │               │
   │ (env var)   │                      │               │
   │             │                      │               │
   │ ⚠️ Chat cfg │                      │               │
   │ (hardcoded) │                      │               │
   └─────────────┘                      └───────────────┘

  Legend: ✅ = fully wired  ⚠️ = partial  ❌ = broken/bypasses
```

## The 7 Integration Points

### Problem 1: `gatekeeper` Use Case Missing from ALLOWED_USE_CASES

**Files:**
- `AURA-CHAT/server/routers/settings.py:55` — `ALLOWED_USE_CASES = {"chat", "embeddings", "entity_extraction", "summarization"}`
- `AURA-NOTES-MANAGER/api/routers/settings.py:55` — identical

**What happens:** `llm_gatekeeper.py:143` calls `get_default_sync("gatekeeper")`, but both
settings routers return 400 for any PUT to `/api/v1/settings/defaults/gatekeeper`. The
settings page has no UI to configure it.

**Additional issue:** `llm_gatekeeper.py:153-159` explicitly skips OpenRouter with:
```
"Gatekeeper skipping OpenRouter default (requires response_mime_type)"
```
Even if `gatekeeper` were in ALLOWED_USE_CASES, selecting OpenRouter is silently ignored.

**Integration change needed:**
- **Modify:** `AURA-CHAT/server/routers/settings.py` — add `"gatekeeper"` to ALLOWED_USE_CASES
- **Modify:** `AURA-NOTES-MANAGER/api/routers/settings.py` — same
- **Modify:** `AURA-CHAT/backend/llm_gatekeeper.py:138-166` — remove OpenRouter skip, route through ModelRouter instead of calling `get_model()` directly
- **Modify:** `AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx` — add gatekeeper use case row

### Problem 2: `relationship_extraction` Not a SettingsStore Use Case

**Files:**
- `AURA-CHAT/backend/utils/config.py:87-88` — `LLM_RELATIONSHIP_MODEL = os.getenv("LLM_RELATIONSHIP_MODEL", "gemini-2.5-flash-lite")`

**What happens:** Relationship extraction reads ONLY from the env var. Never calls
`get_default_sync()`. No settings API endpoint. No UI.

**Integration change needed:**
- **Modify:** `AURA-CHAT/server/routers/settings.py` — add `"relationship_extraction"` to ALLOWED_USE_CASES
- **Modify:** `AURA-NOTES-MANAGER/api/routers/settings.py` — same
- **Modify:** Callers of `config.LLM_RELATIONSHIP_MODEL` — add `get_default_sync("relationship_extraction")` call with env var fallback
- **Modify:** Settings page UI — add relationship_extraction row

### Problem 3: `kg_processor.py` Bypasses SettingsStore Entirely

**Files:**
- `AURA-NOTES-MANAGER/api/kg_processor.py:465` — `GeminiClient.__init__()` takes `model_name` defaulting to `LLM_ENTITY_EXTRACTION_MODEL` from config
- `AURA-NOTES-MANAGER/api/config.py:62-64` — `LLM_ENTITY_EXTRACTION_MODEL = os.getenv(...)` — env var only

**What happens:** The KG processor (main document processing pipeline in NOTES) uses its own
`GeminiClient` class that takes the model from config.py, which only checks env vars. It
never calls `get_default_sync("entity_extraction")`. Even though
`services/llm_entity_extractor.py:204` DOES read SettingsStore, `kg_processor.py` never
reaches that code path — it has its own `GeminiClient`.

**Integration change needed:**
- **Modify:** `AURA-NOTES-MANAGER/api/kg_processor.py:465` — `GeminiClient.__init__()` should call `get_default_sync("entity_extraction")` and use both `provider` and `model`
- **Modify:** `AURA-NOTES-MANAGER/api/kg_processor.py` — pass `provider` through to ModelRouter when making LLM calls
- **New:** Optionally extract a shared `_resolve_use_case_config(use_case)` helper to avoid duplicating the resolution pattern

### Problem 4: Entity Extraction Ignores the `provider` Field

**Files:**
- `AURA-CHAT/backend/llm_entity_extractor.py:307-320` — `_resolve_default_model()` reads `get_default_sync("entity_extraction")`, returns only `_default["model"]`, ignores `provider`
- `AURA-NOTES-MANAGER/services/llm_entity_extractor.py:204-222` — same pattern: reads model but not provider

**What works by accident:** ModelRouter's `_determine_provider_type()` uses the `/` heuristic
to detect OpenRouter model names. So `anthropic/claude-3-opus` routes to OpenRouter without
explicit provider. This breaks for any provider with non-standard naming.

**Integration change needed:**
- **Modify:** `AURA-CHAT/backend/llm_entity_extractor.py:301-320` — return `(provider, model)` tuple, pass `provider` to ModelRouter's `generate()` call
- **Modify:** `AURA-NOTES-MANAGER/services/llm_entity_extractor.py:204-222` — same
- The entity extractors currently use `get_model()` (Vertex AI only) rather than ModelRouter.
  Full wiring requires routing through `router.generate(provider=..., model=...)`.

### Problem 5: Embeddings Partially Ignores Provider Field

**Files:**
- `AURA-CHAT/backend/utils/embeddings.py:57-61` — reads `get_default_sync("embeddings")`, uses `provider` in `_embed_batch_sync()` (line 154-159), but also has hardcoded `VERTEX_PROJECT` checks
- `AURA-NOTES-MANAGER/services/embeddings.py:84-107` — reads `get_default_sync("embeddings")`, overrides `model_name` but the provider field is logged but not used for routing

**What happens:** AURA-CHAT's `_embed_batch_sync()` passes provider to `router.embed()`
which IS correct. But the constructor still requires `VERTEX_PROJECT` env var (line 228-232)
as a precondition — this blocks OpenRouter-only deployments. AURA-NOTES-MANAGER's
`EmbeddingService` logs the provider but never passes it to the router.

**Integration change needed:**
- **Modify:** `AURA-CHAT/backend/utils/embeddings.py:228-232` — remove or soften the `VERTEX_PROJECT` requirement when provider is `openrouter`
- **Modify:** `AURA-CHAT/backend/utils/embeddings.py` — ensure `model_name` is passed to `router.embed()` alongside provider (currently only provider is passed, model defaults)
- **Modify:** `AURA-NOTES-MANAGER/services/embeddings.py` — pass `provider` from `_embedding_default` to router calls

### Problem 6: Chat Config Fallback Hardcoded to Vertex AI

**Files:**
- `AURA-CHAT/server/routers/chat.py:313-337` — `GET /chat/config` tries `router.list_models()`, falls back to `config.RAG_ALLOWED_MODELS`
- `AURA-CHAT/backend/utils/config.py:59-63` — `RAG_ALLOWED_MODELS = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-3-flash-preview"]`

**What happens:** When Redis is down or router is unavailable, only Vertex AI models
appear in the UI. OpenRouter models vanish.

**Integration change needed:**
- **Modify:** `AURA-CHAT/server/routers/chat.py:326-327` — fallback should include OpenRouter models if an OpenRouter key is configured, or return a `router_unavailable: true` flag so the UI can show a warning
- **Consider:** Cache the last-known model list in Redis so fallback is "last known good" rather than hardcoded

### Problem 7: Thinking Mode Model List Hardcoded to Vertex AI

**Files:**
- `AURA-CHAT/backend/utils/config.py:199-206` — `CHAT_MODELS_WITH_THINKING` is a static list of Vertex AI model names

**What happens:** If admin configures an OpenRouter model that supports thinking (e.g.,
`google/gemini-2.0-flash-thinking`), the thinking toggle won't appear because the model
name won't match the hardcoded list.

**Integration change needed:**
- **Modify:** `AURA-CHAT/server/routers/chat.py:332-336` — the `thinking.supported_models` in the config endpoint should be dynamically generated or at minimum include OpenRouter thinking models
- **Consider:** Add a `thinking_capable` flag to `ModelInfo` in the model router, so the config endpoint can filter dynamically

---

## Recommended Architecture: Shared Config Resolution

### The Problem with Current Approach

Each consumer independently calls `get_default_sync("use_case")`, manually builds a Redis
URL from config, handles None returns, extracts fields, and decides fallback behavior.
This pattern is duplicated 7+ times with slight variations.

### Proposed: `resolve_use_case_config()` Utility

Add a single resolution function in `shared/model_router/` that all consumers call:

```python
# shared/model_router/src/model_router/config_resolver.py

from model_router.settings_store import get_default_sync

def resolve_use_case_config(
    use_case: str,
    env_fallback_model: str,
    env_fallback_provider: str = "vertex_ai",
    redis_url: str | None = None,
) -> dict[str, str]:
    """Resolve provider+model for a use case from SettingsStore with env fallback.

    Resolution order:
    1. SettingsStore (Redis) — admin-configured default
    2. Environment variable — fallback model name
    3. Hardcoded default — last resort

    Returns:
        {"provider": str, "model": str} — always returns a dict, never None.
    """
    stored = get_default_sync(use_case, redis_url=redis_url)
    if stored and stored.get("model"):
        return {"provider": stored.get("provider", env_fallback_provider),
                "model": stored["model"]}
    return {"provider": env_fallback_provider, "model": env_fallback_model}
```

**Why a shared utility:**
1. Eliminates 7+ duplicated resolution patterns
2. Enforces the contract: every consumer gets `{provider, model}`, never None
3. Single place to add caching, validation, or logging
4. Makes the fallback chain explicit and testable
5. Future providers only need to update one place

### Resolution Flow (per consumer)

```
Consumer needs model for use_case X
        │
        ▼
resolve_use_case_config("X", env_fallback="gemini-2.5-flash-lite")
        │
        ├─── SettingsStore has entry? → return {provider, model} from store
        │
        └─── No entry? → return {provider: "vertex_ai", model: env_fallback}
        │
        ▼
router.generate(model=config["model"], provider=config["provider"])
```

---

## Component Boundaries (Post-Wiring)

| Component | Responsibility | Reads SettingsStore? | Passes Provider? |
|-----------|---------------|---------------------|------------------|
| `shared/model_router/config_resolver.py` | Resolution + fallback | YES (sole reader) | Returns it |
| `llm_gatekeeper.py` | Query classification | Via resolver | YES → router |
| `llm_entity_extractor.py` (CHAT) | Entity extraction | Via resolver | YES → router |
| `llm_entity_extractor.py` (NOTES) | Entity extraction | Via resolver | YES → router |
| `kg_processor.py` (NOTES) | Document processing | Via resolver | YES → router |
| `embeddings.py` (CHAT) | Vector embedding | Via resolver | YES → router.embed() |
| `embeddings.py` (NOTES) | Vector embedding | Via resolver | YES → router.embed() |
| `summarizer.py` (NOTES) | Transcript summarization | Via resolver | YES → router |
| `config.py` (CHAT) | Static config / thinking | NO (becomes static fallback) | N/A |
| `config.py` (NOTES) | Static config | NO (becomes static fallback) | N/A |
| `chat.py` config endpoint | Client config | Via router.list_models() | N/A |

---

## Build Order and Dependencies

### Phase 1: Foundation — Expand ALLOWED_USE_CASES + Config Resolver (No behavioral change)

**Why first:** Everything else depends on these two things existing.

| Step | File | Change | Risk |
|------|------|--------|------|
| 1a | `shared/model_router/src/model_router/config_resolver.py` | NEW: `resolve_use_case_config()` | None — new file, no consumers yet |
| 1b | `AURA-CHAT/server/routers/settings.py:55` | Add `"gatekeeper"`, `"relationship_extraction"` to ALLOWED_USE_CASES | Low — allows PUT, no reads yet |
| 1c | `AURA-NOTES-MANAGER/api/routers/settings.py:55` | Same | Low |
| 1d | Tests for config_resolver | Unit tests for resolution order | None |

**Validation:** Settings API accepts PUT for new use cases. Config resolver passes tests.
No existing behavior changes.

### Phase 2: Wire AURA-CHAT Consumers (One app, lower blast radius)

**Why second:** AURA-CHAT is the student-facing app with established test coverage.
Wire all 3 consumers together so we can test end-to-end in one app.

| Step | File | Change | Depends On |
|------|------|--------|------------|
| 2a | `AURA-CHAT/backend/llm_gatekeeper.py:138-166` | Use `resolve_use_case_config("gatekeeper", ...)`, remove OpenRouter skip, route through ModelRouter | Phase 1 |
| 2b | `AURA-CHAT/backend/llm_entity_extractor.py:301-320` | Return `(provider, model)` from resolver, pass to ModelRouter | Phase 1 |
| 2c | `AURA-CHAT/backend/utils/embeddings.py:56-77` | Use resolver, remove VERTEX_PROJECT hard requirement for non-vertex providers | Phase 1 |
| 2d | `AURA-CHAT/backend/utils/config.py:87-88` | `LLM_RELATIONSHIP_MODEL` callers use resolver with env fallback | Phase 1 |
| 2e | `AURA-CHAT/server/routers/chat.py:313-337` | Improve fallback: include OpenRouter models when key exists, or flag `router_unavailable` | Phase 1 |
| 2f | `AURA-CHAT/backend/utils/config.py:199-206` | Add OpenRouter thinking models to `CHAT_MODELS_WITH_THINKING` or make dynamic | Phase 1 |
| 2g | Tests | Integration tests for each consumer with mocked SettingsStore | 2a-2f |

**Validation:** All AURA-CHAT use cases respond to settings changes. Gatekeeper works with
OpenRouter. Chat config fallback is graceful.

### Phase 3: Wire AURA-NOTES-MANAGER Consumers

**Why third:** NOTES has separate concerns (KG processing, summarization). Lower risk when
CHAT is already verified.

| Step | File | Change | Depends On |
|------|------|--------|------------|
| 3a | `AURA-NOTES-MANAGER/api/kg_processor.py:465` | `GeminiClient.__init__()` uses resolver instead of hardcoded config import | Phase 1 |
| 3b | `AURA-NOTES-MANAGER/services/llm_entity_extractor.py:204-222` | Use resolver, pass provider to ModelRouter | Phase 1 |
| 3c | `AURA-NOTES-MANAGER/services/embeddings.py:84-107` | Use resolver, pass provider to router.embed() | Phase 1 |
| 3d | `AURA-NOTES-MANAGER/services/summarizer.py:63-72` | Use resolver instead of direct `get_default_sync()` call | Phase 1 |
| 3e | Tests | Integration tests for each consumer | 3a-3d |

**Validation:** All NOTES use cases respond to settings changes. KG processing respects
entity_extraction setting.

### Phase 4: Frontend + Cross-App Validation

| Step | File | Change | Depends On |
|------|------|--------|------------|
| 4a | `AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx` | Add gatekeeper + relationship_extraction rows | Phase 1b/1c |
| 4b | Cross-app test | Verify NOTES settings page controls CHAT behavior and vice-versa | Phase 2, 3 |
| 4c | E2E tests | Playwright tests for settings → behavior flow | 4a, 4b |

**Validation:** Settings page shows all 6 use cases. Changing any use case takes effect
in both apps.

### Dependency Graph

```
Phase 1 (Foundation)
├── 1a: config_resolver.py
├── 1b: CHAT ALLOWED_USE_CASES
├── 1c: NOTES ALLOWED_USE_CASES
└── 1d: Tests
    │
    ├──► Phase 2 (CHAT Consumers) ──► Can run in parallel ◄── Phase 3 (NOTES Consumers)
    │    ├── 2a: gatekeeper                          │    ├── 3a: kg_processor
    │    ├── 2b: entity_extractor                    │    ├── 3b: entity_extractor
    │    ├── 2c: embeddings                          │    ├── 3c: embeddings
    │    ├── 2d: relationship_extraction             │    └── 3d: summarizer
    │    ├── 2e: chat config fallback
    │    └── 2f: thinking models
    │         │                                      │
    └─────────┼──────────────────────────────────────┘
              │
              ▼
         Phase 4 (Frontend + Validation)
         ├── 4a: Settings page UI
         ├── 4b: Cross-app test
         └── 4c: E2E tests
```

---

## Key Decisions

### Why NOT rewire rag_engine.py

`rag_engine.py:177-204` uses `get_model()` (Vertex AI SDK) for chat model selection.
The chat flow is already fully wired through ModelRouter via `chat_manager.py`. The
`rag_engine.set_model()` method is called with a user-selected model name from the
frontend, NOT from SettingsStore. This is intentional: users choose their chat model
per-session, while SettingsStore controls defaults. **No change needed.**

### Why a shared utility instead of per-consumer wiring

Without `resolve_use_case_config()`, each of the 7 consumers must independently:
1. Build a Redis URL from config
2. Call `get_default_sync()`
3. Handle None return
4. Extract provider and model fields
5. Decide env var fallback
6. Pass both to ModelRouter

This is 42 potential failure points (7 × 6 steps). With the utility: 7 call sites, each
3 lines. The utility is ~20 lines and 100% testable in isolation.

### Why not make SettingsStore async-first

`get_default_sync()` exists because 5 of 7 consumers are sync code (entity extractors,
embeddings, summarizer). Converting them to async is a larger refactor out of scope for
this milestone. The sync function with 5-minute cache is the right tradeoff.

### Gatekeeper + OpenRouter: Why the skip existed

The original skip was because `response_mime_type: "application/json"` is a Vertex AI
feature. OpenRouter's API format doesn't support it natively. **Fix:** When provider is
OpenRouter, add the JSON instruction to the prompt text instead of the generation config.
This is provider-specific handling, not a reason to skip the provider entirely.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Inline Resolution Without Shared Utility

**Bad:** Each consumer calls `get_default_sync()` directly with manual fallback.
**Why bad:** Duplicates logic, inconsistent behavior, hard to add providers.
**Instead:** All consumers call `resolve_use_case_config()`.

### Anti-Pattern 2: Silent Provider Skip

**Bad:** `if provider == "openrouter": log_and_use_vertex_instead()`
**Why bad:** Admin thinks they configured OpenRouter, but it's silently ignored.
**Instead:** Either support the provider or return a clear error to the settings API.

### Anti-Pattern 3: Hardcoded Lists as Primary Config

**Bad:** `RAG_ALLOWED_MODELS = ["gemini-2.5-flash-lite", ...]` used as primary model list.
**Why bad:** Doesn't reflect runtime provider configuration.
**Instead:** Dynamic list from `router.list_models()` with hardcoded list as emergency fallback only.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Problem identification | HIGH | All 7 points verified by reading source code |
| Config resolver design | HIGH | Follows existing patterns in codebase |
| Phase ordering | HIGH | Dependencies clear from code analysis |
| Gatekeeper + OpenRouter fix | MEDIUM | Need to verify OpenRouter supports JSON instruction in prompt |
| Thinking model list | MEDIUM | Need to verify which OpenRouter models support thinking |
| kg_processor wiring | HIGH | Clear: replace config import with resolver call |

## Gaps to Address

- **OpenRouter JSON mode:** Verify whether OpenRouter supports structured JSON output
  without `response_mime_type`. This affects the gatekeeper fix. (Phase 2a research flag)
- **Thinking-capable OpenRouter models:** Need to build a mapping of which OpenRouter
  models support thinking. Could be a static list or capability flag on ModelInfo. (Phase 2f)
- **Redis-down graceful degradation:** When Redis is down, `get_default_sync()` returns
  None silently. Consumers should log a warning so operators know settings aren't being
  applied. The resolver utility should include this logging.

## Sources

- `shared/model_router/src/model_router/settings_store.py` — SettingsStore implementation
- `shared/model_router/src/model_router/router.py` — ModelRouter provider routing
- `AURA-CHAT/backend/llm_gatekeeper.py` — Gatekeeper consumer (lines 138-166)
- `AURA-CHAT/backend/llm_entity_extractor.py` — Entity extractor consumer (lines 301-320)
- `AURA-CHAT/backend/utils/embeddings.py` — Embeddings consumer (lines 56-77, 150-161)
- `AURA-CHAT/backend/utils/config.py` — Static config (lines 59-63, 87-88, 199-206)
- `AURA-CHAT/server/routers/settings.py` — Settings API (line 55)
- `AURA-CHAT/server/routers/chat.py` — Chat config endpoint (lines 313-337)
- `AURA-NOTES-MANAGER/api/kg_processor.py` — KG processor consumer (line 465)
- `AURA-NOTES-MANAGER/api/config.py` — NOTES config (lines 62-73)
- `AURA-NOTES-MANAGER/api/routers/settings.py` — NOTES settings API (line 55)
- `AURA-NOTES-MANAGER/services/llm_entity_extractor.py` — NOTES entity extractor (lines 204-222)
- `AURA-NOTES-MANAGER/services/embeddings.py` — NOTES embeddings (lines 84-107)
- `AURA-NOTES-MANAGER/services/summarizer.py` — NOTES summarizer (lines 63-72)
- `.planning/issues/SETTINGS-WIRING-E2E.md` — Issue specification
