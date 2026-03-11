# test_compat.py
# Tests for VertexCompatModel and legacy app shims.

# Exercises the sync and async compatibility surface exposed to legacy
# call-sites in AURA-CHAT and AURA-NOTES, including request translation,
# stream bridging, and graceful shim fallback behavior.

# @see: model_router/compat.py - Legacy Vertex compatibility layer
# @note: App shim tests import the real nested-repo modules with patched roots.

"""Tests for VertexCompatModel and legacy app shims."""

from __future__ import annotations

import builtins
import importlib
import sys
from pathlib import Path
from typing import Any, NamedTuple

import pytest

from model_router.compat import VertexCompatModel, _run_sync
from model_router.router import reset_default_router
from model_router.types import GenerateResponse, ProviderType, StreamChunk, UsageInfo

REPO_ROOT = Path(__file__).resolve().parents[3]


class ShimContext(NamedTuple):
    """Describe one legacy app module that should receive the compat shim."""

    module_name: str
    module_root: Path
    legacy_factory_name: str
    needs_init: bool = False


SHIM_CONTEXTS = (
    ShimContext(
        module_name="backend.utils.vertex_ai_client",
        module_root=REPO_ROOT / "AURA-CHAT",
        legacy_factory_name="_GenerativeModelWrapper",
    ),
    ShimContext(
        module_name="services.vertex_ai_client",
        module_root=REPO_ROOT / "AURA-NOTES-MANAGER",
        legacy_factory_name="GenerativeModel",
        needs_init=True,
    ),
)


class FakeGenerationConfig:
    """Simple config object mirroring legacy GenerationConfig attributes."""

    def __init__(self) -> None:
        self.temperature = 0.25
        self.top_p = 0.95
        self.max_output_tokens = 128
        self.response_mime_type = "application/json"
        self.thinking_budget = 64


class RecordingRouter:
    """Async fake router used to capture compat-layer calls."""

    def __init__(
        self,
        *,
        response: GenerateResponse | None = None,
        stream_chunks: list[StreamChunk] | None = None,
    ) -> None:
        self.calls: list[dict[str, Any]] = []
        self.stream_calls: list[dict[str, Any]] = []
        self._response = response or GenerateResponse(
            text="compat-router output",
            model_used="gemini-2.0-flash",
            provider=ProviderType.VERTEX_AI,
            usage=UsageInfo(),
        )
        self._stream_chunks = stream_chunks or [
            StreamChunk(type="content", text="compat-router output")
        ]

    async def generate(self, **kwargs: Any) -> GenerateResponse:
        self.calls.append(kwargs)
        return self._response.model_copy(update={"model_used": str(kwargs["model"])})

    async def stream(self, **kwargs: Any):
        self.stream_calls.append(kwargs)
        for chunk in self._stream_chunks:
            yield chunk


@pytest.fixture(autouse=True)
def reset_router_singleton() -> None:
    """Keep the shared router singleton isolated between tests."""

    reset_default_router()
    yield
    reset_default_router()


def _import_app_module(
    monkeypatch: pytest.MonkeyPatch,
    context: ShimContext,
):
    """Import an app module after prepending its repo root to sys.path."""

    monkeypatch.syspath_prepend(str(context.module_root))
    sys.modules.pop(context.module_name, None)
    return importlib.import_module(context.module_name)


def _patch_legacy_path(
    monkeypatch: pytest.MonkeyPatch,
    module: Any,
    context: ShimContext,
    *,
    result: object | None = None,
    should_raise: bool = False,
) -> None:
    """Patch the original get_model path so shim behavior can be asserted."""

    def _legacy_factory(*args: Any, **kwargs: Any) -> object:
        if should_raise:
            raise AssertionError("legacy code path should not run")
        return result

    monkeypatch.setattr(
        module,
        "normalize_model_name",
        lambda name: f"norm::{name}",
    )
    monkeypatch.setattr(module, context.legacy_factory_name, _legacy_factory)
    if not context.needs_init:
        return

    def _init_vertex_ai(*args: Any, **kwargs: Any) -> None:
        if should_raise:
            raise AssertionError("legacy init should not run")

    monkeypatch.setattr(module, "init_vertex_ai", _init_vertex_ai)


