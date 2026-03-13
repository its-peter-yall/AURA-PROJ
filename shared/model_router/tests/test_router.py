# test_router.py
# Tests for ModelRouter delegation, routing, and singleton helpers.

# Covers auto-registration, provider resolution, generation/stream routing,
# and singleton behavior for the shared router. This update extends the suite
# with OpenRouter delegation assertions for slash-form model identifiers.

# @see: model_router/router.py - Routing logic under test
# @note: Test mode keeps provider calls deterministic and offline.

"""Tests for ModelRouter delegation, routing, and singleton helpers."""

import pytest

from model_router import ModelRouter, get_default_router, reset_default_router
from model_router.config import OpenRouterConfig, RouterConfig, VertexAIConfig
from model_router.errors import ModelRouterError, ModelUnavailableError
from model_router.providers.openrouter import OpenRouterProvider
from model_router.providers.vertex_ai import (
    VertexAIEmbeddingProvider,
    VertexAIProvider,
)
from model_router.types import GenerateRequest, ProviderType, UsageInfo


def make_config() -> RouterConfig:
    """Create a router config that auto-registers test-mode Vertex AI."""
    return RouterConfig(
        test_mode=True,
        vertex_ai=VertexAIConfig(project_id="test-project", region="global"),
        openrouter=OpenRouterConfig(api_key="test-key"),
    )


def make_manual_router() -> ModelRouter:
    """Create a router with providers registered explicitly."""
    router = ModelRouter(RouterConfig())
    provider_config = VertexAIConfig(project_id="test-project", region="global")
    router.register_provider(
        ProviderType.VERTEX_AI,
        VertexAIProvider(provider_config),
    )
    router.register_embedding_provider(
        VertexAIEmbeddingProvider(provider_config),
    )
    return router


@pytest.fixture(autouse=True)
def reset_router_singleton() -> None:
    """Reset the default router before and after each test."""
    reset_default_router()
    yield
    reset_default_router()


@pytest.mark.asyncio
async def test_router_generate_delegates_to_vertex() -> None:
    router = make_manual_router()
    request = GenerateRequest(model="gemini-2.0-flash", contents="hello")

    response = await router.generate(request)

    assert response.text == "Test-mode output."
    assert response.provider is ProviderType.VERTEX_AI


@pytest.mark.asyncio
async def test_router_generate_with_kwargs() -> None:
    router = ModelRouter(make_config())

    response = await router.generate(model="gemini-2.0-flash", contents="hi")

    assert response.model_used == "gemini-2.0-flash"
    assert response.text == "Test-mode output."


@pytest.mark.asyncio
async def test_router_generate_delegates_to_openrouter() -> None:
    router = ModelRouter(make_config())

    response = await router.generate(
        model="anthropic/claude-sonnet-4",
        contents="hello",
    )

    assert response.provider is ProviderType.OPENROUTER
    assert response.model_used == "anthropic/claude-sonnet-4"


@pytest.mark.asyncio
async def test_router_embed_returns_vectors() -> None:
    router = make_manual_router()

    vectors = await router.embed(texts=["hello", "world"])

    assert len(vectors) == 2
    assert len(vectors[0]) == 768
    assert len(vectors[1]) == 768


@pytest.mark.asyncio
async def test_router_embed_single_text() -> None:
    router = ModelRouter(make_config())

    vectors = await router.embed(text="hello")

    assert len(vectors) == 1
    assert len(vectors[0]) == 768


@pytest.mark.asyncio
async def test_router_resolve_vertex_default() -> None:
    router = ModelRouter(make_config())

    provider = await router._resolve_provider(
        GenerateRequest(model="gemini-2.0-flash", contents="hello")
    )

    assert isinstance(provider, VertexAIProvider)


