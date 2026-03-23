# test_settings_store.py
# Tests for Redis-backed default model settings storage.

# Verifies use-case defaults can be created, overwritten, and fetched through
# the shared SettingsStore abstraction without requiring a live Redis service.

# @see: model_router/settings_store.py - SettingsStore implementation
# @note: Tests rely on FakeAsyncRedis from tests/conftest.py.

"""Tests for the shared Redis-backed settings store."""

import pytest

from model_router import SettingsStore


@pytest.mark.asyncio
async def test_set_and_get_default(fake_redis) -> None:
    store = SettingsStore(fake_redis)

    await store.set_default("chat", "vertex_ai", "gemini-2.5-flash")

    assert await store.get_default("chat") == {
        "provider": "vertex_ai",
        "model": "gemini-2.5-flash",
    }


@pytest.mark.asyncio
async def test_get_default_missing(fake_redis) -> None:
    store = SettingsStore(fake_redis)

    assert await store.get_default("nonexistent") is None


@pytest.mark.asyncio
async def test_get_default_decodes_redis_bytes(fake_redis_bytes) -> None:
    store = SettingsStore(fake_redis_bytes)

    await store.set_default("chat", "vertex_ai", "gemini-2.5-flash")

    assert await store.get_default("chat") == {
        "provider": "vertex_ai",
        "model": "gemini-2.5-flash",
    }


@pytest.mark.asyncio
async def test_get_defaults_multiple(fake_redis) -> None:
    store = SettingsStore(fake_redis)

    await store.set_default("chat", "vertex_ai", "gemini-2.5-flash")
    await store.set_default("embeddings", "vertex_ai", "text-embedding-004")
    await store.set_default(
        "entity_extraction",
        "openrouter",
        "anthropic/claude-3.7-sonnet",
    )

    assert await store.get_defaults() == {
        "chat": {"provider": "vertex_ai", "model": "gemini-2.5-flash"},
        "embeddings": {"provider": "vertex_ai", "model": "text-embedding-004"},
        "entity_extraction": {
            "provider": "openrouter",
            "model": "anthropic/claude-3.7-sonnet",
        },
    }


@pytest.mark.asyncio
async def test_get_defaults_empty(fake_redis) -> None:
    store = SettingsStore(fake_redis)

    assert await store.get_defaults() == {}


@pytest.mark.asyncio
async def test_get_defaults_decodes_redis_bytes(fake_redis_bytes) -> None:
    store = SettingsStore(fake_redis_bytes)

    await store.set_default("chat", "vertex_ai", "gemini-2.5-flash")
    await store.set_default("embeddings", "vertex_ai", "text-embedding-004")

    assert await store.get_defaults() == {
        "chat": {"provider": "vertex_ai", "model": "gemini-2.5-flash"},
        "embeddings": {
            "provider": "vertex_ai",
            "model": "text-embedding-004",
        },
    }


@pytest.mark.asyncio
async def test_overwrite_default(fake_redis) -> None:
    store = SettingsStore(fake_redis)

    await store.set_default("chat", "vertex_ai", "gemini-2.0-flash")
    await store.set_default("chat", "openrouter", "google/gemini-2.5-flash")

    assert await store.get_default("chat") == {
        "provider": "openrouter",
        "model": "google/gemini-2.5-flash",
    }


# ============================================================================
# Sentinel cache fix tests (zombie-None problem)
# ============================================================================

from model_router.settings_store import (
    _SENTINEL_ERROR,
    _ERROR_CACHE_TTL,
    _DEFAULTS_CACHE_TTL,
    _defaults_cache,
    clear_defaults_cache,
)


class TestZombieNoneCache:
    """Tests for sentinel-based cache fix."""

    def setup_method(self) -> None:
        clear_defaults_cache()

    def test_sentinel_cached_on_error(self) -> None:
        """Redis error caches _SENTINEL_ERROR, not None."""
        clear_defaults_cache()
        from model_router.settings_store import get_default_sync

        result = get_default_sync("chat", redis_url="redis://192.0.2.1:6379/0")
        assert result is None
        assert "chat" in _defaults_cache
        assert _defaults_cache["chat"]["value"] is _SENTINEL_ERROR

    def test_sentinel_expires_after_error_ttl(self) -> None:
        """Sentinel entry expires after _ERROR_CACHE_TTL (30s)."""
        import time

        clear_defaults_cache()
        _defaults_cache["chat"] = {
            "value": _SENTINEL_ERROR,
            "_cached_at": time.time() - (_ERROR_CACHE_TTL + 1),
        }

        from model_router.settings_store import _cache_is_valid

        assert _cache_is_valid("chat") is False

    def test_sentinel_still_valid_within_error_ttl(self) -> None:
        """Sentinel entry is valid within _ERROR_CACHE_TTL."""
        import time

        clear_defaults_cache()
        _defaults_cache["chat"] = {
            "value": _SENTINEL_ERROR,
            "_cached_at": time.time() - 10,  # 10s ago, within 30s TTL
        }

        from model_router.settings_store import _cache_is_valid

        assert _cache_is_valid("chat") is True

    def test_normal_cache_uses_longer_ttl(self) -> None:
        """Normal (non-error) cached values use _DEFAULTS_CACHE_TTL (300s)."""
        import time

        clear_defaults_cache()
        _defaults_cache["chat"] = {
            "value": {"provider": "vertex_ai", "model": "gemini-2.5-flash"},
            "_cached_at": time.time() - 100,  # 100s ago, within 300s
        }

        from model_router.settings_store import _cache_is_valid

        assert _cache_is_valid("chat") is True
