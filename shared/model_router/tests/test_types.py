# test_types.py
# Tests for shared request, response, and config models.

# Verifies the normalized request/response contracts, provider enums, and
# environment-backed configuration fallbacks used by the shared model router.

# @see: model_router/types.py - Request and response model definitions
# @note: Config fallbacks should match both legacy AURA env names and GCP envs.

"""Tests for shared request, response, and config models."""

import pytest
from pydantic import ValidationError

from model_router.config import RouterConfig, VertexAIConfig
from model_router.types import (
    GenerateRequest,
    GenerateResponse,
    ModelInfo,
    ProviderType,
    StreamChunk,
    UsageInfo,
)


def test_generate_request_minimal() -> None:
    request = GenerateRequest(model="gemini-2.0-flash", contents="hello")

    assert request.model == "gemini-2.0-flash"
    assert request.contents == "hello"
    assert request.provider is None
    assert request.temperature is None
    assert request.top_p is None
    assert request.max_output_tokens is None
    assert request.response_mime_type is None
    assert request.safety_settings is None
    assert request.system_instruction is None
    assert request.thinking_config is None


def test_generate_request_full() -> None:
    request = GenerateRequest(
        model="gemini-2.0-flash",
        contents=["hello"],
        provider="vertex_ai",
        temperature=0.2,
        top_p=0.95,
        max_output_tokens=512,
        response_mime_type="application/json",
        safety_settings=[
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_ONLY_HIGH",
            }
        ],
        system_instruction="be helpful",
        thinking_config={"budget_tokens": 64},
    )

    assert request.contents == ["hello"]
    assert request.provider == "vertex_ai"
    assert request.temperature == 0.2
    assert request.top_p == 0.95
    assert request.max_output_tokens == 512
    assert request.response_mime_type == "application/json"
    assert request.safety_settings == [
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_ONLY_HIGH",
        }
    ]
    assert request.system_instruction == "be helpful"
    assert request.thinking_config == {"budget_tokens": 64}


def test_generate_request_rejects_empty_model() -> None:
    with pytest.raises(ValidationError):
        GenerateRequest(model="", contents="hello")


def test_generate_request_strips_model_whitespace() -> None:
    request = GenerateRequest(model="  gemini-2.5-pro  ", contents="hello")

    assert request.model == "gemini-2.5-pro"


def test_generate_response_shape() -> None:
    response = GenerateResponse(
        text="hi",
        model_used="gemini-2.0-flash",
        provider=ProviderType.VERTEX_AI,
    )

    assert response.text == "hi"
    assert response.model_used == "gemini-2.0-flash"
    assert response.provider is ProviderType.VERTEX_AI
    assert response.usage.input_tokens == 0
    assert response.usage.output_tokens == 0
    assert response.usage.thinking_tokens == 0
    assert response.metadata == {}


def test_generate_response_metadata_shape() -> None:
    response = GenerateResponse(
        text="hi",
        model_used="gemini-2.0-flash",
        provider=ProviderType.VERTEX_AI,
        metadata={
            "finish_reason": "STOP",
            "prompt_feedback_block_reason": "SAFETY",
        },
    )

    assert response.metadata == {
        "finish_reason": "STOP",
        "prompt_feedback_block_reason": "SAFETY",
    }


def test_usage_info_defaults() -> None:
    usage = UsageInfo()

    assert usage.input_tokens == 0
    assert usage.output_tokens == 0
    assert usage.thinking_tokens == 0


def test_stream_chunk_types() -> None:
    thinking = StreamChunk(type="thinking", text="step")
    content = StreamChunk(type="content", text="answer")

    assert thinking.type == "thinking"
    assert content.type == "content"

    with pytest.raises(ValidationError):
        StreamChunk(type="other", text="bad")


def test_provider_type_enum() -> None:
    assert ProviderType.VERTEX_AI.value == "vertex_ai"
    assert ProviderType.OPENROUTER.value == "openrouter"
    assert ProviderType.OLLAMA.value == "ollama"


def test_model_info_basic() -> None:
    info = ModelInfo(name="gemini-2.0-flash", provider=ProviderType.VERTEX_AI)

    assert info.name == "gemini-2.0-flash"
    assert info.provider is ProviderType.VERTEX_AI
    assert info.display_name is None

    with pytest.raises(ValidationError):
        ModelInfo(provider=ProviderType.VERTEX_AI)


def test_vertex_ai_config_from_env_region(monkeypatch_env) -> None:
    monkeypatch_env.setenv("VERTEX_PROJECT", "project-1")
    monkeypatch_env.setenv("VERTEX_REGION", "us-central1")
    monkeypatch_env.delenv("VERTEX_LOCATION", raising=False)

    config = VertexAIConfig.from_env()

    assert config.project_id == "project-1"
    assert config.region == "us-central1"


def test_vertex_ai_config_from_google_cloud_env_fallback(monkeypatch_env) -> None:
    monkeypatch_env.delenv("VERTEX_PROJECT", raising=False)
    monkeypatch_env.delenv("VERTEX_REGION", raising=False)
    monkeypatch_env.delenv("VERTEX_LOCATION", raising=False)
    monkeypatch_env.setenv("GOOGLE_CLOUD_PROJECT", "cloud-project")
    monkeypatch_env.setenv("GOOGLE_CLOUD_LOCATION", "asia-south1")

    config = VertexAIConfig.from_env()

    assert config.project_id == "cloud-project"
    assert config.region == "asia-south1"


def test_vertex_ai_config_from_env_location_fallback(
    monkeypatch_env,
) -> None:
    monkeypatch_env.delenv("VERTEX_REGION", raising=False)
    monkeypatch_env.setenv("VERTEX_LOCATION", "europe-west1")

    config = VertexAIConfig.from_env()

    assert config.region == "europe-west1"


def test_vertex_ai_config_from_env_default(monkeypatch_env) -> None:
    monkeypatch_env.delenv("VERTEX_REGION", raising=False)
    monkeypatch_env.delenv("VERTEX_LOCATION", raising=False)
    monkeypatch_env.delenv("VERTEX_CREDENTIALS", raising=False)
    monkeypatch_env.delenv(
        "GOOGLE_APPLICATION_CREDENTIALS",
        raising=False,
    )

    config = VertexAIConfig.from_env()

    assert config.region == "global"
    assert config.credentials_path == ""


def test_router_config_from_env_test_mode(monkeypatch_env) -> None:
    monkeypatch_env.setenv("AURA_TEST_MODE", "true")

    config = RouterConfig.from_env()

    assert config.default_provider is ProviderType.VERTEX_AI
    assert config.test_mode is True


def test_router_config_from_env_truthy_numeric_test_mode(
    monkeypatch_env,
) -> None:
    monkeypatch_env.setenv("AURA_TEST_MODE", "1")

    config = RouterConfig.from_env()

    assert config.test_mode is True
