# openrouter.py
# OpenRouter generation provider for the shared model router package.

# Implements test-mode behavior, OpenAI-compatible request translation,
# normalized streaming chunks, curated model discovery, and OpenRouter-specific
# credit/health endpoints without leaking SDK-specific types to callers.

# @see: model_router/providers/base.py - Provider contracts
# @note: Keep imports lazy so the optional openai extra is only needed at use time.

"""OpenRouter provider for the shared model router."""

from __future__ import annotations

import asyncio
import hashlib
import os
from typing import Any, AsyncGenerator

import httpx

from model_router.config import OpenRouterConfig
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

_OPENROUTER_EXCLUDED_PREFIXES: list[str] = []

_TEST_MODELS = [
    ModelInfo(
        name="anthropic/claude-sonnet-4",
        provider=ProviderType.OPENROUTER,
        display_name="Claude Sonnet 4",
        thinking_supported=True,
    ),
    ModelInfo(
        name="google/gemini-2.5-flash",
        provider=ProviderType.OPENROUTER,
        display_name="Gemini 2.5 Flash",
        thinking_supported=True,
    ),
    ModelInfo(
        name="openai/gpt-4.1-mini",
        provider=ProviderType.OPENROUTER,
        display_name="GPT-4.1 Mini",
        thinking_supported=False,
    ),
    ModelInfo(
        name="deepseek/deepseek-r1",
        provider=ProviderType.OPENROUTER,
        display_name="DeepSeek R1",
        thinking_supported=True,
    ),
    ModelInfo(
        name="meta-llama/llama-3.3-70b-instruct",
        provider=ProviderType.OPENROUTER,
        display_name="Llama 3.3 70B Instruct",
        thinking_supported=False,
    ),
    ModelInfo(
        name="mistralai/mistral-large",
        provider=ProviderType.OPENROUTER,
        display_name="Mistral Large",
        thinking_supported=False,
    ),
    ModelInfo(
        name="qwen/qwen-2.5-72b-instruct",
        provider=ProviderType.OPENROUTER,
        display_name="Qwen 2.5 72B Instruct",
        thinking_supported=False,
    ),
]

_EMBEDDING_TEST_MODELS = [
    ModelInfo(
        name="openai/text-embedding-3-small",
        provider=ProviderType.OPENROUTER,
        display_name="Text Embedding 3 Small",
        model_type="embedding",
    ),
    ModelInfo(
        name="openai/text-embedding-3-large",
        provider=ProviderType.OPENROUTER,
        display_name="Text Embedding 3 Large",
        model_type="embedding",
    ),
]

_OPENROUTER_EMBEDDING_PREFIXES = [
    "openai/text-embedding",
]

_REASONING_PARAMETER_NAMES = {
    "reasoning",
    "include_reasoning",
    "reasoning_effort",
}


def _supports_thinking(
    model_name: str,
    supported_parameters: list[Any] | None = None,
) -> bool:
    """Return True when a model supports or exposes reasoning output."""
    normalized = model_name.lower()

    normalized_params = {
        str(param).strip().lower()
        for param in (supported_parameters or [])
        if isinstance(param, str) and str(param).strip()
    }
    if normalized_params.intersection(_REASONING_PARAMETER_NAMES):
        return True

    if "deepseek" in normalized and "r1" in normalized:
        return True

    if "claude" in normalized or "anthropic" in normalized:
        return True

    if normalized.startswith("google/") and "gemini" in normalized:
        return True

    if ":thinking" in normalized:
        return True

    return False


def _is_test_mode() -> bool:
    """Return True when provider calls should avoid live OpenRouter access."""
    return os.getenv("AURA_TEST_MODE", "").strip().lower() == "true"


