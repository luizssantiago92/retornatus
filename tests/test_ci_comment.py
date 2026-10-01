"""Sticky PR comment rendering from verify and gate JSON."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from retornatus.application.report.comment import (
    MARKER,
    MAX_COMMENT_CHARS,
    combined_verdict,
    render_ci_comment,
)
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app

runner = CliRunner()
ROOT = Path(__file__).resolve().parents[1]


def _verify(verdict: str, status: str, evidence_id: str | None = "C-0001/E-001") -> dict:
    evidence = []
    if evidence_id is not None:
        evidence.append(
            {
                "id": evidence_id,
                "type": "test_result",
                "subject": "pytest exits 0",
                "provenance": "executed",
                "exit_code": 0,
                "git_commit": None,
            }
        )
    return {
        "schema_version": 1,
        "command": "verify",
        "exit_code": 0 if verdict == "SATISFIED" else 1,
        "verdict": verdict,
        "change_id": "C-0001",
        "rationale": "All claims have matching attributable evidence"
        if verdict == "SATISFIED"
        else "Unmet claims: C-0001/claim-done-1",
        "claims": [
            {
                "id": "C-0001/claim-done-1",
                "subject": "pytest exits 0",
                "statement": "pytest exits 0 for the health command",
                "status": status,
                "required_evidence_types": ["test_result"],
                "evidence": evidence,
            }
        ],
    }


def _gate(name: str, *, passed: bool, change_id: str | None = None, errors: list[str] | None = None) -> dict:
    return {
        "schema_version": 1,
        "command": "gate",
        "exit_code": 0 if passed else 1,
        "verdict": "PASS" if passed else "FAIL",
        "passed": passed,
        "gate": name,
        "change_id": change_id,
        "findings": errors or (["Scope OK (1 path(s))"] if passed else []),
        "errors": [] if passed else (errors or ["scope failed"]),
        "warnings": [],
    }


def test_comment_satisfied_lists_claim_status_and_evidence() -> None:
    body, verdict = render_ci_comment(
        verify_documents=[_verify("SATISFIED", "SATISFIED")],
        gate_documents=[_gate("suppressions", passed=True), _gate("scope", passed=True, change_id="C-0001")],
        overview_markdown=["## C-0001 — Health\n\n**Assurance:** SATISFIED"],
    )
    assert verdict == "SATISFIED"
    assert body.startswith(MARKER + "\n")
    assert "**SATISFIED** — 1/1 claim satisfied, 2/2 gates passed." in body
    assert "change overview --format pr" in body
    assert "## C-0001 — Health" in body
    assert "C-0001/claim-done-1" in body
    assert "SATISFIED" in body
    assert "`C-0001/E-001`" in body
    assert "| suppressions | — | PASS |" in body
    assert "| scope | C-0001 | PASS |" in body


def test_comment_drops_overview_gates_and_collapses_warnings() -> None:
    document = _verify("SATISFIED", "SATISFIED")
    document["warnings"] = [
        "C-0001/E-001 recorded git_commit abc does not match HEAD def (stale snapshot; not a failure)",
        "C-0001/E-002 recorded git_commit abc does not match HEAD def (stale snapshot; not a failure)",
    ]
    document["evidence_labels"] = ["C-0001/E-001 type=test_result provenance=executed exit_code=0 status=executed"]
    overview = "\n".join(
        [
            "## C-0001 — Health",
            "",
            "**Assurance:** SATISFIED",
            "",
            "### Gates",
            "",
            "- **assurance** — pass — Verdict=SATISFIED: every claim and eight WARN lines",
            "- **scope** — pass — No changed paths",
            "",
            "### Next",
            "",
            "`retornatus loop next C-0001`",
        ]
    )
    body, verdict = render_ci_comment(
        verify_documents=[document],
        gate_documents=[
            _gate("scope", passed=True, change_id="C-0001"),
        ],
        overview_markdown=[overview],
    )
    assert verdict == "SATISFIED"
    assert "**Assurance:** SATISFIED" in body
    assert "### Next" in body
    assert "No changed paths" not in body
    assert "### Gates" not in body
    assert "Scope OK (1 path(s))" in body
    verify = body.split("### Verify", 1)[1].split("<details>", 1)[0]
    assert "stale snapshot" not in verify
    assert "every claim and eight WARN" not in body
    assert "<details>" in body
    assert "</details>" in body
    assert "2 evidence snapshots predate HEAD (expected in CI merge refs)" in body
    details = body.split("<details>", 1)[1]
    assert "stale snapshot" in details
    assert "C-0001/E-001 type=test_result" in details


def test_comment_collapses_other_warnings_and_labels() -> None:
    warned = _verify("SATISFIED", "SATISFIED")
    warned["warnings"] = ["subject state unavailable"]
    body, _verdict = render_ci_comment(verify_documents=[warned], gate_documents=[])
    assert "<summary>1 warning</summary>" in body
    assert "subject state unavailable" in body.split("<details>", 1)[1]

    labeled = _verify("SATISFIED", "SATISFIED")
    labeled["evidence_labels"] = ["C-0001/E-001 type=test_result status=executed"]
    labels_body, _verdict = render_ci_comment(verify_documents=[labeled], gate_documents=[])
    assert "<summary>Evidence details</summary>" in labels_body
    assert "C-0001/E-001 type=test_result" in labels_body


def test_comment_singular_stale_snapshot_summary() -> None:
    document = _verify("SATISFIED", "SATISFIED")
    document["warnings"] = [
        "C-0001/E-001 recorded git_commit abc does not match HEAD def (stale snapshot; not a failure)"
    ]
    body, _verdict = render_ci_comment(
        verify_documents=[document],
        gate_documents=[],
    )
    assert "1 evidence snapshot predates HEAD (expected in CI merge refs)" in body
    assert "**SATISFIED** — 1/1 claim satisfied, 0 gates passed." in body


def test_comment_not_satisfied_names_the_claim() -> None:
    document = _verify("NOT_SATISFIED", "NOT_SATISFIED", evidence_id=None)
    body, verdict = render_ci_comment(
        verify_documents=[document],
        gate_documents=[_gate("suppressions", passed=True)],
    )
    assert verdict == "NOT_SATISFIED"
    assert "NOT_SATISFIED" in body
    assert "Unmet claims: C-0001/claim-done-1" in body
    assert "C-0001/claim-done-1" in body
    row = next(line for line in body.splitlines() if "claim-done-1" in line and line.startswith("|"))
    assert "NOT_SATISFIED" in row
    assert "—" in row


def test_comment_gate_failure_is_not_satisfied() -> None:
    body, verdict = render_ci_comment(
        verify_documents=[_verify("SATISFIED", "SATISFIED")],
        gate_documents=[
            _gate(
                "scope",
                passed=False,
                change_id="C-0001",
                errors=["sensitive paths require a satisfied review_result claim"],
            )
        ],
    )
    assert verdict == "NOT_SATISFIED"
    assert "| scope | C-0001 | FAIL |" in body
    assert "sensitive paths require a satisfied review_result claim" in body
    assert combined_verdict([], [{"passed": False}]) == "NOT_SATISFIED"


def test_comment_omission_overrides_a_passing_gate() -> None:
    body, verdict = render_ci_comment(
        verify_documents=[],
        gate_documents=[_gate("suppressions", passed=True)],
        notes=["Code changed but no .retornatus Change was touched."],
        omission=True,
    )
    assert verdict == "NOT_SATISFIED"
    assert "no .retornatus Change was touched" in body


def test_comment_escapes_pipes_in_claim_text() -> None:
    document = _verify("SATISFIED", "SATISFIED")
    document["claims"][0]["statement"] = "left | right <tag>"
    body, _verdict = render_ci_comment(
        verify_documents=[document],
        gate_documents=[],
    )
    row = next(line for line in body.splitlines() if "left" in line)
    cells = re.split(r"(?<!\\)\|", row)
    assert len(cells) == 5
    assert "left \\| right &lt;tag&gt;" in row


def test_comment_truncates_to_the_github_limit() -> None:
    body, _verdict = render_ci_comment(
        verify_documents=[],
        gate_documents=[],
        overview_markdown=["x" * (MAX_COMMENT_CHARS + 5000)],
    )
    assert body.startswith(MARKER)
    assert len(body) <= MAX_COMMENT_CHARS
    assert "truncated" in body


def test_comment_covers_sparse_json_shapes() -> None:
    from retornatus.application.report.comment import comment_bundle
    from retornatus.domain.errors import UsageError

    body, verdict = render_ci_comment(
        verify_documents=[
            {"verdict": None, "claims": None, "rationale": "  "},
            {
                "verdict": "INCONCLUSIVE",
                "claims": ["nope", {"statement": "   ", "evidence": "none"}],
            },
        ],
        gate_documents=[{"findings": "nope", "warnings": ["  "]}],
    )
    assert verdict == "INCONCLUSIVE"
    assert "`claim`" in body
    assert "| gate | — | — | — |" in body
    long_note = "n" * 200
    noted, _ = render_ci_comment(
        verify_documents=[],
        gate_documents=[{"verdict": "PASS", "passed": True, "gate": "suppressions"}],
        notes=["  ", long_note],
    )
    assert "..." in noted
    try:
        comment_bundle([], [], "MAYBE")
    except UsageError as exc:
        assert "MAYBE" in str(exc)
    else:
        raise AssertionError("expected UsageError")


def test_ci_comment_notes_a_missing_change(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    verify_path = tmp_path / "verify.json"
    verify_path.write_text(json.dumps(_verify("SATISFIED", "SATISFIED")), encoding="utf-8")
    # The fixture change id is C-0001, which this empty project does not have.
    result = runner.invoke(
        app,
        ["ci", "comment", "--path", str(tmp_path), "--verify", str(verify_path)],
    )
    assert result.exit_code == 0, result.stderr
    assert "no overview in this checkout" in result.stdout


def test_empty_input_is_inconclusive() -> None:
    _body, verdict = render_ci_comment(verify_documents=[], gate_documents=[])
    assert verdict == "INCONCLUSIVE"


def test_ci_comment_cli_writes_verdict_bundle_and_markdown(tmp_path: Path) -> None:
    verify_path = tmp_path / "verify.json"
    gate_path = tmp_path / "gate.json"
    verify_path.write_text(json.dumps(_verify("SATISFIED", "SATISFIED")), encoding="utf-8")
    gate_path.write_text(json.dumps(_gate("suppressions", passed=True)), encoding="utf-8")
    verdict_file = tmp_path / "verdict.txt"
    bundle = tmp_path / "bundle.json"
    result = runner.invoke(
        app,
        [
            "ci",
            "comment",
            "--verify",
            str(verify_path),
            "--gate",
            str(gate_path),
            "--verdict-file",
            str(verdict_file),
            "--bundle",
            str(bundle),
        ],
    )
    assert result.exit_code == 0, result.stderr
    assert result.stdout.startswith(MARKER)
    assert verdict_file.read_text(encoding="utf-8").strip() == "SATISFIED"
    payload = json.loads(bundle.read_text(encoding="utf-8"))
    assert payload["kind"] == "ci-comment"
    assert payload["verdict"] == "SATISFIED"
    assert payload["verify"][0]["change_id"] == "C-0001"


def test_ci_comment_cli_includes_overview(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    created = runner.invoke(
        app,
        [
            "change",
            "create",
            "--path",
            str(tmp_path),
            "--title",
            "Health",
            "--demand",
            "Reviewers must see the health verdict in one comment",
            "--what",
            "Document GET /health for the comment overview",
            "--done",
            "pytest covers GET /health returns 200",
        ],
    )
    assert created.exit_code == 0, created.stdout
    verify_path = tmp_path / "verify.json"
    verify_path.write_text(json.dumps(_verify("NOT_SATISFIED", "NOT_SATISFIED")), encoding="utf-8")
    result = runner.invoke(
        app,
        ["ci", "comment", "--path", str(tmp_path), "--verify", str(verify_path)],
    )
    assert result.exit_code == 0, result.stderr
    assert "## C-0001 — Health" in result.stdout
    assert "### Claims" in result.stdout
    assert "\n### Gates\n" not in result.stdout
    assert "### Claim results" in result.stdout
    assert "### Gate results" in result.stdout
    assert "NOT_SATISFIED" in result.stdout


def test_ci_comment_rejects_a_json_array(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("[]", encoding="utf-8")
    result = runner.invoke(app, ["ci", "comment", "--verify", str(path)])
    assert result.exit_code == 2
    assert "object" in (result.stderr + result.stdout)


def test_action_script_is_valid_bash() -> None:
    bash = shutil.which("bash")
    if bash is None:
        import pytest

        pytest.skip("bash is not installed")
    script = ROOT / "scripts" / "github_action.sh"
    subprocess.run([bash, "-n", str(script)], check=True)
    text = script.read_text(encoding="utf-8")
    assert "${{" not in text
    assert 'echo "$GH_TOKEN"' not in text
    assert "echo $GH_TOKEN" not in text
    assert "printenv" not in text
    assert "set -x" not in text
