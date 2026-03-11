# test_cross_provider_integration.py
# Repo-root integration tests for shared router cross-provider behavior.

# Validates that the shared model_router package behaves consistently from the
# top-level import context used by both AURA apps, including compat-layer
# routing for slash-form OpenRouter model identifiers.

# @see: shared/model_router/src/model_router/router.py - Router entrypoint
# @note: Uses test mode so cross-app assertions stay offline and deterministic.

"""Repo-root cross-provider integration tests."""

from __future__ import annotations

import pytest

from model_router.compat import VertexCompatModel
from model_router.config import OpenRouterConfig, RouterConfig, VertexAIConfig
from model_router.router import ModelRouter, reset_default_router
from model_router.types import ProviderType, StreamChunk


def make_config() -> RouterConfig:
    """Create a test-mode router config with Vertex and OpenRouter enabled."""
    return RouterConfig(
        test_mode=True,
        vertex_ai=VertexAIConfig(project_id="test-project", region="global"),
        openrouter=OpenRouterConfig(api_key="test-key"),
    )


@pytest.fixture(autouse=True)
def reset_router_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep compat-layer router singleton state isolated between tests."""
    monkeypatch.setenv("AURA_TEST_MODE", "true")
    reset_default_router()
    yield
    reset_default_router()


@pytest.mark.asyncio
async def test_cross_app_vertex_generate() -> None:
    """Repo-root callers can generate through the Vertex provider."""
    router = ModelRouter(make_config())

    response = await router.generate(model="gemini-2.0-flash", contents="hello")

    assert response.provider is ProviderType.VERTEX_AI
    assert response.text == "Test-mode output."


@pytest.mark.asyncio
async def test_cross_app_openrouter_generate() -> None:
    """Repo-root callers can generate through the OpenRouter provider."""
    router = ModelRouter(make_config())

    response = await router.generate(
        model="anthropic/claude-sonnet-4",
        contents="hello",
    )

    assert response.provider is ProviderType.OPENROUTER
    assert response.text == "Test-mode output."


@pytest.mark.asyncio
async def test_cross_app_stream_contract_parity() -> None:
    """Both providers expose identical StreamChunk schema from repo root."""
    router = ModelRouter(make_config())

    vertex_chunks = [
        chunk
        async for chunk in router.stream(model="gemini-2.0-flash", contents="hello")
    ]
    openrouter_chunks = [
        chunk
        async for chunk in router.stream(
            model="anthropic/claude-sonnet-4",
            contents="hello",
        )
    ]

    assert all(isinstance(chunk, StreamChunk) for chunk in vertex_chunks)
    assert all(isinstance(chunk, StreamChunk) for chunk in openrouter_chunks)
    assert set(vertex_chunks[0].model_dump().keys()) == set(
        openrouter_chunks[0].model_dump().keys()
    )


@pytest.mark.asyncio
async def test_compat_layer_routes_openrouter_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """VertexCompatModel routes slash-form model IDs through OpenRouter."""
    monkeypatch.setenv("AURA_TEST_MODE", "true")
    model = VertexCompatModel("anthropic/claude-sonnet-4")

    response = await model.generate_content_async("hello")

    assert response.text == "Test-mode output."
