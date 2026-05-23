"""
========================================================================
FILE: test_general_compute_provider.py
LOCATION: shared/model_router/tests/test_general_compute_provider.py
========================================================================

PURPOSE:
    Unit and integration tests for the General Compute provider.

ROLE IN PROJECT:
    Verifies that the General Compute provider behaves correctly in both test
    and live mode, and integrates with the main ModelRouter.

KEY COMPONENTS:
    - Test suites for generate, stream, list_models, health_check, and errors.
    - Helper mock classes for HTTP requests.
========================================================================
"""

from __future__ import annotations

from typing import Any, AsyncGenerator, Callable
import httpx
import pytest

from model_router import ModelRouter
from model_router.config import GeneralComputeConfig, RouterConfig, VertexAIConfig
from model_router.errors import (
    AuthenticationError,
    ModelRouterError,
    RateLimitError,
)
from model_router.types import GenerateRequest, GenerateResponse, ProviderType, StreamChunk

try:
    from model_router.providers.general_compute import (
        GeneralComputeProvider,
        _map_gc_error,
    )
except ImportError:
    GeneralComputeProvider = None
    _map_gc_error = None


class FakeAsyncClient:
    """Minimal async httpx client stub for General Compute tests."""

    def __init__(self, handler: Callable[..., httpx.Response], **_: object) -> None:
        self._handler = handler

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def post(self, url: str, headers: dict[str, str], json: dict[str, Any] = None) -> httpx.Response:
        return self._handler(url=url, headers=headers, json=json)


def make_config() -> GeneralComputeConfig:
    """Create a minimal config for General Compute."""
    return GeneralComputeConfig(api_key="test-key")


def make_router() -> ModelRouter:
    """Create a router configured to auto-register in test mode."""
    return ModelRouter(
        RouterConfig(
            test_mode=True,
            vertex_ai=VertexAIConfig(project_id="test-project", region="global"),
            general_compute=make_config(),
        )
    )


def make_http_status_error(
    status_code: int,
    url: str,
    message: str,
    *,
    retry_after: str | None = None,
) -> httpx.HTTPStatusError:
    """Create an HTTPStatusError with request/response metadata."""
    headers = {"Retry-After": retry_after} if retry_after is not None else None
    request = httpx.Request("POST", url)
    response = httpx.Response(status_code, request=request, headers=headers)
    return httpx.HTTPStatusError(message, request=request, response=response)


@pytest.mark.asyncio
async def test_generate_returns_correct_shape() -> None:
    provider = GeneralComputeProvider(make_config())
    request = GenerateRequest(
        model="minimax-m2.7",
        contents="hello",
    )

    response = await provider.generate(request)

    assert isinstance(response, GenerateResponse)
    assert response.text == "Test-mode output."
    assert response.provider is ProviderType.GENERAL_COMPUTE
    assert response.usage.input_tokens == 0
    assert response.usage.output_tokens == 0
    assert response.usage.thinking_tokens == 0


@pytest.mark.asyncio
async def test_generate_uses_request_model() -> None:
    provider = GeneralComputeProvider(make_config())
    request = GenerateRequest(
        model="deepseek-v3.2",
        contents="hello",
    )

    response = await provider.generate(request)

    assert response.model_used == "deepseek-v3.2"


@pytest.mark.asyncio
async def test_stream_yields_chunks() -> None:
    provider = GeneralComputeProvider(make_config())
    request = GenerateRequest(
        model="deepseek-v3.2",
        contents="hello",
    )

    chunks = [chunk async for chunk in provider.stream(request)]

    assert len(chunks) == 1
    assert chunks[0].type == "content"
    assert chunks[0].text == "Test-mode stream output."


@pytest.mark.asyncio
async def test_list_models_returns_curated_models() -> None:
    provider = GeneralComputeProvider(make_config())

    models = await provider.list_models()

    assert len(models) == 3
    names = {model.name for model in models}
    assert names == {"minimax-m2.7", "deepseek-v3.2", "deepseek-v3.1"}
    assert all(model.provider is ProviderType.GENERAL_COMPUTE for model in models)


@pytest.mark.asyncio
async def test_list_models_thinking_support() -> None:
    provider = GeneralComputeProvider(make_config())

    models = await provider.list_models()
    by_name = {model.name: model for model in models}

    assert by_name["deepseek-v3.2"].thinking_supported is True
    assert by_name["deepseek-v3.1"].thinking_supported is True
    assert by_name["minimax-m2.7"].thinking_supported is False


@pytest.mark.asyncio
async def test_health_check_passes() -> None:
    provider = GeneralComputeProvider(make_config())

    assert await provider.health_check() is True


@pytest.mark.asyncio
async def test_router_auto_registers_gc_in_test_mode() -> None:
    router = make_router()

    response = await router.generate(
        model="deepseek-v3.2",
        contents="hello",
        provider=ProviderType.GENERAL_COMPUTE,
    )

    assert ProviderType.GENERAL_COMPUTE in router._providers
    assert response.provider is ProviderType.GENERAL_COMPUTE


def test_public_exports_include_gc_symbols() -> None:
    from model_router import GeneralComputeConfig as ExportedConfig
    from model_router import GeneralComputeProvider as ExportedProvider

    assert ExportedConfig is GeneralComputeConfig
    assert ExportedProvider is GeneralComputeProvider


def test_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GENERALCOMPUTE_API_KEY", "env-key")
    monkeypatch.setenv("GENERALCOMPUTE_BASE_URL", "https://custom.api.generalcompute.com/v1")

    config = GeneralComputeConfig.from_env()

    assert config.api_key == "env-key"
    assert config.base_url == "https://custom.api.generalcompute.com/v1"


def test_auth_error_mapping() -> None:
    url = "https://api.generalcompute.com/v1/chat/completions"
    err = make_http_status_error(401, url, "Unauthorized")
    mapped = _map_gc_error(err, model="deepseek-v3.2")

    assert isinstance(mapped, AuthenticationError)
    assert mapped.provider == ProviderType.GENERAL_COMPUTE.value
    assert mapped.model == "deepseek-v3.2"
    assert mapped.original is err


def test_rate_limit_error_mapping() -> None:
    url = "https://api.generalcompute.com/v1/chat/completions"
    err = make_http_status_error(429, url, "Too Many Requests", retry_after="15.5")
    mapped = _map_gc_error(err, model="deepseek-v3.2")

    assert isinstance(mapped, RateLimitError)
    assert mapped.provider == ProviderType.GENERAL_COMPUTE.value
    assert mapped.model == "deepseek-v3.2"
    assert mapped.original is err
    assert mapped.retry_after == 15.5


def test_generic_error_mapping() -> None:
    err = ValueError("Something else")
    mapped = _map_gc_error(err, model="deepseek-v3.2")

    assert type(mapped) is ModelRouterError
    assert mapped.provider == ProviderType.GENERAL_COMPUTE.value
    assert mapped.model == "deepseek-v3.2"
    assert mapped.original is err
