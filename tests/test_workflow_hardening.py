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


def _job_block(text: str, job_id: str, following: list[str]) -> str:
    marker = f"\n  {job_id}:\n"
    assert marker in text, job_id
    rest = text.split(marker, 1)[1]
    ends = [rest.find(f"\n  {name}:\n") for name in following]
    ends = [index for index in ends if index >= 0]
    if not ends:
        return rest
    return rest[: min(ends)]


def test_every_checkout_step_drops_credentials() -> None:
    for path in [*WORKFLOWS, TEMPLATE]:
        text = path.read_text(encoding="utf-8")
        steps = re.split(r"\n\s*- ", text)
        saw_checkout = False
        for step in steps:
            if "actions/checkout@" not in step:
                continue
            saw_checkout = True
            assert "persist-credentials: false" in step, path
        if "actions/checkout@" in text:
            assert saw_checkout, path


def test_read_only_jobs_set_contents_read() -> None:
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    test_job = _job_block(ci, "test", ["governance", "lowest-direct"])
    lowest = _job_block(ci, "lowest-direct", [])
    assert "permissions:\n      contents: read\n" in test_job
    assert "id-token:" not in test_job
    assert "pull-requests:" not in test_job
    assert "permissions:\n      contents: read\n" in lowest
    assert "id-token:" not in lowest

    publish = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    verify = _job_block(publish, "verify", ["package", "publish", "publish-testpypi"])
    package = _job_block(publish, "package", ["publish", "publish-testpypi"])
    assert "permissions:\n      contents: read\n" in verify
    assert "id-token:" not in verify
    assert "permissions:\n      contents: read\n" in package
    assert "id-token:" not in package


def test_publish_job_keeps_pypi_environment() -> None:
    text = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    publish = _job_block(text, "publish", ["publish-testpypi"])
    assert "name: pypi" in publish
    assert "id-token: write" in publish
    assert "attestations: write" in publish
    testpypi = _job_block(text, "publish-testpypi", [])
    assert "name: testpypi" in testpypi
    assert "id-token: write" in testpypi
    assert "name: pypi" not in testpypi


def test_dependabot_updates_github_actions_weekly() -> None:
    text = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    assert re.search(
        r"package-ecosystem:\s*github-actions\s+"
        r"directory:\s*/\s+"
        r"schedule:\s+"
        r"interval:\s*weekly\b",
        text,
    )
    assert re.search(
        r"package-ecosystem:\s*uv\s+"
        r"directory:\s*/\s+"
        r"schedule:\s+"
        r"interval:\s*weekly\b",
        text,
    )
    assert "package-ecosystem: pip" not in text


def _folded_scalar(lines: list[str], start: int) -> tuple[str, int]:
    """Join a YAML folded or literal block that begins on the next indented lines."""
    chunks: list[str] = []
    index = start
    while index < len(lines):
        row = lines[index]
        if row.strip() == "":
            if chunks:
                break
            index += 1
            continue
        if not row.startswith((" ", "\t")):
            break
        chunks.append(row.strip())
        index += 1
    return " ".join(chunks), index


def _action_marketplace_fields(text: str) -> dict[str, str]:
    """Read the action name, description, and branding without a YAML dependency."""
    lines = text.splitlines()
    fields = {"name": "", "description": "", "icon": "", "color": ""}
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line or line[0].isspace() or line.startswith("#"):
            index += 1
            continue
        key, _, rest = line.partition(":")
        value = rest.strip()
        if key == "name":
            fields["name"] = value.strip("\"'")
        elif key == "description":
            if value in {">", ">-", "|", "|-"}:
                folded, index = _folded_scalar(lines, index + 1)
                fields["description"] = folded
                continue
            fields["description"] = value.strip("\"'")
        elif key == "branding":
            index += 1
            while index < len(lines) and lines[index].startswith((" ", "\t")):
                stripped = lines[index].strip()
                brand_key, _, brand_rest = stripped.partition(":")
                brand_value = brand_rest.strip().strip("\"'")
                if brand_key in {"icon", "color"}:
                    fields[brand_key] = brand_value
                index += 1
            continue
        index += 1
    return fields


def test_action_marketplace_description_is_under_125_characters() -> None:
    fields = _action_marketplace_fields(ACTION.read_text(encoding="utf-8"))
    assert fields["name"] == "Retornatus"
    assert fields["icon"] == "check-circle"
    assert fields["color"] == "green"
    assert fields["description"]
    assert len(fields["description"]) < 125


def test_contributing_states_the_pin_rule() -> None:
    text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "full commit SHA" in text
    assert "contents: read" in text
    assert "persist-credentials: false" in text
    assert "pypi" in text


def test_changelog_unreleased_security_entry() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    unreleased = text.split("## [1.8.0]", 1)[0]
    assert "## [Unreleased]" in unreleased
    assert "### Security" in unreleased
    assert "contents: read" in unreleased
    assert "pypi" in unreleased
