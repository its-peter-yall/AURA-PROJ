# Phase 14: Foundation — Config Resolver + Allowlist + Cache Fixes - Research

**Researched:** 2026-03-23
**Domain:** Redis-backed settings resolution, use-case configuration, cache invalidation
**Confidence:** HIGH

## Summary

Phase 14 is the foundation phase for v1.2 (Settings Wiring E2E). It introduces a shared `resolve_use_case_config()` utility in `shared/model_router/`, expands `ALLOWED_USE_CASES` to include `gatekeeper` and `relationship_extraction`, and fixes the zombie-None caching problem in `get_default_sync()`. No new dependencies are required — all changes use existing shared packages.

The core problem: consumers currently duplicate config resolution logic with slight variations (Redis URL construction, None handling, provider/model extraction). The new utility centralizes a 3-step resolution chain (SettingsStore → env var → hardcoded default) and returns `{provider, model}` reliably, never None. The 5-minute cache TTL and module-level `_defaults_cache` create multi-worker staleness that must be addressed before any consumer wiring proceeds.

**Primary recommendation:** Add `resolve_use_case_config()` to `settings_store.py`, expand `ALLOWED_USE_CASES` in both settings routers, and fix caching with a sentinel-object pattern (30s error TTL, 60s miss TTL) to eliminate zombie-None behavior.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| model_router (shared) | local `shared/model_router/` | Config resolution, routing | Existing shared package — no new deps |
| redis (sync) | installed | `get_default_sync()` Redis client | Already used by consumers |
| redis.asyncio | installed | SettingsStore async Redis client | Already used by settings routers |
| pytest | >=8.0 | Unit test framework | Existing test runner |
| pytest-asyncio | >=0.23 | Async test support | Existing async test patterns |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| fakeredis | - | NOT needed — use existing FakeAsyncRedis | Already in `shared/model_router/tests/conftest.py` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Sentinel object for error cache | Shorter TTL only | Sentinel explicitly marks errors vs misses; cleaner logic |
| Redis pub/sub invalidation | TTL-only approach | Adds complexity; TTL is sufficient for v1.2 |
| Async-only resolution | Keep sync `get_default_sync()` | Sync consumers (embeddings, entity extractors) can't await |

**Installation:**
```bash
# No new packages needed — all dependencies exist
```

## Architecture Patterns

### Recommended Project Structure
```
shared/model_router/src/model_router/
├── settings_store.py          # ADD: resolve_use_case_config(), _MISS sentinel
├── __init__.py                # UPDATE: export resolve_use_case_config
└── ...

shared/model_router/tests/
├── test_settings_store.py     # ADD: tests for resolve_use_case_config()
├── conftest.py                # Existing FakeAsyncRedis (no changes needed)
└── ...

AURA-CHAT/server/routers/
└── settings.py                # UPDATE: ALLOWED_USE_CASES += gatekeeper, relationship_extraction

AURA-NOTES-MANAGER/api/routers/
└── settings.py                # UPDATE: ALLOWED_USE_CASES += gatekeeper, relationship_extraction
```

### Pattern 1: `resolve_use_case_config()` — Central Resolution Utility
**What:** A single function that returns `{provider, model}` via a 3-step fallback chain: SettingsStore → env var → hardcoded default. Never returns None.
**When to use:** Every sync consumer that needs a provider/model pair for a use case.
**Example:**
```python
# Source: derived from SUMMARY.md + consumer analysis
# Location: shared/model_router/src/model_router/settings_store.py

# Hardcoded defaults per use case
_USE_CASE_DEFAULTS: dict[str, dict[str, str]] = {
    "chat": {"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"},
    "embeddings": {"provider": "vertex_ai", "model": "text-embedding-004"},
    "entity_extraction": {"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"},
    "summarization": {"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"},
    "gatekeeper": {"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"},
    "relationship_extraction": {"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"},
}

# Env var mapping per use case
_USE_CASE_ENV_VARS: dict[str, tuple[str, str]] = {
    "entity_extraction": ("LLM_ENTITY_EXTRACTION_MODEL", "vertex_ai"),
    "summarization": ("LLM_SUMMARIZATION_MODEL", "vertex_ai"),
    "relationship_extraction": ("LLM_RELATIONSHIP_MODEL", "vertex_ai"),
}

def resolve_use_case_config(
    use_case: str,
    redis_url: str | None = None,
    redis_client: Any = None,
) -> dict[str, str]:
    """Return {provider, model} for a use case with fallback chain.

    Resolution order:
      1. SettingsStore (Redis) — authoritative when reachable
      2. Environment variable — per-use-case env override
      3. Hardcoded default — always-available fallback

    Never returns None.  Never raises on Redis failure.
    """
    # Step 1: SettingsStore
    store_value = get_default_sync(use_case, redis_url, redis_client)
    if store_value is not None:
        return store_value

    # Step 2: Env var
    env_spec = _USE_CASE_ENV_VARS.get(use_case)
    if env_spec:
        env_var, provider = env_spec
        env_model = os.getenv(env_var)
        if env_model:
            return {"provider": provider, "model": env_model}

    # Step 3: Hardcoded default
    return _USE_CASE_DEFAULTS.get(
        use_case,
        {"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"},
    )
```

