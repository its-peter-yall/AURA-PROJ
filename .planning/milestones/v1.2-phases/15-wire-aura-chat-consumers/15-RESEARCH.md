# Phase 15: Wire AURA-CHAT Consumers - Research

**Researched:** 2026-03-23
**Domain:** AURA-CHAT backend consumer wiring to ModelRouter via SettingsStore
**Confidence:** HIGH

## Summary

Phase 15 wires four AURA-CHAT backend consumers to read provider+model from the
`resolve_use_case_config()` utility (built in Phase 14) and pass the `provider`
explicitly through the `VertexCompatModel` compat layer to the shared ModelRouter.
Currently, all consumers rely on the router's `/` heuristic to guess the provider
from the model name, which breaks for non-OpenRouter model IDs that contain `/`
and prevents OpenRouter models from being used for entity extraction, gatekeeper,
and relationship extraction.

**Primary recommendation:** Add a `provider` field to `VertexCompatModel` so that
`_build_request_kwargs` passes it to `GenerateRequest`, then replace `get_default_sync`
calls in each consumer with `resolve_use_case_config()` and wire the returned provider
through.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `model_router` (shared) | 0.1.0 | Unified provider routing | Already in use across project |
| `model_router.settings_store` | — | `resolve_use_case_config()` + `get_default_sync()` | Phase 14 built this |
| `model_router.compat.VertexCompatModel` | — | Legacy-compatible model wrapper | Current call surface for all consumers |
| `model_router.types.GenerateRequest` | — | Normalized request with `provider` field | Router already supports explicit provider |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `backend.utils.config` | — | Env-var-backed config singleton | Fallback chain (Step 2) |
| `backend.utils.vertex_ai_client.get_model()` | — | Creates `VertexCompatModel` | Needs provider-aware variant |

### Installation
No new dependencies. All infrastructure exists in `shared/model_router/`.

## Architecture Patterns

### Current (Broken) Flow
```
Consumer → get_default_sync("use_case") → {"model": "X", "provider": "vertex_ai"}
                                          ↓ (provider IGNORED)
Consumer → get_model(model_name) → VertexCompatModel(model_name)
                                          ↓ (_build_request_kwargs has no provider)
Router → GenerateRequest(model="X") → _determine_provider_type()
                                          ↓ (/ heuristic)
Provider = OPENROUTER if "/" in model, else default_provider
```

### Target Flow
```
Consumer → resolve_use_case_config("use_case") → {"model": "X", "provider": "Y"}
                                          ↓ (provider PASSED through)
Consumer → get_model(model_name, provider=provider) → VertexCompatModel(model_name, provider)
                                          ↓ (_build_request_kwargs passes provider)
Router → GenerateRequest(model="X", provider="Y") → _determine_provider_type()
                                          ↓ (explicit provider, no heuristic)
Provider = Y (direct lookup)
```

### Pattern 1: `resolve_use_case_config()` Usage
**What:** 3-step config resolution: SettingsStore (Redis) → env var → hardcoded default
**When to use:** Every consumer that needs provider+model config
**Example:**
```python
# Source: shared/model_router/src/model_router/settings_store.py:142-170
from model_router.settings_store import resolve_use_case_config

redis_url = f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}"
cfg = resolve_use_case_config("entity_extraction", redis_url=redis_url)
# cfg = {"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"}
```

### Pattern 2: Provider-Aware `VertexCompatModel`
**What:** Pass `provider` through the compat model to the router's `GenerateRequest`
**When to use:** All consumers that call `get_model()` and then `generate_content()`
**Current problem:** `VertexCompatModel.__init__` only takes `model_name`, and
`_build_request_kwargs` never sets `provider` on the request kwargs dict.
**Required change:** Add optional `provider` parameter to `VertexCompatModel.__init__`
and propagate it through `_build_request_kwargs`.

