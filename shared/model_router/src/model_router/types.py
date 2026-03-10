"""Shared request and response types for model router providers."""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ProviderType(str, Enum):
    """Supported model router providers."""

    VERTEX_AI = 'vertex_ai'
    OPENROUTER = 'openrouter'
    OLLAMA = 'ollama'


class UsageInfo(BaseModel):
    """Normalized token usage information."""

    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0


class GenerateRequest(BaseModel):
    """Normalized generation request across providers."""

    model: str
    contents: str | list[Any]
    provider: str | None = None
    temperature: float | None = None
    max_output_tokens: int | None = None
    system_instruction: str | None = None
    thinking_config: dict[str, Any] | None = None

    @field_validator('model')
    @classmethod
    def validate_model(cls, value: str) -> str:
        """Reject empty model names."""
        if not value.strip():
            raise ValueError('model must be a non-empty string')
        return value


class GenerateResponse(BaseModel):
    """Normalized generation response across providers."""

    text: str
    model_used: str
    provider: ProviderType
    usage: UsageInfo = Field(default_factory=UsageInfo)
    thinking_text: str | None = None


class StreamChunk(BaseModel):
    """A normalized streaming chunk."""

    type: Literal['thinking', 'content']
    text: str


class ModelInfo(BaseModel):
    """Metadata for a provider model."""

    name: str
    provider: ProviderType
    display_name: str | None = None
