"""
========================================================================
FILE: test_multi_model_config.py
LOCATION: shared/model_router/tests/test_multi_model_config.py
========================================================================

PURPOSE:
    Unit tests for multi-model chat configuration methods on SettingsStore.

ROLE IN PROJECT:
    Validates the SettingsStore multi-model extension that allows 1-5 models
    with a default_index, while maintaining backward compatibility with the
    legacy single-model format.
    - Tests get_chat_models_config() with legacy migration
    - Tests set_chat_models() validation and storage
    - Tests backward compatibility with get_default()

KEY COMPONENTS:
    - test_set_chat_models_single_model: Single model round-trip
    - test_set_chat_models_multiple_models: Multi-model with non-zero default
    - test_set_chat_models_empty_list_raises: Validation of empty input
    - test_set_chat_models_over_five_raises: Validation of max models
    - test_set_chat_models_invalid_default_index_raises: Index bounds check
    - test_set_chat_models_missing_keys_raises: Required key validation
    - test_get_chat_models_config_legacy_format_migration: Legacy→new conversion
    - test_get_chat_models_config_missing_returns_none: Missing key behavior
    - test_set_chat_models_backward_compat_get_default: get_default() compat

DEPENDENCIES:
    - External: pytest, pytest-asyncio
    - Internal: model_router.settings_store, conftest.py (fake_redis)

USAGE:
    python -m pytest shared/model_router/tests/test_multi_model_config.py -x
========================================================================
"""

import pytest

from model_router import SettingsStore


@pytest.mark.asyncio
async def test_set_chat_models_single_model(fake_redis) -> None:
    """Single model round-trip with default_index=0."""
    store = SettingsStore(fake_redis)

    await store.set_chat_models(
        [{"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"}],
        default_index=0,
    )

    config = await store.get_chat_models_config()
    assert config is not None
    assert len(config["models"]) == 1
    assert config["default_index"] == 0
    assert config["provider"] == "vertex_ai"
    assert config["model"] == "gemini-2.5-flash-lite"
    assert config["models"][0] == {
        "provider": "vertex_ai",
        "model": "gemini-2.5-flash-lite",
    }


@pytest.mark.asyncio
async def test_set_chat_models_multiple_models(fake_redis) -> None:
    """Three models with non-zero default_index."""
    store = SettingsStore(fake_redis)

    models = [
        {"provider": "vertex_ai", "model": "gemini-2.5-flash"},
        {"provider": "openrouter", "model": "openai/gpt-4o-mini"},
        {"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"},
    ]
    await store.set_chat_models(models, default_index=1)

    config = await store.get_chat_models_config()
    assert config is not None
    assert len(config["models"]) == 3
    assert config["default_index"] == 1
    assert config["provider"] == "openrouter"
    assert config["model"] == "openai/gpt-4o-mini"


@pytest.mark.asyncio
async def test_set_chat_models_empty_list_raises(fake_redis) -> None:
    """Empty models list raises ValueError."""
    store = SettingsStore(fake_redis)

    with pytest.raises(ValueError, match="At least one model must be configured"):
        await store.set_chat_models([], 0)


@pytest.mark.asyncio
async def test_set_chat_models_over_five_raises(fake_redis) -> None:
    """More than 5 models raises ValueError."""
    store = SettingsStore(fake_redis)

    six_models = [
        {"provider": "vertex_ai", "model": f"model-{i}"}
        for i in range(6)
    ]

    with pytest.raises(ValueError, match="Maximum 5 models allowed"):
        await store.set_chat_models(six_models, 0)


@pytest.mark.asyncio
async def test_set_chat_models_invalid_default_index_raises(fake_redis) -> None:
    """Out-of-range default_index raises ValueError."""
    store = SettingsStore(fake_redis)

    three_models = [
        {"provider": "vertex_ai", "model": "model-0"},
        {"provider": "vertex_ai", "model": "model-1"},
        {"provider": "vertex_ai", "model": "model-2"},
    ]

    with pytest.raises(ValueError, match="default_index out of range"):
        await store.set_chat_models(three_models, 5)


@pytest.mark.asyncio
async def test_set_chat_models_missing_keys_raises(fake_redis) -> None:
    """Model entry without 'provider' or 'model' raises ValueError."""
    store = SettingsStore(fake_redis)

    # Missing "provider"
    with pytest.raises(ValueError, match="Each model must have 'provider' and 'model' keys"):
        await store.set_chat_models(
            [{"model": "gemini-2.5-flash"}],
            default_index=0,
        )

    # Missing "model"
    with pytest.raises(ValueError, match="Each model must have 'provider' and 'model' keys"):
        await store.set_chat_models(
            [{"provider": "vertex_ai"}],
            default_index=0,
        )


@pytest.mark.asyncio
async def test_get_chat_models_config_legacy_format_migration(fake_redis) -> None:
    """Legacy single-model format is converted to multi-model on read."""
    store = SettingsStore(fake_redis)

    await store.set_default("chat", "vertex_ai", "gemini-2.5-flash")

    config = await store.get_chat_models_config()
    assert config is not None
    assert len(config["models"]) == 1
    assert config["default_index"] == 0
    assert config["provider"] == "vertex_ai"
    assert config["model"] == "gemini-2.5-flash"
    assert config["models"][0] == {
        "provider": "vertex_ai",
        "model": "gemini-2.5-flash",
    }


@pytest.mark.asyncio
async def test_get_chat_models_config_missing_returns_none(fake_redis) -> None:
    """Missing chat key returns None."""
    store = SettingsStore(fake_redis)

    config = await store.get_chat_models_config()
    assert config is None


@pytest.mark.asyncio
async def test_set_chat_models_backward_compat_get_default(fake_redis) -> None:
    """get_default() returns backward-compatible single-model view."""
    store = SettingsStore(fake_redis)

    await store.set_chat_models(
        [
            {"provider": "openrouter", "model": "openai/gpt-4o-mini"},
            {"provider": "vertex_ai", "model": "gemini-2.5-flash"},
        ],
        default_index=0,
    )

    default = await store.get_default("chat")
    assert default is not None
    assert default["provider"] == "openrouter"
    assert default["model"] == "openai/gpt-4o-mini"


@pytest.mark.asyncio
async def test_set_chat_models_does_not_break_get_defaults(fake_redis) -> None:
    """Setting multi-model chat config does not break get_defaults() for other use cases.

    Regression test: set_chat_models writes to the 'chat' key, but get_defaults()
    must still return all configured use cases including non-chat ones like
    'embeddings'. This ensures backward compatibility for systems that call
    get_defaults() to enumerate all settings.
    """
    store = SettingsStore(fake_redis)

    await store.set_chat_models(
        [
            {"provider": "openrouter", "model": "openai/gpt-4o-mini"},
            {"provider": "vertex_ai", "model": "gemini-2.5-flash"},
        ],
        default_index=0,
    )

    await store.set_default("embeddings", "vertex_ai", "text-embedding-004")

    defaults = await store.get_defaults()
    assert "chat" in defaults
    assert "embeddings" in defaults
    assert defaults["chat"]["provider"] == "openrouter"
    assert defaults["chat"]["model"] == "openai/gpt-4o-mini"
    assert defaults["embeddings"] == {"provider": "vertex_ai", "model": "text-embedding-004"}