def _coerce_text_value(value: Any) -> str:
    """Normalize mixed SDK content shapes into a plain text string."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                continue
            text = getattr(item, "text", None)
            if isinstance(text, str):
                parts.append(text)
        return "".join(parts)
    return str(value)


def _build_messages(request: GenerateRequest) -> list[dict[str, Any]]:
    """Convert shared request contents into OpenAI-compatible messages."""
    messages: list[dict[str, Any]] = []

    if request.system_instruction:
        messages.append(
            {
                "role": "system",
                "content": request.system_instruction,
            }
        )

    if isinstance(request.contents, str):
        messages.append({"role": "user", "content": request.contents})
        return messages

    for item in request.contents:
        if isinstance(item, str):
            messages.append({"role": "user", "content": item})
            continue

        if not isinstance(item, dict):
            continue

        role = str(item.get("role", "user"))
        if role == "model":
            role = "assistant"

        parts = item.get("parts", [])
        content_parts: list[str] = []
        for part in parts:
            if isinstance(part, str):
                content_parts.append(part)
            elif isinstance(part, dict):
                text = part.get("text")
                if isinstance(text, str):
                    content_parts.append(text)

        content = "".join(content_parts)
        if content:
            messages.append({"role": role, "content": content})

    return messages


def _build_thinking_params(
    model: str,
    thinking_config: dict[str, Any] | None,
) -> dict[str, Any]:
    """Translate shared thinking config to OpenRouter request params."""
    if not thinking_config:
        return {}

    model_name = model.lower()
    budget = int(thinking_config.get("thinking_budget", 0) or 0)
    if budget <= 0:
        return {}

    if "claude" in model_name or "anthropic" in model_name:
        if budget <= 1024:
            effort = "low"
        elif budget <= 4096:
            effort = "medium"
        else:
            effort = "high"
        return {"reasoning": {"effort": effort}}

    if "deepseek" in model_name and "r1" in model_name:
        return {}

    return {}


def _build_headers(config: OpenRouterConfig) -> dict[str, str]:
    """Build OpenRouter attribution and auth headers."""
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "X-Title": config.site_name,
    }
    if config.site_url:
        headers["HTTP-Referer"] = config.site_url
    return headers


def _map_openrouter_error(
    error: BaseException,
    *,
    model: str = "",
) -> ModelRouterError:
    """Map OpenRouter/OpenAI SDK failures to the shared error hierarchy."""
    if isinstance(error, httpx.HTTPStatusError):
        status_code = error.response.status_code
        if status_code in (401, 403):
            return AuthenticationError(
                str(error),
                provider=ProviderType.OPENROUTER.value,
                model=model,
                original=error,
            )
        if status_code == 429:
            retry_after_value = error.response.headers.get("Retry-After")
            retry_after: float | None = None
            if retry_after_value is not None:
                try:
                    retry_after = float(retry_after_value)
                except ValueError:
                    retry_after = None
            return RateLimitError(
                str(error),
                provider=ProviderType.OPENROUTER.value,
                model=model,
                original=error,
                retry_after=retry_after,
            )

    try:
        import openai as openai_mod
    except ImportError:
        return ModelRouterError(
            str(error),
            provider=ProviderType.OPENROUTER.value,
            model=model,
            original=error,
        )

    if isinstance(error, openai_mod.AuthenticationError):
        return AuthenticationError(
            str(error),
            provider=ProviderType.OPENROUTER.value,
            model=model,
            original=error,
        )
    if isinstance(error, openai_mod.RateLimitError):
        return RateLimitError(
            str(error),
            provider=ProviderType.OPENROUTER.value,
            model=model,
            original=error,
        )
    if isinstance(error, openai_mod.NotFoundError):
        return ModelUnavailableError(
            str(error),
            provider=ProviderType.OPENROUTER.value,
            model=model,
            original=error,
        )
    if isinstance(error, openai_mod.BadRequestError):
        error_text = str(error).lower()
        if "safety" in error_text or "content" in error_text:
            return ContentPolicyError(
                str(error),
                provider=ProviderType.OPENROUTER.value,
                model=model,
                original=error,
            )
    if isinstance(error, openai_mod.APITimeoutError):
        return ProviderTimeoutError(
            str(error),
            provider=ProviderType.OPENROUTER.value,
            model=model,
            original=error,
        )

    return ModelRouterError(
        str(error),
        provider=ProviderType.OPENROUTER.value,
        model=model,
        original=error,
    )


class OpenRouterProvider(BaseProvider):
    """Generation provider backed by OpenRouter's OpenAI-compatible API."""

    def __init__(self, config: OpenRouterConfig) -> None:
        self._config = config
        self._test_mode = _is_test_mode()
        self._client: Any | None = None

    def _get_client(self) -> Any | None:
        """Create and cache an AsyncOpenAI client when live access is needed."""
        if self._test_mode:
            return None
        if self._client is not None:
            return self._client

        try:
            from openai import AsyncOpenAI
        except ImportError as error:
            raise ModelRouterError(
                "OpenRouter support requires the openai extra dependency",
                provider=ProviderType.OPENROUTER.value,
                original=error,
            ) from error

        default_headers = {"X-Title": self._config.site_name}
        if self._config.site_url:
            default_headers["HTTP-Referer"] = self._config.site_url

        self._client = AsyncOpenAI(
            base_url=self._config.base_url,
            api_key=self._config.api_key,
            default_headers=default_headers,
        )
        return self._client

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Generate a normalized response for an OpenRouter request."""
        if self._test_mode:
            return GenerateResponse(
                text="Test-mode output.",
                model_used=request.model,
                provider=ProviderType.OPENROUTER,
                usage=UsageInfo(),
            )

        client = self._get_client()
        try:
            extra_body = _build_thinking_params(
                request.model,
                request.thinking_config,
            )
            kwargs: dict[str, Any] = {
                "model": request.model,
                "messages": _build_messages(request),
            }
            if request.temperature is not None:
                kwargs["temperature"] = request.temperature
            if request.max_output_tokens is not None:
                kwargs["max_tokens"] = request.max_output_tokens
            if getattr(request, "response_mime_type", None) == "application/json":
                kwargs["response_format"] = {"type": "json_object"}
            if extra_body:
                kwargs["extra_body"] = extra_body

            response = await client.chat.completions.create(**kwargs)
        except ModelRouterError:
            raise
        except Exception as error:
            raise _map_openrouter_error(error, model=request.model) from error

        choice = response.choices[0]
        message = choice.message
        reasoning = getattr(message, "reasoning_content", None)
        if not reasoning:
            reasoning = getattr(message, "reasoning", None)
        usage = getattr(response, "usage", None)
        return GenerateResponse(
            text=_coerce_text_value(getattr(message, "content", "")),
            model_used=str(getattr(response, "model", None) or request.model),
            provider=ProviderType.OPENROUTER,
            usage=UsageInfo(
                input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
                output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
                thinking_tokens=int(getattr(usage, "reasoning_tokens", 0) or 0),
            ),
            thinking_text=_coerce_text_value(reasoning) or None,
        )

    async def stream(
        self,
        request: GenerateRequest,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream normalized thinking/content chunks from OpenRouter."""
        if self._test_mode:
            yield StreamChunk(type="content", text="Test-mode stream output.")
            return

        client = self._get_client()
        stream: Any = None
        last_usage: Any = None
        try:
            extra_body = _build_thinking_params(
                request.model,
                request.thinking_config,
            )
            kwargs: dict[str, Any] = {
                "model": request.model,
                "messages": _build_messages(request),
                "stream": True,
                "stream_options": {"include_usage": True},
            }
            if request.temperature is not None:
                kwargs["temperature"] = request.temperature
            if request.max_output_tokens is not None:
                kwargs["max_tokens"] = request.max_output_tokens
            if extra_body:
                kwargs["extra_body"] = extra_body

            stream = await client.chat.completions.create(**kwargs)
            async for chunk in stream:
                if getattr(chunk, "choices", None):
                    delta = chunk.choices[0].delta
                    reasoning = getattr(delta, "reasoning_content", None)
                    if not reasoning:
                        reasoning = getattr(delta, "reasoning", None)
                    reasoning_text = _coerce_text_value(reasoning)
                    if reasoning_text:
                        yield StreamChunk(type="thinking", text=reasoning_text)

                    content_text = _coerce_text_value(
                        getattr(delta, "content", None)
                    )
                    if content_text:
                        yield StreamChunk(type="content", text=content_text)

                usage = getattr(chunk, "usage", None)
                if usage is not None:
                    last_usage = usage

            if last_usage is not None:
                yield StreamChunk(
                    type="content",
                    text="",
                    usage=UsageInfo(
                        input_tokens=int(
                            getattr(last_usage, "prompt_tokens", 0) or 0
                        ),
                        output_tokens=int(
                            getattr(last_usage, "completion_tokens", 0)
                            or 0
                        ),
                        thinking_tokens=int(
                            getattr(last_usage, "reasoning_tokens", 0) or 0
                        ),
                    ),
                )
        except ModelRouterError:
            raise
        except Exception as error:
            raise _map_openrouter_error(error, model=request.model) from error
        finally:
            if stream is not None:
                close_fn = getattr(stream, "close", None)
                if callable(close_fn):
                    try:
                        await close_fn()
                    except Exception:
                        pass
                aclose_fn = getattr(stream, "aclose", None)
                if callable(aclose_fn):
                    try:
                        await aclose_fn()
                    except Exception:
                        pass

    async def list_models(self) -> list[ModelInfo]:
        """Return curated models exposed to the AURA router."""
        if self._test_mode:
            return list(_TEST_MODELS)

        try:
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                response = await http_client.get(
                    f"{self._config.base_url.rstrip('/')}/models",
                    headers=_build_headers(self._config),
                )
                response.raise_for_status()
        except Exception as error:
            raise _map_openrouter_error(error) from error

        payload = response.json().get("data", [])
        models: list[ModelInfo] = []
        for item in payload:
            name = item.get("id", "")
            if not isinstance(name, str):
                continue
            if any(
                name.startswith(prefix) for prefix in _OPENROUTER_EXCLUDED_PREFIXES
            ):
                continue

            display_name = item.get("name")
            models.append(
                ModelInfo(
                    name=name,
                    provider=ProviderType.OPENROUTER,
                    display_name=(
                        display_name if isinstance(display_name, str) else None
                    ),
                    thinking_supported=_supports_thinking(
                        name,
                        item.get("supported_parameters"),
                    ),
                )
            )
        return models

    async def health_check(self) -> bool:
        """Return True when OpenRouter auth metadata can be fetched."""
        if self._test_mode:
            return True

        try:
            await self.get_credit_balance()
        except ModelRouterError:
            return False
        return True

    async def get_credit_balance(self) -> dict[str, Any]:
        """Fetch OpenRouter usage and credit metadata."""
        if self._test_mode:
            return {
                "usage": 0.0,
                "limit": 100.0,
                "is_free_tier": False,
            }

        try:
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                response = await http_client.get(
                    f"{self._config.base_url.rstrip('/')}/auth/key",
                    headers=_build_headers(self._config),
                )
                response.raise_for_status()
        except Exception as error:
            raise _map_openrouter_error(error) from error

        data = response.json().get("data", {})
        return {
            "usage": float(data.get("usage", 0.0) or 0.0),
            "limit": data.get("limit"),
            "is_free_tier": bool(data.get("is_free_tier", False)),
            "rate_limit": data.get("rate_limit", {}),
        }