def test_compat_model_generate_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AURA_TEST_MODE", "true")
    model = VertexCompatModel("gemini-2.0-flash")

    response = model.generate_content("hello")

    assert response.text == "Test-mode output."
    assert response.candidates[0].content.parts[0].text == "Test-mode output."


def test_compat_model_with_generation_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import model_router.router as router_module

    router = RecordingRouter()
    monkeypatch.setattr(router_module, "get_default_router", lambda: router)
    model = VertexCompatModel("gemini-2.0-flash")

    response = model.generate_content(
        "hello",
        generation_config=FakeGenerationConfig(),
    )

    assert response.text == "compat-router output"
    assert router.calls == [
        {
            "model": "gemini-2.0-flash",
            "contents": "hello",
            "temperature": 0.25,
            "top_p": 0.95,
            "max_output_tokens": 128,
            "response_mime_type": "application/json",
            "thinking_config": {
                "thinking_budget": 64,
                "include_thoughts": True,
            },
        }
    ]


def test_compat_model_normalizes_models_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import model_router.router as router_module

    router = RecordingRouter()
    monkeypatch.setattr(router_module, "get_default_router", lambda: router)
    model = VertexCompatModel("models/gemini-2.5-pro")

    response = model.generate_content("hello")

    assert response.text == "compat-router output"
    assert router.calls[0]["model"] == "gemini-2.5-pro"


def test_compat_model_forwards_system_instruction_and_safety_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from vertexai.generative_models import (
        HarmBlockThreshold,
        HarmCategory,
        SafetySetting,
    )
    import model_router.router as router_module

    router = RecordingRouter()
    monkeypatch.setattr(router_module, "get_default_router", lambda: router)
    model = VertexCompatModel("gemini-2.0-flash")
    safety_settings = [
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        )
    ]

    model.generate_content(
        "hello",
        generation_config=FakeGenerationConfig(),
        safety_settings=safety_settings,
        system_instruction="reply with json",
    )

    assert router.calls == [
        {
            "model": "gemini-2.0-flash",
            "contents": "hello",
            "temperature": 0.25,
            "top_p": 0.95,
            "max_output_tokens": 128,
            "response_mime_type": "application/json",
            "thinking_config": {
                "thinking_budget": 64,
                "include_thoughts": True,
            },
            "system_instruction": "reply with json",
            "safety_settings": safety_settings,
        }
    ]


def test_compat_model_response_has_text_attr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AURA_TEST_MODE", "true")
    model = VertexCompatModel("gemini-2.0-flash")

    response = model.generate_content("hello")

    assert hasattr(response, "text")
    assert response.text == response.candidates[0].content.parts[0].text


def test_compat_model_test_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AURA_TEST_MODE", "true")
    model = VertexCompatModel("gemini-2.5-flash")

    response = model.generate_content("hello")

    assert response.text == "Test-mode output."


def test_compat_response_exposes_finish_reason_and_prompt_feedback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import model_router.router as router_module

    router = RecordingRouter(
        response=GenerateResponse(
            text="",
            model_used="gemini-2.0-flash",
            provider=ProviderType.VERTEX_AI,
            usage=UsageInfo(),
            metadata={
                "finish_reason": 1,
                "prompt_feedback_block_reason": "SAFETY",
            },
        )
    )
    monkeypatch.setattr(router_module, "get_default_router", lambda: router)
    model = VertexCompatModel("gemini-2.0-flash")

    response = model.generate_content("hello")

    assert response.candidates[0].finish_reason == 1
    assert response.prompt_feedback.block_reason == "SAFETY"


@pytest.mark.asyncio
async def test_run_sync_handles_running_loop() -> None:
    async def _sample() -> str:
        return "loop-output"

    assert _run_sync(_sample()) == "loop-output"


