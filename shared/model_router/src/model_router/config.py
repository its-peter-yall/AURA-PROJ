# config.py
# Environment-backed configuration models for the shared model router.

# Defines provider-specific config objects and the top-level RouterConfig
# assembled from environment variables. This phase extends the package with
# OpenRouter settings while keeping env loading deterministic in test mode.

# @see: model_router/router.py - Runtime auto-registration logic
# @note: Vertex region prefers VERTEX_REGION, then VERTEX_LOCATION.

"""Environment-backed configuration models for model router setup."""

import os

from pydantic import BaseModel, Field

from model_router.types import ProviderType


def _env_flag(name: str) -> bool:
    """Parse a truthy environment variable."""
    return os.getenv(name, '').strip().lower() in {
        '1',
        'true',
        'yes',
        'on',
    }


class VertexAIConfig(BaseModel):
    """Configuration for the Vertex AI provider."""

    project_id: str = ''
    region: str = 'global'
    credentials_path: str = ''

    @classmethod
    def from_env(cls) -> 'VertexAIConfig':
        """Build config from the documented env var fallback chain."""
        return cls(
            project_id=os.getenv('VERTEX_PROJECT', ''),
            region=(
                os.getenv('VERTEX_REGION')
                or os.getenv('VERTEX_LOCATION')
                or 'global'
            ),
            credentials_path=(
                os.getenv('VERTEX_CREDENTIALS')
                or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                or ''
            ),
        )


class OpenRouterConfig(BaseModel):
    """Configuration for the OpenRouter provider."""

    api_key: str = ''
    base_url: str = 'https://openrouter.ai/api/v1'
    site_url: str = ''
    site_name: str = 'AURA'

    @classmethod
    def from_env(cls) -> 'OpenRouterConfig':
        """Build OpenRouter config from environment variables."""
        return cls(
            api_key=os.getenv('OPENROUTER_API_KEY', ''),
            base_url=os.getenv(
                'OPENROUTER_BASE_URL',
                'https://openrouter.ai/api/v1',
            ),
            site_url=os.getenv('OPENROUTER_SITE_URL', ''),
            site_name=os.getenv('OPENROUTER_SITE_NAME', 'AURA'),
        )


class RouterConfig(BaseModel):
    """Top-level router configuration."""

    default_provider: ProviderType = ProviderType.VERTEX_AI
    vertex_ai: VertexAIConfig = Field(default_factory=VertexAIConfig)
    openrouter: OpenRouterConfig = Field(default_factory=OpenRouterConfig)
    test_mode: bool = False

    @classmethod
    def from_env(cls) -> 'RouterConfig':
        """Build router config from process environment."""
        return cls(
            default_provider=ProviderType.VERTEX_AI,
            vertex_ai=VertexAIConfig.from_env(),
            openrouter=OpenRouterConfig.from_env(),
            test_mode=_env_flag('AURA_TEST_MODE'),
        )
