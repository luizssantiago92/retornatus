"""Deterministic Host Execution boundary for construction dogfood tests.

Represents Environment-native Agent work without calling a real LLM.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class HostExecutionResult:
    """Observable result of a simulated native implementation."""

    artifacts: list[Path]
    test_passed: bool
    stdout: str
    subject_state: str


def simulate_health_endpoint_implementation(project_root: Path) -> HostExecutionResult:
    """
    Deterministic fixture: implement GET /health in a tiny app layout
    and a pytest module that validates it — without network or LLM.
    """
    project_root = project_root.resolve()
    app_dir = project_root / "app"
    tests_dir = project_root / "tests"
    docs_dir = project_root / "docs"
    app_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    app_py = app_dir / "main.py"
    app_py.write_text(
        '"""Minimal app with health endpoint (dogfood fixture)."""\n\n'
        "def health() -> tuple[dict, int]:\n"
        '    return {"status": "ok"}, 200\n',
        encoding="utf-8",
    )
    (app_dir / "__init__.py").write_text("", encoding="utf-8")

    test_py = tests_dir / "test_health.py"
    test_py.write_text(
        "from app.main import health\n\n"
        "def test_health_returns_ok() -> None:\n"
        "    body, status = health()\n"
        "    assert status == 200\n"
        '    assert body == {"status": "ok"}\n',
        encoding="utf-8",
    )

    doc = docs_dir / "health.md"
    doc.write_text(
        "# Health\n\n"
        '`GET /health` returns `200` and `{"status":"ok"}`.\n',
        encoding="utf-8",
    )

    # Deterministic in-process verification (Host execution boundary)
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from app.main import health  # type: ignore

    body, status = health()
    passed = status == 200 and body == {"status": "ok"}
    stdout = f"test_health_returns_ok {'PASSED' if passed else 'FAILED'}"

    return HostExecutionResult(
        artifacts=[app_py, test_py, doc],
        test_passed=passed,
        stdout=stdout,
        subject_state="passing" if passed else "failing",
    )
