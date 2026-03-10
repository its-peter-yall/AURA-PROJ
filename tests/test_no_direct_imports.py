# test_no_direct_imports.py
# Cross-app audit for forbidden provider SDK imports and import contexts.

# Verifies both AURA apps only use the shared model_router surface in
# non-test Python modules, and confirms the shared package remains importable
# from repo, app, and Celery worker working-directory contexts.

# @see: shared/model_router/tests/test_import_contexts.py
# @note: Uses AST import inspection so string literals do not create false hits.

from __future__ import annotations

import os
import ast
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PATTERNS = [
    r"from\s+vertexai",
    r"import\s+vertexai",
    r"from\s+google\.generativeai",
    r"import\s+google\.generativeai",
    r"from\s+google\.genai\s",
    r"from\s+google\s+import\s+genai",
    r"import\s+openai\b",
    r"from\s+openai\s",
    r"from\s+google\.cloud\s+import\s+aiplatform",
    r"from\s+vertexai\.language_models",
    r"from\s+google\.auth",
    r"import\s+google\.auth",
]
SCAN_DIRS = {
    "AURA-CHAT": ["AURA-CHAT/backend", "AURA-CHAT/server"],
    "AURA-NOTES-MANAGER": ["AURA-NOTES-MANAGER/api", "AURA-NOTES-MANAGER/services"],
}


def _iter_python_files(base_dirs: list[str]) -> list[Path]:
    files: list[Path] = []
    for base_dir in base_dirs:
        for path in (REPO_ROOT / base_dir).rglob("*.py"):
            normalized = str(path).replace("\\", "/").lower()
            if "test" in path.name.lower():
                continue
            if "__pycache__" in normalized or normalized.endswith(".pyc"):
                continue
            files.append(path)
    return sorted(files)


def _find_violations(app_name: str) -> list[str]:
    violations: list[str] = []
    for path in _iter_python_files(SCAN_DIRS[app_name]):
        source = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source, filename=str(path))
        lines = source.splitlines()
        imports = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        for node in imports:
            matched = False
            if isinstance(node, ast.Import):
                for alias in node.names:
                    candidate = f"import {alias.name}"
                    if any(
                        re.search(pattern, candidate) for pattern in FORBIDDEN_PATTERNS
                    ):
                        matched = True
                        break
            else:
                module = node.module or ""
                candidate = f"from {module} import sentinel"
                matched = any(
                    re.search(pattern, candidate) for pattern in FORBIDDEN_PATTERNS
                )

            if matched:
                relative_path = path.relative_to(REPO_ROOT)
                import_line = lines[node.lineno - 1].strip()
                violations.append(f"{relative_path}:{node.lineno}: {import_line}")
    return violations


def _run_python(cwd: Path, code: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["AURA_TEST_MODE"] = "true"
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
        env=env,
    )


def _assert_import_ok(cwd: Path, code: str, marker: str) -> None:
    result = _run_python(cwd, code)
    assert result.returncode == 0, result.stderr or result.stdout
    assert marker in result.stdout, result.stdout


def test_no_direct_sdk_imports_aura_chat() -> None:
    violations = _find_violations("AURA-CHAT")
    assert violations == [], "\n".join(violations)


def test_no_direct_sdk_imports_aura_notes() -> None:
    violations = _find_violations("AURA-NOTES-MANAGER")
    assert violations == [], "\n".join(violations)


def test_model_router_importable_from_repo_root() -> None:
    _assert_import_ok(
        REPO_ROOT,
        'from model_router import get_default_router; print("OK")',
        "OK",
    )


def test_model_router_importable_from_chat_dir() -> None:
    _assert_import_ok(
        REPO_ROOT / "AURA-CHAT",
        'from model_router import get_default_router; print("OK")',
        "OK",
    )


def test_model_router_importable_from_notes_dir() -> None:
    _assert_import_ok(
        REPO_ROOT / "AURA-NOTES-MANAGER",
        'from model_router import get_default_router; print("OK")',
        "OK",
    )


def test_celery_worker_import_context() -> None:
    celery_code = (
        "import sys; "
        "from pathlib import Path; "
        "notes_root = Path.cwd().parent; "
        "sys.path.insert(0, str(notes_root)); "
        "from model_router import get_default_router; "
        "print(type(get_default_router()).__name__)"
    )
    _assert_import_ok(
        REPO_ROOT / "AURA-NOTES-MANAGER" / "api",
        celery_code,
        "ModelRouter",
    )
