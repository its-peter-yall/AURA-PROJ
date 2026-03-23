# Phase 16: Wire AURA-NOTES-MANAGER Consumers — Research

**Researched:** 2026-03-23
**Domain:** LLM consumer wiring, SettingsStore config resolution, ModelRouter integration
**Confidence:** HIGH

## Summary

Phase 16 wires four AURA-NOTES-MANAGER consumers (KG processor, entity extractor, embeddings, summarizer) to read provider/model from `resolve_use_case_config()` and route all LLM calls through the shared ModelRouter. The infrastructure from Phase 14 (`resolve_use_case_config()` with 3-step fallback chain, sentinel cache fix, expanded `ALLOWED_USE_CASES`) is complete and ready.

Each consumer currently has a partial or incorrect integration pattern:
- **KG processor** (`kg_processor.py`): Imports `LLM_ENTITY_EXTRACTION_MODEL` as a module-level constant from `api.config` — changing the env var requires a process restart.
- **Entity extractor** (`llm_entity_extractor.py`): Calls `get_default_sync()` at **import time** (line 204) — reads SettingsStore once at module load, then freezes. Does not pass `provider` to `GenerateRequest`. Directly calls `vertex_ai_client.generate_content()`.
- **Embeddings** (`embeddings.py`): Reads SettingsStore at init time and passes `provider` to `router.embed()` — **closest to correct** but reads config once at construction, not at each call.
- **Summarizer** (`summarizer.py`): Has a `bare except: pass` (line 71-72) that silently swallows SettingsStore errors. Falls through to direct Vertex AI SDK calls via `genai_client` and `vertex_ai_client` — never uses `router.generate()`.

**Primary recommendation:** Use `resolve_use_case_config()` at **call time** (not import/init time) in each consumer, pass `{provider, model}` explicitly to the ModelRouter's `generate()`/`embed()` methods, and replace all bare `except: pass` with logged error handling.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `model_router` (shared) | local | Config resolution + request routing | Built for this milestone |
| `resolve_use_case_config()` | Phase 14 | 3-step config resolution (Store → env → default) | Centralizes fallback logic |
| `ModelRouter.generate()` | current | Async generation with provider routing | Uniform LLM API |
| `ModelRouter.embed()` | current | Async embedding with provider routing | Uniform embedding API |
| `get_default_sync()` | current | Sync Redis read for sync call-sites | Needed by embedding/entity services |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `model_router.compat._run_sync` | current | Bridge async router calls from sync code | Sync consumer entry points |
| `GenerateRequest` | Pydantic v2 | Normalized request model with `provider` field | All generation calls |
| `VertexCompatModel` | current | Legacy compatibility wrapper | When existing code expects `model.generate_content()` |
| `tenacity` | current | Retry logic (already in kg_processor) | Keep existing retry decorators |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `resolve_use_case_config()` | `get_default_sync()` + manual env fallback | Duplicates the 3-step chain already built |
| `router.generate()` | Keeping `vertex_ai_client.generate_content()` shim | Shim routes through router internally but hides `provider` param — defeats the purpose |
| Call-time resolution | Init-time resolution | Init-time means settings changes require restart — violates success criterion 1 |

**Installation:**
No new packages needed — all dependencies already installed.

## Architecture Patterns

### Recommended Project Structure
```
AURA-NOTES-MANAGER/
├── api/
│   ├── kg_processor.py          # PP-05: Replace LLM_ENTITY_EXTRACTION_MODEL const
│   └── tests/
│       └── test_consumer_wiring.py  # NEW: Integration tests for all 4 consumers
├── services/
│   ├── llm_entity_extractor.py  # PP-06: Remove import-time get_default_sync, pass provider
│   ├── embeddings.py            # PP-07: Call-time provider resolution, pass to router.embed()
│   └── summarizer.py            # PP-08: Replace direct SDK calls with router.generate()
```

