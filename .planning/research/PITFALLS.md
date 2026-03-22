# Domain Pitfalls: SettingsStore Wiring

**Domain:** Config-store integration through existing backend consumers
**Researched:** 2026-03-23
**Confidence:** HIGH (based on direct codebase analysis of settings_store.py,
all 7 problem consumers, and both settings routers; supplemented by community
patterns for Redis-backed config stores and dynamic config race conditions)

---

## Critical Pitfalls

Mistakes that cause silent misconfiguration, production confusion, or require
re-architecture to fix.

---

### Pitfall 1: Redis-Down Gets Cached as "No Config" (Zombie None)

**What goes wrong:**
`get_default_sync()` in `settings_store.py` catches all exceptions and returns
`None`. The `_defaults_cache` then stores `{"value": None, "_cached_at": t}`.
Once cached, a `None` entry is valid for `_DEFAULTS_CACHE_TTL` (5 minutes). If
Redis goes down briefly and recovers 10 seconds later, every consumer will still
return `None` for up to 5 minutes because the "Redis was unreachable" None is
indistinguishable from "no setting configured" None.

**Why it happens:**
The cache does not distinguish between:
- `client.hget()` returned `None` (genuinely no setting configured)
- Exception was caught (Redis down, network timeout, auth failure)

Both paths produce `None` and get cached identically at `settings_store.py:83`
and `settings_store.py:90-95`.

**Consequences:**
- All consumers fall back to env vars / hardcoded defaults for 5+ minutes after
  Redis recovers
- Admin sees "Settings applied" in UI but backend uses old model for up to 5 min
- No log signal distinguishes "not configured" from "config unavailable"
  (currently DEBUG-level only at `settings_store.py:90`)

**Prevention:**
- Cache a sentinel object (e.g., `{"_source": "error"}`) on exception, NOT
  plain `None`. Consumers check for sentinel and skip cache on next call.
- OR: Track cache entry source (`"redis"`, `"missing"`, `"error"`) and use
  shorter TTL (30-60s) for error-sourced entries vs confirmed-missing (5 min).
- Log at WARNING level when falling back due to Redis unavailability, not
  DEBUG (current behavior at `settings_store.py:90`).

**Detection:**
- Health endpoint comparing cached values vs live Redis values.
- Monitor `_defaults_cache` entries — if all are `None` while Redis is healthy,
  the zombie-None is active.

**Phase to address:** Phase 1 (Foundation) — fix before wiring any consumer.

---

### Pitfall 2: Per-Process Cache Creates Multi-Worker Inconsistency

**What goes wrong:**
`_defaults_cache` in `settings_store.py:27` is a module-level dict. Each
uvicorn worker process has its own Python interpreter and its own copy. When
an admin changes a setting via the API, the change goes to Redis but the
`_defaults_cache` in other workers is NOT invalidated.

**Why it happens:**
- Worker A handles PUT `/settings/defaults/entity_extraction` → writes to Redis
- Worker B handles the next entity extraction request → reads from its own
  `_defaults_cache` → returns stale value for up to 5 minutes
- No pub/sub, no shared memory, no cache-bust mechanism across processes

**Consequences:**
- Settings change appears to "sometimes work, sometimes not" depending on
  which worker handles the request
- Testing with a single worker masks this bug entirely
- Production with `--workers 4` shows intermittent stale config
- Support ticket: "I changed the model but some documents still use the old one"

**Prevention:**
- After any `set_default()` write, broadcast invalidation via Redis pub/sub
  so all workers clear their local cache for that use case.
- OR: Reduce `_DEFAULTS_CACHE_TTL` to 15-30s (trade latency for consistency).
- OR: Use Redis itself as the L1 cache layer (no in-process dict). Slightly
  more round-trips but always consistent.
- At minimum: expose `_DEFAULTS_CACHE_TTL` as an env var and document that
  settings changes take up to TTL seconds to propagate across workers.

**Detection:**
- Integration test starting 2+ workers, changing a setting, and asserting all
  workers see the new value within N seconds.

**Phase to address:** Phase 1 (Foundation) — cache invalidation strategy must
be decided before wiring consumers.

---

### Pitfall 3: Reading `model` but Ignoring `provider` (Accidental Routing)

