# test_openrouter_provider.py
# Tests for the shared OpenRouter provider and its package wiring.

# Covers the provider's deterministic test-mode behavior, error mapping,
# router auto-registration, and public exports. The suite avoids requiring
# the openai SDK by patching a fake module for error-mapping tests.

# @see: model_router/providers/openrouter.py - OpenRouter provider implementation
# @note: These tests rely on AURA_TEST_MODE being enabled by tests/conftest.py.

"""Tests for the shared OpenRouter provider implementation."""

import sys
import types
from unittest.mock import patch

import pytest

from model_router import ModelRouter
from model_router.config import OpenRouterConfig, RouterConfig, VertexAIConfig
from model_router.errors import (
    AuthenticationError,
    ContentPolicyError,
    ModelRouterError,
    ModelUnavailableError,
    ProviderTimeoutError,
    RateLimitError,
)
from model_router.types import GenerateRequest, GenerateResponse, ProviderType

try:
    from model_router.providers.openrouter import (
        OpenRouterProvider,
        _map_openrouter_error,
    )
except ImportError:
    OpenRouterProvider = None
    _map_openrouter_error = None


class FakeOpenAIError(Exception):
    """Base fake error used to mimic the openai SDK exception hierarchy."""

    def __init__(
        self,
        message: str,
        response: object | None = None,
        body: object | None = None,
    ) -> None:
        super().__init__(message)
        self.response = response
        self.body = body


def make_config() -> OpenRouterConfig:
    """Create a minimal config for test-mode OpenRouter provider checks."""
    return OpenRouterConfig(api_key='test-key')


def make_router() -> ModelRouter:
    """Create a router configured to auto-register providers in test mode."""
    return ModelRouter(
        RouterConfig(
            test_mode=True,
            vertex_ai=VertexAIConfig(project_id='test-project', region='global'),
            openrouter=make_config(),
        )
    )


def install_fake_openai_module() -> types.ModuleType:
    """Create a fake openai module exposing the exception classes we need."""
    fake_module = types.ModuleType('openai')

    class FakeAuthenticationError(FakeOpenAIError):
        pass

    class FakeRateLimitError(FakeOpenAIError):
        pass

    class FakeNotFoundError(FakeOpenAIError):
        pass

    class FakeBadRequestError(FakeOpenAIError):
        pass

    class FakeAPITimeoutError(FakeOpenAIError):
        pass

    fake_module.AuthenticationError = FakeAuthenticationError
    fake_module.RateLimitError = FakeRateLimitError
    fake_module.NotFoundError = FakeNotFoundError
    fake_module.BadRequestError = FakeBadRequestError
    fake_module.APITimeoutError = FakeAPITimeoutError
    return fake_module


@pytest.mark.asyncio
async def test_generate_returns_correct_shape() -> None:
    provider = OpenRouterProvider(make_config())
    request = GenerateRequest(
        model='anthropic/claude-sonnet-4',
        contents='hello',
    )

    response = await provider.generate(request)

    assert isinstance(response, GenerateResponse)
    assert response.text == 'Test-mode output.'
    assert response.provider is ProviderType.OPENROUTER
    assert response.usage.input_tokens == 0
    assert response.usage.output_tokens == 0
    assert response.usage.thinking_tokens == 0


@pytest.mark.asyncio
async def test_generate_uses_request_model() -> None:
    provider = OpenRouterProvider(make_config())
    request = GenerateRequest(
        model='google/gemini-2.5-flash',
        contents='hello',
    )

    response = await provider.generate(request)

    assert response.model_used == 'google/gemini-2.5-flash'


@pytest.mark.asyncio
async def test_stream_yields_chunks() -> None:
    provider = OpenRouterProvider(make_config())
    request = GenerateRequest(
        model='deepseek/deepseek-r1',
        contents='hello',
    )

    chunks = [chunk async for chunk in provider.stream(request)]

    assert len(chunks) == 1
    assert chunks[0].type == 'content'
    assert chunks[0].text == 'Test-mode stream output.'


