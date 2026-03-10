"""Public package exports for the AURA model router."""

from model_router.errors import (
    AuthenticationError,
    ContentPolicyError,
    EmbeddingDimensionError,
    ModelRouterError,
    ModelUnavailableError,
    ProviderTimeoutError,
    RateLimitError,
)
from model_router.providers.base import BaseEmbeddingProvider, BaseProvider
from model_router.router import ModelRouter, get_default_router, reset_default_router
from model_router.types import (
    GenerateRequest,
    GenerateResponse,
    ModelInfo,
    ProviderType,
    StreamChunk,
    UsageInfo,
)

__all__ = [
    'AuthenticationError',
    'BaseEmbeddingProvider',
    'BaseProvider',
    'ContentPolicyError',
    'EmbeddingDimensionError',
    'GenerateRequest',
    'GenerateResponse',
    'get_default_router',
    'ModelInfo',
    'ModelRouter',
    'ModelRouterError',
    'ModelUnavailableError',
    'ProviderTimeoutError',
    'ProviderType',
    'RateLimitError',
    'reset_default_router',
    'StreamChunk',
    'UsageInfo',
]

__version__ = '0.1.0'
