"""Tests for ModelRouter delegation, routing, and singleton helpers."""

import pytest

from model_router import ModelRouter, get_default_router, reset_default_router
from model_router.config import RouterConfig, VertexAIConfig
from model_router.errors import ModelRouterError, ModelUnavailableError
from model_router.providers.vertex_ai import (
    VertexAIEmbeddingProvider,
    VertexAIProvider,
)
from model_router.types import GenerateRequest, ProviderType


def make_config() -> RouterConfig:
    """Create a router config that auto-registers test-mode Vertex AI."""
    return RouterConfig(
        test_mode=True,
        vertex_ai=VertexAIConfig(project_id='test-project', region='global'),
    )


def make_manual_router() -> ModelRouter:
    """Create a router with providers registered explicitly."""
    router = ModelRouter(RouterConfig())
    provider_config = VertexAIConfig(project_id='test-project', region='global')
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
    request = GenerateRequest(model='gemini-2.0-flash', contents='hello')

    response = await router.generate(request)

    assert response.text == 'Test-mode output.'
    assert response.provider is ProviderType.VERTEX_AI


@pytest.mark.asyncio
async def test_router_generate_with_kwargs() -> None:
    router = ModelRouter(make_config())

    response = await router.generate(model='gemini-2.0-flash', contents='hi')

    assert response.model_used == 'gemini-2.0-flash'
    assert response.text == 'Test-mode output.'


@pytest.mark.asyncio
async def test_router_embed_returns_vectors() -> None:
    router = make_manual_router()

    vectors = await router.embed(texts=['hello', 'world'])

    assert len(vectors) == 2
    assert len(vectors[0]) == 768
    assert len(vectors[1]) == 768


@pytest.mark.asyncio
async def test_router_embed_single_text() -> None:
    router = ModelRouter(make_config())

    vectors = await router.embed(text='hello')

    assert len(vectors) == 1
    assert len(vectors[0]) == 768


def test_router_resolve_vertex_default() -> None:
    router = ModelRouter(make_config())

    provider = router._resolve_provider(
        GenerateRequest(model='gemini-2.0-flash', contents='hello')
    )

    assert isinstance(provider, VertexAIProvider)


def test_router_resolve_openrouter_slash() -> None:
    router = ModelRouter(make_config())

    with pytest.raises(ModelUnavailableError):
        router._resolve_provider(
            GenerateRequest(
                model='anthropic/claude-sonnet-4',
                contents='hello',
            )
        )


def test_router_resolve_explicit_provider() -> None:
    router = ModelRouter(make_config())

    provider = router._resolve_provider(
        GenerateRequest(
            model='anthropic/claude-sonnet-4',
            contents='hello',
            provider='vertex_ai',
        )
    )

    assert isinstance(provider, VertexAIProvider)


@pytest.mark.asyncio
async def test_router_no_provider_raises() -> None:
    router = ModelRouter(RouterConfig())

    with pytest.raises(ModelUnavailableError):
        await router.generate(model='gemini-2.0-flash', contents='hello')


@pytest.mark.asyncio
async def test_router_no_embedding_provider_raises() -> None:
    router = ModelRouter(RouterConfig())

    with pytest.raises(ModelRouterError):
        await router.embed(texts=['hello'])


@pytest.mark.asyncio
async def test_router_embed_rejects_non_vertex_provider() -> None:
    router = ModelRouter(make_config())

    with pytest.raises(ModelRouterError):
        await router.embed(
            texts=['hello'],
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
            model='gemini-2.0-flash',
            contents='hello',
        )
    ]

    assert len(chunks) == 1
    assert chunks[0].type == 'content'
    assert chunks[0].text == 'Test-mode stream output.'