@pytest.mark.asyncio
async def test_generate_content_async_returns_compat_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import model_router.router as router_module

    router = RecordingRouter()
    monkeypatch.setattr(router_module, "get_default_router", lambda: router)
    model = VertexCompatModel("gemini-2.0-flash")

    response = await model.generate_content_async(
        "hello",
        generation_config={
            "max_output_tokens": 64,
            "thinking_level": "HIGH",
        },
        system_instruction="be concise",
    )

    assert response.text == "compat-router output"
    assert router.calls == [
        {
            "model": "gemini-2.0-flash",
            "contents": "hello",
            "max_output_tokens": 64,
            "thinking_config": {
                "thinking_level": "HIGH",
                "include_thoughts": True,
            },
            "system_instruction": "be concise",
        }
    ]


@pytest.mark.asyncio
async def test_generate_content_async_stream_filters_thinking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import model_router.router as router_module

    router = RecordingRouter(
        stream_chunks=[
            StreamChunk(type="thinking", text="internal"),
            StreamChunk(type="content", text="hello "),
            StreamChunk(type="content", text="world"),
        ]
    )
    monkeypatch.setattr(router_module, "get_default_router", lambda: router)
    model = VertexCompatModel("gemini-2.0-flash")

    response = await model.generate_content_async(
        "hello",
        generation_config={"thinking_budget": 128},
        system_instruction="be friendly",
        stream=True,
    )
    chunks = [chunk.text async for chunk in response]

    assert chunks == ["hello ", "world"]
    assert router.stream_calls == [
        {
            "model": "gemini-2.0-flash",
            "contents": "hello",
            "thinking_config": {
                "thinking_budget": 128,
                "include_thoughts": True,
            },
            "system_instruction": "be friendly",
        }
    ]


@pytest.mark.parametrize("context", SHIM_CONTEXTS)
def test_shim_disabled_by_default(
    monkeypatch: pytest.MonkeyPatch,
    context: ShimContext,
) -> None:
    monkeypatch.setenv("AURA_TEST_MODE", "false")
    monkeypatch.delenv("USE_MODEL_ROUTER", raising=False)
    module = _import_app_module(monkeypatch, context)
    sentinel = object()
    _patch_legacy_path(monkeypatch, module, context, result=sentinel)

    result = module.get_model("gemini-test")

    assert result is sentinel


@pytest.mark.parametrize("context", SHIM_CONTEXTS)
def test_shim_enabled_returns_compat_model(
    monkeypatch: pytest.MonkeyPatch,
    context: ShimContext,
) -> None:
    import model_router.compat as compat_module

    monkeypatch.setenv("AURA_TEST_MODE", "false")
    monkeypatch.setenv("USE_MODEL_ROUTER", "true")
    module = _import_app_module(monkeypatch, context)
    sentinel = object()
    _patch_legacy_path(
        monkeypatch,
        module,
        context,
        should_raise=True,
    )
    monkeypatch.setattr(compat_module, "VertexCompatModel", lambda name: sentinel)

    result = module.get_model("gemini-test")

    assert result is sentinel


@pytest.mark.parametrize("context", SHIM_CONTEXTS)
def test_shim_import_failure_fallback(
    monkeypatch: pytest.MonkeyPatch,
    context: ShimContext,
) -> None:
    monkeypatch.setenv("AURA_TEST_MODE", "false")
    monkeypatch.setenv("USE_MODEL_ROUTER", "true")
    module = _import_app_module(monkeypatch, context)
    sentinel = object()
    _patch_legacy_path(monkeypatch, module, context, result=sentinel)

    original_import = builtins.__import__
    import_attempted = {"value": False}

    def _import_with_failure(
        name: str,
        globals_dict: dict[str, Any] | None = None,
        locals_dict: dict[str, Any] | None = None,
        fromlist: Any = (),
        level: int = 0,
    ) -> Any:
        if name == "model_router.compat":
            import_attempted["value"] = True
            raise ImportError("forced compat import failure")
        return original_import(name, globals_dict, locals_dict, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _import_with_failure)

    result = module.get_model("gemini-test")

    assert import_attempted["value"] is True
    assert result is sentinel
