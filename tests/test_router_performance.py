# test_router_performance.py
# Router overhead benchmarks for shared model_router request delegation.

# Measures average time for direct provider calls versus router-mediated calls
# in deterministic test mode, ensuring the abstraction layer remains below the
# roadmap overhead target for generate, stream, and provider resolution paths.

# @see: shared/model_router/src/model_router/router.py - Routing overhead target
# @note: Uses perf_counter_ns() averages instead of wall-clock assertions.

"""Performance tests for router abstraction overhead."""

from __future__ import annotations

from time import perf_counter_ns

import pytest

from model_router.config import OpenRouterConfig, RouterConfig, VertexAIConfig
from model_router.router import ModelRouter
from model_router.types import GenerateRequest, ProviderType


ITERATIONS = 200
RESOLUTION_ITERATIONS = 1000


def make_config() -> RouterConfig:
    """Create a test-mode router config with both providers registered."""
    return RouterConfig(
        test_mode=True,
        vertex_ai=VertexAIConfig(project_id="test-project", region="global"),
        openrouter=OpenRouterConfig(api_key="test-key"),
    )


@pytest.fixture(autouse=True)
def enable_test_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force offline provider test mode for repo-root benchmarks."""
    monkeypatch.setenv("AURA_TEST_MODE", "true")


@pytest.mark.asyncio
async def test_router_generate_overhead_under_10ms() -> None:
    """Router generate overhead stays below the 10ms target."""
    router = ModelRouter(make_config())
    provider = router._providers[ProviderType.VERTEX_AI]
    request = GenerateRequest(model="gemini-2.0-flash", contents="hello")

    direct_avg_ns = await _measure_generate_average_ns(provider, request)
    router_avg_ns = await _measure_router_generate_average_ns(router, request)
    overhead_ms = (router_avg_ns - direct_avg_ns) / 1_000_000

    assert overhead_ms < 10.0


@pytest.mark.asyncio
async def test_router_stream_overhead_under_10ms() -> None:
    """Router stream overhead stays below the 10ms target."""
    router = ModelRouter(make_config())
    provider = router._providers[ProviderType.VERTEX_AI]
    request = GenerateRequest(model="gemini-2.0-flash", contents="hello")

    direct_avg_ns = await _measure_stream_average_ns(provider, request)
    router_avg_ns = await _measure_router_stream_average_ns(router, request)
    overhead_ms = (router_avg_ns - direct_avg_ns) / 1_000_000

    assert overhead_ms < 10.0


def test_provider_resolution_overhead_under_1ms() -> None:
    """Provider resolution remains comfortably sub-millisecond."""
    router = ModelRouter(make_config())
    request = GenerateRequest(model="gemini-2.0-flash", contents="hello")

    start_ns = perf_counter_ns()
    for _ in range(RESOLUTION_ITERATIONS):
        router._resolve_provider(request)
    avg_ns = (perf_counter_ns() - start_ns) / RESOLUTION_ITERATIONS
    overhead_ms = avg_ns / 1_000_000

    assert overhead_ms < 1.0


async def _measure_generate_average_ns(
    provider: object,
    request: GenerateRequest,
) -> float:
    """Measure average direct provider generate() duration."""
    start_ns = perf_counter_ns()
    for _ in range(ITERATIONS):
        await provider.generate(request)
    return (perf_counter_ns() - start_ns) / ITERATIONS


async def _measure_router_generate_average_ns(
    router: ModelRouter,
    request: GenerateRequest,
) -> float:
    """Measure average router generate() duration."""
    start_ns = perf_counter_ns()
    for _ in range(ITERATIONS):
        await router.generate(request=request)
    return (perf_counter_ns() - start_ns) / ITERATIONS


async def _measure_stream_average_ns(
    provider: object,
    request: GenerateRequest,
) -> float:
    """Measure average direct provider stream() duration."""
    start_ns = perf_counter_ns()
    for _ in range(ITERATIONS):
        async for _chunk in provider.stream(request):
            pass
    return (perf_counter_ns() - start_ns) / ITERATIONS


async def _measure_router_stream_average_ns(
    router: ModelRouter,
    request: GenerateRequest,
) -> float:
    """Measure average router stream() duration."""
    start_ns = perf_counter_ns()
    for _ in range(ITERATIONS):
        async for _chunk in router.stream(request=request):
            pass
    return (perf_counter_ns() - start_ns) / ITERATIONS
