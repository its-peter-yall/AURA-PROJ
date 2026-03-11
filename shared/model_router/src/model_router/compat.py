# compat.py
# Compatibility adapters for legacy Vertex AI client call sites.

# Preserves the synchronous and asynchronous surface expected by existing
# AURA-CHAT and AURA-NOTES code while routing requests through the shared
# ModelRouter package.

# @see: model_router/router.py - Shared request routing entrypoint
# @note: Only content chunks are exposed from async streaming for legacy parity.

"""Compatibility adapters for legacy Vertex AI client call sites."""

from __future__ import annotations

import asyncio
import concurrent.futures
from types import SimpleNamespace
from typing import Any, TypeVar

from model_router.providers.vertex_ai import _normalize_vertex_model_name

T = TypeVar("T")

_GENERATION_CONFIG_FIELDS = (
    "temperature",
    "top_p",
    "max_output_tokens",
    "response_mime_type",
    "thinking_budget",
    "thinking_level",
)


def _build_thinking_config_from_config(
    generation_config: Any | None,
) -> dict[str, Any]:
    """Translate legacy generation config thinking fields into router kwargs."""
    if generation_config is None:
        return {}

    thinking_config: dict[str, Any] = {}
    thinking_budget = getattr(generation_config, "thinking_budget", None)
    thinking_level = getattr(generation_config, "thinking_level", None)

    if isinstance(generation_config, dict):
        if thinking_budget is None:
            thinking_budget = generation_config.get("thinking_budget")
        if thinking_level is None:
            thinking_level = generation_config.get("thinking_level")

    if thinking_budget is not None:
        thinking_config["thinking_budget"] = thinking_budget
    if thinking_level is not None:
        thinking_config["thinking_level"] = thinking_level
    if thinking_config:
        thinking_config["include_thoughts"] = True
    return thinking_config


class _CompatPart:
    """Compatibility wrapper for response parts."""

    def __init__(self, text: str) -> None:
        self.text = text


class _CompatContent:
    """Compatibility wrapper for candidate content."""

    def __init__(self, text: str) -> None:
        self.parts = [_CompatPart(text)]


class _CompatCandidate:
    """Compatibility wrapper for response candidates."""

    def __init__(self, text: str, finish_reason: Any | None = None) -> None:
        self.content = _CompatContent(text)
        self.finish_reason = finish_reason


class VertexCompatResponse:
    """Response object matching GenerativeModel.generate_content() shape."""

    def __init__(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        metadata = metadata or {}
        self.text = text
        self.candidates = [
            _CompatCandidate(text, finish_reason=metadata.get("finish_reason"))
        ]
        block_reason = metadata.get("prompt_feedback_block_reason")
        self.prompt_feedback = (
            SimpleNamespace(block_reason=block_reason)
            if block_reason is not None
            else None
        )


class _CompatAsyncContentStream:
    """Async iterator that exposes only legacy text chunks."""

    def __init__(self, stream: Any) -> None:
        self._stream = stream.__aiter__()

    def __aiter__(self) -> "_CompatAsyncContentStream":
        return self

    async def __anext__(self) -> VertexCompatResponse:
        while True:
            chunk = await self._stream.__anext__()
            if getattr(chunk, "type", None) != "content":
                continue
            return VertexCompatResponse(getattr(chunk, "text", ""))


def _extract_generation_config(
    generation_config: Any | None,
) -> dict[str, Any]:
    """Normalize legacy GenerationConfig input into router kwargs."""

    if generation_config is None:
        return {}

    config_kwargs: dict[str, Any] = {}
    if isinstance(generation_config, dict):
        for field_name in _GENERATION_CONFIG_FIELDS:
            value = generation_config.get(field_name)
            if value is not None:
                config_kwargs[field_name] = value
    else:
        to_dict = getattr(generation_config, "to_dict", None)
        if callable(to_dict):
            try:
                raw_config = to_dict()
            except Exception:
                raw_config = None
            if isinstance(raw_config, dict):
                for field_name in _GENERATION_CONFIG_FIELDS:
                    value = raw_config.get(field_name)
                    if value is not None:
                        config_kwargs[field_name] = value

        for field_name in _GENERATION_CONFIG_FIELDS:
            if field_name in config_kwargs:
                continue
            value = getattr(generation_config, field_name, None)
            if value is not None:
                config_kwargs[field_name] = value

    thinking_config = _build_thinking_config_from_config(generation_config)
    if thinking_config:
        config_kwargs["thinking_config"] = thinking_config
    config_kwargs.pop("thinking_budget", None)
    config_kwargs.pop("thinking_level", None)
    return config_kwargs


def _run_sync(coro: Any) -> T:
    """Run an async router coroutine from sync legacy call sites."""

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


class VertexCompatModel:
    """Legacy-looking model wrapper backed by the shared ModelRouter."""

    def __init__(self, model_name: str) -> None:
        normalized_model = _normalize_vertex_model_name(model_name)
        self._model_name = normalized_model
        self.model_name = normalized_model
        self._router: Any | None = None

    def _get_router(self) -> Any:
        """Lazily resolve the shared router singleton."""

        if self._router is None:
            from model_router.router import get_default_router

            self._router = get_default_router()
        return self._router

    def _build_request_kwargs(
        self,
        contents: Any,
        generation_config: Any | None,
        safety_settings: Any | None,
        system_instruction: str | None,
    ) -> dict[str, Any]:
        """Build normalized router kwargs from legacy parameters."""
        request_kwargs: dict[str, Any] = {
            "model": self._model_name,
            "contents": contents,
        }
        request_kwargs.update(_extract_generation_config(generation_config))
        if safety_settings is not None:
            request_kwargs["safety_settings"] = safety_settings
        if system_instruction is not None:
            request_kwargs["system_instruction"] = system_instruction
        return request_kwargs

    def generate_content(
        self,
        contents: Any,
        generation_config: Any | None = None,
        safety_settings: Any | None = None,
        system_instruction: str | None = None,
    ) -> VertexCompatResponse:
        """Generate content with the legacy sync response surface."""

        request_kwargs = self._build_request_kwargs(
            contents,
            generation_config,
            safety_settings,
            system_instruction,
        )
        response = _run_sync(self._get_router().generate(**request_kwargs))
        return VertexCompatResponse(response.text, metadata=response.metadata)

    async def generate_content_async(
        self,
        contents: Any,
        generation_config: Any | None = None,
        safety_settings: Any | None = None,
        system_instruction: str | None = None,
        stream: bool = False,
    ) -> Any:
        """Generate content with an async interface for legacy async call sites."""

        request_kwargs = self._build_request_kwargs(
            contents,
            generation_config,
            safety_settings,
            system_instruction,
        )
        if stream:
            return _CompatAsyncContentStream(
                self._get_router().stream(**request_kwargs)
            )

        response = await self._get_router().generate(**request_kwargs)
        return VertexCompatResponse(response.text, metadata=response.metadata)
