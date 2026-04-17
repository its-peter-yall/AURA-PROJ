# vertex_ai.py
# Vertex AI generation and embedding providers for the shared router.

# Implements request normalization, google-genai config translation, shared
# error mapping, and a deterministic test mode used by both AURA apps and the
# package test suite.

# @see: model_router/types.py - Shared request and response contracts
# @note: Normalize `models/` prefixes to preserve legacy Vertex call-sites.

"""Vertex AI generation and embedding providers for the shared router."""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
from typing import Any

from model_router.config import VertexAIConfig
from model_router.errors import (
    AuthenticationError,
    ContentPolicyError,
    ModelRouterError,
    ModelUnavailableError,
    ProviderTimeoutError,
    RateLimitError,
)
from model_router.providers.base import (
    AURA_EMBEDDING_DIMENSIONS,
    BaseEmbeddingProvider,
    BaseProvider,
)
from model_router.types import (
    GenerateRequest,
    GenerateResponse,
    ModelInfo,
    ProviderType,
    StreamChunk,
    UsageInfo,
)

_GEMINI_MODELS = [
    ModelInfo(
        name="gemini-2.0-flash",
        provider=ProviderType.VERTEX_AI,
        display_name="Gemini 2.0 Flash",
    ),
    ModelInfo(
        name="gemini-2.5-flash",
        provider=ProviderType.VERTEX_AI,
        display_name="Gemini 2.5 Flash",
        thinking_supported=True,
    ),
    ModelInfo(
        name="gemini-2.5-pro",
        provider=ProviderType.VERTEX_AI,
        display_name="Gemini 2.5 Pro",
        thinking_supported=True,
    ),
]

_EMBEDDING_MODELS = [
    ModelInfo(
        name="text-embedding-004",
        provider=ProviderType.VERTEX_AI,
        display_name="Text Embedding 004",
        model_type="embedding",
    ),
    ModelInfo(
        name="text-embedding-005",
        provider=ProviderType.VERTEX_AI,
        display_name="Text Embedding 005",
        model_type="embedding",
    ),
    ModelInfo(
        name="text-multilingual-embedding-002",
        provider=ProviderType.VERTEX_AI,
        display_name="Text Multilingual Embedding 002",
        model_type="embedding",
    ),
]

_TEST_MODE_TRUTHY_VALUES = {"1", "true", "yes", "on"}


def _is_test_mode() -> bool:
    """Return True when the shared package should avoid live Vertex calls."""
    return os.getenv("AURA_TEST_MODE", "").strip().lower() in _TEST_MODE_TRUTHY_VALUES


def _normalize_vertex_model_name(model_name: str) -> str:
    """Strip the legacy `models/` prefix used by some Vertex call sites."""
    normalized = model_name.strip()
    if normalized.startswith("models/"):
        return normalized[len("models/") :]
    return normalized


def _extract_http_code(error_text: str) -> int | None:
    """Extract a likely HTTP status code from an error string."""
    match = re.search(r"\b(400|401|403|404|408|429|500|503|504)\b", error_text)
    if match is None:
        return None
    return int(match.group(1))


def _get_error_code(error: BaseException) -> int | None:
    """Read a status code from a provider error if one is exposed."""
    raw_code = getattr(error, "code", None)
    if callable(raw_code):
        try:
            raw_code = raw_code()
        except Exception:
            raw_code = None

    if isinstance(raw_code, int):
        return raw_code

    if raw_code is not None:
        extracted = _extract_http_code(str(raw_code))
        if extracted is not None:
            return extracted

    return _extract_http_code(str(error))


def _map_vertex_error(
    error: BaseException,
    *,
    model: str = "",
) -> ModelRouterError:
    """Map Vertex AI SDK failures to the shared error hierarchy."""
    error_str = str(error).lower()
    class_name = error.__class__.__name__.lower()
    combined = f"{class_name} {error_str}"
    error_code = _get_error_code(error)

    if (
        error_code in {401, 403}
        or "permission_denied" in combined
        or "permission denied" in combined
        or "unauth" in combined
    ):
        return AuthenticationError(
            str(error),
            provider=ProviderType.VERTEX_AI.value,
            model=model,
            original=error,
        )

    if (
        error_code == 429
        or "resource_exhausted" in combined
        or "resource exhausted" in combined
        or "quota" in combined
    ):
        return RateLimitError(
            str(error),
            provider=ProviderType.VERTEX_AI.value,
            model=model,
            original=error,
        )

    if error_code == 400 and (
        "safety" in combined or "blocked" in combined or "policy" in combined
    ):
        return ContentPolicyError(
            str(error),
            provider=ProviderType.VERTEX_AI.value,
            model=model,
            original=error,
        )

    if error_code == 404 or "not_found" in combined or "not found" in combined:
        return ModelUnavailableError(
            str(error),
            provider=ProviderType.VERTEX_AI.value,
            model=model,
            original=error,
        )

    if "deadline" in combined or "timeout" in combined:
        return ProviderTimeoutError(
            str(error),
            provider=ProviderType.VERTEX_AI.value,
            model=model,
            original=error,
        )

    return ModelRouterError(
        str(error),
        provider=ProviderType.VERTEX_AI.value,
        model=model,
        original=error,
    )


