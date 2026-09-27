"""Publish preflight: tag/version match is workflow-side; changelog matching is pure."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "publish_preflight",
    Path(__file__).resolve().parents[1] / "scripts" / "publish_preflight.py",
)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def test_changelog_section_matches_version_not_unreleased() -> None:
    text = "## [Unreleased]\n\nnotes\n\n## [1.4.0] - 2026-01-01\n\nshipped\n"
    assert _MODULE.changelog_has_version(text, "1.4.0")
    assert not _MODULE.changelog_has_version(text, "1.3.0")
    assert _MODULE.changelog_has_version("## 1.2.1\n", "1.2.1")
    assert not _MODULE.changelog_has_version("## [1.4.0]\n", "1.4")
