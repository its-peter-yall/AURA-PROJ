# test_key_manager.py
# Tests for encrypted provider API key storage and masking.

# Covers Fernet-backed key encryption, retrieval, masking, deletion, and
# validation hooks so provider credentials can be managed without plaintext
# storage in Redis or live provider credentials during unit tests.

# @see: model_router/key_manager.py - KeyManager implementation
# @note: All tests use FakeAsyncRedis and generated Fernet keys.

"""Tests for encrypted provider API key management."""

import pytest

from model_router import KeyManager


@pytest.mark.asyncio
async def test_store_and_retrieve_key(fake_redis, master_key: str) -> None:
    manager = KeyManager(fake_redis)

    await manager.store_key("openrouter", "sk-ant-api03-longkey")

    assert await manager.get_key("openrouter") == "sk-ant-api03-longkey"


@pytest.mark.asyncio
async def test_store_returns_masked(fake_redis, master_key: str) -> None:
    manager = KeyManager(fake_redis)

    masked = await manager.store_key("openrouter", "sk-ant-api03-longkey")

    assert masked == "sk-...key"


@pytest.mark.asyncio
async def test_get_masked_key(fake_redis, master_key: str) -> None:
    manager = KeyManager(fake_redis)
    await manager.store_key("openrouter", "sk-ant-api03-longkey")

    assert await manager.get_masked_key("openrouter") == "sk-...key"


def test_mask_short_key(fake_redis, master_key: str) -> None:
    manager = KeyManager(fake_redis)

    assert manager._mask_key("abc1234") == "***"


def test_mask_long_key(fake_redis, master_key: str) -> None:
    manager = KeyManager(fake_redis)

    assert manager._mask_key("sk-ant-api03-longkey") == "sk-...key"


@pytest.mark.asyncio
async def test_get_key_missing(fake_redis, master_key: str) -> None:
    manager = KeyManager(fake_redis)

    assert await manager.get_key("vertex_ai") is None


@pytest.mark.asyncio
async def test_get_key_decodes_redis_bytes(
    fake_redis_bytes,
    master_key: str,
) -> None:
    manager = KeyManager(fake_redis_bytes)

    await manager.store_key("openrouter", "sk-ant-api03-longkey")

    assert await manager.get_key("openrouter") == "sk-ant-api03-longkey"


@pytest.mark.asyncio
async def test_delete_key(fake_redis, master_key: str) -> None:
    manager = KeyManager(fake_redis)
    await manager.store_key("openrouter", "sk-ant-api03-longkey")

    assert await manager.delete_key("openrouter") is True
    assert await manager.get_key("openrouter") is None


@pytest.mark.asyncio
async def test_delete_key_missing(fake_redis, master_key: str) -> None:
    manager = KeyManager(fake_redis)

    assert await manager.delete_key("openrouter") is False


@pytest.mark.asyncio
async def test_validate_key_calls_health_check(fake_redis, master_key: str) -> None:
    manager = KeyManager(fake_redis)
    await manager.store_key("openrouter", "sk-ant-api03-longkey")
    observed_key: list[str] = []

    async def health_check(api_key: str) -> bool:
        observed_key.append(api_key)
        return api_key.startswith("sk-")

    assert await manager.validate_key("openrouter", health_check) is True
    assert observed_key == ["sk-ant-api03-longkey"]


@pytest.mark.asyncio
async def test_validate_key_missing_returns_false(
    fake_redis,
    master_key: str,
) -> None:
    manager = KeyManager(fake_redis)

    async def health_check(_: str) -> bool:
        return True

    assert await manager.validate_key("openrouter", health_check) is False


def test_missing_master_key_raises(
    fake_redis,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AURA_MASTER_KEY", raising=False)

    with pytest.raises(ValueError, match="AURA_MASTER_KEY environment variable"):
        KeyManager(fake_redis)


@pytest.mark.asyncio
async def test_stored_value_is_encrypted(fake_redis, master_key: str) -> None:
    manager = KeyManager(fake_redis)

    await manager.store_key("openrouter", "sk-ant-api03-longkey")

    stored_value = fake_redis.dump_hash("aura:model_router:api_keys")["openrouter"]
    assert stored_value != "sk-ant-api03-longkey"