@pytest.mark.asyncio
async def test_router_resolve_openrouter_slash() -> None:
    router = ModelRouter(make_config())

    provider = await router._resolve_provider(
        GenerateRequest(
            model="anthropic/claude_sonnet-4",
            contents="hello",
        )
    )

    assert isinstance(provider, OpenRouterProvider)


@pytest.mark.asyncio
async def test_router_resolve_models_prefix_to_vertex() -> None:
    router = ModelRouter(make_config())

    provider = await router._resolve_provider(
        GenerateRequest(
            model="models/gemini-2.5-pro",
            contents="hello",
        )
    )

    assert isinstance(provider, VertexAIProvider)


def test_router_openrouter_auto_registered_in_test_mode() -> None:
    router = ModelRouter(make_config())

    assert ProviderType.OPENROUTER in router._providers


@pytest.mark.asyncio
async def test_router_resolve_openrouter_succeeds() -> None:
    router = ModelRouter(make_config())

    provider = await router._resolve_provider(
        GenerateRequest(
            model="anthropic/claude_sonnet-4",
            contents="hello",
        )
    )

    assert isinstance(provider, OpenRouterProvider)


@pytest.mark.asyncio
async def test_router_resolve_explicit_provider() -> None:
    router = ModelRouter(make_config())

    provider = await router._resolve_provider(
        GenerateRequest(
            model="anthropic/claude_sonnet-4",
            contents="hello",
            provider="vertex_ai",
        )
    )

    assert isinstance(provider, VertexAIProvider)


@pytest.mark.asyncio
async def test_router_no_provider_raises() -> None:
    router = ModelRouter(RouterConfig())

    with pytest.raises(ModelUnavailableError):
        await router.generate(model="gemini-2.0-flash", contents="hello")


@pytest.mark.asyncio
async def test_router_no_embedding_provider_raises() -> None:
    router = ModelRouter(RouterConfig())

    with pytest.raises(ModelRouterError):
        await router.embed(texts=["hello"])


@pytest.mark.asyncio
async def test_router_embed_rejects_non_vertex_provider() -> None:
    router = ModelRouter(make_config())

    with pytest.raises(ModelRouterError):
        await router.embed(
            texts=["hello"],
            provider=ProviderType.OPENROUTER,
        )


def test_router_from_config_auto_registers() -> None:
    router = ModelRouter(make_config())

    assert isinstance(router._providers[ProviderType.VERTEX_AI], VertexAIProvider)
    assert isinstance(router._embedding_provider, VertexAIEmbeddingProvider)


def test_get_default_router_singleton() -> None:
    router_one = get_default_router()
    router_two = get_default_router()

    assert router_one is router_two


@pytest.mark.asyncio
async def test_router_stream_yields_chunks() -> None:
    router = ModelRouter(make_config())

    chunks = [
        chunk
        async for chunk in router.stream(
            model="gemini-2.0-flash",
            contents="hello",
        )
    ]

    assert len(chunks) == 1
    assert chunks[0].type == "content"
    assert chunks[0].text == "Test-mode stream output."


@pytest.mark.asyncio
async def test_router_stream_delegates_to_openrouter() -> None:
    router = ModelRouter(make_config())

    provider = await router._resolve_provider(
        GenerateRequest(
            model="anthropic/claude-sonnet-4",
            contents="hello",
        )
    )
    chunks = [
        chunk
        async for chunk in router.stream(
            model="anthropic/claude-sonnet-4",
            contents="hello",
        )
    ]

    assert isinstance(provider, OpenRouterProvider)
    assert len(chunks) == 1
    assert chunks[0].type == "content"
    assert chunks[0].text == "Test-mode stream output."


