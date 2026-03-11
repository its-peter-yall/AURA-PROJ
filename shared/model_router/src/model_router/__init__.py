# __init__.py
# Public exports for the shared AURA model router package.

# Re-exports the shared contracts, provider types, config models, and router
# entry points so callers can import the package from the repo root without
# needing to know the internal module layout.

# @see: model_router/router.py - Router runtime and singleton helpers
# @note: Provider implementations keep optional SDK imports lazy at runtime.

"""Public package exports for the AURA model router."""

from model_router.compat import VertexCompatModel
from model_router.config import OpenRouterConfig
from model_router.cache import ModelCache, get_cached_models
from model_router.cost_calculator import CostCalculator
from model_router.errors import (
    AuthenticationError,
    ContentPolicyError,
    EmbeddingDimensionError,
    ModelRouterError,
    ModelUnavailableError,
    ProviderTimeoutError,
    RateLimitError,
)
from model_router.key_manager import KeyManager
from model_router.providers.base import BaseEmbeddingProvider, BaseProvider
from model_router.providers.openrouter import OpenRouterProvider
from model_router.router import ModelRouter, get_default_router, reset_default_router
from model_router.settings_store import SettingsStore
from model_router.types import (
    GenerateRequest,
    GenerateResponse,
    ModelInfo,
    ProviderType,
    StreamChunk,
    UsageInfo,
    UsageRecord,
)
from model_router.usage_tracker import UsageTracker

__all__ = [
    "AuthenticationError",
    "BaseEmbeddingProvider",
    "BaseProvider",
    "CostCalculator",
    "get_cached_models",
    "ContentPolicyError",
    "EmbeddingDimensionError",
    "GenerateRequest",
    "GenerateResponse",
    "get_default_router",
    "KeyManager",
    "ModelInfo",
    "ModelCache",
    "ModelRouter",
    "ModelRouterError",
    "ModelUnavailableError",
    "OpenRouterConfig",
    "OpenRouterProvider",
    "ProviderTimeoutError",
    "ProviderType",
    "RateLimitError",
    "reset_default_router",
    "SettingsStore",
    "StreamChunk",
    "UsageInfo",
    "UsageRecord",
    "UsageTracker",
    "VertexCompatModel",
]

__version__ = "0.1.0"