**What goes wrong:**
Multiple consumers call `get_default_sync("entity_extraction")` which returns
`{"provider": "openrouter", "model": "anthropic/claude-3-opus"}`. The consumer
reads `model` but ignores `provider`, relying on ModelRouter's name-based
heuristic (`_determine_provider_type()` in `router.py:196-215`) to detect
OpenRouter via the `/` in the model name.

**Affected files:**
- `AURA-CHAT/backend/llm_entity_extractor.py:307-320` — reads model, ignores
  provider
- `AURA-NOTES-MANAGER/services/llm_entity_extractor.py:204-222` — same
- `AURA-NOTES-MANAGER/services/summarizer.py:64-72` — reads model only

**Why it happens:**
The `/` heuristic works by accident for OpenRouter (model names like
`anthropic/claude-3-opus`). But:
- A Vertex AI model name `gemini-2.5-flash` has no `/` → correctly routes
  to Vertex AI default provider
- If a future provider has non-`/` model names, the heuristic breaks
- If admin selects `provider: "vertex_ai"` with an OpenRouter-format model
  name, routing breaks silently

**Consequences:**
- Provider selection is implicit and fragile
- Adding a third provider (Ollama) requires changing every heuristic
- Settings UI shows "OpenRouter selected" but backend may route differently

**Prevention:**
- ALWAYS pass `provider` from SettingsStore explicitly to ModelRouter calls.
- The `GenerateRequest` model already has a `provider` field (`router.py:198`).
  Use it.
- Remove reliance on name-based detection as the primary routing mechanism.
- Keep the heuristic as a fallback only when `provider` is not set.

**Phase to address:** Phase 3 (Provider Passthrough) — wire provider field
through all consumers.

---

### Pitfall 4: `kg_processor.py` Module-Level Config Ignores SettingsStore

**What goes wrong:**
`AURA-NOTES-MANAGER/api/kg_processor.py:465` initializes `GeminiClient` with
`LLM_ENTITY_EXTRACTION_MODEL` imported from `api/config.py:62`. This is a
module-level constant set at import time from an env var. It never reads from
SettingsStore, so changing the entity extraction model in the settings page
has zero effect on KG processing.

Additionally, `GeminiClient.__init__()` creates its own `EmbeddingService()`
at `kg_processor.py:476`, which does read from SettingsStore for embeddings,
but the extraction model is still hardcoded.

**Why it happens:**
- `kg_processor.py` was written before SettingsStore existed
- It uses its own `GeminiClient` class instead of ModelRouter
- The config module (`api/config.py`) has no SettingsStore integration

**Consequences:**
- The most visible AI feature (document processing) ignores admin settings
- "I changed the model but documents still process with Gemini" — support
  tickets
- OpenRouter is completely unusable for KG processing
- Confusing: the settings page shows entity_extraction configured but the
  processing pipeline ignores it

**Prevention:**
- Replace `LLM_ENTITY_EXTRACTION_MODEL` import with `get_default_sync()`
  call at runtime (not import time).
- OR: Inject the resolved model into `GeminiClient.__init__()` rather than
  using a module-level constant.
- OR: Migrate `kg_processor.py` to use ModelRouter directly, eliminating the
  `GeminiClient` wrapper entirely (longer-term).

**Phase to address:** Phase 2 (NOTS-MANAGER Wiring) — highest-impact consumer
to fix.

---

### Pitfall 5: Gatekeeper Hard-Blocks OpenRouter with Blanket Skip

**What goes wrong:**
`AURA-CHAT/backend/llm_gatekeeper.py:153-159` explicitly skips OpenRouter
with a log message: "Gatekeeper skipping OpenRouter default (requires
response_mime_type)". Even if `gatekeeper` were in `ALLOWED_USE_CASES`,
selecting OpenRouter would be silently ignored and the hardcoded Vertex AI
model would be used.

**Why it happens:**
The gatekeeper requires `response_mime_type: "application/json"` for
structured output (`llm_gatekeeper.py:169`). The original developer assumed
OpenRouter doesn't support this parameter and blanket-skipped it.

**Consequences:**
- Admin configures OpenRouter for gatekeeper → silently ignored
- No error, no warning visible to admin — just Vertex AI used anyway
- Creates a class of "configurable but not really" use cases that erodes
  trust in the settings system
