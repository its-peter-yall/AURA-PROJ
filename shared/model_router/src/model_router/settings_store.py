# settings_store.py
# Redis-backed storage for admin-configurable default provider settings.

# Stores per-use-case provider/model defaults in a shared Redis hash so both
# AURA applications read the same runtime configuration without app restarts.
# The store is Redis-client-agnostic and only depends on injected async methods.

# @see: model_router/key_manager.py - Related runtime configuration storage
# @note: Values are JSON-serialized for cross-process compatibility.

"""Redis-backed settings store for admin-configurable LLM defaults."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

SETTINGS_KEY = "aura:model_router:settings"

_DEFAULTS_CACHE_TTL = 300  # 5 minutes — for key-miss entries
_ERROR_CACHE_TTL = 30  # 30 seconds — for error-sourced entries
_SENTINEL_ERROR = object()  # Marks "Redis was unreachable"

_defaults_cache: dict[str, dict] = {}


def _decode_redis_text(value: str | bytes) -> str:
    """Normalize Redis text responses to Python strings."""
    if isinstance(value, bytes):
        return value.decode()
    return value


def _cache_is_valid(use_case: str) -> bool:
    """Return True if the cached entry for use_case is still fresh."""
    entry = _defaults_cache.get(use_case)
    if entry is None:
        return False
    age = time.time() - entry["_cached_at"]
    if entry["value"] is _SENTINEL_ERROR:
        return age < _ERROR_CACHE_TTL
    return age < _DEFAULTS_CACHE_TTL


def get_default_sync(
    use_case: str,
    redis_url: str | None = None,
    redis_client: Any = None,
) -> dict[str, str] | None:
    """Synchronously read a provider/model default from Redis.

    Designed for sync call-sites (embedding services, entity extractors)
    that cannot await the async ``SettingsStore.get_default`` method.

    Args:
        use_case: Logical use case such as ``chat``, ``embeddings``, or
            ``entity_extraction``.
        redis_url: Redis connection URL.  Defaults to the ``REDIS_URL``
            environment variable.
        redis_client: Pre-created synchronous Redis client.  When provided
            ``redis_url`` is ignored.

    Returns:
        A dict ``{"provider": str, "model": str}`` when a default is
        configured, or ``None`` on any error or missing key.
    """
    if _cache_is_valid(use_case):
        entry = _defaults_cache[use_case]
        if entry["value"] is _SENTINEL_ERROR:
            return None  # Error cached — return None, caller will fall back
        return entry["value"]

    client_to_close = None
    try:
        client: Any = redis_client
        if client is None:
            import redis as _redis  # type: ignore[import-untyped]

            url = redis_url or os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
            client = _redis.Redis.from_url(url)
            client_to_close = client

        raw = client.hget(SETTINGS_KEY, use_case)
        if raw is None:
            logger.debug("No default configured for use_case=%s", use_case)
            _defaults_cache[use_case] = {"value": None, "_cached_at": time.time()}
            return None

        parsed = json.loads(_decode_redis_text(raw))
        _defaults_cache[use_case] = {"value": parsed, "_cached_at": time.time()}
        return parsed
    except Exception:
        logger.warning(
            "Redis unavailable for use_case=%s, falling back",
            use_case,
            exc_info=True,
        )
        _defaults_cache[use_case] = {
            "value": _SENTINEL_ERROR,
            "_cached_at": time.time(),
        }
        return None
    finally:
        if client_to_close is not None:
            try:
                client_to_close.close()
            except Exception:
                pass


def clear_defaults_cache() -> None:
    """Clear the in-memory defaults cache.  Useful for testing."""
    _defaults_cache.clear()


class SettingsStore:
    """Read and write default model settings from Redis."""

    def __init__(self, redis_client: Any) -> None:
        """Store the injected async Redis client.

        Args:
            redis_client: Async Redis-compatible client with hash methods.
        """
        self._redis = redis_client

    async def get_defaults(self) -> dict[str, dict[str, str]]:
        """Return all configured use-case defaults.

        Returns:
            Mapping of use case to provider/model pair.
        """
        raw_defaults = await self._redis.hgetall(SETTINGS_KEY)
        return {
            _decode_redis_text(use_case): json.loads(_decode_redis_text(value))
            for use_case, value in raw_defaults.items()
        }

    async def set_default(
        self,
        use_case: str,
        provider: str,
        model: str,
    ) -> None:
        """Persist a provider/model default for a use case.

        Args:
            use_case: Logical use case such as chat or embeddings.
            provider: Provider identifier.
            model: Model identifier.
        """
        payload = json.dumps({"provider": provider, "model": model})
        await self._redis.hset(SETTINGS_KEY, use_case, payload)

    async def get_default(self, use_case: str) -> dict[str, str] | None:
        """Return the configured default for a specific use case.

        Args:
            use_case: Logical use case such as chat or embeddings.

        Returns:
            Provider/model pair if configured, otherwise None.
        """
        raw_value = await self._redis.hget(SETTINGS_KEY, use_case)
        if raw_value is None:
            return None
        return json.loads(_decode_redis_text(raw_value))