@pytest.mark.asyncio
async def test_router_stream_with_usage_returns_usage_info() -> None:
    """stream_with_usage() returns usage data via mutable container."""
    router = ModelRouter(make_config())
    usage_data: list[UsageInfo] = []

    chunks = [
        chunk
        async for chunk in router.stream_with_usage(
            model="gemini-2.0-flash",
            contents="hello world",  # ~2 tokens
            usage_out=usage_data,
        )
    ]

    assert len(chunks) == 1
    assert chunks[0].type == "content"
    # Usage should be populated after stream completes
    assert len(usage_data) == 1
    usage = usage_data[0]
    assert usage.input_tokens >= 1  # "hello world" ~ 2 tokens
    assert usage.output_tokens >= 1  # "Test-mode stream output." ~ 6 tokens
    assert usage.thinking_tokens == 0  # No thinking in test mode


@pytest.mark.asyncio
async def test_router_stream_with_usage_thinking_tokens() -> None:
    """stream_with_usage() tracks thinking tokens separately."""
    router = ModelRouter(make_config())
    usage_data: list[UsageInfo] = []

    # In test mode, the provider returns a single content chunk
    # but we can verify the structure works for real thinking streams
    chunks = [
        chunk
        async for chunk in router.stream_with_usage(
            model="gemini-2.0-flash",
            contents="test",
            usage_out=usage_data,
        )
    ]

    assert len(chunks) == 1
    assert len(usage_data) == 1
    # Verify UsageInfo has all fields
    usage = usage_data[0]
    assert hasattr(usage, "input_tokens")
    assert hasattr(usage, "output_tokens")
    assert hasattr(usage, "thinking_tokens")


@pytest.mark.asyncio
async def test_router_stream_with_usage_no_container() -> None:
    """stream_with_usage() works without usage_out container."""
    router = ModelRouter(make_config())

    chunks = [
        chunk
        async for chunk in router.stream_with_usage(
            model="gemini-2.0-flash",
            contents="hello",
        )
    ]

    assert len(chunks) == 1
    assert chunks[0].type == "content"


@pytest.mark.asyncio
async def test_stream_with_usage_records_once() -> None:
    """stream_with_usage() must record usage exactly once to tracker."""
    from unittest.mock import AsyncMock, MagicMock

    router = ModelRouter(make_config())
    mock_tracker = MagicMock()
    mock_tracker.record = AsyncMock()
    mock_calculator = MagicMock()
    mock_calculator.estimate = MagicMock(return_value=0.001)
    router.set_usage_tracking(mock_tracker, mock_calculator)

    usage_data: list[UsageInfo] = []
    chunks = [
        chunk
        async for chunk in router.stream_with_usage(
            model="gemini-2.0-flash",
            contents="hello",
            usage_out=usage_data,
        )
    ]

    assert len(chunks) == 1
    assert len(usage_data) == 1
    # Critical: record() must be called exactly once, not twice
    assert mock_tracker.record.await_count == 1


@pytest.mark.asyncio
async def test_stream_with_usage_no_instance_state() -> None:
    """stream_with_usage() must not set _stream_usage_info on router."""
    router = ModelRouter(make_config())

    _ = [
        chunk
        async for chunk in router.stream_with_usage(
            model="gemini-2.0-flash",
            contents="hello",
        )
    ]

    assert not hasattr(router, "_stream_usage_info")


@pytest.mark.asyncio
async def test_router_list_models_all_providers() -> None:
    """list_models() with no filter aggregates from all providers."""
    router = ModelRouter(make_config())

    models = await router.list_models()

    assert len(models) >= 10
    providers_seen = {model.provider for model in models}
    assert ProviderType.VERTEX_AI in providers_seen
    assert ProviderType.OPENROUTER in providers_seen


@pytest.mark.asyncio
async def test_router_list_models_single_provider() -> None:
    """list_models(provider=...) filters to a single provider."""
    router = ModelRouter(make_config())

    vertex_models = await router.list_models(provider=ProviderType.VERTEX_AI)
    openrouter_models = await router.list_models(provider=ProviderType.OPENROUTER)

    assert all(model.provider is ProviderType.VERTEX_AI for model in vertex_models)
    assert all(model.provider is ProviderType.OPENROUTER for model in openrouter_models)
    assert len(vertex_models) == 3
    assert len(openrouter_models) >= 5


