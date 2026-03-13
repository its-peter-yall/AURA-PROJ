---
phase: quick/18-implement-lazy-openrouter-registration-f
plan: 01
type: summary
subsystem: shared/model_router
tags: [openrouter, lazy-registration, key-manager, redis]
dependency_graph:
  requires: []
  provides: [shared/model_router/src/model_router/router.py]
  affects: [shared/model_router/tests/test_router.py]
tech_stack:
  added: []
  patterns: [lazy-initialization, async-registration, key-manager-integration]
key_files:
  created: []
  modified:
    - shared/model_router/src/model_router/router.py
    - shared/model_router/tests/test_router.py
decisions:
  - "Add optional key_manager parameter to ModelRouter.__init__() for lazy registration support"
  - "Make _resolve_provider() async to support async KeyManager.get_key() calls"
  - "Use config defaults (base_url, site_url, site_name) with KeyManager-provided API key"
  - "Preserve existing provider registration if already present (no duplicate registration)"
  - "Update all existing tests to await _resolve_provider() after async conversion"
metrics:
  duration: 22
  completed_date: "2026-03-13"
  tests_added: 8
  tests_total: 43
---

# Phase quick/18: Plan 01 - Lazy OpenRouter Registration Summary

## Objective

Enable lazy OpenRouter provider registration from Redis when slash-form model IDs are used but OpenRouter isn't pre-registered at startup.

## Implementation

### Task 1: Add Lazy OpenRouter Registration to ModelRouter

**Modified `shared/model_router/src/model_router/router.py`:**

1. **Added `key_manager` parameter**: Optional `KeyManager` parameter to `__init__()` stored as `self._key_manager`

2. **Created `_maybe_lazy_register_openrouter()`**: Async helper that:
   - Early returns if OpenRouter already registered
   - Early returns if no KeyManager available
   - Fetches key via `await self._key_manager.get_key("openrouter")`
   - Registers OpenRouterProvider with fetched key if present
   - Logs lazy registration for debugging

3. **Made `_resolve_provider()` async**: 
   - Calls lazy registration before raising "No provider registered" error
   - Re-checks providers dict after lazy registration attempt
   - Maintains backward compatibility with existing error handling

4. **Updated all callers**:
   - `generate()` - now awaits `_resolve_provider()`
   - `stream()` - now awaits `_resolve_provider()`
   - `stream_with_usage()` - now awaits `_resolve_provider()`

5. **Added imports**:
   - `OpenRouterConfig` from `model_router.config`
   - `KeyManager` in TYPE_CHECKING block

### Task 2: Add Comprehensive Test Coverage

**Modified `shared/model_router/tests/test_router.py`:**

Added 8 new tests covering lazy registration scenarios:

1. **`test_lazy_openrouter_registration_with_key`** - Lazy registration succeeds when key exists
2. **`test_lazy_registration_no_key_raises_error`** - Graceful failure when no key available
3. **`test_lazy_registration_caches_provider`** - Provider cached after first registration
4. **`test_lazy_registration_skips_if_already_registered`** - No-op if provider already present
5. **`test_lazy_registration_no_key_manager`** - Handles missing KeyManager gracefully
6. **`test_generate_triggers_lazy_registration`** - End-to-end via generate() method
7. **`test_stream_triggers_lazy_registration`** - End-to-end via stream() method
8. **`test_lazy_registration_uses_correct_config`** - Config values preserved (base_url, site_url, site_name)

**Updated 5 existing tests** to await `_resolve_provider()` after async conversion.

## Key Design Decisions

1. **Backward Compatibility**: `key_manager` is optional - existing code continues to work
2. **Transparent Operation**: Lazy registration happens automatically without API changes
3. **Config Preservation**: Uses existing config for base_url, site_url, site_name; only overrides api_key
4. **Error Handling**: Falls back to original "No provider registered" error if lazy registration fails
5. **Caching**: Provider registered once and reused for subsequent requests

## Flow to Fix (Now Working)

```
1. UI stores key in Redis via KeyManager ✓
2. Router initializes without OpenRouter (no env var) ✓
3. Request comes with slash-form model ID (e.g., "anthropic/claude-sonnet-4") ✓
4. Router routes to ProviderType.OPENROUTER ✓
5. OpenRouter not in _providers dict → triggers lazy registration ✓
6. KeyManager fetches key from Redis → auto-registers provider ✓
7. Request continues successfully ✓
```

## Test Results

```
43 tests passed (35 existing + 8 new)
All lazy registration tests: PASSED
No regressions in existing tests: CONFIRMED
```

## Files Modified

| File | Changes |
|------|---------|
| `shared/model_router/src/model_router/router.py` | +85 lines, added lazy registration logic |
| `shared/model_router/tests/test_router.py` | +254 lines, added 8 new tests, updated 5 existing |

## Verification

- [x] ModelRouter accepts KeyManager for lazy registration
- [x] Slash-form model IDs work without OPENROUTER_API_KEY env var
- [x] Keys stored via KeyManager are fetched and used
- [x] Proper error handling when no key available (ModelUnavailableError)
- [x] All 43 tests pass (35 existing + 8 new)
- [x] No breaking changes to existing API

## Commits

- `54fee75`: feat(quick/18-01): add lazy OpenRouter registration to ModelRouter
- `f610b91`: test(quick/18-01): add comprehensive lazy OpenRouter registration tests

## Notes

The implementation follows the existing provider registration patterns and integrates cleanly with the KeyManager for encrypted API key storage. This enables users to configure OpenRouter API keys through the UI settings without requiring environment variable configuration at router initialization.