def _coerce_safety_settings(raw_safety_settings: list[Any]) -> list[Any]:
    """Convert legacy or dict safety settings into google-genai settings."""
    from google.genai import types as genai_types

    normalized: list[Any] = []
    for setting in raw_safety_settings:
        if isinstance(setting, genai_types.SafetySetting):
            normalized.append(setting)
            continue

        if isinstance(setting, dict):
            payload = setting
        else:
            to_dict = getattr(setting, "to_dict", None)
            if callable(to_dict):
                try:
                    payload = to_dict()
                except Exception:
                    payload = None
            else:
                payload = None

        if not isinstance(payload, dict):
            continue

        category = payload.get("category")
        threshold = payload.get("threshold")
        method = payload.get("method")
        if category is None or threshold is None:
            continue

        setting_kwargs: dict[str, Any] = {
            "category": str(category),
            "threshold": str(threshold),
        }
        if method is not None:
            setting_kwargs["method"] = str(method)
        normalized.append(genai_types.SafetySetting(**setting_kwargs))

    return normalized


def _normalize_thinking_config(raw_config: dict[str, Any]) -> Any:
    """Convert shared thinking config into a google-genai ThinkingConfig."""
    from google.genai import types as genai_types

    config_kwargs: dict[str, Any] = {}
    if "thinking_budget" in raw_config and raw_config["thinking_budget"] is not None:
        config_kwargs["thinking_budget"] = int(raw_config["thinking_budget"])
    if "thinking_level" in raw_config and raw_config["thinking_level"] is not None:
        config_kwargs["thinking_level"] = str(raw_config["thinking_level"]).upper()
    if "include_thoughts" in raw_config:
        config_kwargs["include_thoughts"] = bool(raw_config["include_thoughts"])
    else:
        config_kwargs["include_thoughts"] = True
    return genai_types.ThinkingConfig(**config_kwargs)


def _build_generate_config_kwargs(request: GenerateRequest) -> dict[str, Any]:
    """Translate shared request fields to google-genai config kwargs."""
    config_kwargs: dict[str, Any] = {}
    if request.temperature is not None:
        config_kwargs["temperature"] = request.temperature
    if request.top_p is not None:
        config_kwargs["top_p"] = request.top_p
    if request.max_output_tokens is not None:
        config_kwargs["max_output_tokens"] = request.max_output_tokens
    if request.response_mime_type:
        config_kwargs["response_mime_type"] = request.response_mime_type
    if request.system_instruction:
        config_kwargs["system_instruction"] = request.system_instruction
    if request.thinking_config:
        config_kwargs["thinking_config"] = _normalize_thinking_config(
            request.thinking_config
        )
    if request.safety_settings:
        config_kwargs["safety_settings"] = _coerce_safety_settings(
            request.safety_settings
        )
    return config_kwargs


def _extract_usage(response: Any) -> UsageInfo:
    """Normalize usage metadata from a google-genai response object."""
    usage_metadata = getattr(response, "usage_metadata", None)
    if usage_metadata is None:
        return UsageInfo()

    return UsageInfo(
        input_tokens=int(getattr(usage_metadata, "prompt_token_count", 0) or 0),
        output_tokens=int(getattr(usage_metadata, "candidates_token_count", 0) or 0),
        thinking_tokens=int(getattr(usage_metadata, "thoughts_token_count", 0) or 0),
    )


def _extract_response_metadata(response: Any) -> dict[str, Any]:
    """Extract portable metadata fields from a provider response object."""
    metadata: dict[str, Any] = {}

    candidates = getattr(response, "candidates", None) or []
    if candidates:
        finish_reason = getattr(candidates[0], "finish_reason", None)
        if finish_reason is not None:
            metadata["finish_reason"] = (
                finish_reason.value
                if hasattr(finish_reason, "value")
                else finish_reason
            )

    prompt_feedback = getattr(response, "prompt_feedback", None)
    block_reason = getattr(prompt_feedback, "block_reason", None)
    if block_reason is not None:
        metadata["prompt_feedback_block_reason"] = (
            block_reason.value if hasattr(block_reason, "value") else block_reason
        )

    return metadata