### Pattern 3: Embeddings Already Correct
The `EmbeddingService` in `backend/utils/embeddings.py` (lines 154-161) already passes
`provider=self._embedding_default["provider"]` to `router.embed()`. This is the pattern
all consumers should follow. No change needed for PP-03 — it already works.

### Anti-Patterns to Avoid
- **Don't pass provider as `GenerateRequest` kwarg directly from consumers** — the compat
  layer should handle this so existing call sites (`model.generate_content(...)`) continue
  working unchanged
- **Don't duplicate the 3-step fallback chain** — use `resolve_use_case_config()`, not
  `get_default_sync()` + manual env var + manual default
- **Don't blanket-skip providers** — the gatekeeper's lines 153-159 that skip all
  OpenRouter defaults must be replaced with capability-aware routing

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Config resolution | Manual 3-step fallback | `resolve_use_case_config()` | Already built in Phase 14, tested |
| Provider routing | `/` heuristic override in each consumer | Explicit `provider` on `GenerateRequest` | Router already handles this at lines 196-215 |
| SettingsStore error handling | Custom Redis error catch | Sentinel-based cache (Phase 14) | 30s error TTL already implemented |

**Key insight:** `VertexCompatModel` is the single integration point. Adding `provider`
propagation there fixes ALL consumers that go through `get_model()` — which is all of them.

## Common Pitfalls

### Pitfall 1: OpenRouter JSON Mode Gap
**What goes wrong:** The gatekeeper needs `response_mime_type: "application/json"` for
structured output. OpenRouter's provider (`openrouter.py:348-397`) does NOT translate
`response_mime_type` to OpenAI's `response_format` parameter. If you remove the blanket
skip, JSON parsing will fail for OpenRouter models.

**Why it happens:** The OpenRouter provider's `generate()` method never reads
`request.response_mime_type` from the `GenerateRequest`.

**How to avoid:** Two options:
1. **(Recommended) Add `response_format` translation to OpenRouter provider** — when
   `response_mime_type` is `"application/json"`, pass
   `response_format={"type": "json_object"}` to `client.chat.completions.create()`
2. Keep the blanket skip but replace it with a capability check —
   check if the provider supports JSON mode before routing

**Warning signs:** Gatekeeper returns `JSONDecodeError` on every OpenRouter model call.

### Pitfall 2: Entity Extractor Model vs Relationship Model
**What goes wrong:** The entity extractor has TWO LLM call paths:
1. `extract_entities()` → `_extract_from_batch()` → uses `self.model` (entity extraction)
2. `extract_entity_relationships()` → `_extract_relationships_via_llm()` → also uses `self.model`

Both currently use the SAME model. The `relationship_extraction` use case in SettingsStore
is configured separately, but no code path reads it. Wire them independently:
- Entity extraction → `resolve_use_case_config("entity_extraction")`
- Relationship extraction → `resolve_use_case_config("relationship_extraction")`

**Warning signs:** Relationship extraction model ignores admin settings.

### Pitfall 3: `_build_request_kwargs` Missing Provider
**What goes wrong:** `VertexCompatModel._build_request_kwargs()` (compat.py:188-205)
builds the `kwargs` dict without a `provider` key. Even if `VertexCompatModel` stores
a `_provider` field, it won't reach `GenerateRequest` unless `_build_request_kwargs` is
updated.

**Warning signs:** Provider is set in `__init__` but router still uses `/` heuristic.

### Pitfall 4: Gatekeeper Sync/Async Boundary
**What goes wrong:** `llm_gatekeeper_reclassify()` is async but calls `get_model()` and
`model.generate_content()` via `run_in_executor`. The `resolve_use_case_config()` function
is synchronous (as is `get_default_sync`). This is fine — the sync config call happens
before the executor.

**How to avoid:** Keep the config resolution outside the executor lambda.

## Code Examples