@pytest.mark.asyncio
async def test_router_list_models_unregistered_provider_raises() -> None:
    """list_models() raises when a requested provider is not registered."""
    router = ModelRouter(RouterConfig())

    with pytest.raises(ModelUnavailableError):
        await router.list_models(provider=ProviderType.VERTEX_AI)


@pytest.mark.asyncio
async def test_router_health_check_all_providers() -> None:
    """health_check() returns a status entry for each provider."""
    router = ModelRouter(make_config())

    health = await router.health_check()

    assert health[ProviderType.VERTEX_AI] is True
    assert health[ProviderType.OPENROUTER] is True


@pytest.mark.asyncio
async def test_router_health_check_single_provider() -> None:
    """health_check(provider=...) scopes the result to one provider."""
    router = ModelRouter(make_config())

    health = await router.health_check(provider=ProviderType.OPENROUTER)

    assert health == {ProviderType.OPENROUTER: True}


@pytest.mark.asyncio
async def test_router_health_check_unregistered_returns_false() -> None:
    """health_check() returns False for unregistered providers."""
    router = ModelRouter(RouterConfig())

    health = await router.health_check(provider=ProviderType.VERTEX_AI)

    assert health == {ProviderType.VERTEX_AI: False}


@pytest.mark.asyncio
async def test_router_health_check_invalid_string_raises_model_unavailable() -> None:
    """health_check() should not leak raw provider coercion errors."""
    router = ModelRouter(make_config())

    with pytest.raises(ModelUnavailableError) as error_info:
        await router.health_check(provider="invalid-provider")

    assert error_info.value.provider == "invalid-provider"
    assert "invalid-provider" in str(error_info.value)
    assert isinstance(error_info.value.__cause__, ValueError)


def test_router_get_provider_returns_instance() -> None:
    """get_provider() returns registered provider instances."""
    router = ModelRouter(make_config())

    vertex = router.get_provider(ProviderType.VERTEX_AI)
    openrouter = router.get_provider(ProviderType.OPENROUTER)

    assert isinstance(vertex, VertexAIProvider)
    assert isinstance(openrouter, OpenRouterProvider)


def test_router_get_provider_unregistered_raises() -> None:
    """get_provider() raises when the provider is not registered."""
    router = ModelRouter(RouterConfig())

    with pytest.raises(ModelUnavailableError):
        router.get_provider(ProviderType.VERTEX_AI)


def test_router_get_provider_invalid_string_raises_model_unavailable() -> None:
    """get_provider() normalizes invalid provider strings to shared errors."""
    router = ModelRouter(make_config())

    with pytest.raises(ModelUnavailableError) as error_info:
        router.get_provider("invalid-provider")

    assert error_info.value.provider == "invalid-provider"
    assert "invalid-provider" in str(error_info.value)
    assert isinstance(error_info.value.__cause__, ValueError)


@pytest.mark.asyncio
async def test_router_list_models_invalid_string_raises_model_unavailable() -> None:
    """list_models() should not leak raw provider coercion errors."""
    router = ModelRouter(make_config())

    with pytest.raises(ModelUnavailableError) as error_info:
        await router.list_models(provider="invalid-provider")

    assert error_info.value.provider == "invalid-provider"
    assert "invalid-provider" in str(error_info.value)
    assert isinstance(error_info.value.__cause__, ValueError)


@pytest.mark.asyncio
async def test_router_openrouter_credit_balance_via_get_provider() -> None:
    """OpenRouter credit balance is accessible through router.get_provider()."""
    router = ModelRouter(make_config())

    provider = router.get_provider(ProviderType.OPENROUTER)

    assert isinstance(provider, OpenRouterProvider)
    credits = await provider.get_credit_balance()

    assert "usage" in credits
    assert "limit" in credits
    assert "is_free_tier" in credits