def _extract_response_parts(response: Any) -> tuple[str, str | None]:
    """Extract content and thinking text from a generation response."""
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content_parts: list[str] = []
        thinking_parts: list[str] = []
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            part_text = getattr(part, "text", None)
            if not isinstance(part_text, str) or not part_text:
                continue

            is_thought = getattr(part, "thought", False) is True
            is_thought_summary = bool(getattr(part, "thought_summary", None))
            if is_thought or is_thought_summary:
                thinking_parts.append(part_text)
            else:
                content_parts.append(part_text)

        if content_parts:
            thinking_text = "".join(thinking_parts) or None
            return "".join(content_parts), thinking_text

    fallback_text = getattr(response, "text", None)
    if isinstance(fallback_text, str) and fallback_text:
        return fallback_text, None

    return "", None


def _normalize_stream_chunk(chunk: Any) -> list[StreamChunk]:
    """Normalize a google-genai stream chunk into shared StreamChunk items."""
    normalized: list[StreamChunk] = []
    candidates = getattr(chunk, "candidates", None) or []

    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            part_text = getattr(part, "text", None)
            if not isinstance(part_text, str) or not part_text:
                continue

            is_thought = getattr(part, "thought", False) is True
            is_thought_summary = bool(getattr(part, "thought_summary", None))
            normalized.append(
                StreamChunk(
                    type="thinking" if is_thought or is_thought_summary else "content",
                    text=part_text,
                )
            )

    if normalized:
        return normalized

    fallback_text = getattr(chunk, "text", None)
    if isinstance(fallback_text, str) and fallback_text:
        normalized.append(StreamChunk(type="content", text=fallback_text))
    return normalized


class _VertexAuthMixin:
    """Shared credential helpers for Vertex AI generation and embedding."""

    def __init__(self, config: VertexAIConfig) -> None:
        self._config = config

    def _apply_credentials_path(self) -> None:
        """Mirror existing env behavior for credentials file overrides."""
        if self._config.credentials_path and not os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS"
        ):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self._config.credentials_path


