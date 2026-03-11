"""Shared pytest fixtures for model_router tests."""

# conftest.py
# Shared pytest fixtures and fake Redis helpers for model_router tests.

# Provides deterministic test-mode environment setup, an offline async Redis
# double for settings/key/cache coverage, and reusable embedding helpers.
# These fixtures keep unit tests fast and independent from external services.

# @see: tests/test_settings_store.py - Redis-backed settings store coverage
# @note: FakeAsyncRedis simulates TTL expiry via advance_time() for cache tests.

import os
import time
from typing import Any

import pytest
from cryptography.fernet import Fernet

from model_router.providers.base import BaseEmbeddingProvider


@pytest.fixture(scope="session", autouse=True)
def enable_test_mode() -> None:
    """Enable AURA test mode for the package test session."""
    os.environ["AURA_TEST_MODE"] = "true"


class FakeAsyncRedis:
    """In-memory async Redis double used by unit tests."""

    def __init__(self, decode_responses: bool = True) -> None:
        self._decode_responses = decode_responses
        self._hashes: dict[str, dict[str, str]] = {}
        self._values: dict[str, str] = {}
        self._expirations: dict[str, float] = {}
        self._time_offset = 0.0
        self._sorted_sets: dict[str, dict[str, float]] = {}

    def _format_value(self, value: str | None) -> str | bytes | None:
        """Return string or bytes based on the configured response mode."""
        if value is None or self._decode_responses:
            return value
        return value.encode()

    def _format_hash(
        self,
        bucket: dict[str, str],
    ) -> dict[str | bytes, str | bytes]:
        """Return hash contents using the configured response mode."""
        if self._decode_responses:
            return dict(bucket)
        return {key.encode(): value.encode() for key, value in bucket.items()}

    def _now(self) -> float:
        """Return the fake clock timestamp."""
        return time.monotonic() + self._time_offset

    def _purge_if_expired(self, key: str) -> None:
        """Remove expired string keys before reads."""
        expires_at = self._expirations.get(key)
        if expires_at is None:
            return
        if self._now() >= expires_at:
            self._values.pop(key, None)
            self._expirations.pop(key, None)

    def advance_time(self, seconds: float) -> None:
        """Advance the fake clock to simulate TTL expiry."""
        self._time_offset += seconds

    async def hset(self, name: str, key: str, value: str) -> int:
        """Store a hash field value."""
        bucket = self._hashes.setdefault(name, {})
        is_new = key not in bucket
        bucket[key] = value
        return 1 if is_new else 0

    async def hget(self, name: str, key: str) -> str | bytes | None:
        """Return a hash field value if present."""
        return self._format_value(self._hashes.get(name, {}).get(key))

    async def hgetall(self, name: str) -> dict[str | bytes, str | bytes]:
        """Return all fields for a hash."""
        return self._format_hash(self._hashes.get(name, {}))

    async def hdel(self, name: str, key: str) -> int:
        """Delete a hash field and report whether it existed."""
        bucket = self._hashes.get(name, {})
        if key not in bucket:
            return 0
        del bucket[key]
        return 1

    async def get(self, key: str) -> str | bytes | None:
        """Return a string value if present and unexpired."""
        self._purge_if_expired(key)
        return self._format_value(self._values.get(key))

    async def setex(self, key: str, ttl_seconds: int, value: str) -> bool:
        """Store a string value with TTL semantics."""
        self._values[key] = value
        self._expirations[key] = self._now() + ttl_seconds
        return True

    async def set(self, key: str, value: str) -> bool:
        """Store a string value without expiry."""
        self._values[key] = value
        self._expirations.pop(key, None)
        return True

    def dump_hash(self, name: str) -> dict[str, str]:
        """Expose hash contents for assertions in tests."""
        return dict(self._hashes.get(name, {}))

    def dump_value(self, key: str) -> str | None:
        """Expose string values for assertions in tests."""
        self._purge_if_expired(key)
        return self._values.get(key)

    # ---- Sorted set methods (for UsageTracker tests) ----

    async def zadd(
        self,
        name: str,
        mapping: dict[str, float],
    ) -> int:
        """Add members to a sorted set with scores."""
        zset = self._sorted_sets.setdefault(name, {})
        added = 0
        for member, score in mapping.items():
            if member not in zset:
                added += 1
            zset[member] = score
        return added

    async def zrangebyscore(
        self,
        name: str,
        min: float | str = "-inf",  # noqa: A002
        max: float | str = "+inf",  # noqa: A002
    ) -> list[str | bytes]:
        """Return members in a sorted set within the score range."""
        zset = self._sorted_sets.get(name, {})
        min_val = float("-inf") if min == "-inf" else float(min)
        max_val = float("inf") if max == "+inf" else float(max)
        results = [
            member
            for member, score in sorted(zset.items(), key=lambda x: x[1])
            if min_val <= score <= max_val
        ]
        if not self._decode_responses:
            return [r.encode() if isinstance(r, str) else r for r in results]
        return results

    async def zcard(self, name: str) -> int:
        """Return the number of members in a sorted set."""
        return len(self._sorted_sets.get(name, {}))


@pytest.fixture
def monkeypatch_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Provide a dedicated monkeypatch fixture for env var tests."""
    return monkeypatch


@pytest.fixture
def fake_redis() -> FakeAsyncRedis:
    """Return an in-memory fake async Redis client."""
    return FakeAsyncRedis()


@pytest.fixture
def fake_redis_bytes() -> FakeAsyncRedis:
    """Return a fake Redis client that responds with bytes."""
    return FakeAsyncRedis(decode_responses=False)


@pytest.fixture
def master_key(monkeypatch: pytest.MonkeyPatch) -> str:
    """Set a valid Fernet master key for key manager tests."""
    generated_key = Fernet.generate_key().decode()
    monkeypatch.setenv("AURA_MASTER_KEY", generated_key)
    return generated_key


class TestEmbeddingProvider(BaseEmbeddingProvider):
    """Concrete embedding provider used to test base-class behavior."""

    def __init__(self, vectors: list[list[float]]) -> None:
        self._vectors = vectors

    async def _embed_raw(self, texts: list[str]) -> list[list[float]]:
        return self._vectors[: len(texts)]


@pytest.fixture
def embedding_provider_factory():
    """Create a test embedding provider with predefined vectors."""

    def _factory(vectors: list[list[float]]) -> TestEmbeddingProvider:
        return TestEmbeddingProvider(vectors)

    return _factory


__all__ = ["FakeAsyncRedis"]