### Consumer Wiring Template (What All 4 Consumers Should Look Like)
```python
# Source: derived from resolve_use_case_config() in settings_store.py:142-170
from model_router.settings_store import resolve_use_case_config

# In consumer __init__ or top-level function:
redis_url = f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}"
cfg = resolve_use_case_config("entity_extraction", redis_url=redis_url)
model_name = cfg["model"]
provider = cfg["provider"]

# Create model with provider routing
model = get_model(model_name, provider=provider)  # NEW: provider parameter

# generate_content() call is unchanged — provider flows through compat layer
response = model.generate_content(prompt, generation_config=generation_config)
```

### VertexCompatModel Provider Addition
```python
# Source: shared/model_router/src/model_router/compat.py:170-205
class VertexCompatModel:
    def __init__(self, model_name: str, provider: str | None = None) -> None:
        normalized_model = _normalize_vertex_model_name(model_name)
        self._model_name = normalized_model
        self.model_name = normalized_model
        self._provider = provider  # NEW
        self._router: Any | None = None

    def _build_request_kwargs(self, contents, generation_config, safety_settings, system_instruction):
        request_kwargs = {
            "model": self._model_name,
            "contents": contents,
        }
        if self._provider is not None:  # NEW
            request_kwargs["provider"] = self._provider
        # ... rest unchanged
```

### get_model() Provider-Aware Variant
```python
# Source: AURA-CHAT/backend/utils/vertex_ai_client.py:237-248
def get_model(model_name: str, provider: str | None = None) -> VertexCompatModel:
    """Return a model-router-backed legacy-compatible model wrapper."""
    if os.getenv("USE_MODEL_ROUTER", "").lower() == "true":
        try:
            import model_router.compat as compat_module
            return compat_module.VertexCompatModel(model_name, provider=provider)
        except ImportError:
            pass
    normalized = normalize_model_name(model_name)
    return _GenerativeModelWrapper(normalized, provider=provider)
```

### OpenRouter JSON Mode Fix
```python
# Source: shared/model_router/src/model_router/providers/openrouter.py:348-375
async def generate(self, request: GenerateRequest) -> GenerateResponse:
    # ... existing code ...
    kwargs: dict[str, Any] = {
        "model": request.model,
        "messages": _build_messages(request),
    }
    # NEW: Translate response_mime_type to OpenAI response_format
    if request.response_mime_type == "application/json":
        kwargs["response_format"] = {"type": "json_object"}
    # ... rest unchanged
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded env var `LLM_ENTITY_EXTRACTION_MODEL` | `resolve_use_case_config("entity_extraction")` | Phase 14 | SettingsStore authoritative |
| `/` heuristic in router | Explicit `provider` on `GenerateRequest` | Phase 15 | Correct provider routing |
| Gatekeeper blanket OpenRouter skip | Provider-aware JSON mode check | Phase 15 | OpenRouter gatekeeper support |
| `get_default_sync()` (reads SettingsStore only) | `resolve_use_case_config()` (3-step chain) | Phase 14 | Graceful env var fallback |

**Deprecated/outdated:**
- `get_default_sync()` for consumer wiring — use `resolve_use_case_config()` instead
  (get_default_sync is still valid internally for the resolution chain's Step 1)
- Blanket OpenRouter skip in gatekeeper (lines 153-159) — must be removed

## Open Questions

1. **Should `relationship_extraction` use the SAME model as entity extraction, or separate?**
   - What we know: Phase 14 added `relationship_extraction` to `ALLOWED_USE_CASES` as a
     separate use case. `resolve_use_case_config("relationship_extraction")` exists.
   - What's unclear: Currently `extract_entity_relationships()` reuses `self.model` from
     entity extraction. Should it have its own model resolved from SettingsStore?
   - Recommendation: Wire it independently — use
     `resolve_use_case_config("relationship_extraction")` in
     `_extract_relationships_via_llm()`. This is a separate task from entity extraction
     wiring since it requires a second model instance.

2. **OpenRouter JSON mode: Should we add `response_format` translation now?**
   - What we know: OpenRouter provider doesn't pass `response_format`. Gatekeeper needs
     it. Blanket skip is currently the only defense.
   - What's unclear: Whether all OpenRouter models support `response_format: json_object`.
   - Recommendation: Add translation now with a per-model opt-in check, or add a
     `supports_json_mode` flag to provider metadata. Start conservative.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | Root `pytest.ini` |
| Quick run command | `python -m pytest AURA-CHAT/tests/backend/test_llm_entity_extractor.py -x` |
| Full suite command | `python -m pytest AURA-CHAT/tests/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PP-01 | Entity extractor passes explicit provider | unit | `python -m pytest AURA-CHAT/tests/backend/test_llm_entity_extractor.py -x` | ✅ |
| PP-02 | Gatekeeper routes through ModelRouter without OpenRouter skip | unit | `python -m pytest AURA-CHAT/tests/test_llm_gatekeeper.py -x` | ✅ |
| PP-03 | Embeddings passes provider to router.embed() | unit | (no dedicated test file — covered by existing embeddings tests) | ⚠️ Partial |
| PP-04 | Relationship extraction reads from SettingsStore | unit | `python -m pytest AURA-CHAT/tests/backend/test_llm_relationship_extractor.py -x` | ✅ |

