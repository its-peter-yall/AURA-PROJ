# test_no_direct_imports.py
# Cross-app audit for forbidden provider SDK imports and worker import contexts.

# Verifies both AURA apps only use the shared model_router surface across app
# code and test files, and confirms the shared package remains importable from
# repo, app, Celery, and ARQ worker working-directory contexts.

# @see: shared/model_router/tests/test_import_contexts.py
# @note: Uses AST import inspection so string literals do not create false hits.

from __future__ import annotations

import ast
import os
import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_VENV_PYTHON = (
    REPO_ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
)
FORBIDDEN_PATTERNS = [
    r"from\s+vertexai",
    r"import\s+vertexai",
    r"from\s+google\.generativeai",
    r"import\s+google\.generativeai",
    r"from\s+google\.genai\s",
    r"import\s+google\.genai\b",
    r"from\s+google\s+import\s+genai",
    r"import\s+openai\b",
    r"from\s+openai\s",
    r"from\s+google\.cloud\s+import\s+aiplatform",
    r"from\s+google\.cloud\.aiplatform\b",
    r"import\s+google\.cloud\.aiplatform\b",
    r"from\s+vertexai\.language_models",
    r"from\s+google\.auth",
    r"import\s+google\.auth",
]
SCAN_DIRS = {
    "AURA-CHAT": ["AURA-CHAT/backend", "AURA-CHAT/server"],
    "AURA-NOTES-MANAGER": [
        "AURA-NOTES-MANAGER/api",
        "AURA-NOTES-MANAGER/services",
    ],
}
TEST_SCAN_DIRS = {
    "AURA-CHAT tests": [
        "AURA-CHAT/backend/tests",
        "AURA-CHAT/server/tests",
    ],
    "AURA-NOTES-MANAGER tests": ["AURA-NOTES-MANAGER/api/tests"],
}


def _iter_python_files(base_dirs: list[str]) -> list[Path]:
    files: list[Path] = []
    for base_dir in base_dirs:
        root = REPO_ROOT / base_dir
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            normalized = str(path).replace("\\", "/").lower()
            if "__pycache__" in normalized or normalized.endswith(".pyc"):
                continue
            files.append(path)
    return sorted(files)


def _build_import_candidates(node: ast.Import | ast.ImportFrom) -> list[str]:
    """Return normalized candidate strings for an import node."""
    if isinstance(node, ast.Import):
        return [f"import {alias.name}" for alias in node.names]

    module = node.module or ""
    return [f"from {module} import {alias.name}" for alias in node.names]


def _matches_forbidden_import(node: ast.Import | ast.ImportFrom) -> bool:
    """Return whether an import node matches a forbidden SDK pattern."""
    return any(
        re.search(pattern, candidate)
        for candidate in _build_import_candidates(node)
        for pattern in FORBIDDEN_PATTERNS
    )


def _find_violations_for_dirs(label: str, base_dirs: list[str]) -> list[str]:
    del label
    violations: list[str] = []
    for path in _iter_python_files(base_dirs):
        source = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source, filename=str(path))
        lines = source.splitlines()
        imports = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        for node in imports:
            if _matches_forbidden_import(node):
                relative_path = path.relative_to(REPO_ROOT)
                import_line = lines[node.lineno - 1].strip()
                violations.append(f"{relative_path}:{node.lineno}: {import_line}")
    return violations


def _parse_single_import(source: str) -> ast.Import | ast.ImportFrom:
    """Parse a source snippet and return its single import node."""
    tree = ast.parse(source)
    node = tree.body[0]
    assert isinstance(node, (ast.Import, ast.ImportFrom))
    return node


def test_matches_forbidden_from_import_member() -> None:
    node = _parse_single_import("from google import genai as google_genai")

    assert _matches_forbidden_import(node) is True


def test_matches_forbidden_module_import() -> None:
    node = _parse_single_import("import google.genai as google_genai")

    assert _matches_forbidden_import(node) is True


def _find_violations(app_name: str) -> list[str]:
    return _find_violations_for_dirs(app_name, SCAN_DIRS[app_name])


def _run_python(cwd: Path, code: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["AURA_TEST_MODE"] = "true"
    return subprocess.run(
        [str(ROOT_VENV_PYTHON), "-c", code],
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


def test_no_direct_sdk_imports_chat_tests() -> None:
    violations = _find_violations_for_dirs(
        "AURA-CHAT tests",
        TEST_SCAN_DIRS["AURA-CHAT tests"],
    )
    assert violations == [], "\n".join(violations)


def test_no_direct_sdk_imports_notes_tests() -> None:
    violations = _find_violations_for_dirs(
        "AURA-NOTES-MANAGER tests",
        TEST_SCAN_DIRS["AURA-NOTES-MANAGER tests"],
    )
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


def test_arq_worker_import_context() -> None:
    """Verify AURA-CHAT ARQ worker can reach model_router-backed services."""
    arq_code = (
        "import sys; "
        "from pathlib import Path; "
        "sys.path.insert(0, str(Path.cwd())); "
        "from backend.tasks.worker import WorkerSettings; "
        "from backend.utils.vertex_ai_client import get_model; "
        "from backend.utils.embeddings import EmbeddingService; "
        'print("ARQ_OK")'
    )
    _assert_import_ok(
        REPO_ROOT / "AURA-CHAT",
        arq_code,
        "ARQ_OK",
    )
