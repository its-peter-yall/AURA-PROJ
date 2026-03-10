# key_manager.py
# Fernet-encrypted storage for provider API keys in Redis.

# Encrypts provider credentials at rest with an environment-supplied master key,
# exposes masked values for admin UIs, and delegates live validation to an
# injected async callback so tests stay offline and providers remain decoupled.

# @see: model_router/settings_store.py - Shared runtime settings storage
# @note: AURA_MASTER_KEY must be a valid Fernet key string.

"""Encrypted API key management for provider credentials."""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from typing import Any

from cryptography.fernet import Fernet

KEYS_HASH = "aura:model_router:api_keys"
_MISSING_MASTER_KEY_MESSAGE = (
    "AURA_MASTER_KEY environment variable is required for API key encryption"
)


class KeyManager:
    """Encrypt, decrypt, and validate provider API keys."""

    def __init__(self, redis_client: Any) -> None:
        """Create a key manager with an injected Redis client.

        Args:
            redis_client: Async Redis-compatible client with hash methods.

        Raises:
            ValueError: If AURA_MASTER_KEY is not configured.
        """
        self._redis = redis_client
        master_key = os.environ.get("AURA_MASTER_KEY")
        if not master_key:
            raise ValueError(_MISSING_MASTER_KEY_MESSAGE)
        self._fernet = Fernet(master_key.encode())

    def _mask_key(self, key: str) -> str:
        """Return a masked key for display in admin responses."""
        if len(key) < 8:
            return "***"
        return f"{key[:3]}...{key[-3:]}"

    async def store_key(self, provider: str, api_key: str) -> str:
        """Encrypt and store a provider API key.

        Args:
            provider: Provider identifier.
            api_key: Plaintext provider API key.

        Returns:
            Masked version of the stored key.
        """
        encrypted_key = self._fernet.encrypt(api_key.encode()).decode()
        await self._redis.hset(KEYS_HASH, provider, encrypted_key)
        return self._mask_key(api_key)

    async def get_key(self, provider: str) -> str | None:
        """Return the decrypted provider API key if present."""
        encrypted_key = await self._redis.hget(KEYS_HASH, provider)
        if encrypted_key is None:
            return None
        return self._fernet.decrypt(encrypted_key.encode()).decode()

    async def get_masked_key(self, provider: str) -> str | None:
        """Return a masked key string if a provider key exists."""
        api_key = await self.get_key(provider)
        if api_key is None:
            return None
        return self._mask_key(api_key)

    async def delete_key(self, provider: str) -> bool:
        """Delete a stored provider key.

        Returns:
            True if a key was removed, otherwise False.
        """
        return bool(await self._redis.hdel(KEYS_HASH, provider))

    async def validate_key(
        self,
        provider: str,
        health_check_fn: Callable[[str], Awaitable[bool]],
    ) -> bool:
        """Validate a stored key with a provider-specific callback.

        Args:
            provider: Provider identifier.
            health_check_fn: Async callback accepting the plaintext API key.

        Returns:
            Validation result, or False if no key is stored.
        """
        api_key = await self.get_key(provider)
        if api_key is None:
            return False
        return bool(await health_check_fn(api_key))