### Pattern 2: Sentinel-Based Cache Fix (Zombie-None)
**What:** Distinguish "key doesn't exist" (cache with long TTL) from "Redis error" (cache with short TTL, or don't cache) using a sentinel object.
**When to use:** Inside `get_default_sync()` to prevent 5-minute zombie-None when Redis recovers.
**Example:**
```python
# Source: settings_store.py lines 25-42, 80-95
# Fix: Add sentinel + error TTL

_ERROR_CACHE_TTL = 30  # 30 seconds for error-sourced entries
_MISS_CACHE_TTL = 300  # 5 minutes for confirmed-miss entries

_SENTINEL_ERROR = object()  # Marks "Redis was unreachable"

def get_default_sync(use_case, redis_url=None, redis_client=None):
    # Check cache
    entry = _defaults_cache.get(use_case)
    if entry is not None:
        age = time.time() - entry["_cached_at"]
        if entry["value"] is _SENTINEL_ERROR:
            if age < _ERROR_CACHE_TTL:
                return None  # Still within error cache window
            # Error cache expired — retry Redis
        elif age < _MISS_CACHE_TTL:
            return entry["value"]  # Valid cache hit or miss

    # Attempt Redis read...
    try:
        raw = client.hget(SETTINGS_KEY, use_case)
        if raw is None:
            _defaults_cache[use_case] = {"value": None, "_cached_at": time.time()}
            return None
        parsed = json.loads(_decode_redis_text(raw))
        _defaults_cache[use_case] = {"value": parsed, "_cached_at": time.time()}
        return parsed
    except Exception:
        logger.warning("Redis unavailable for use_case=%s", use_case, exc_info=True)
        _defaults_cache[use_case] = {"value": _SENTINEL_ERROR, "_cached_at": time.time()}
        return None
```

### Pattern 3: Allowlist Expansion
**What:** Add `"gatekeeper"` and `"relationship_extraction"` to the `ALLOWED_USE_CASES` set constant.
**When to use:** Both settings routers (CHAT + NOTES) must be updated identically.
**Example:**
```python
# Source: AURA-CHAT/server/routers/settings.py:55
# Source: AURA-NOTES-MANAGER/api/routers/settings.py:55

# BEFORE:
ALLOWED_USE_CASES = {"chat", "embeddings", "entity_extraction", "summarization"}

# AFTER:
ALLOWED_USE_CASES = {
    "chat",
    "embeddings",
    "entity_extraction",
    "summarization",
    "gatekeeper",
    "relationship_extraction",
}
```

### Anti-Patterns to Avoid
- **Caching errors the same as misses:** Redis-down and key-miss are different states — use sentinels or separate TTLs
- **Returning None from resolution:** Every use case must have a hardcoded default; callers should never need to handle None
- **Building Redis URLs in consumers:** `resolve_use_case_config()` should accept `redis_url` or use the `REDIS_URL` env var internally; consumers should not construct URLs
- **Module-level config reads:** Resolution must happen at call-time, not import-time, to support runtime settings changes

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Config resolution chain | Custom per-consumer SettingsStore + env var + default logic | `resolve_use_case_config()` | Eliminates 7+ duplicated patterns; single test surface |
| Redis URL construction | `f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}"` in every consumer | `REDIS_URL` env var (already defined in `settings_store.py:76`) | Prevents `localhost` vs `127.0.0.1` inconsistency |
| Cache error handling | Bare `except: return None` without caching distinction | Sentinel object with differentiated TTL | Prevents 30-60s of stale None after Redis recovers |

**Key insight:** The `resolve_use_case_config()` function is ~25 lines but eliminates 42+ potential failure points across 7 consumers. Each consumer currently does its own Redis URL building, None-checking, provider extraction, env-fallback, and default-selection — with slight variations that cause bugs.

## Common Pitfalls

### Pitfall 1: Zombie-None Cache (CRITICAL)
**What goes wrong:** When a use case has no configured value in Redis, `get_default_sync()` caches `None` for 5 minutes. If a value is written to Redis after the cache is populated, consumers continue reading stale `None` for up to 5 minutes. Worse, if Redis is down during a read, the current code does NOT cache the error (retries on every call), but if the key previously existed and was cached, the old value persists indefinitely until the TTL expires.
**Why it happens:** Single cache dict, single TTL, no distinction between "Redis error" and "key absent."
**How to avoid:** Use sentinel objects for error entries (30s TTL) vs miss entries (5-min TTL). On Redis error, cache sentinel with short TTL so recovery is prompt.
**Warning signs:** Settings changes take >30s to propagate; `get_default_sync()` returns None even after `set_default()` confirms the write.

### Pitfall 2: Multi-Worker Cache Inconsistency (CRITICAL)
**What goes wrong:** Module-level `_defaults_cache` is per-process. When uvicorn runs with multiple workers, Worker A's cache is not invalidated when Worker B writes to Redis via `set_default()`. Each worker holds stale values until its own TTL expires.
**Why it happens:** In-process cache without cross-process invalidation.
**How to avoid:** Acceptable for v1.2 with 30-60s TTL (fast enough for admin settings). Document the behavior. If inconsistency is observed in production, add Redis pub/sub invalidation in a later milestone.
**Warning signs:** Settings page shows one value but the system behaves differently; intermittent config mismatches between requests.

### Pitfall 3: Redis URL Inconsistency (MODERATE)
**What goes wrong:** `settings_store.py:76` defaults to `redis://127.0.0.1:6379/0`. `AURA-CHAT/backend/utils/config.py:228` builds from `REDIS_HOST` (defaults to `localhost`). `AURA-CHAT/server/routers/settings.py:56` defaults to `redis://localhost:6379`. `AURA-NOTES-MANAGER/api/config.py:88` defaults to `redis://127.0.0.1:6379/0`. Mixing `localhost` and `127.0.0.1` causes IPv4/IPv6 resolution differences.
**Why it happens:** Each module defines its own default independently.
**How to avoid:** Use `REDIS_URL` env var everywhere (single source of truth). The `resolve_use_case_config()` function should default to `os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")` consistently.
**Warning signs:** Connection errors on some platforms but not others; intermittent Redis connectivity.

### Pitfall 4: Hardcoded Defaults Diverge from Env Var Defaults (LOW)
**What goes wrong:** If `_USE_CASE_DEFAULTS` in `resolve_use_case_config()` specifies `gemini-2.5-flash-lite` but the consumer's env var default is `gemini-2.5-flash`, the behavior depends on whether the env var is set.
**Why it happens:** Defaults defined in two places.
**How to avoid:** Keep `_USE_CASE_DEFAULTS` as the single source of truth for fallback models. Use the same model strings as the existing env var defaults.
**Warning signs:** Different default model selected depending on which code path runs.

## Code Examples

Verified patterns from existing code:

### Existing `get_default_sync()` (current implementation)
```python
# Source: shared/model_router/src/model_router/settings_store.py:45-101
def get_default_sync(use_case, redis_url=None, redis_client=None):
    if _cache_is_valid(use_case):
        return _defaults_cache[use_case]["value"]
    try:
        # ... Redis read ...
        if raw is None:
            _defaults_cache[use_case] = {"value": None, "_cached_at": time.time()}
            return None
        parsed = json.loads(_decode_redis_text(raw))
        _defaults_cache[use_case] = {"value": parsed, "_cached_at": time.time()}
        return parsed
    except Exception:
        logger.debug("Failed to read sync default...", exc_info=True)
        return None  # <-- NOT cached; next call retries Redis
```

### Consumer Pattern: Gatekeeper (current)
```python
# Source: AURA-CHAT/backend/llm_gatekeeper.py:138-164
redis_url = f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}"
_admin_default = get_default_sync("gatekeeper", redis_url=redis_url)
if _admin_default is not None:
    _admin_provider = _admin_default.get("provider", "")
    _admin_model = _admin_default.get("model", "")
    if _admin_model and _admin_provider == "vertex_ai":
        _gatekeeper_model = _admin_model
    elif _admin_model and _admin_provider == "openrouter":
        logger.info("Gatekeeper skipping OpenRouter default...")
```

### Consumer Pattern: Embeddings (current)
```python
# Source: AURA-CHAT/backend/utils/embeddings.py:56-77
redis_url = f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}"
self._embedding_default = get_default_sync("embeddings", redis_url=redis_url)
if self._embedding_default is not None:
    admin_model = self._embedding_default.get("model", "")
    if admin_model and admin_model != self.model_name:
        self.model_name = admin_model
```

### What `resolve_use_case_config()` replaces (both consumers above)
```python
# After Phase 14, each consumer becomes:
cfg = resolve_use_case_config("gatekeeper")
# cfg = {"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"}
# Always returns a value, never None
```

### Settings Router Endpoint (current)
```python
# Source: AURA-CHAT/server/routers/settings.py:186-204
@router.put("/defaults/{use_case}")
async def set_default(use_case, payload, store):
    if use_case not in ALLOWED_USE_CASES:  # <-- blocks gatekeeper, relationship_extraction
        raise HTTPException(status_code=400, detail=f"Unknown use case: {use_case}")
    await store.set_default(use_case, payload.provider, payload.model)
    return {"use_case": use_case, "provider": payload.provider, "model": payload.model}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Per-consumer config resolution | `resolve_use_case_config()` (Phase 14) | This phase | Eliminates 7+ duplicated patterns |
| 5-min cache for all entries | Sentinel: 30s error TTL, 5-min miss TTL (Phase 14) | This phase | Redis recovery within 30s |
| 4 use cases configurable | 6 use cases (Phase 14) | This phase | gatekeeper + relationship_extraction configurable |
| Bare `except: return None` | Logged warning + sentinel cache (Phase 14) | This phase | Observable Redis failures |

**Deprecated/outdated:**
- Per-consumer Redis URL construction: replaced by centralized `resolve_use_case_config()`
- Gatekeeper OpenRouter blanket skip (llm_gatekeeper.py:153-159): addressed in Phase 15, not Phase 14
- Module-level `LLM_ENTITY_EXTRACTION_MODEL` in `AURA-NOTES-MANAGER/api/config.py:62`: addressed in Phase 16

## Open Questions

1. **Should `resolve_use_case_config()` accept `redis_client` for injected testing?**
   - What we know: `get_default_sync()` already accepts `redis_client` parameter
   - What's unclear: Whether consumers will pass pre-built clients or always rely on URL
   - Recommendation: Accept both `redis_url` and `redis_client`, mirroring `get_default_sync()` signature

2. **Should error entries be cached at all, or just retry immediately?**
   - What we know: Current code does NOT cache errors (retries every call)
   - What's unclear: Whether rapid retries during Redis outage causes connection storm
   - Recommendation: Cache errors with 30s TTL to prevent connection storms; 30s is fast enough for admin recovery expectations

3. **Should `_USE_CASE_DEFAULTS` include all future use cases or just Phase 14's 6?**
   - What we know: Phase 15/16 will wire the same 6 use cases to consumers
   - What's unclear: Whether new use cases will be added in later milestones
   - Recommendation: Include all 6 use cases now; add new ones when requirements appear

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=8.0 + pytest-asyncio >=0.23 |
| Config file | `shared/model_router/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `python -m pytest shared/model_router/tests/test_settings_store.py -x` |
| Full suite command | `python -m pytest shared/model_router/tests/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | PUT `gatekeeper` returns 200 | unit | `python -m pytest AURA-CHAT/server/tests/test_settings_router.py::test_set_default_gatekeeper -x` | ❌ Wave 0 |
| API-02 | PUT `relationship_extraction` returns 200 (both routers) | unit | `python -m pytest AURA-CHAT/server/tests/test_settings_router.py::test_set_default_relationship_extraction -x` | ❌ Wave 0 |
| FB-01 | SettingsStore value authoritative over env vars | unit | `python -m pytest shared/model_router/tests/test_settings_store.py::test_resolve_store_overrides_env -x` | ❌ Wave 0 |
| FB-02 | Graceful degradation — log warning, fall back, never crash | unit | `python -m pytest shared/model_router/tests/test_settings_store.py::test_resolve_redis_down_falls_back -x` | ❌ Wave 0 |
| SC-3 | `resolve_use_case_config("gatekeeper")` returns `{provider, model}` | unit | `python -m pytest shared/model_router/tests/test_settings_store.py::test_resolve_settings_store_hit -x` | ❌ Wave 0 |
| SC-4 | Redis recovery within 30s (no zombie-None) | unit | `python -m pytest shared/model_router/tests/test_settings_store.py::test_zombie_none_cache_recovery -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest shared/model_router/tests/test_settings_store.py -x`
- **Per wave merge:** `python -m pytest shared/model_router/tests/ -x && python -m pytest AURA-CHAT/server/tests/test_settings_router.py -x`
- **Phase gate:** Both test suites green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `shared/model_router/tests/test_settings_store.py` — add tests for `resolve_use_case_config()` (settings-store hit, env-var fallback, hardcoded default, Redis-down)
- [ ] `shared/model_router/tests/test_settings_store.py` — add tests for zombie-None cache fix (sentinel TTL behavior, recovery timing)
- [ ] `AURA-CHAT/server/tests/test_settings_router.py` — add test for `gatekeeper` and `relationship_extraction` as valid use cases
- [ ] `AURA-NOTES-MANAGER` — add parallel settings router test if one doesn't exist (check `AURA-NOTES-MANAGER/api/tests/`)

## Sources

### Primary (HIGH confidence)
- `shared/model_router/src/model_router/settings_store.py` — SettingsStore implementation, `get_default_sync()` caching (lines 25-101), `_defaults_cache` module-level dict (line 27), `_DEFAULTS_CACHE_TTL = 300` (line 25)
- `shared/model_router/src/model_router/__init__.py` — Package exports (SettingsStore, get_default_sync, clear_defaults_cache)
- `AURA-CHAT/server/routers/settings.py:55` — `ALLOWED_USE_CASES = {"chat", "embeddings", "entity_extraction", "summarization"}`
- `AURA-NOTES-MANAGER/api/routers/settings.py:55` — Identical `ALLOWED_USE_CASES` definition
- `AURA-CHAT/backend/llm_gatekeeper.py:138-164` — Consumer pattern: manual Redis URL + `get_default_sync("gatekeeper")` + OpenRouter skip
- `AURA-CHAT/backend/utils/embeddings.py:56-77` — Consumer pattern: manual Redis URL + `get_default_sync("embeddings")` + model override
- `AURA-CHAT/backend/utils/config.py:228-231` — `REDIS_HOST` defaults to `localhost` (IPv6 risk)
- `AURA-NOTES-MANAGER/api/config.py:62-73,88` — Module-level env var constants, `REDIS_URL` defaults to `redis://127.0.0.1:6379/0`
- `shared/model_router/tests/test_settings_store.py` — Existing test patterns (FakeAsyncRedis, async tests)
- `shared/model_router/tests/conftest.py` — `FakeAsyncRedis` class with `advance_time()` for TTL simulation
- `AURA-CHAT/server/tests/test_settings_router.py` — Settings router test patterns (FakeAsyncRedis, dependency overrides)
- `shared/model_router/pyproject.toml` — `asyncio_mode = 'auto'`, `testpaths = ['tests']`
- `.planning/REQUIREMENTS.md` — API-01, API-02, FB-01, FB-02 definitions
- `.planning/ROADMAP.md` — Phase 14 scope and success criteria
- `.planning/research/SUMMARY.md` — Prior research findings (HIGH confidence)

### Secondary (MEDIUM confidence)
- Redis connection URL patterns — `localhost` vs `127.0.0.1` IPv4/IPv6 behavior (community knowledge, verified by source code)

### Tertiary (LOW confidence)
- None — all findings verified against source code

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — No new dependencies; all changes within existing shared package
- Architecture: HIGH — Pattern verified against 3 existing consumers and 2 settings routers
- Pitfalls: HIGH — All 4 pitfalls verified from source code; zombie-None confirmed in `get_default_sync()` lines 80-95
- Cache fix design: MEDIUM — Sentinel pattern is standard, but optimal error TTL (30s) is a tuning decision

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (30 days — stable foundation code, low churn risk)
