# Feature Landscape: SettingsStore E2E Wiring

**Domain:** Multi-provider LLM configuration consistency across dual-app platform
**Researched:** 2026-03-23

## Table Stakes

Features that MUST work for this milestone to ship. Missing any = settings page
is still misleading.

### 1. All Use Cases Configurable via Settings API

**Why Expected:** The settings UI promises per-use-case defaults. If a use case
cannot be configured via the API, the UI cannot control it. Currently
`gatekeeper` and `relationship_extraction` return 400 on PUT.

| Use Case | Where It Lives Today | Current Read Pattern | Target |
|----------|---------------------|---------------------|--------|
| `chat` | SettingsStore (working) | `get_default_sync("chat")` | Already wired |
| `embeddings` | SettingsStore (working) | `get_default_sync("embeddings")` — model read, provider fragile | Fix provider passthrough |
| `entity_extraction` | SettingsStore (working) | `get_default_sync("entity_extraction")` in CHAT and NOTES services; env var in NOTES kg_processor | Wire kg_processor |
| `summarization` | SettingsStore (working) | `get_default_sync("summarization")` in services/summarizer | Route through ModelRouter |
| `gatekeeper` | **MISSING** from `ALLOWED_USE_CASES` | `get_default_sync("gatekeeper")` called, but API rejects config | Add to API + UI |
| `relationship_extraction` | **MISSING entirely** | `LLM_RELATIONSHIP_MODEL` env var only | Add to API, SettingsStore, UI |

**Complexity:** Low — constant change in two files + type union update

**Files:**
- `AURA-CHAT/server/routers/settings.py:55` — add `"gatekeeper"`, `"relationship_extraction"`
- `AURA-NOTES-MANAGER/api/routers/settings.py:55` — same
- `AURA-NOTES-MANAGER/frontend/src/types/settings.ts:32` — update `UseCase` union
- `AURA-NOTES-MANAGER/frontend/src/features/settings/components/DefaultModelSection.tsx:44-48` — add to `USE_CASES` array

---

### 2. Provider Field Respected Everywhere

**Why Expected:** The whole point of multi-provider support is that selecting
`"openrouter"` as the provider actually routes through OpenRouter. If the
`provider` field is ignored, only the `model` field matters — the settings
UI's provider selector is decorative.

**Current State — Provider Passthrough Matrix:**

| Consumer | SettingsStore Read | Provider Used? | Gap |
|----------|-------------------|----------------|-----|
| AURA-CHAT chat | `get_default_sync("chat")` | YES — passed to `GenerateRequest.provider` | Working |
| AURA-CHAT entity_extractor | `get_default_sync("entity_extraction")` | NO — reads `model` only, relies on `/` heuristic | Must pass provider |
| AURA-CHAT gatekeeper | `get_default_sync("gatekeeper")` | NO — explicitly skips OpenRouter, uses Vertex only | Must remove skip |
| AURA-CHAT embeddings | `get_default_sync("embeddings")` | Fragile — model override but provider inconsistency | Must pass provider to `router.embed()` |
| AURA-CHAT relationship extraction | Not read at all | N/A — env var only | Must add SettingsStore + provider |
| NOTES kg_processor | Not read at all | N/A — env var `LLM_ENTITY_EXTRACTION_MODEL` to `GeminiClient` | Must add SettingsStore + provider |
| NOTES services/entity_extractor | `get_default_sync("entity_extraction")` | NO — reads model only | Must pass provider |
| NOTES services/embeddings | `get_default_sync("embeddings")` | Fragile — same pattern as CHAT | Must pass provider |
| NOTES services/summarizer | `get_default_sync("summarization")` | NO — reads model only, uses Vertex SDK directly | Must route through ModelRouter |

**Complexity:** Medium — touching 8+ files across both apps

**Pattern to Follow:**
```python
# Correct: pass both provider and model
_default = get_default_sync("entity_extraction", redis_url=redis_url)
if _default:
    provider = _default.get("provider")
    model = _default.get("model")
    response = await router.generate(
        model=model,
        provider=provider,  # Explicit provider, don't rely on heuristics
        ...
    )
```

---

### 3. No Silent Env-Var Fallbacks When SettingsStore Has a Value

**Why Expected:** If an admin configures a model in the settings page, that
should be authoritative. Silent fallback to env vars makes the settings page
a lie.

**Current Violations:**

| File | Issue |
|------|-------|
| `AURA-CHAT/backend/llm_gatekeeper.py:153-159` | Silently skips OpenRouter even when explicitly configured |
| `AURA-CHAT/backend/utils/config.py:59-63` | `RAG_ALLOWED_MODELS` hardcodes Vertex-only models as chat config fallback |
| `AURA-CHAT/backend/utils/config.py:199-206` | `CHAT_MODELS_WITH_THINKING` hardcodes Vertex-only models |
| `AURA-NOTES-MANAGER/api/config.py:62-73` | `LLM_ENTITY_EXTRACTION_MODEL`, `LLM_SUMMARIZATION_MODEL`, `EMBEDDING_MODEL` env vars used as primary source in kg_processor |

