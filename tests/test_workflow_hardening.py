"""Workflow files stay SHA-pinned and least-privilege."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
TEMPLATE = ROOT / "templates" / "ci" / "retornatus-pr.yml"
ACTION = ROOT / "action.yml"
USES = re.compile(r"^\s*(?:-\s*)?uses:\s+(\S+)", re.MULTILINE)
PINNED = re.compile(r"^[A-Za-z0-9_.-]+/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+@[0-9a-f]{40}$")
# This repository's own action is the product interface (local dogfood or the v1 tag).
SELF_ACTION = re.compile(r"^(?:\./|luizssantiago92/retornatus@v1)$")


def test_actions_are_pinned_to_commit_shas() -> None:
    paths = [*WORKFLOWS, TEMPLATE, ACTION]
    assert paths
    for path in paths:
        text = path.read_text(encoding="utf-8")
        uses = USES.findall(text)
        assert uses, path
        for ref in uses:
            if SELF_ACTION.fullmatch(ref):
                continue
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


def test_ci_governance_job_runs_local_gates() -> None:
    text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "name: Retornatus gates" in text
    assert "uv run retornatus doctor" in text
    assert "uv run retornatus wake" in text
    assert "uv run retornatus ops run gate-scan" in text
    assert "uses: ./" in text
    assert "version: local" in text
    assert "pull-requests: write" in text
    assert "uv tool install" not in text
    assert "fetch-depth: 0" in text
    script = (ROOT / "scripts" / "github_action.sh").read_text(encoding="utf-8")
    assert "gate suppressions" in script
    assert 'retornatus verify "$cid"' in script or "retornatus verify" in script
    assert "gate scope" in script
    assert "ci comment" in script
    assert "retornatus-verdict" in script


def test_action_passes_untrusted_input_through_the_environment() -> None:
    text = (ROOT / "action.yml").read_text(encoding="utf-8")
    run_lines = [line for line in text.splitlines() if line.strip().startswith("run:")]
    assert run_lines
    for line in run_lines:
        assert "${{" not in line
    assert "GH_TOKEN: ${{ inputs.github-token }}" in text
    script = (ROOT / "scripts" / "github_action.sh").read_text(encoding="utf-8")
    assert "${{" not in script
    assert "printenv" not in script
    assert "set -x" not in script


def test_publish_workflow_disables_uv_cache() -> None:
    text = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    assert "enable-cache: true" not in text
    assert text.count("enable-cache: false") == 2
