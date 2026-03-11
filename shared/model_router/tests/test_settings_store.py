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