**Expected Behavior:** When SettingsStore is reachable and returns a value, that
value wins. Env vars serve as bootstrap defaults only — they must not shadow
admin-configured settings.

---

### 4. Graceful Degradation When SettingsStore Is Unavailable

**Why Expected:** Redis may be down during startup or intermittently. The system
must not crash — it should degrade visibly, not silently.

**Required Behaviors:**

| Scenario | Expected | Current |
|----------|----------|---------|
| Redis down at startup | Log warning, use env var defaults, retry on next call | Partially works — `get_default_sync` catches exceptions and returns None, callers fall through to env vars |
| Redis comes back mid-operation | Cache TTL (5 min) picks up new values | Works via `_DEFAULTS_CACHE_TTL` |
| Redis down during settings page load | API returns error (500), UI shows "unable to load" | Works (FastAPI raises) |
| Redis down during chat config fetch | Return env var fallback list, log warning | Works but returns Vertex-only list (see gap below) |

**Key Gap:** The chat config fallback (`RAG_ALLOWED_MODELS`) should include
models from all registered providers, not just Vertex AI. This is a
differentiator (Feature 8) and can be deferred.

---

### 5. Gatekeeper Works with OpenRouter (No Silent Skip)

**Why Expected:** If the admin configures gatekeeper to use an OpenRouter model,
it should route through OpenRouter. The current explicit skip at
`llm_gatekeeper.py:153-159` was added because gatekeeper requires
`response_mime_type: "application/json"`, which was assumed to be Vertex-only.

**Investigation Required:** Whether OpenRouter models (especially
`google/gemini-*` via OpenRouter) support `response_mime_type`. If not, this
needs provider-specific handling rather than a blanket skip.

**Complexity:** Medium — requires testing OpenRouter's JSON mode support

**Acceptance Criteria:**
- If OpenRouter supports JSON mode: remove skip, route through ModelRouter
- If not: replace silent skip with documented capability check, clear log
  message, and provider-aware fallback (not generic env var)

---

### 6. Summarizer Routes Through ModelRouter

**Why Expected:** The summarizer in `AURA-NOTES-MANAGER/services/summarizer.py`
reads the model from SettingsStore but calls the Vertex AI SDK directly
(`get_model()` from `vertexai`). It never goes through `ModelRouter.generate()`.
Selecting OpenRouter as the summarization provider is impossible.

**Current Pattern (Wrong):**
```python
_summarization_model = LLM_SUMMARIZATION_MODEL
_admin_default = get_default_sync("summarization", redis_url=REDIS_URL)
if _admin_default:
    _summarization_model = _admin_default["model"]
# Then calls Vertex SDK directly — provider field ignored entirely
```

**Target Pattern:**
```python
_default = get_default_sync("summarization", redis_url=REDIS_URL)
if _default:
    provider = _default.get("provider")
    model = _default.get("model")
# Route through ModelRouter.generate() with explicit provider
```

**Complexity:** Medium — summarizer uses synchronous Vertex SDK pattern;
needs async ModelRouter integration or sync wrapper.

---

## Differentiators

Features that go beyond basic wiring. Valued, but not required for this milestone.

### 7. Dynamic Thinking Mode Model List

**Value:** Instead of hardcoding `CHAT_MODELS_WITH_THINKING` in config.py,
derive thinking-capable models from the provider's model metadata. OpenRouter
models like `google/gemini-2.0-flash-thinking` would automatically appear as
thinking-capable.

**Complexity:** High — requires model capability metadata from providers

**Recommendation:** Defer. For now, add a comment in config.py that the list
must be manually updated when new providers are added. A future milestone can
add capability metadata to `ModelInfo`.

---

### 8. Chat Config Fallback Includes All Providers

**Value:** When the model router is unavailable, the chat config endpoint
should return a fallback list that includes models from all registered
providers, not just Vertex AI. This prevents OpenRouter models from
disappearing from the UI during Redis outages.

**Complexity:** Medium — requires reading model list from a non-Redis source

**Recommendation:** Defer to a resilience milestone. For now, document the
Vertex-only fallback behavior.

---

### 9. Health Indicator for SettingsStore Connectivity

**Value:** The settings page could show whether SettingsStore (Redis) is
reachable, so admins know if their changes will actually take effect.

**Complexity:** Low — add a health check endpoint

**Recommendation:** Nice-to-have if time permits. Not blocking.

---

## Anti-Features

Things to explicitly NOT do in this milestone.

### Don't: Add New Providers

This is a wiring milestone, not a provider milestone. The existing providers
(Vertex AI, OpenRouter, Ollama stub) are sufficient. Adding more providers
would expand scope without addressing the core problem.

### Don't: Refactor SettingsStore to Async-Only

