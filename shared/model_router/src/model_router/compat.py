"""Compatibility adapters for legacy Vertex AI client call sites."""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any, TypeVar

T = TypeVar('T')

_GENERATION_CONFIG_FIELDS = (
    'temperature',
    'max_output_tokens',
    'response_mime_type',
)


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

    def __init__(self, text: str) -> None:
        self.content = _CompatContent(text)


class VertexCompatResponse:
    """Response object matching GenerativeModel.generate_content() shape."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.candidates = [_CompatCandidate(text)]


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
        return config_kwargs

    to_dict = getattr(generation_config, 'to_dict', None)
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
        self._model_name = model_name
        self.model_name = model_name
        self._router: Any | None = None

    def _get_router(self) -> Any:
        """Lazily resolve the shared router singleton."""

        if self._router is None:
            from model_router.router import get_default_router

            self._router = get_default_router()
        return self._router

    def generate_content(
        self,
        contents: Any,
        generation_config: Any | None = None,
        safety_settings: Any | None = None,
    ) -> VertexCompatResponse:
        """Generate content with the legacy sync response surface."""

        del safety_settings

        request_kwargs: dict[str, Any] = {
            'model': self._model_name,
            'contents': contents,
        }
        request_kwargs.update(_extract_generation_config(generation_config))

        response = _run_sync(self._get_router().generate(**request_kwargs))
        return VertexCompatResponse(response.text)
