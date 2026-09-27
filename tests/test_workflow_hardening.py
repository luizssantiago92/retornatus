"""Workflow files stay SHA-pinned and least-privilege."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
TEMPLATE = ROOT / "templates" / "ci" / "retornatus-pr.yml"
USES = re.compile(r"^\s*uses:\s+(\S+)", re.MULTILINE)
PINNED = re.compile(r"^[A-Za-z0-9_.-]+/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+@[0-9a-f]{40}$")


def test_actions_are_pinned_to_commit_shas() -> None:
    paths = [*WORKFLOWS, TEMPLATE]
    assert paths
    for path in paths:
        text = path.read_text(encoding="utf-8")
        uses = USES.findall(text)
        assert uses, path
        for ref in uses:
            assert PINNED.fullmatch(ref), f"{path}: {ref}"
            line = next(row for row in text.splitlines() if ref in row)
            assert "#" in line, f"{path}: missing version comment for {ref}"


def test_workflows_default_to_contents_read() -> None:
    for path in [*WORKFLOWS, TEMPLATE]:
        text = path.read_text(encoding="utf-8")
        assert re.search(r"(?m)^permissions:\n  contents: read\n", text), path


def test_checkout_does_not_persist_credentials() -> None:
    for path in [*WORKFLOWS, TEMPLATE]:
        text = path.read_text(encoding="utf-8")
        if "actions/checkout@" not in text:
            continue
        assert "persist-credentials: false" in text, path


def test_publish_workflow_disables_uv_cache() -> None:
    text = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    assert "enable-cache: true" not in text
    assert text.count("enable-cache: false") == 2
