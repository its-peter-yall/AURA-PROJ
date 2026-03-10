"""Tests for the shared Vertex AI provider implementations."""

import pytest

from model_router.config import VertexAIConfig
from model_router.errors import (
    AuthenticationError,
    ContentPolicyError,
    ModelRouterError,
    ModelUnavailableError,
    ProviderTimeoutError,
    RateLimitError,
)
from model_router.providers.vertex_ai import (
    VertexAIEmbeddingProvider,
    VertexAIProvider,
    _map_vertex_error,
)
from model_router.types import GenerateRequest, GenerateResponse, ProviderType


class FakeVertexError(Exception):
    """Simple exception type used to exercise error mapping."""

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


def make_config() -> VertexAIConfig:
    """Create a minimal test config for Vertex AI providers."""
    return VertexAIConfig(project_id='test-project', region='global')


@pytest.mark.asyncio
async def test_generate_returns_correct_shape() -> None:
    provider = VertexAIProvider(make_config())
    request = GenerateRequest(model='gemini-2.0-flash', contents='hello')

    response = await provider.generate(request)

    assert isinstance(response, GenerateResponse)
    assert response.text == 'Test-mode output.'
    assert response.provider is ProviderType.VERTEX_AI
    assert response.usage.input_tokens == 0
    assert response.usage.output_tokens == 0
    assert response.usage.thinking_tokens == 0


@pytest.mark.asyncio
async def test_generate_uses_request_model() -> None:
    provider = VertexAIProvider(make_config())
    request = GenerateRequest(model='gemini-2.5-pro', contents='hello')

    response = await provider.generate(request)

    assert response.model_used == 'gemini-2.5-pro'


@pytest.mark.asyncio
async def test_stream_yields_chunks() -> None:
    provider = VertexAIProvider(make_config())
    request = GenerateRequest(model='gemini-2.0-flash', contents='hello')

    chunks = [chunk async for chunk in provider.stream(request)]

    assert len(chunks) == 1
    assert chunks[0].type == 'content'
    assert chunks[0].text == 'Test-mode stream output.'


@pytest.mark.asyncio
async def test_list_models_returns_gemini_models() -> None:
    provider = VertexAIProvider(make_config())

    models = await provider.list_models()

    assert [model.name for model in models] == [
        'gemini-2.0-flash',
        'gemini-2.5-flash',
        'gemini-2.5-pro',
    ]


@pytest.mark.asyncio
async def test_health_check_passes() -> None:
    provider = VertexAIProvider(make_config())

    assert await provider.health_check() is True


@pytest.mark.asyncio
async def test_embed_returns_768_dim_vectors() -> None:
    provider = VertexAIEmbeddingProvider(make_config())

    vectors = await provider.embed(['hello', 'world'])

    assert len(vectors) == 2
    assert len(vectors[0]) == 768
    assert len(vectors[1]) == 768


@pytest.mark.asyncio
async def test_embed_single_returns_single_vector() -> None:
    provider = VertexAIEmbeddingProvider(make_config())

    vector = await provider.embed_single('hello')

    assert len(vector) == 768


@pytest.mark.asyncio
async def test_embed_empty_returns_empty() -> None:
    provider = VertexAIEmbeddingProvider(make_config())

    vectors = await provider.embed([])

    assert vectors == []


def test_map_vertex_error_auth() -> None:
    original = FakeVertexError('403 permission_denied', code=403)

    mapped = _map_vertex_error(original, model='gemini-2.0-flash')

    assert isinstance(mapped, AuthenticationError)


def test_map_vertex_error_rate_limit() -> None:
    original = FakeVertexError('429 resource_exhausted', code=429)

    mapped = _map_vertex_error(original, model='gemini-2.0-flash')

    assert isinstance(mapped, RateLimitError)


def test_map_vertex_error_content_policy() -> None:
    original = FakeVertexError('400 blocked by safety settings', code=400)

    mapped = _map_vertex_error(original, model='gemini-2.0-flash')

    assert isinstance(mapped, ContentPolicyError)


def test_map_vertex_error_not_found() -> None:
    original = FakeVertexError('404 not_found', code=404)

    mapped = _map_vertex_error(original, model='gemini-2.0-flash')

    assert isinstance(mapped, ModelUnavailableError)


def test_map_vertex_error_timeout() -> None:
    original = FakeVertexError('deadline exceeded while waiting')

    mapped = _map_vertex_error(original, model='gemini-2.0-flash')

    assert isinstance(mapped, ProviderTimeoutError)


def test_map_vertex_error_generic() -> None:
    original = FakeVertexError('unexpected upstream failure')

    mapped = _map_vertex_error(original, model='gemini-2.0-flash')

    assert type(mapped) is ModelRouterError


def test_error_preserves_original_cause() -> None:
    original = FakeVertexError('403 permission_denied', code=403)

    mapped = _map_vertex_error(original, model='gemini-2.0-flash')

    assert mapped.original is original
    assert mapped.__cause__ is original
