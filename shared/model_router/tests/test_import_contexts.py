"""Import verification for model_router across repo working directories."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _run_python(cwd: Path, code: str) -> subprocess.CompletedProcess[str]:
    """Run a small Python snippet from the requested working directory."""

    return subprocess.run(
        [sys.executable, '-c', code],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
        env=os.environ.copy(),
    )


def _assert_import_ok(cwd: Path, code: str, marker: str) -> None:
    """Assert a subprocess import check completed successfully."""

    result = _run_python(cwd, code)
    assert result.returncode == 0, result.stderr or result.stdout
    assert marker in result.stdout, result.stdout


def test_import_from_project_root() -> None:
    _assert_import_ok(
        REPO_ROOT,
        "from model_router import ModelRouter; print('OK')",
        'OK',
    )


def test_import_from_aura_chat() -> None:
    _assert_import_ok(
        REPO_ROOT / 'AURA-CHAT',
        "from model_router import ModelRouter; print('OK')",
        'OK',
    )


def test_import_from_aura_notes() -> None:
    _assert_import_ok(
        REPO_ROOT / 'AURA-NOTES-MANAGER',
        "from model_router import ModelRouter; print('OK')",
        'OK',
    )


def test_import_from_celery_worker_context() -> None:
    _assert_import_ok(
        REPO_ROOT / 'AURA-NOTES-MANAGER' / 'api',
        "from model_router import ModelRouter; print('OK')",
        'OK',
    )


def test_import_all_public_api() -> None:
    command = (
        'from model_router import '
        'AuthenticationError, BaseEmbeddingProvider, BaseProvider, '
        'ContentPolicyError, EmbeddingDimensionError, GeneralComputeConfig, '
        'GeneralComputeProvider, GenerateRequest, '
        'GenerateResponse, ModelInfo, ModelRouter, ModelRouterError, '
        'ModelUnavailableError, ProviderTimeoutError, ProviderType, '
        'RateLimitError, StreamChunk, UsageInfo, VertexCompatModel, '
        "get_default_router, reset_default_router; print('ALL OK')"
    )
    _assert_import_ok(REPO_ROOT, command, 'ALL OK')