- `gatekeeper` use case is also missing from `ALLOWED_USE_CASES` (Pitfall 7)
  — double block

**Prevention:**
- Verify whether OpenRouter actually supports `response_mime_type` before
  skipping. Many OpenRouter models DO support JSON mode.
- If some models support it and others don't, check at provider registration
  time and expose a capabilities metadata flag.
- If OpenRouter genuinely can't support it, make the skip EXPLICIT in the
  settings UI (show "Vertex AI only" badge) rather than silent.
- Remove the blanket skip. Instead: attempt the call, catch the specific
  error, fall back to Vertex AI with a WARNING log.

**Phase to address:** Phase 5 (Gatekeeper Wiring) — requires provider
capability investigation first.

---

### Pitfall 6: EmbeddingService Blocks Non-Vertex Providers with Project Check

**What goes wrong:**
`AURA-CHAT/backend/utils/embeddings.py:228-232` raises `RuntimeError(
"VERTEX_PROJECT not configured")` if `self._project` is empty. This check
runs on EVERY `get_embeddings_batch()` call, even if the configured provider
is OpenRouter (which doesn't need a Vertex project).

**Why it happens:**
The `EmbeddingService` was originally Vertex-only. The project check was a
safety guard. When SettingsStore was added, the check wasn't removed because
the developer didn't want to risk breaking Vertex flows.

**Consequences:**
- If admin selects OpenRouter for embeddings but `VERTEX_PROJECT` env var is
  unset, the embedding call fails with a Vertex-specific error
- OpenRouter embeddings are architecturally impossible until this check is
  provider-aware
- Confusing error message: "VERTEX_PROJECT not configured" when the actual
  provider is OpenRouter

**Prevention:**
- Make the project check conditional: only enforce when
  `provider == "vertex_ai"`.
- OR: Move the project check to `VertexAIEmbeddingProvider.__init__()` where
  it belongs — the router should not enforce provider-specific requirements.
- The embedding service should delegate to `router.embed(provider=...)` and
  trust the provider to validate its own config.

**Phase to address:** Phase 4 (Embeddings Wiring) — must be fixed alongside
provider passthrough.

---

## Moderate Pitfalls

---

### Pitfall 7: `ALLOWED_USE_CASES` Gate Prevents Configuration of Real Use Cases

**What goes wrong:**
Both settings routers define `ALLOWED_USE_CASES = {"chat", "embeddings",
"entity_extraction", "summarization"}`. The `gatekeeper` and
`relationship_extraction` use cases are not in this set, so PUT requests
return 400. But backend code already calls `get_default_sync("gatekeeper")`
and `get_default_sync("relationship_extraction")` — the API just refuses to
let you configure them.

**Why it happens:**
The allowlist was created when only 4 use cases existed. New consumers were
added without updating the allowlist.

**Consequences:**
- Backend code for gatekeeper/relationship_extraction reads from SettingsStore
  but can never get a configured value via the API
- Admin UI shows only 4 use cases — the others are invisible
- Confusing: code looks like it supports SettingsStore but the API blocks it

**Prevention:**
- Treat `ALLOWED_USE_CASES` as the SINGLE SOURCE OF TRUTH for use cases.
  When adding a consumer that reads from SettingsStore, add its use case to
  the allowlist IN THE SAME PR.
- Add a test: `assert all consumer use cases ⊆ ALLOWED_USE_CASES`.
- OR: Remove the allowlist entirely and let any use case be configured
  (defense: validate provider/model pair instead).

**Phase to address:** Phase 1 (Foundation) — fix before any wiring work.

---

### Pitfall 8: Summarizer Silent Exception Swallowing

**What goes wrong:**
`AURA-NOTES-MANAGER/services/summarizer.py:66-72`:
```python
try:
    _admin_default = get_default_sync("summarization", redis_url=REDIS_URL)
    if _admin_default is not None:
        _admin_model = _admin_default.get("model", "")
        if _admin_model:
            _summarization_model = _admin_model
except Exception:
    pass  # silent swallow
```

**Why it happens:**
Developer added a bare `except: pass` to avoid crashing when Redis is
unavailable. But this means any exception — JSON parse error, connection
refused, authentication failure — is silently ignored with no log.

**Consequences:**
- Redis auth failure → silently uses env var, no indication anything is wrong
- Corrupt data in Redis → silently uses env var
- Impossible to debug "settings don't work" complaints
- Inconsistent with other consumers that at least log at DEBUG level

**Prevention:**
- At minimum: `except Exception: logger.debug("...", exc_info=True)`
- Better: The outer try/except is redundant — `get_default_sync()` already
  handles exceptions internally and returns `None`. Remove the outer try/except
  entirely.
- Never use bare `except: pass` in production code.

**Phase to address:** Phase 2 (NOTS-MANAGER Wiring) — fix as part of
summarizer wiring.

---

### Pitfall 9: Thinking Mode List Blocks OpenRouter Thinking Models

**What goes wrong:**
`AURA-CHAT/backend/utils/config.py:199-206` has a hardcoded list of
Vertex AI model names that support thinking mode. If an admin configures an
OpenRouter model that supports thinking (e.g.,
`google/gemini-2.0-flash-thinking`), the thinking toggle won't appear in
the UI because the model name won't match.

**Why it happens:**
The thinking mode feature was built before multi-provider support. The model
list was the simplest way to gate the feature.

**Consequences:**
- OpenRouter thinking-capable models are invisible to the thinking toggle
- Admin sees model in picker but can't enable thinking for it
- Feature parity gap between Vertex AI and OpenRouter

**Prevention:**
- Make `CHAT_MODELS_WITH_THINKING` dynamic: query provider capabilities
  metadata instead of maintaining a hardcoded list.
- OR: Add a `supports_thinking` flag to `ModelInfo` and populate it from
  provider-specific knowledge.
- OR: At minimum, include common OpenRouter thinking models in the list and
  document that it must be updated when new thinking models are added.

**Phase to address:** Phase 7 (Chat Config Fix) — alongside chat config
fallback work.

---

### Pitfall 10: RAG Engine Fallback Swaps Provider Silently

**What goes wrong:**
`AURA-CHAT/backend/rag_engine.py:183-184` falls back to
`config.RAG_MODEL_DEFAULT` which is `"gemini-2.5-flash-lite"` — a Vertex AI
model. If the user selected an OpenRouter model and that model fails to
initialize, the fallback silently switches to Vertex AI.

**Why it happens:**
The fallback chain was designed before multi-provider support. It always
resolves to a Vertex AI model name, which routes through Vertex AI provider.

**Consequences:**
- User selects `anthropic/claude-3-opus` → model init fails → silently gets
  `gemini-2.5-flash-lite` via Vertex AI
- User sees completely different model behavior with no explanation
- Cost tracking records the wrong provider
- Conversation history may show inconsistent model attribution

**Prevention:**
- The fallback should respect the user's provider preference. If OpenRouter
  is selected and fails, try the OpenRouter default model, not Vertex AI's.
- OR: Surface the fallback to the user with a visible warning in the chat
  response metadata.
- OR: Fail loudly rather than silently switching providers.

**Phase to address:** Phase 7 (Chat Config Fix) — model fallback strategy
needs multi-provider awareness.

---

## Minor Pitfalls

---

### Pitfall 11: Redis URL Construction Fragility

**What goes wrong:**
Multiple consumers manually construct the Redis URL:
```python
redis_url = f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}"
```
While `config.py` has `REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")`
already defined. This creates two sources of truth for the same connection.

**Affected files:**
- `AURA-CHAT/backend/llm_gatekeeper.py:140-142`
- `AURA-CHAT/backend/llm_entity_extractor.py` (via constructor)
- `AURA-CHAT/backend/utils/embeddings.py:56`

**Prevention:**
- Use `config.REDIS_URL` everywhere instead of reconstructing from parts.
- Single env var, single source of truth.

**Phase to address:** Phase 1 (Foundation) — cleanup before wiring.

---

### Pitfall 12: Import-Time SettingsStore Reads Create Stale Module Globals

**What goes wrong:**
`AURA-NOTES-MANAGER/services/llm_entity_extractor.py:204-222` calls
`get_default_sync()` at MODULE IMPORT TIME to set the module-level constant
`LLM_ENTITY_EXTRACTION_MODEL`. This value is computed once when the module
is first imported and never refreshed.

**Why it's risky:**
- If the module is imported before Redis is ready, it falls back to env var
  permanently (for that process lifetime)
- The 5-minute cache in `get_default_sync()` is irrelevant because the
  module-level assignment captures the value at import time
- If settings change after import, the module global is stale until process
  restart

**Prevention:**
- Read from SettingsStore at call time (inside the class/function), not at
  import time.
- Module-level constants should come from env vars only (startup-time config).
  Runtime config should be resolved lazily.

**Phase to address:** Phase 2 (NOTS-MANAGER Wiring) — refactor to lazy
resolution.

---

## Cross-Cutting Concerns

### Race Condition: Settings Change vs In-Flight Requests

**Scenario:** Admin changes entity_extraction model from Gemini to Claude via
settings UI. A document processing request started 2 seconds earlier is
mid-pipeline. The first LLM call used Gemini (read from cache before change).
The second LLM call (after cache expired or was invalidated) reads Claude.

**Impact:** Mixed-model processing within a single document. Entity extraction
style changes mid-document. Potential for inconsistent entity schemas.

**Mitigation:**
- Snapshot the SettingsStore value at the START of a long-running operation
  and pass it through the pipeline. Don't re-read mid-operation.
- For document processing: read settings once in `document_processor.py`
  and inject into all downstream consumers.
- For chat: settings are per-request, so the race window is tiny (acceptable).
- For batch operations (KG processing, embeddings): the settings snapshot
  approach is essential.

**Phase to address:** Phase 2-4 (consumer-specific) — each consumer must
snapshot at operation start.

### Race Condition: Concurrent Settings Writes

**Scenario:** Two admins update different use cases simultaneously. Both
read-modify-write the Redis hash.

**Impact:** Redis HSET is per-field, not whole-hash. Concurrent writes to
DIFFERENT use cases are safe (no conflict). Concurrent writes to the SAME
use case: last write wins (acceptable for admin settings — unlikely and
non-destructive).

**Mitigation:** None needed. Current Redis hash design is safe for this use
case.

### SettingsStore Unavailability During Long-Running Operations

**Scenario:** Document processing starts. 30 seconds in, Redis goes down.
`get_default_sync()` returns `None` (Redis unreachable). Consumer falls back
to env var. Different model than the first batch.

**Impact:** Mixed-model processing. Same as the settings-change race.

**Mitigation:**
- Snapshot settings at operation start (same as above).
- The `_defaults_cache` with 5-minute TTL helps — if the setting was cached
  before Redis went down, subsequent reads within 5 min return the cached
  value.
- BUT: if the cache expires during the operation AND Redis is down, the
  zombie-None problem (Pitfall 1) kicks in.

**Phase to address:** Phase 1 — fix zombie-None caching first.

---

## Phase-Specific Warnings

| Phase | Topic | Likely Pitfall | Mitigation |
|-------|-------|---------------|------------|
| 1 | Foundation | Zombie-None caching masks Redis recovery | Sentinel cache entries, error-source tracking |
| 1 | Foundation | Multi-worker cache inconsistency | Redis pub/sub invalidation or shorter TTL |
| 1 | Foundation | `ALLOWED_USE_CASES` not updated | Sync allowlist with consumer use cases in same PR |
| 1 | Foundation | Redis URL construction fragility | Use `config.REDIS_URL` everywhere |
| 2 | NOTES Wiring | `kg_processor.py` ignores SettingsStore | Replace module-level constant with runtime read |
| 2 | NOTES Wiring | Summarizer swallows exceptions silently | Add logging, remove bare `except: pass` |
| 2 | NOTES Wiring | Import-time reads create stale globals | Move to lazy resolution at call time |
| 3 | Provider Pass | Entity extraction ignores `provider` field | Always pass provider to `GenerateRequest` |
| 3 | Provider Pass | Name-based routing heuristic is fragile | Use explicit provider, keep heuristic as fallback |
| 4 | Embeddings | Vertex project check blocks OpenRouter | Make check provider-conditional |
| 4 | Embeddings | `router.embed()` defaults to first provider | Always pass `provider=` explicitly |
| 5 | Gatekeeper | Blanket OpenRouter skip hides real capability | Verify JSON mode support per-model, not per-provider |
| 5 | Gatekeeper | `gatekeeper` not in `ALLOWED_USE_CASES` | Add to allowlist (Phase 1 dependency) |
| 6 | Relationship | No SettingsStore integration at all | Add `get_default_sync("relationship_extraction")` |
| 6 | Relationship | Env var fallback chain undocumented | Document: SettingsStore → env var → hardcoded |
| 7 | Chat Config | Hardcoded model list only has Vertex AI | Dynamic model list from router capabilities |
| 7 | Chat Config | Fallback swaps provider silently | Respect provider preference or fail loudly |
| 7 | Thinking | Hardcoded thinking model list blocks OR models | Capability metadata on `ModelInfo` |

---

## Summary of Severity

| Pitfall | Severity | Silent? | Phase |
|---------|----------|---------|-------|
| 1. Zombie-None caching | CRITICAL | Yes | 1 |
| 2. Multi-worker inconsistency | CRITICAL | Yes | 1 |
| 3. Provider field ignored | CRITICAL | Yes | 3 |
| 4. kg_processor bypass | CRITICAL | Yes | 2 |
| 5. Gatekeeper OpenRouter skip | MODERATE | Yes | 5 |
| 6. Embedding project check | MODERATE | No | 4 |
| 7. ALLOWED_USE_CASES gate | MODERATE | No | 1 |
| 8. Summarizer silent swallow | MODERATE | Yes | 2 |
| 9. Thinking model list | MODERATE | Yes | 7 |
| 10. RAG engine fallback swap | MODERATE | Yes | 7 |
| 11. Redis URL fragility | MINOR | No | 1 |
| 12. Import-time stale globals | MODERATE | Yes | 2 |

---

## Sources

- `shared/model_router/src/model_router/settings_store.py` — cache behavior,
  exception handling, TTL logic, `_defaults_cache` module-level dict
- `shared/model_router/src/model_router/router.py` — provider routing
  heuristic (`_determine_provider_type()`), `GenerateRequest.provider` field
- `AURA-CHAT/backend/llm_gatekeeper.py` — OpenRouter blanket skip,
  Vertex-only fallback, `get_default_sync("gatekeeper")` call
- `AURA-CHAT/backend/llm_entity_extractor.py` — provider field ignored
  at line 307-320
- `AURA-CHAT/backend/utils/embeddings.py` — Vertex project check at
  line 228-232, provider passthrough at line 154-159
- `AURA-CHAT/backend/utils/config.py` — hardcoded model lists at lines
  59-63 (RAG_ALLOWED_MODELS), 87-88 (LLM_RELATIONSHIP_MODEL), 199-206
  (CHAT_MODELS_WITH_THINKING)
- `AURA-CHAT/server/routers/chat.py` — config fallback at lines 313-337
- `AURA-CHAT/server/routers/settings.py` — ALLOWED_USE_CASES at line 55
- `AURA-NOTES-MANAGER/api/kg_processor.py` — bypasses SettingsStore at
  line 465 (GeminiClient init)
- `AURA-NOTES-MANAGER/api/config.py` — module-level constants at lines
  62-73 (LLM_ENTITY_EXTRACTION_MODEL, LLM_SUMMARIZATION_MODEL, EMBEDDING_MODEL)
- `AURA-NOTES-MANAGER/api/routers/settings.py` — ALLOWED_USE_CASES at line 55
- `AURA-NOTES-MANAGER/services/summarizer.py` — silent exception swallowing
  at lines 66-72
- `AURA-NOTES-MANAGER/services/llm_entity_extractor.py` — import-time
  SettingsStore read at lines 204-222
- `AURA-NOTES-MANAGER/services/embeddings.py` — SettingsStore read at
  lines 84-107
- Community patterns: Redis two-level cache with circuit breaker (go-cache,
  2026), config-as-dependency anti-patterns (Stackademic, 2026), dynamic
  config race conditions (Spring Boot incident, 2026)
- Production postmortems: Redis failover cascading failures (Medium, 2026),
  config reload without coordination (DAP iQ, 2026)