### Pattern 1: Call-Time Config Resolution

**What:** Call `resolve_use_case_config()` at each LLM invocation, not at import/init time. This ensures settings changes take effect immediately without restart.

**When to use:** All consumers that make LLM calls.

**Example:**
```python
# Source: model_router/settings_store.py resolve_use_case_config()
from model_router import resolve_use_case_config

def some_consumer_function(text: str) -> str:
    cfg = resolve_use_case_config("entity_extraction")
    # cfg = {"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"}
    # Use cfg["provider"] and cfg["model"] in the router call
```

### Pattern 2: Explicit Provider in GenerateRequest

**What:** Pass `provider` from the resolved config to `GenerateRequest`, ensuring the router routes to the correct provider.

**When to use:** All generation calls (entity extraction, summarization, KG processing).

**Example:**
```python
# Source: model_router/types.py GenerateRequest
from model_router import get_default_router, resolve_use_case_config

cfg = resolve_use_case_config("entity_extraction")
router = get_default_router()
response = await router.generate(
    model=cfg["model"],
    contents=prompt,
    provider=cfg["provider"],
    temperature=0.2,
    max_output_tokens=4096,
)
```

### Pattern 3: Provider in router.embed()

**What:** Pass `provider` keyword argument to `router.embed()` so embeddings route to the configured provider.

**When to use:** All embedding calls.

**Example:**
```python
# Source: model_router/router.py ModelRouter.embed()
from model_router import get_default_router, resolve_use_case_config

cfg = resolve_use_case_config("embeddings")
router = get_default_router()
embeddings = await router.embed(
    texts=texts,
    provider=cfg["provider"],
)
```

### Pattern 4: Logged Error Handling (No Bare except)

**What:** Replace `except: pass` with `except Exception: logger.warning(...)` and explicit fallback behavior.

**When to use:** Every error handler — especially in `summarizer.py` lines 71-72.

**Example:**
```python
# WRONG (current summarizer.py:71-72):
except Exception:
    pass

# RIGHT:
except Exception:
    logger.warning(
        "SettingsStore unavailable for summarization, using env var fallback",
        exc_info=True,
    )
```

### Anti-Patterns to Avoid

- **Import-time config reads:** `get_default_sync()` at module level (current `llm_entity_extractor.py:204`) means settings changes never take effect. Must move to call-time.
- **Init-time config reads:** `get_default_sync()` in `__init__()` (current `embeddings.py:84`) means config is frozen at object creation. Move to call-time if object is long-lived.
- **Bare `except: pass`:** Silently swallows SettingsStore errors (current `summarizer.py:71-72`). Always log and handle explicitly.
- **Dual SDK path in summarizer:** Current code tries `genai_client` first, then falls through to `vertex_ai_client` — both are compatibility shims that route through model_router internally, but neither passes `provider`. Replace both with a single `router.generate()` call.
- **Missing provider in legacy shims:** `vertex_ai_client.generate_content()` and `genai_client.generate_content_with_thinking()` are shims that internally call the router but don't expose the `provider` parameter. Using them bypasses the explicit provider routing.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Config resolution | Custom 3-step fallback | `resolve_use_case_config()` | Already built in Phase 14, handles SettingsStore → env → default with sentinel cache |
| Request routing | Direct provider SDK calls | `router.generate(provider=cfg["provider"])` | Router handles provider selection, retries, usage tracking |
| Embedding routing | Direct Vertex AI embed calls | `router.embed(provider=cfg["provider"])` | Same — uniform routing across providers |
| Error logging | `except: pass` | `logger.warning("...", exc_info=True)` | Silent failures hide production issues |
| Sync-to-async bridge | Custom threading | `model_router.compat._run_sync()` | Already handles event loop edge cases |

**Key insight:** All four consumers currently use legacy compatibility shims (`vertex_ai_client`, `genai_client`) that internally route through the model_router but **hide the `provider` parameter**. The fix is to call `router.generate()` / `router.embed()` directly with the explicit `provider` from `resolve_use_case_config()`.