@pytest.mark.asyncio
async def test_list_models_returns_curated_models() -> None:
    provider = OpenRouterProvider(make_config())

    models = await provider.list_models()

    model_names = {model.name for model in models}
    assert any(name.startswith('anthropic/') for name in model_names)
    assert any(name.startswith('google/') for name in model_names)
    assert any(name.startswith('openai/') for name in model_names)
    assert any(name.startswith('deepseek/') for name in model_names)
    assert any(name.startswith('meta-llama/') for name in model_names)
    assert any(name.startswith('mistralai/') for name in model_names)
    assert all(model.provider is ProviderType.OPENROUTER for model in models)


@pytest.mark.asyncio
async def test_health_check_passes() -> None:
    provider = OpenRouterProvider(make_config())

    assert await provider.health_check() is True


@pytest.mark.asyncio
async def test_get_credit_balance_returns_dict() -> None:
    provider = OpenRouterProvider(make_config())

    credits = await provider.get_credit_balance()

    assert credits['usage'] == 0.0
    assert credits['limit'] == 100.0
    assert 'is_free_tier' in credits


@pytest.mark.asyncio
async def test_router_auto_registers_openrouter_in_test_mode() -> None:
    router = make_router()

    response = await router.generate(
        model='anthropic/claude-sonnet-4',
        contents='hello',
    )

    assert ProviderType.OPENROUTER in router._providers
    assert response.provider is ProviderType.OPENROUTER


def test_public_exports_include_openrouter_symbols() -> None:
    from model_router import OpenRouterConfig as ExportedOpenRouterConfig
    from model_router import OpenRouterProvider as ExportedOpenRouterProvider

    assert ExportedOpenRouterConfig is OpenRouterConfig
    assert ExportedOpenRouterProvider is OpenRouterProvider


def test_map_openrouter_error_auth() -> None:
    fake_openai = install_fake_openai_module()
    original = fake_openai.AuthenticationError('invalid api key')

    with patch.dict(sys.modules, {'openai': fake_openai}):
        mapped = _map_openrouter_error(original, model='anthropic/claude-sonnet-4')

    assert isinstance(mapped, AuthenticationError)


def test_map_openrouter_error_rate_limit() -> None:
    fake_openai = install_fake_openai_module()
    original = fake_openai.RateLimitError('too many requests')

    with patch.dict(sys.modules, {'openai': fake_openai}):
        mapped = _map_openrouter_error(original, model='anthropic/claude-sonnet-4')

    assert isinstance(mapped, RateLimitError)


def test_map_openrouter_error_not_found() -> None:
    fake_openai = install_fake_openai_module()
    original = fake_openai.NotFoundError('model not found')

    with patch.dict(sys.modules, {'openai': fake_openai}):
        mapped = _map_openrouter_error(original, model='anthropic/claude-sonnet-4')

    assert isinstance(mapped, ModelUnavailableError)


def test_map_openrouter_error_content_policy() -> None:
    fake_openai = install_fake_openai_module()
    original = fake_openai.BadRequestError('blocked by safety content filter')

    with patch.dict(sys.modules, {'openai': fake_openai}):
        mapped = _map_openrouter_error(original, model='anthropic/claude-sonnet-4')

    assert isinstance(mapped, ContentPolicyError)


def test_map_openrouter_error_timeout() -> None:
    fake_openai = install_fake_openai_module()
    original = fake_openai.APITimeoutError('request timed out')

    with patch.dict(sys.modules, {'openai': fake_openai}):
        mapped = _map_openrouter_error(original, model='anthropic/claude-sonnet-4')

    assert isinstance(mapped, ProviderTimeoutError)


def test_map_openrouter_error_generic() -> None:
    original = RuntimeError('unexpected upstream failure')

    mapped = _map_openrouter_error(original, model='anthropic/claude-sonnet-4')

    assert type(mapped) is ModelRouterError


def test_error_preserves_original_cause() -> None:
    fake_openai = install_fake_openai_module()
    original = fake_openai.AuthenticationError('invalid api key')

    with patch.dict(sys.modules, {'openai': fake_openai}):
        mapped = _map_openrouter_error(original, model='anthropic/claude-sonnet-4')

    assert mapped.original is original
    assert mapped.__cause__ is original
