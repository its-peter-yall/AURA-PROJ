"""Shared pytest fixtures for model_router tests."""

import os

import pytest

from model_router.providers.base import BaseEmbeddingProvider


@pytest.fixture(scope='session', autouse=True)
def enable_test_mode() -> None:
    """Enable AURA test mode for the package test session."""
    os.environ['AURA_TEST_MODE'] = 'true'


@pytest.fixture
def monkeypatch_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Provide a dedicated monkeypatch fixture for env var tests."""
    return monkeypatch


class TestEmbeddingProvider(BaseEmbeddingProvider):
    """Concrete embedding provider used to test base-class behavior."""

    def __init__(self, vectors: list[list[float]]) -> None:
        self._vectors = vectors

    async def _embed_raw(self, texts: list[str]) -> list[list[float]]:
        return self._vectors[: len(texts)]


@pytest.fixture
def embedding_provider_factory():
    """Create a test embedding provider with predefined vectors."""

    def _factory(vectors: list[list[float]]) -> TestEmbeddingProvider:
        return TestEmbeddingProvider(vectors)

    return _factory