## Common Pitfalls

### Pitfall 1: Import-Time Config Freezing
**What goes wrong:** `get_default_sync()` called at module level caches the config at import time. Changing the setting in the admin UI has no effect until process restart.
**Why it happens:** Module-level code runs once at import.
**How to avoid:** Move `resolve_use_case_config()` calls to function/method body, executing at each invocation.
**Warning signs:** `get_default_sync()` or `resolve_use_case_config()` outside any `def` or `async def` block.

### Pitfall 2: Ignoring the `provider` Field
**What goes wrong:** Consumer reads `model` from config but lets the router guess the provider from the model name (the `/` heuristic for OpenRouter). This fails for non-slash-form model IDs.
**Why it happens:** Historical code predates the `provider` field in `GenerateRequest`.
**How to avoid:** Always pass `provider=cfg["provider"]` explicitly.
**Warning signs:** `GenerateRequest(model=cfg["model"])` without `provider=` kwarg.

### Pitfall 3: Summarizer's Dual-Path SDK Dance
**What goes wrong:** `summarizer.py` tries `genai_client.get_genai_model()` → `genai_client.generate_content_with_thinking()` first, then falls through to `vertex_ai_client.get_model()` → `vertex_ai_client.generate_content()`. Both paths are shims that route through model_router internally but don't pass `provider`.
**Why it happens:** Legacy code from pre-model-router era.
**How to avoid:** Replace both paths with a single `router.generate()` call.
**Warning signs:** Importing from both `genai_client` and `vertex_ai_client` in the same file.

### Pitfall 4: Bare `except: pass` Hiding Failures
**What goes wrong:** `summarizer.py:71-72` catches all exceptions from `get_default_sync()` and silently ignores them. If Redis is down, the fallback to env vars happens silently — no warning in logs.
**Why it happens:** Defensive coding without logging discipline.
**How to avoid:** Always log at `WARNING` level with `exc_info=True`.
**Warning signs:** `except Exception: pass` or `except: pass`.

### Pitfall 5: Sync/Async Boundary Confusion
**What goes wrong:** Some consumers are sync (`EmbeddingService.embed_text()`, `LLMEntityExtractor` module-level functions) while `ModelRouter.generate()` and `router.embed()` are async.
**Why it happens:** Legacy sync APIs that can't easily become async.
**How to avoid:** Use `_run_sync()` from `model_router.compat` to bridge sync call-sites to async router methods. This is already the pattern in `embeddings.py:_embed_batch_sync()`.
**Warning signs:** Calling `await` in a sync function or not using `_run_sync()`.

## Code Examples

### Verified pattern: resolve_use_case_config() (Phase 14)
```python
# Source: shared/model_router/src/model_router/settings_store.py
from model_router import resolve_use_case_config

# Always returns {"provider": str, "model": str} — never None, never raises
cfg = resolve_use_case_config("entity_extraction")
# Returns e.g. {"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"}
```

### Verified pattern: router.generate() with explicit provider
```python
# Source: shared/model_router/src/model_router/router.py:248
from model_router import get_default_router, resolve_use_case_config

cfg = resolve_use_case_config("entity_extraction")
router = get_default_router()
response = await router.generate(
    model=cfg["model"],
    contents=prompt,
    provider=cfg["provider"],   # <-- explicit provider routing
    temperature=0.2,
    max_output_tokens=4096,
)
# response.text, response.model_used, response.provider, response.metadata
```

### Verified pattern: router.embed() with explicit provider
```python
# Source: shared/model_router/src/model_router/router.py:314
from model_router import get_default_router, resolve_use_case_config

cfg = resolve_use_case_config("embeddings")
router = get_default_router()
embeddings = await router.embed(
    texts=texts,
    provider=cfg["provider"],   # <-- explicit provider routing
)
# Returns List[List[float]]
```