class OpenRouterEmbeddingProvider(BaseEmbeddingProvider):
    """Embedding provider backed by OpenRouter's OpenAI-compatible embeddings API."""

    def __init__(self, config: OpenRouterConfig) -> None:
        self._config = config
        self._test_mode = _is_test_mode()

    def _build_test_vector(self, text: str) -> list[float]:
        """Create a deterministic 768-dimension vector for test mode."""
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:4], "big")
        return [
            ((seed + index + digest[index % len(digest)]) % 1000) / 1000.0
            for index in range(AURA_EMBEDDING_DIMENSIONS)
        ]

    async def _embed_raw(self, texts: list[str]) -> list[list[float]]:
        """Return raw embedding vectors for the provided texts."""
        if self._test_mode:
            return [self._build_test_vector(text) for text in texts]

        try:
            async with httpx.AsyncClient(timeout=60.0) as http_client:
                response = await http_client.post(
                    f"{self._config.base_url.rstrip('/')}/embeddings",
                    headers=_build_headers(self._config),
                    json={
                        "model": "openai/text-embedding-3-small",
                        "input": texts,
                        "dimensions": AURA_EMBEDDING_DIMENSIONS,
                    },
                )
                response.raise_for_status()
        except Exception as error:
            raise _map_openrouter_error(error) from error

        payload = response.json().get("data", [])
        vectors: list[list[float]] = []
        for item in sorted(payload, key=lambda x: x.get("index", 0)):
            embedding = item.get("embedding", [])
            vectors.append(list(embedding))

        if len(vectors) != len(texts):
            raise RuntimeError(f"Expected {len(texts)} embeddings, got {len(vectors)}")
        return vectors

    async def list_models(self) -> list[ModelInfo]:
        """Return OpenRouter embedding models."""
        if self._test_mode:
            return list(_EMBEDDING_TEST_MODELS)

        try:
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                # OpenRouter does not have a separate /models/embeddings endpoint.
                # All models are returned from /models.
                response = await http_client.get(
                    f"{self._config.base_url.rstrip('/')}/models",
                    headers=_build_headers(self._config),
                )
                response.raise_for_status()
        except Exception as error:
            raise _map_openrouter_error(error) from error

        payload = response.json().get("data", [])
        models: list[ModelInfo] = []
        for item in payload:
            name = item.get("id", "")
            if not isinstance(name, str):
                continue
            
            # Filter for models that start with our known embedding prefixes
            if not any(
                name.startswith(prefix) for prefix in _OPENROUTER_EMBEDDING_PREFIXES
            ):
                continue

            display_name = item.get("name")
            models.append(
                ModelInfo(
                    name=name,
                    provider=ProviderType.OPENROUTER,
                    display_name=(
                        display_name if isinstance(display_name, str) else None
                    ),
                    model_type="embedding",
                )
            )
        return models


__all__ = [
    "OpenRouterProvider",
    "OpenRouterEmbeddingProvider",
    "_map_openrouter_error",
]
