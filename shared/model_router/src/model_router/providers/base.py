"""Abstract provider contracts for generation and embedding providers."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator

from model_router.errors import EmbeddingDimensionError
from model_router.types import (
    GenerateRequest,
    GenerateResponse,
    ModelInfo,
    StreamChunk,
)

AURA_EMBEDDING_DIMENSIONS = 768


class BaseProvider(ABC):
    """Abstract base class for generation providers."""

    @abstractmethod
    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Generate a complete response for a request."""

    @abstractmethod
    async def stream(
        self,
        request: GenerateRequest,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream normalized response chunks for a request."""

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """List models available from this provider."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True when the provider is reachable."""


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def _embed_raw(self, texts: list[str]) -> list[list[float]]:
        """Return raw embedding vectors for the provided texts."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts and enforce the AURA vector dimension contract."""
        if not texts:
            return []

        vectors = await self._embed_raw(texts)
        for vector in vectors:
            if len(vector) != AURA_EMBEDDING_DIMENSIONS:
                raise EmbeddingDimensionError(
                    expected=AURA_EMBEDDING_DIMENSIONS,
                    actual=len(vector),
                )
        return vectors

    async def embed_single(self, text: str) -> list[float]:
        """Embed a single text and return the first vector."""
        return (await self.embed([text]))[0]