### Verified pattern: _run_sync() for bridging sync call-sites
```python
# Source: model_router/compat.py
from model_router.compat import _run_sync

# From a sync function, call an async router method:
embeddings = _run_sync(router.embed(texts, provider=cfg["provider"]))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct `vertexai` SDK calls | `router.generate()` via compat shims | Phase 8-10 (v1.1) | All generation goes through model_router |
| `get_default_sync()` at import time | `resolve_use_case_config()` at call time | Phase 14 (v1.2) | Settings changes take effect without restart |
| Ignoring `provider` field | Explicit `provider=` in GenerateRequest/embed | Phase 16 (v1.2) | Correct multi-provider routing |
| `except: pass` | `logger.warning(..., exc_info=True)` | Phase 16 (v1.2) | Errors visible in logs |

**Deprecated/outdated:**
- Import-time `get_default_sync()` in `llm_entity_extractor.py:204` — replaced by call-time `resolve_use_case_config()`
- `genai_client.get_genai_model()` + `generate_content_with_thinking()` dual path in summarizer — replaced by single `router.generate()` call
- `vertex_ai_client.get_model()` + `generate_content()` direct path — only use when legacy compat surface is required (not here)

## Open Questions

1. **GeminiClient class in kg_processor.py — refactor or patch?**
   - What we know: `GeminiClient` wraps `vertex_ai_client.get_model()` and `generate_content()` for entity extraction and text generation. It's used by `KnowledgeGraphProcessor`.
   - What's unclear: Whether to rewrite `GeminiClient` to use `router.generate()` directly, or just patch the callers in `KnowledgeGraphProcessor` to use `resolve_use_case_config()` + `router.generate()` and leave `GeminiClient` as a legacy path.
   - Recommendation: Patch the callers. `GeminiClient` is used in ~4 places in `kg_processor.py` (init, generate_text, extract_entities, get_embedding). Replace each with `resolve_use_case_config()` + direct router calls. This minimizes blast radius.

2. **Summarizer thinking mode — how to preserve?**
   - What we know: Current summarizer uses `genai_client.generate_content_with_thinking()` which sets `temperature=0.2, max_output_tokens=4096`. The Vertex path uses `temperature=1.0, top_p=0.95, max_output_tokens=32000`.
   - What's unclear: Which config is the "correct" summarizer config? The genai path seems to be the newer one.
   - Recommendation: Use the genai path's config (temperature=0.2, max_output_tokens=4096) as the default `GenerationConfig` for `router.generate()` in the summarizer, since it's the newer code path.

3. **LLMEntityExtractor singleton — how to handle runtime config?**
   - What we know: `_get_extractor()` creates a singleton `LLMEntityExtractor` whose model is set at construction time from import-time config.
   - What's unclear: Whether the singleton needs to be invalidated on config changes, or whether we just call `resolve_use_case_config()` at each `extract_from_batch()` call.
   - Recommendation: Call `resolve_use_case_config()` inside `_extract_from_batch()` and use `router.generate()` directly, bypassing `self._model`. The singleton can remain for test mode and backward compat, but actual LLM calls should resolve config at call time.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio |
| Config file | `AURA-NOTES-MANAGER/conftest.py` (sets AURA_TEST_MODE=true, REDIS_ENABLED=false) |
| Quick run command | `cd AURA-NOTES-MANAGER && python -m pytest api/tests/ -x -v` |
| Full suite command | `cd AURA-NOTES-MANAGER && python -m pytest -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PP-05 | KG processor uses `resolve_use_case_config("entity_extraction")` at runtime | unit | `pytest api/tests/test_consumer_wiring.py::test_kg_processor_uses_resolve_config -x` | ❌ Wave 0 |
| PP-06 | Entity extractor passes `provider` from SettingsStore to GenerateRequest | unit | `pytest api/tests/test_consumer_wiring.py::test_entity_extractor_passes_provider -x` | ❌ Wave 0 |
| PP-07 | Embeddings passes `provider` from SettingsStore to `router.embed()` | unit | `pytest api/tests/test_consumer_wiring.py::test_embeddings_passes_provider -x` | ❌ Wave 0 |
| PP-08 | Summarizer routes through ModelRouter, no bare `except: pass` | unit | `pytest api/tests/test_consumer_wiring.py::test_summarizer_uses_router -x` | ❌ Wave 0 |
| PP-05/06/07/08 | Consumers fall back to env vars when Redis unreachable | integration | `pytest api/tests/test_consumer_wiring.py::test_redis_fallback_graceful -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd AURA-NOTES-MANAGER && python -m pytest api/tests/test_consumer_wiring.py -x -v`
- **Per wave merge:** `cd AURA-NOTES-MANAGER && python -m pytest -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `AURA-NOTES-MANAGER/api/tests/test_consumer_wiring.py` — covers PP-05 through PP-08
- [ ] Test uses `FakeSyncRedis` or pre-populated `_defaults_cache` to simulate SettingsStore values
- [ ] Test mocks `ModelRouter.generate()` and `ModelRouter.embed()` to verify `provider` parameter

*(No framework gaps — pytest + pytest-asyncio already installed and configured)*

## Sources

### Primary (HIGH confidence)
- `shared/model_router/src/model_router/settings_store.py` — `resolve_use_case_config()` implementation, 3-step fallback, sentinel cache
- `shared/model_router/src/model_router/router.py:248-279` — `ModelRouter.generate()` signature with `provider` routing
- `shared/model_router/src/model_router/router.py:314-350` — `ModelRouter.embed()` signature with `provider` routing
- `shared/model_router/src/model_router/types.py:36-58` — `GenerateRequest` Pydantic model with `provider` field
- `AURA-NOTES-MANAGER/api/kg_processor.py` — Current KG processor (1336+ lines, direct Vertex SDK calls)
- `AURA-NOTES-MANAGER/services/llm_entity_extractor.py` — Current entity extractor (import-time config at line 204)
- `AURA-NOTES-MANAGER/services/embeddings.py` — Current embedding service (init-time config at line 84)
- `AURA-NOTES-MANAGER/services/summarizer.py` — Current summarizer (bare except at line 71-72, dual SDK path)
- `AURA-NOTES-MANAGER/api/config.py` — Module-level constants: `LLM_ENTITY_EXTRACTION_MODEL`, `LLM_SUMMARIZATION_MODEL`, `EMBEDDING_MODEL`
- `.planning/phases/14-foundation-config-resolver-allowlist-cache-fixes/14-01-SUMMARY.md` — Phase 14 completion evidence

### Secondary (MEDIUM confidence)
- `AURA-NOTES-MANAGER/services/vertex_ai_client.py` — Legacy compat shim (routes through model_router internally but hides `provider`)
- `AURA-NOTES-MANAGER/services/genai_client.py` — Legacy genai compat shim (same issue)
- `shared/model_router/tests/test_settings_store.py` — Test patterns for `resolve_use_case_config()`
- `AURA-NOTES-MANAGER/api/tests/test_settings_router.py` — Test patterns for NOTES settings endpoints (FakeAsyncRedis)

### Tertiary (LOW confidence)
- Existing `AURA-NOTES-MANAGER/tests/test_summarizer.py` — Tests mock genai/vertex paths, will need updating for router-based approach

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — `resolve_use_case_config()`, `router.generate()`, `router.embed()` are well-documented Phase 14 deliverables
- Architecture: HIGH — Patterns verified from Phase 14 summary and source code inspection
- Pitfalls: HIGH — Import-time config freeze, bare except, dual SDK path all confirmed in source

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (30 days — Phase 14 infrastructure is stable)
