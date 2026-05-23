"""
========================================================================
FILE: general_compute.py
LOCATION: shared/model_router/src/model_router/providers/general_compute.py
========================================================================

PURPOSE:
    General Compute generation provider for the shared model router package.

ROLE IN PROJECT:
    Implements test-mode behavior, OpenAI-compatible request translation,
    normalized streaming chunks, and model discovery without leaking SDK-specific
    types to callers.

KEY COMPONENTS:
    - GeneralComputeProvider: Provider implementation for General Compute.
    - _supports_thinking: Helper to check if model supports thinking.
    - _map_gc_error: Map HTTP and other errors to model router hierarchy.
    - _build_messages: Convert request contents to OpenAI format.
    - _coerce_text_value: Normalize text values.

DEPENDENCIES:
    - External: httpx
    - Internal: model_router.types, model_router.config, model_router.errors

USAGE:
    provider = GeneralComputeProvider(config)
    response = await provider.generate(request)
========================================================================
"""

from __future__ import annotations

import json
import os
from typing import Any, AsyncGenerator

import httpx

from model_router.config import GeneralComputeConfig
from model_router.errors import (
    AuthenticationError,
    ContentPolicyError,
    ModelRouterError,
    ModelUnavailableError,
    ProviderTimeoutError,
    RateLimitError,
)
from model_router.providers.base import BaseProvider
from model_router.types import (
    GenerateRequest,
    GenerateResponse,
    ModelInfo,
    ProviderType,
    StreamChunk,
    UsageInfo,
)


_GC_TEST_MODELS = [
    ModelInfo(
        name="minimax-m2.7",
        provider=ProviderType.GENERAL_COMPUTE,
        display_name="MiniMax M2.7",
        thinking_supported=False,
    ),
    ModelInfo(
        name="deepseek-v3.2",
        provider=ProviderType.GENERAL_COMPUTE,
        display_name="DeepSeek V3.2",
        thinking_supported=True,
    ),
    ModelInfo(
        name="deepseek-v3.1",
        provider=ProviderType.GENERAL_COMPUTE,
        display_name="DeepSeek V3.1",
        thinking_supported=True,
    ),
]


def _supports_thinking(model_name: str) -> bool:
    """Return True when a model supports or exposes reasoning output."""
    normalized = model_name.lower()
    return "deepseek" in normalized


def _is_test_mode() -> bool:
    """Return True when provider calls should avoid live General Compute access."""
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


def _map_gc_error(
    error: BaseException,
    *,
    model: str = "",
) -> ModelRouterError:
    """Map General Compute/httpx failures to the shared error hierarchy."""
    if isinstance(error, httpx.HTTPStatusError):
        status_code = error.response.status_code
        if status_code in (401, 403):
            return AuthenticationError(
                str(error),
                provider=ProviderType.GENERAL_COMPUTE.value,
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
                provider=ProviderType.GENERAL_COMPUTE.value,
                model=model,
                original=error,
                retry_after=retry_after,
            )

    return ModelRouterError(
        str(error),
        provider=ProviderType.GENERAL_COMPUTE.value,
        model=model,
        original=error,
    )


class GeneralComputeProvider(BaseProvider):
    """Generation provider backed by General Compute's OpenAI-compatible API."""

    def __init__(self, config: GeneralComputeConfig) -> None:
        self._config = config
        self._test_mode = _is_test_mode()

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Generate a normalized response for a General Compute request."""
        if self._test_mode:
            return GenerateResponse(
                text="Test-mode output.",
                model_used=request.model,
                provider=ProviderType.GENERAL_COMPUTE,
                usage=UsageInfo(),
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

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self._config.base_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {self._config.api_key}"},
                    json=kwargs,
                )
                response.raise_for_status()
        except Exception as error:
            raise _map_gc_error(error, model=request.model) from error

        data = response.json()
        choice = data["choices"][0]
        message = choice["message"]
        content = message.get("content") or ""
        reasoning = message.get("reasoning_content") or message.get("reasoning")
        usage = data.get("usage") or {}

        return GenerateResponse(
            text=_coerce_text_value(content),
            model_used=str(data.get("model") or request.model),
            provider=ProviderType.GENERAL_COMPUTE,
            usage=UsageInfo(
                input_tokens=int(usage.get("prompt_tokens") or 0),
                output_tokens=int(usage.get("completion_tokens") or 0),
                thinking_tokens=int(usage.get("reasoning_tokens") or 0),
            ),
            thinking_text=_coerce_text_value(reasoning) or None,
        )

    async def stream(
        self,
        request: GenerateRequest,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream normalized thinking/content chunks from General Compute."""
        if self._test_mode:
            yield StreamChunk(type="content", text="Test-mode stream output.")
            return

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

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self._config.base_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {self._config.api_key}"},
                    json=kwargs,
                ) as response:
                    response.raise_for_status()

                    buffer = ""
                    async for chunk in response.iter_text():
                        buffer += chunk
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if not line:
                                continue
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str == "[DONE]":
                                    break
                                try:
                                    chunk_data = json.loads(data_str)
                                except Exception:
                                    continue

                                if "choices" in chunk_data and chunk_data["choices"]:
                                    delta = chunk_data["choices"][0].get("delta", {})

                                    reasoning = delta.get("reasoning_content") or delta.get("reasoning")
                                    reasoning_text = _coerce_text_value(reasoning)
                                    if reasoning_text:
                                        yield StreamChunk(type="thinking", text=reasoning_text)

                                    content = delta.get("content")
                                    content_text = _coerce_text_value(content)
                                    if content_text:
                                        yield StreamChunk(type="content", text=content_text)

                                usage = chunk_data.get("usage")
                                if usage:
                                    yield StreamChunk(
                                        type="content",
                                        text="",
                                        usage=UsageInfo(
                                            input_tokens=int(usage.get("prompt_tokens") or 0),
                                            output_tokens=int(usage.get("completion_tokens") or 0),
                                            thinking_tokens=int(usage.get("reasoning_tokens") or 0),
                                        ),
                                    )
        except Exception as error:
            raise _map_gc_error(error, model=request.model) from error

    async def list_models(self) -> list[ModelInfo]:
        """Return models exposed by General Compute."""
        if self._test_mode:
            return list(_GC_TEST_MODELS)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self._config.base_url.rstrip('/')}/models/list",
                    headers={"Authorization": f"Bearer {self._config.api_key}"},
                )
                response.raise_for_status()
        except Exception as error:
            raise _map_gc_error(error) from error

        data = response.json()
        models: list[ModelInfo] = []
        items = data if isinstance(data, list) else data.get("data", [])
        for item in items:
            name = item.get("id", "")
            if not isinstance(name, str) or not name:
                continue
            models.append(
                ModelInfo(
                    name=name,
                    provider=ProviderType.GENERAL_COMPUTE,
                    display_name=item.get("name") if isinstance(item.get("name"), str) else None,
                    thinking_supported=_supports_thinking(name),
                )
            )
        return models

    async def health_check(self) -> bool:
        """Return True when the API key is valid."""
        if self._test_mode:
            return True
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self._config.base_url.rstrip('/')}/models/list",
                    headers={"Authorization": f"Bearer {self._config.api_key}"},
                )
                response.raise_for_status()
            return True
        except Exception:
            return False


__all__ = [
    "GeneralComputeProvider",
    "_map_gc_error",
]
