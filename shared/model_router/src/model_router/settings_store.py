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
from typing import Any

SETTINGS_KEY = "aura:model_router:settings"


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
        return {use_case: json.loads(value) for use_case, value in raw_defaults.items()}

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
        return json.loads(raw_value)
