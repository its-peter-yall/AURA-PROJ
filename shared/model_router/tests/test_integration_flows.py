# test_integration_flows.py
# Cross-provider integration tests for provider switching and usage flows.

# Exercises multi-concern scenarios that combine router delegation,
# streaming contract parity, thinking chunk normalization, and usage
# tracking across provider switches in a single session.

# @see: model_router/router.py - Shared routing and usage tracking logic
# @note: Uses offline fake providers and FakeAsyncRedis for deterministic tests.

"""Integration tests for cross-provider router flows."""

from __future__ import annotations

import json

import pytest

from model_router.cost_calculator import CostCalculator
from model_router.config import OpenRouterConfig, RouterConfig, VertexAIConfig
from model_router.router import ModelRouter
from model_router.types import GenerateRequest, ProviderType, StreamChunk
from model_router.usage_tracker import USAGE_KEY, USAGE_SESSION_PREFIX, UsageTracker

from .conftest import FakeAsyncRedis
from .test_streaming import (
    make_openrouter_chunk,
    make_openrouter_provider,
    make_vertex_chunk,
    make_vertex_provider,
)


def make_config() -> RouterConfig:
    """Create a test-mode router config with both providers enabled."""
    return RouterConfig(
        test_mode=True,
        vertex_ai=VertexAIConfig(project_id="test-project", region="global"),
        openrouter=OpenRouterConfig(api_key="test-key"),
    )


@pytest.mark.asyncio
async def test_mid_session_provider_switch_generate() -> None:
    """Switching providers mid-session preserves the response contract."""
    router = ModelRouter(make_config())

    vertex_response = await router.generate(
        model="gemini-2.0-flash",
        contents="hello",
        metadata={"session_id": "sess-1"},
    )
    openrouter_response = await router.generate(
        model="anthropic/claude-sonnet-4",
        contents="follow up",
        metadata={"session_id": "sess-1"},
    )

    assert vertex_response.provider is ProviderType.VERTEX_AI
    assert openrouter_response.provider is ProviderType.OPENROUTER
    assert set(vertex_response.model_dump().keys()) == set(
        openrouter_response.model_dump().keys()
    )


@pytest.mark.asyncio
async def test_mid_session_provider_switch_stream() -> None:
    """Both providers yield the same StreamChunk schema mid-session."""
    router = ModelRouter(make_config())

    vertex_chunks = [
        chunk
        async for chunk in router.stream(
            model="gemini-2.0-flash",
            contents="hello",
            metadata={"session_id": "sess-1"},
        )
    ]
    openrouter_chunks = [
        chunk
        async for chunk in router.stream(
            model="anthropic/claude-sonnet-4",
            contents="follow up",
            metadata={"session_id": "sess-1"},
        )
    ]

    assert vertex_chunks
    assert openrouter_chunks
    assert all(isinstance(chunk, StreamChunk) for chunk in vertex_chunks)
    assert all(isinstance(chunk, StreamChunk) for chunk in openrouter_chunks)
    assert set(vertex_chunks[0].model_dump().keys()) == set(
        openrouter_chunks[0].model_dump().keys()
    )


@pytest.mark.asyncio
async def test_thinking_mode_parity_across_providers() -> None:
    """Identical thinking config yields thinking then content chunks."""
    vertex_provider = make_vertex_provider(
        [
            make_vertex_chunk(text="thinking...", is_thought=True),
            make_vertex_chunk(text="answer"),
        ]
    )
    openrouter_provider = make_openrouter_provider(
        [
            make_openrouter_chunk(reasoning_content="thinking..."),
            make_openrouter_chunk(content="answer"),
        ]
    )
    vertex_request = GenerateRequest(
        model="gemini-2.0-flash",
        contents="hello",
        thinking_config={"thinking_budget": 2048},
    )
    openrouter_request = GenerateRequest(
        model="anthropic/claude-sonnet-4",
        contents="hello",
        thinking_config={"thinking_budget": 2048},
    )

    vertex_chunks = [chunk async for chunk in vertex_provider.stream(vertex_request)]
    openrouter_chunks = [
        chunk async for chunk in openrouter_provider.stream(openrouter_request)
    ]

    assert vertex_chunks[0].type == "thinking"
    assert openrouter_chunks[0].type == "thinking"
    assert vertex_chunks[1].type == "content"
    assert openrouter_chunks[1].type == "content"
    assert type(vertex_chunks[0]) is type(openrouter_chunks[0])


@pytest.mark.asyncio
async def test_usage_tracking_across_provider_switch() -> None:
    """Usage tracking records both provider calls for one session."""
    fake_redis = FakeAsyncRedis()
    tracker = UsageTracker(fake_redis)
    calculator = CostCalculator()
    router = ModelRouter(make_config())
    router.set_usage_tracking(tracker, calculator)

    await router.generate(
        model="gemini-2.0-flash",
        contents="hello",
        metadata={"session_id": "sess-usage", "user_id": "user-1"},
    )
    await router.generate(
        model="anthropic/claude-sonnet-4",
        contents="follow up",
        metadata={"session_id": "sess-usage", "user_id": "user-1"},
    )

    session_key = f"{USAGE_SESSION_PREFIX}sess-usage"
    assert await fake_redis.zcard(USAGE_KEY) == 2
    assert await fake_redis.zcard(session_key) == 2

    payloads = [
        json.loads(payload) for payload in fake_redis._sorted_sets[USAGE_KEY].keys()
    ]
    providers_seen = {payload["provider"] for payload in payloads}
    assert providers_seen == {"vertex_ai", "openrouter"}


@pytest.mark.asyncio
async def test_usage_tracking_failure_does_not_break_generate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Telemetry failures are swallowed so generate() still succeeds."""
    fake_redis = FakeAsyncRedis()
    tracker = UsageTracker(fake_redis)
    calculator = CostCalculator()
    router = ModelRouter(make_config())
    router.set_usage_tracking(tracker, calculator)

    async def raising_record(**kwargs: object) -> None:
        del kwargs
        raise RuntimeError("boom")

    monkeypatch.setattr(tracker, "record", raising_record)

    response = await router.generate(
        model="gemini-2.0-flash",
        contents="hello",
        metadata={"session_id": "sess-fail"},
    )

    assert response.text == "Test-mode output."
    assert response.provider is ProviderType.VERTEX_AI