class VertexAIProvider(_VertexAuthMixin, BaseProvider):
    """Generation provider backed by Vertex AI Gemini models."""

    def __init__(self, config: VertexAIConfig) -> None:
        super().__init__(config)
        self._test_mode = _is_test_mode()
        self._client: Any | None = None

    def _get_client(self) -> Any | None:
        """Create and cache a google-genai client outside test mode."""
        if self._test_mode:
            return None

        if self._client is not None:
            return self._client

        try:
            from google import genai

            self._apply_credentials_path()
            self._client = genai.Client(
                vertexai=True,
                project=self._config.project_id,
                location=self._config.region,
            )
            return self._client
        except Exception as error:
            raise AuthenticationError(
                str(error),
                provider=ProviderType.VERTEX_AI.value,
                original=error,
            ) from error

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Generate a normalized response for a Vertex AI request."""
        normalized_model = _normalize_vertex_model_name(request.model)
        if self._test_mode:
            return GenerateResponse(
                text="Test-mode output.",
                model_used=normalized_model,
                provider=ProviderType.VERTEX_AI,
                usage=UsageInfo(),
            )

        client = self._get_client()
        try:
            from google.genai import types as genai_types

            config_kwargs = _build_generate_config_kwargs(request)
            gen_config = (
                genai_types.GenerateContentConfig(**config_kwargs)
                if config_kwargs
                else None
            )
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=normalized_model,
                contents=request.contents,
                config=gen_config,
            )
        except ModelRouterError:
            raise
        except Exception as error:
            raise _map_vertex_error(error, model=normalized_model) from error

        text, thinking_text = _extract_response_parts(response)
        return GenerateResponse(
            text=text,
            model_used=normalized_model,
            provider=ProviderType.VERTEX_AI,
            usage=_extract_usage(response),
            thinking_text=thinking_text,
            metadata=_extract_response_metadata(response),
        )

    async def stream(
        self,
        request: GenerateRequest,
    ):
        """Stream normalized content chunks from Vertex AI."""
        if self._test_mode:
            yield StreamChunk(type="content", text="Test-mode stream output.")
            return

        normalized_model = _normalize_vertex_model_name(request.model)
        client = self._get_client()
        try:
            from google.genai import types as genai_types

            config_kwargs = _build_generate_config_kwargs(request)
            gen_config = (
                genai_types.GenerateContentConfig(**config_kwargs)
                if config_kwargs
                else None
            )
            stream_iter = client.models.generate_content_stream(
                model=normalized_model,
                contents=request.contents,
                config=gen_config,
            )
        except ModelRouterError:
            raise
        except Exception as error:
            raise _map_vertex_error(error, model=normalized_model) from error

        sentinel = object()

        def _next_chunk() -> Any:
            return next(stream_iter, sentinel)

        try:
            while True:
                chunk = await asyncio.to_thread(_next_chunk)
                if chunk is sentinel:
                    break
                for normalized_chunk in _normalize_stream_chunk(chunk):
                    yield normalized_chunk
        except Exception as error:
            raise _map_vertex_error(error, model=normalized_model) from error
        finally:
            close_fn = getattr(stream_iter, "close", None)
            if callable(close_fn):
                try:
                    close_fn()
                except Exception:
                    pass

    async def list_models(self) -> list[ModelInfo]:
        """Return the supported Gemini model list."""
        return list(_GEMINI_MODELS)

    async def health_check(self) -> bool:
        """Return True when the provider can initialize its client."""
        if self._test_mode:
            return True

        try:
            self._get_client()
        except ModelRouterError:
            return False
        return True


class VertexAIEmbeddingProvider(_VertexAuthMixin, BaseEmbeddingProvider):
    """Embedding provider backed by the Vertex AI REST embeddings API."""

    def __init__(self, config: VertexAIConfig) -> None:
        super().__init__(config)
        self._test_mode = _is_test_mode()
        self._credentials: Any | None = None

    def _build_test_vector(self, text: str) -> list[float]:
        """Create a deterministic 768-dimension vector for test mode."""
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:4], "big")
        return [
            ((seed + index + digest[index % len(digest)]) % 1000) / 1000.0
            for index in range(AURA_EMBEDDING_DIMENSIONS)
        ]

    def _get_access_token(self) -> str:
        """Fetch an access token using application default credentials."""
        from google.auth import default
        from google.auth.transport.requests import Request

        self._apply_credentials_path()
        if self._credentials is None:
            self._credentials, _ = default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )

        self._credentials.refresh(Request())
        return str(self._credentials.token)

    def _get_endpoint(self) -> str:
        """Return the Vertex AI text embedding endpoint URL."""
        region = self._config.region or "global"
        project_id = self._config.project_id
        if region == "global":
            return (
                "https://aiplatform.googleapis.com/v1/projects/"
                f"{project_id}/locations/global/publishers/google/models/"
                "text-embedding-004:predict"
            )
        return (
            f"https://{region}-aiplatform.googleapis.com/v1/projects/"
            f"{project_id}/locations/{region}/publishers/google/models/"
            "text-embedding-004:predict"
        )

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        """Perform the blocking REST call to Vertex AI embeddings."""
        import requests

        access_token = self._get_access_token()
        payload = {
            "instances": [{"content": text} for text in texts],
            "parameters": {
                "autoTruncation": True,
                "outputDimensionality": AURA_EMBEDDING_DIMENSIONS,
            },
        }
        response = requests.post(
            self._get_endpoint(),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=120,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Vertex API error: {response.status_code} - {response.text[:200]}"
            )

        data = response.json()
        predictions = data.get("predictions", [])
        vectors: list[list[float]] = []
        for prediction in predictions:
            embedding = prediction.get("embeddings", {}).get("values", [])
            if not embedding:
                embedding = prediction.get("values", [])
            vectors.append(list(embedding))

        if len(vectors) != len(texts):
            raise RuntimeError(f"Expected {len(texts)} embeddings, got {len(vectors)}")
        return vectors

    async def _embed_raw(self, texts: list[str]) -> list[list[float]]:
        """Return raw embedding vectors for the provided texts."""
        if self._test_mode:
            return [self._build_test_vector(text) for text in texts]

        try:
            return await asyncio.to_thread(self._embed_sync, texts)
        except Exception as error:
            raise _map_vertex_error(
                error,
                model="text-embedding-004",
            ) from error

    async def list_models(self) -> list[ModelInfo]:
        """Return the supported Vertex AI embedding model list."""
        return list(_EMBEDDING_MODELS)


__all__ = [
    "VertexAIEmbeddingProvider",
    "VertexAIProvider",
    "_extract_response_metadata",
    "_extract_response_parts",
    "_extract_usage",
    "_map_vertex_error",
    "_normalize_vertex_model_name",
]
