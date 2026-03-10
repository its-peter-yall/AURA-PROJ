# test_model_cache.py
# Tests for Redis-backed model list caching with TTL handling.

# Verifies cache misses populate Redis, cache hits avoid redundant router calls,
# and forced or expired refreshes return fresh ModelInfo objects for admin model
# discovery endpoints shared by both AURA applications.

# @see: model_router/cache.py - Cache helpers under test
# @note: FakeAsyncRedis.advance_time() simulates TTL expiry without sleeping.

"""Tests for model list caching helpers."""

import pytest

from model_router import ModelCache, get_cached_models
from model_router.types import ModelInfo, ProviderType


class FakeRouter:
    """Simple router stub that records list_models() calls."""

    def __init__(self) -> None:
        self.call_count = 0
        self._responses = [
            [
                ModelInfo(
                    name="gemini-2.5-flash",
                    provider=ProviderType.VERTEX_AI,
                    display_name="Gemini 2.5 Flash",
                )
            ],
            [
                ModelInfo(
                    name="gemini-2.5-pro",
                    provider=ProviderType.VERTEX_AI,
                    display_name="Gemini 2.5 Pro",
                )
            ],
        ]

    async def list_models(self, provider: ProviderType | str) -> list[ModelInfo]:
        self.call_count += 1
        if self.call_count <= len(self._responses):
            return self._responses[self.call_count - 1]
        return self._responses[-1]


@pytest.mark.asyncio
async def test_cache_miss_calls_router(fake_redis) -> None:
    router = FakeRouter()

    models = await get_cached_models("vertex_ai", fake_redis, router)

    assert router.call_count == 1
    assert models[0].name == "gemini-2.5-flash"
    assert fake_redis.dump_value("aura:models:vertex_ai") is not None


@pytest.mark.asyncio
async def test_cache_hit_returns_cached(fake_redis) -> None:
    router = FakeRouter()

    first = await get_cached_models("vertex_ai", fake_redis, router)
    second = await get_cached_models("vertex_ai", fake_redis, router)

    assert router.call_count == 1
    assert second[0].name == first[0].name


@pytest.mark.asyncio
async def test_force_refresh_bypasses_cache(fake_redis) -> None:
    router = FakeRouter()

    await get_cached_models("vertex_ai", fake_redis, router)
    refreshed = await get_cached_models(
        "vertex_ai",
        fake_redis,
        router,
        force_refresh=True,
    )

    assert router.call_count == 2
    assert refreshed[0].name == "gemini-2.5-pro"


@pytest.mark.asyncio
async def test_cache_returns_model_info_objects(fake_redis) -> None:
    router = FakeRouter()

    await get_cached_models("vertex_ai", fake_redis, router)
    cached = await get_cached_models("vertex_ai", fake_redis, router)

    assert isinstance(cached[0], ModelInfo)
    assert cached[0].provider is ProviderType.VERTEX_AI


@pytest.mark.asyncio
async def test_empty_model_list(fake_redis) -> None:
    class EmptyRouter:
        async def list_models(self, provider: ProviderType | str) -> list[ModelInfo]:
            return []

    cache = ModelCache(fake_redis, EmptyRouter())

    assert await cache.get_models("vertex_ai") == []
    assert fake_redis.dump_value("aura:models:vertex_ai") == "[]"


@pytest.mark.asyncio
async def test_expired_cache_returns_fresh_results(fake_redis) -> None:
    router = FakeRouter()

    initial = await get_cached_models("vertex_ai", fake_redis, router, ttl_seconds=300)
    fake_redis.advance_time(301)
    refreshed = await get_cached_models(
        "vertex_ai", fake_redis, router, ttl_seconds=300
    )

    assert router.call_count == 2
    assert initial[0].name == "gemini-2.5-flash"
    assert refreshed[0].name == "gemini-2.5-pro"
