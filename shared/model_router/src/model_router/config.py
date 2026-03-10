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


class RouterConfig(BaseModel):
    """Top-level router configuration."""

    default_provider: ProviderType = ProviderType.VERTEX_AI
    vertex_ai: VertexAIConfig = Field(default_factory=VertexAIConfig)
    test_mode: bool = False

    @classmethod
    def from_env(cls) -> 'RouterConfig':
        """Build router config from process environment."""
        return cls(
            default_provider=ProviderType.VERTEX_AI,
            vertex_ai=VertexAIConfig.from_env(),
            test_mode=_env_flag('AURA_TEST_MODE'),
        )