### Sampling Rate
- **Per task commit:** `python -m pytest AURA-CHAT/tests/backend/test_llm_entity_extractor.py AURA-CHAT/tests/test_llm_gatekeeper.py -x`
- **Phase gate:** Full `python -m pytest AURA-CHAT/tests/ -x` suite green

### Wave 0 Gaps
- [ ] `AURA-CHAT/tests/backend/test_embeddings_provider.py` — dedicated test for PP-03
      confirming `provider` is passed to `router.embed()` when SettingsStore is configured
- [ ] `AURA-CHAT/tests/test_llm_gatekeeper.py` — needs test for OpenRouter provider path
      (currently all tests mock `get_model` and don't test provider routing)
- [ ] `AURA-CHAT/tests/backend/test_llm_relationship_extractor.py` — needs test confirming
      `resolve_use_case_config("relationship_extraction")` is called independently

## Sources

### Primary (HIGH confidence)
- `shared/model_router/src/model_router/settings_store.py` — `resolve_use_case_config()`
  implementation with 3-step chain (lines 142-170)
- `shared/model_router/src/model_router/compat.py` — `VertexCompatModel` class,
  `_build_request_kwargs()` (lines 170-247) — CONFIRMED missing provider passthrough
- `shared/model_router/src/model_router/router.py` — `_determine_provider_type()` lines
  196-215 — CONFIRMED `/` heuristic and explicit provider support
- `shared/model_router/src/model_router/types.py` — `GenerateRequest` with `provider:
  str | None = None` field (line 41) — CONFIRMED router supports explicit provider

### Secondary (MEDIUM confidence)
- `AURA-CHAT/backend/utils/embeddings.py` lines 154-161 — CONFIRMED already passes
  provider to `router.embed()`
- `AURA-CHAT/backend/llm_gatekeeper.py` lines 138-163 — CONFIRMED blanket OpenRouter skip
  with comment "requires response_mime_type"
- `AURA-CHAT/backend/llm_entity_extractor.py` lines 301-320 — CONFIRMED `_resolve_default_model`
  uses `get_default_sync("entity_extraction")` but ignores provider

### Tertiary (LOW confidence)
- `shared/model_router/src/model_router/providers/openrouter.py` lines 348-397 — CONFIRMED
  no `response_format` translation in `generate()` method

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All infrastructure exists from Phase 14, confirmed in code
- Architecture: HIGH — Clear integration point (VertexCompatModel), no ambiguity
- Pitfalls: MEDIUM — OpenRouter JSON mode gap needs verification against live API

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (30 days — model_router is stable, SettingsStore Phase 14 just completed)
