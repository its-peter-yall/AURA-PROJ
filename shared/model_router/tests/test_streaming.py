# test_streaming.py
# Cross-provider streaming normalization tests for the shared router.

# Verifies that Vertex AI and OpenRouter streams both surface the same
# StreamChunk contract, while OpenRouter normalization skips empty deltas and
# choice-less chunks without leaking provider-specific payload details.

# @see: model_router/router.py - Router stream delegation
# @note: Test mode is enabled globally; direct provider tests stub live clients.

"""Tests for cross-provider streaming normalization."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from types import SimpleNamespace

import pytest

from model_router.config import OpenRouterConfig, RouterConfig, VertexAIConfig
from model_router.providers.openrouter import OpenRouterProvider
from model_router.providers.vertex_ai import VertexAIProvider
from model_router.router import ModelRouter
from model_router.types import GenerateRequest, StreamChunk


class FakeAsyncStream:
    """Simple async iterator for OpenRouter streaming tests."""

    def __init__(self, chunks: list[object]) -> None:
        self._chunks = chunks
        self._index = 0
        self.closed = False

    def __aiter__(self) -> AsyncIterator[object]:
        return self

    async def __anext__(self) -> object:
        if self._index >= len(self._chunks):
            raise StopAsyncIteration
        chunk = self._chunks[self._index]
        self._index += 1
        return chunk

    async def aclose(self) -> None:
        self.closed = True


class FakeOpenRouterCompletions:
    """Fake chat completions namespace returning a prepared async stream."""

    def __init__(self, stream: FakeAsyncStream) -> None:
        self._stream = stream

    async def create(self, **_: object) -> FakeAsyncStream:
        return self._stream


class FakeOpenRouterClient:
    """Fake OpenRouter client exposing chat.completions.create."""

    def __init__(self, stream: FakeAsyncStream) -> None:
        self.chat = SimpleNamespace(
            completions=FakeOpenRouterCompletions(stream),
        )


class FakeVertexModels:
    """Fake Vertex models namespace for sync streaming iteration."""

    def __init__(self, chunks: list[object]) -> None:
        self._chunks = chunks

    def generate_content_stream(self, **_: object) -> Iterator[object]:
        return iter(self._chunks)


class FakeVertexClient:
    """Fake Vertex client exposing models.generate_content_stream."""

    def __init__(self, chunks: list[object]) -> None:
        self.models = FakeVertexModels(chunks)


def make_test_router() -> ModelRouter:
    """Create a router with both providers registered in test mode."""
    return ModelRouter(
        RouterConfig(
            test_mode=True,
            vertex_ai=VertexAIConfig(
                project_id='test-project',
                region='global',
            ),
            openrouter=OpenRouterConfig(api_key='test-key'),
        )
    )


def make_openrouter_provider(chunks: list[object]) -> OpenRouterProvider:
    """Create an OpenRouter provider that streams fake live chunks."""
    provider = OpenRouterProvider(OpenRouterConfig(api_key='test-key'))
    provider._test_mode = False
    provider._client = FakeOpenRouterClient(FakeAsyncStream(chunks))
    return provider


def make_vertex_provider(chunks: list[object]) -> VertexAIProvider:
    """Create a Vertex provider that streams fake live chunks."""
    provider = VertexAIProvider(
        VertexAIConfig(project_id='test-project', region='global')
    )
    provider._test_mode = False
    provider._client = FakeVertexClient(chunks)
    return provider


def make_openrouter_chunk(
    *,
    content: object | None = None,
    reasoning_content: object | None = None,
    choices: list[object] | None = None,
) -> object:
    """Create a fake OpenRouter chunk with delta content fields."""
    if choices is None:
        delta = SimpleNamespace(
            content=content,
            reasoning_content=reasoning_content,
        )
        choices = [SimpleNamespace(delta=delta)]
    return SimpleNamespace(choices=choices)


def make_vertex_chunk(
    *,
    text: str,
    is_thought: bool = False,
) -> object:
    """Create a fake Vertex chunk mirroring google-genai content parts."""
    part = SimpleNamespace(
        text=text,
        thought=is_thought,
        thought_summary=None,
    )
    content = SimpleNamespace(parts=[part])
    candidate = SimpleNamespace(content=content)
    return SimpleNamespace(candidates=[candidate])


@pytest.mark.asyncio
async def test_vertex_stream_yields_streamchunk() -> None:
    provider = make_vertex_provider([make_vertex_chunk(text='hello')])
    request = GenerateRequest(model='gemini-2.0-flash', contents='hello')

    chunks = [chunk async for chunk in provider.stream(request)]

    assert len(chunks) == 1
    assert isinstance(chunks[0], StreamChunk)
    assert chunks[0].type == 'content'
    assert chunks[0].text == 'hello'


@pytest.mark.asyncio
async def test_vertex_thinking_chunk_yields_thinking_streamchunk() -> None:
    """Vertex thought chunks normalize to thinking StreamChunk items."""
    provider = make_vertex_provider(
        [make_vertex_chunk(text='reasoning step...', is_thought=True)]
    )
    request = GenerateRequest(model='gemini-2.0-flash', contents='hello')

    chunks = [chunk async for chunk in provider.stream(request)]

    assert len(chunks) == 1
    assert chunks[0] == StreamChunk(type='thinking', text='reasoning step...')


@pytest.mark.asyncio
async def test_vertex_thought_summary_yields_thinking_streamchunk() -> None:
    """Vertex thought-summary parts normalize to thinking chunks."""
    part = SimpleNamespace(
        text='summary of reasoning',
        thought=False,
        thought_summary='brief summary',
    )
    content = SimpleNamespace(parts=[part])
    candidate = SimpleNamespace(content=content)
    chunk_obj = SimpleNamespace(candidates=[candidate])

    provider = make_vertex_provider([chunk_obj])
    request = GenerateRequest(model='gemini-2.0-flash', contents='hello')

    chunks = [chunk async for chunk in provider.stream(request)]

    assert len(chunks) == 1
    assert chunks[0] == StreamChunk(
        type='thinking',
        text='summary of reasoning',
    )


@pytest.mark.asyncio
async def test_vertex_mixed_thinking_and_content_stream() -> None:
    """Vertex streams preserve thinking/content order in mixed responses."""
    provider = make_vertex_provider(
        [
            make_vertex_chunk(text='let me think...', is_thought=True),
            make_vertex_chunk(text='here is the answer'),
        ]
    )
    request = GenerateRequest(model='gemini-2.0-flash', contents='hello')

    chunks = [chunk async for chunk in provider.stream(request)]

    assert len(chunks) == 2
    assert chunks[0] == StreamChunk(type='thinking', text='let me think...')
    assert chunks[1] == StreamChunk(
        type='content',
        text='here is the answer',
    )


@pytest.mark.asyncio
async def test_openrouter_stream_yields_streamchunk() -> None:
    provider = make_openrouter_provider(
        [make_openrouter_chunk(content='hello')]
    )
    request = GenerateRequest(
        model='anthropic/claude-sonnet-4',
        contents='hello',
    )

    chunks = [chunk async for chunk in provider.stream(request)]

    assert len(chunks) == 1
    assert isinstance(chunks[0], StreamChunk)
    assert chunks[0].type == 'content'
    assert chunks[0].text == 'hello'


@pytest.mark.asyncio
async def test_openrouter_reasoning_content_yields_thinking_chunk() -> None:
    provider = make_openrouter_provider(
        [make_openrouter_chunk(reasoning_content='thinking...')]
    )
    request = GenerateRequest(
        model='deepseek/deepseek-r1',
        contents='hello',
    )

    chunks = [chunk async for chunk in provider.stream(request)]

    assert chunks == [StreamChunk(type='thinking', text='thinking...')]


@pytest.mark.asyncio
async def test_both_providers_yield_same_chunk_schema() -> None:
    vertex_provider = make_vertex_provider([make_vertex_chunk(text='vertex')])
    openrouter_provider = make_openrouter_provider(
        [make_openrouter_chunk(content='openrouter')]
    )
    vertex_request = GenerateRequest(model='gemini-2.0-flash', contents='hello')
    openrouter_request = GenerateRequest(
        model='anthropic/claude-sonnet-4',
        contents='hello',
    )

    vertex_chunk = [chunk async for chunk in vertex_provider.stream(vertex_request)][0]
    openrouter_chunk = [
        chunk async for chunk in openrouter_provider.stream(openrouter_request)
    ][0]

    assert set(vertex_chunk.model_dump().keys()) == {'type', 'text'}
    assert set(openrouter_chunk.model_dump().keys()) == {'type', 'text'}
    assert type(vertex_chunk) is type(openrouter_chunk)


@pytest.mark.asyncio
async def test_router_stream_vertex_content() -> None:
    router = make_test_router()

    chunks = [
        chunk
        async for chunk in router.stream(
            model='gemini-2.0-flash',
            contents='hello',
        )
    ]

    assert chunks == [StreamChunk(type='content', text='Test-mode stream output.')]


@pytest.mark.asyncio
async def test_router_stream_openrouter_content() -> None:
    router = make_test_router()

    chunks = [
        chunk
        async for chunk in router.stream(
            model='anthropic/claude-sonnet-4',
            contents='hello',
        )
    ]

    assert chunks == [StreamChunk(type='content', text='Test-mode stream output.')]


@pytest.mark.asyncio
async def test_empty_delta_content_skipped() -> None:
    provider = make_openrouter_provider(
        [
            make_openrouter_chunk(content=None),
            make_openrouter_chunk(content=''),
            make_openrouter_chunk(content='kept'),
        ]
    )
    request = GenerateRequest(
        model='anthropic/claude-sonnet-4',
        contents='hello',
    )

    chunks = [chunk async for chunk in provider.stream(request)]

    assert chunks == [StreamChunk(type='content', text='kept')]


@pytest.mark.asyncio
async def test_chunks_with_no_choices_skipped() -> None:
    provider = make_openrouter_provider(
        [
            make_openrouter_chunk(choices=[]),
            make_openrouter_chunk(content='kept'),
        ]
    )
    request = GenerateRequest(
        model='anthropic/claude-sonnet-4',
        contents='hello',
    )

    chunks = [chunk async for chunk in provider.stream(request)]

    assert chunks == [StreamChunk(type='content', text='kept')]
