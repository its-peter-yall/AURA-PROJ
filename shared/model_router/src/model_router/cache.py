# cache.py
# Redis-backed TTL cache for provider model listings.

# Caches router.list_models() responses in Redis so settings endpoints can
# serve model discovery quickly across both AURA applications while still
# allowing TTL expiry and explicit refreshes when providers change.

# @see: model_router/router.py - ModelRouter list_models integration
# @note: ModelInfo values are serialized with Pydantic JSON mode for enums.

"""TTL-based model list cache backed by Redis."""

from __future__ import annotations

import json
from typing import Any

from model_router.router import ModelRouter
from model_router.types import ModelInfo, ProviderType


MIN_TTL_SECONDS = 300
MAX_TTL_SECONDS = 3600
DEFAULT_TTL_SECONDS = 900


def _validate_ttl_seconds(ttl_seconds: int) -> int:
    """Validate model cache TTL bounds.

    Args:
        ttl_seconds: Cache TTL in seconds.

    Returns:
        The validated TTL value.

    Raises:
        ValueError: If the TTL is outside the supported range.
    """
    if not (MIN_TTL_SECONDS <= ttl_seconds <= MAX_TTL_SECONDS):
        raise ValueError(
            f"TTL must be between {MIN_TTL_SECONDS} and "
            f"{MAX_TTL_SECONDS} seconds, got {ttl_seconds}"
        )
    return ttl_seconds


def _provider_cache_value(provider: ProviderType | str) -> str:
    """Normalize provider identifiers for Redis cache keys."""
    if isinstance(provider, ProviderType):
        return provider.value
    return provider


async def get_cached_models(
    provider: ProviderType | str,
    redis_client: Any,
    router: ModelRouter,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    force_refresh: bool = False,
) -> list[ModelInfo]:
    """Return cached models for a provider or refresh them from the router."""
    ttl_seconds = _validate_ttl_seconds(ttl_seconds)
    provider_key = _provider_cache_value(provider)
    cache_key = f"aura:models:{provider_key}"

    if not force_refresh:
        cached_value = await redis_client.get(cache_key)
        if cached_value is not None:
            return [ModelInfo(**model_data) for model_data in json.loads(cached_value)]

    models = await router.list_models(provider)
    serialized_models = json.dumps([model.model_dump(mode="json") for model in models])
    await redis_client.setex(cache_key, ttl_seconds, serialized_models)
    return models


class ModelCache:
    """Small wrapper around get_cached_models for dependency injection."""

    def __init__(
        self,
        redis_client: Any,
        router: ModelRouter,
        default_ttl: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        """Store cache dependencies.

        Args:
            redis_client: Async Redis-compatible client with get/setex methods.
            router: Shared model router used on cache miss.
            default_ttl: Default cache TTL in seconds.
        """
        self._redis = redis_client
        self._router = router
        self._default_ttl = _validate_ttl_seconds(default_ttl)

    async def get_models(
        self,
        provider: ProviderType | str,
        force_refresh: bool = False,
    ) -> list[ModelInfo]:
        """Return cached provider models using the configured default TTL."""
        return await get_cached_models(
            provider,
            self._redis,
            self._router,
            ttl_seconds=self._default_ttl,
            force_refresh=force_refresh,
        )
