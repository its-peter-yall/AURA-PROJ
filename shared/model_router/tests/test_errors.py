"""Tests for the model router error hierarchy and embedding base class."""

import pytest

from model_router.errors import (
    AuthenticationError,
    ContentPolicyError,
    EmbeddingDimensionError,
    ModelRouterError,
    ModelUnavailableError,
    ProviderTimeoutError,
    RateLimitError,
)


def test_model_router_error_base() -> None:
    error = ModelRouterError(
        'boom',
        provider='vertex_ai',
        model='gemini-2.0-flash',
    )

    assert str(error) == 'boom'
    assert error.provider == 'vertex_ai'
    assert error.model == 'gemini-2.0-flash'
    assert error.original is None


def test_error_cause_chain() -> None:
    original = ValueError('x')
    error = ModelRouterError(
        'boom',
        provider='vertex_ai',
        model='gemini-2.0-flash',
        original=original,
    )

    assert error.original is original
    assert error.__cause__ is original


def test_error_no_original() -> None:
    error = ModelRouterError('boom', provider='vertex_ai', model='gemini')

    assert error.original is None
    assert error.__cause__ is None


@pytest.mark.parametrize(
    ('error_cls', 'kwargs'),
    [
        (AuthenticationError, {}),
        (RateLimitError, {}),
        (ContentPolicyError, {}),
        (ModelUnavailableError, {}),
        (ProviderTimeoutError, {}),
        (EmbeddingDimensionError, {'expected': 768, 'actual': 256}),
    ],
)
def test_all_subclasses_are_model_router_error(error_cls, kwargs) -> None:
    if error_cls is EmbeddingDimensionError:
        error = error_cls(**kwargs, provider='vertex_ai', model='embedding')
    else:
        error = error_cls(
            'boom',
            provider='vertex_ai',
            model='gemini-2.0-flash',
        )

    assert isinstance(error, ModelRouterError)


def test_catch_hierarchy() -> None:
    with pytest.raises(ModelRouterError):
        raise AuthenticationError(
            'denied',
            provider='vertex_ai',
            model='gemini-2.0-flash',
        )


def test_direct_subclasses() -> None:
    assert AuthenticationError.__bases__ == (ModelRouterError,)
    assert ContentPolicyError.__bases__ == (ModelRouterError,)
    assert ModelUnavailableError.__bases__ == (ModelRouterError,)
    assert ProviderTimeoutError.__bases__ == (ModelRouterError,)


def test_rate_limit_retry_after() -> None:
    error = RateLimitError(
        'slow down',
        provider='vertex_ai',
        model='gemini-2.0-flash',
        retry_after=30.0,
    )

    assert error.retry_after == 30.0


def test_rate_limit_default_retry_after() -> None:
    error = RateLimitError(
        'slow down',
        provider='vertex_ai',
        model='gemini-2.0-flash',
    )

    assert error.retry_after is None


def test_embedding_dimension_error() -> None:
    error = EmbeddingDimensionError(
        expected=768,
        actual=256,
        provider='vertex_ai',
        model='text-embedding-004',
    )

    assert '768' in str(error)
    assert '256' in str(error)


def test_embedding_dimension_error_attributes() -> None:
    error = EmbeddingDimensionError(expected=768, actual=256)

    assert error.expected == 768
    assert error.actual == 256


@pytest.mark.asyncio
async def test_base_embedding_provider_validates_dimensions(
    embedding_provider_factory,
) -> None:
    provider = embedding_provider_factory([[0.0] * 768])

    vectors = await provider.embed(['text'])

    assert len(vectors) == 1
    assert len(vectors[0]) == 768


@pytest.mark.asyncio
async def test_base_embedding_provider_rejects_wrong_dimensions(
    embedding_provider_factory,
) -> None:
    provider = embedding_provider_factory([[0.0] * 256])

    with pytest.raises(EmbeddingDimensionError):
        await provider.embed(['text'])


@pytest.mark.asyncio
async def test_base_embedding_provider_empty_input(
    embedding_provider_factory,
) -> None:
    provider = embedding_provider_factory([])

    vectors = await provider.embed([])

    assert vectors == []


@pytest.mark.asyncio
async def test_base_embedding_provider_embed_single(
    embedding_provider_factory,
) -> None:
    provider = embedding_provider_factory([[0.0] * 768])

    vector = await provider.embed_single('text')

    assert len(vector) == 768
