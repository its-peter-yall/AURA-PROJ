# types.py
# Shared request, response, and metadata models for the model router.

# Defines the normalized contracts passed between callers, the shared router,
# and provider implementations. These models preserve provider-specific knobs
# only where AURA apps depend on them while keeping the public API uniform.

# @see: model_router/router.py - Request routing and provider delegation
# @note: Keep fields aligned with legacy Vertex call-sites before pruning them.

"""Shared request and response types for model router providers."""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ProviderType(str, Enum):
    """Supported model router providers."""

    VERTEX_AI = "vertex_ai"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


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
    top_p: float | None = None
    max_output_tokens: int | None = None
    response_mime_type: str | None = None
    safety_settings: list[Any] | None = None
    system_instruction: str | None = None
    thinking_config: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str) -> str:
        """Reject empty model names and normalize surrounding whitespace."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("model must be a non-empty string")
        return normalized


class GenerateResponse(BaseModel):
    """Normalized generation response across providers."""

    text: str
    model_used: str
    provider: ProviderType
    usage: UsageInfo = Field(default_factory=UsageInfo)
    thinking_text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class StreamChunk(BaseModel):
    """A normalized streaming chunk."""

    type: Literal["thinking", "content"]
    text: str
    usage: UsageInfo | None = None


class ModelInfo(BaseModel):
    """Metadata for a provider model."""

    name: str
    provider: ProviderType
    display_name: str | None = None
    model_type: Literal["generation", "embedding"] = "generation"
    thinking_supported: bool = False


class UsageRecord(BaseModel):
    """Persisted usage record for a single LLM request.

    Captures token usage, estimated cost, and attribution metadata
    for a single generation or streaming call through the router.

    Args:
        timestamp: When the request completed.
        provider: Which provider handled the request.
        model: Model identifier used for the request.
        input_tokens: Number of input/prompt tokens.
        output_tokens: Number of output/completion tokens.
        thinking_tokens: Number of thinking/reasoning tokens.
        estimated_cost_usd: Estimated cost in USD.
        is_estimated: Whether the cost is an approximation.
        session_id: Optional study session identifier.
        user_id: Optional user identifier.
        operation: Type of operation (chat, embed, extract).
    """

    timestamp: datetime
    provider: ProviderType
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    estimated_cost_usd: float = 0.0
    is_estimated: bool = True
    session_id: str | None = None
    user_id: str | None = None
    operation: str = "chat"