`get_default_sync()` exists because many consumers are synchronous (embedding
services, entity extractors run in thread pools). Removing the sync path would
require async-ifying every consumer — scope creep.

### Don't: Change the Redis Schema

The current hash at `aura:model_router:settings` with `{provider, model}` per
use case is adequate. Adding new fields (e.g., `temperature`, `max_tokens`)
is a separate concern.

### Don't: Build a Unified Config Migration System

Both apps have their own env var configs (`config.py`). This milestone should
not try to unify them into one file. Instead, each consumer reads from
SettingsStore first, env vars second.

### Don't: Add Provider-Specific Logic to SettingsStore

SettingsStore should remain provider-agnostic. Provider capability checks
(e.g., "does OpenRouter support JSON mode?") belong in the provider
implementation, not the settings layer.

---

## Feature Dependencies

```
Feature 1 (All use cases configurable)
  └── Must complete before: Feature 2, 5, 6

Feature 2 (Provider field respected everywhere)
  └── Depends on: Feature 1
  └── Must complete before: Feature 5, 6

Feature 3 (No silent env-var fallbacks)
  └── Depends on: Feature 1, 2
  └── Parallel with: Feature 4

Feature 4 (Graceful degradation)
  └── Depends on: Feature 3 (so we know what "graceful" means)
  └── Parallel with: Feature 3

Feature 5 (Gatekeeper with OpenRouter)
  └── Depends on: Feature 1, 2
  └── Needs investigation: OpenRouter JSON mode support

Feature 6 (Summarizer through ModelRouter)
  └── Depends on: Feature 2
  └── Risk: Sync-to-async refactor

Feature 7 (Dynamic thinking models)
  └── No dependency on wiring — defer to later milestone

Feature 8 (Multi-provider fallback)
  └── Depends on: Feature 4 — defer to later milestone
```

---

## MVP Recommendation

### Must Ship (Table Stakes)

1. **Feature 1** — Add `gatekeeper` and `relationship_extraction` to
   `ALLOWED_USE_CASES` + UI. Low risk, high value.
2. **Feature 2** — Wire provider passthrough in all 8 consumer locations.
   Medium risk, core of the milestone.
3. **Feature 3** — Audit and fix all env-var-overrides-settingsStore patterns.
   Shipped as part of Feature 2 verification.

### Should Ship

4. **Feature 4** — Document graceful degradation behavior. Verify
   `get_default_sync` exception handling is correct (it mostly is already).
5. **Feature 5** — Remove gatekeeper OpenRouter skip, test JSON mode support.
   Medium risk, depends on investigation.
6. **Feature 6** — Wire summarizer through ModelRouter. Medium risk, may
   require sync-to-async work.

### Defer

7. **Feature 7** — Dynamic thinking model list. Future milestone.
8. **Feature 8** — Multi-provider chat config fallback. Future resilience milestone.

---

## Sources

- `.planning/PROJECT.md` — Project context and v1.1/v1.2 milestones
- `.planning/issues/SETTINGS-WIRING-E2E.md` — Detailed problem analysis with
  file references
- `shared/model_router/src/model_router/settings_store.py` — SettingsStore
  implementation (lines 45-101 for sync path, 109-160 for async)
- `shared/model_router/src/model_router/router.py` — ModelRouter routing logic
  (lines 196-215 for provider determination, 314-350 for embed)
- `AURA-CHAT/server/routers/settings.py` — `ALLOWED_USE_CASES` at line 55
- `AURA-CHAT/backend/llm_gatekeeper.py:138-166` — Gatekeeper provider
  resolution with OpenRouter skip
- `AURA-CHAT/backend/utils/embeddings.py:57-77` — Embeddings SettingsStore read
- `AURA-CHAT/backend/utils/config.py:59-63, 199-206` — Hardcoded model lists
- `AURA-CHAT/server/routers/chat.py:313-337` — Chat config endpoint fallback
- `AURA-NOTES-MANAGER/api/routers/settings.py:55` — NOTES ALLOWED_USE_CASES
- `AURA-NOTES-MANAGER/api/kg_processor.py:457-476` — GeminiClient with
  env-var-only model
- `AURA-NOTES-MANAGER/api/config.py:62-73` — Env var defaults (entity,
  summarization, embedding)
- `AURA-NOTES-MANAGER/services/llm_entity_extractor.py:204-222` — SettingsStore
  read (model only)
- `AURA-NOTES-MANAGER/services/embeddings.py:84-107` — SettingsStore read
  (model only)
- `AURA-NOTES-MANAGER/services/summarizer.py:64-72` — SettingsStore read +
  direct Vertex SDK call
- `AURA-NOTES-MANAGER/frontend/src/types/settings.ts:32` — `UseCase` union type
  (missing 2 use cases)
- `AURA-NOTES-MANAGER/frontend/src/features/settings/components/DefaultModelSection.tsx:44-48` —
  UI use case list
