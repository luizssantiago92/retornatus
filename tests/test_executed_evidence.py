"""Executed Evidence: provenance, verify, subject match, and git snapshot."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from typer.testing import CliRunner

from retornatus.application.assurance.evaluate import (
    AssuranceVerdict,
    Claim,
    evaluate_assurance,
    evidence_subject_matches_claim,
    subjects_match,
)
from retornatus.application.assurance.evidence import EvidenceService
from retornatus.application.assurance.execute import OUTPUT_TAIL_MAX_CHARS
from retornatus.application.assurance.independent import evaluate_change_assurance
from retornatus.cli.main import app
from retornatus.domain.enums import EvidenceProvenance
from retornatus.domain.models import Evidence
from retornatus.domain.relations import Relation, RelationType
from retornatus.infrastructure.persistence.repository import FileRepository

runner = CliRunner()

_CLAIM = "C-0001/claim-done-1"


def _init_health(tmp_path: Path) -> None:
    init = runner.invoke(app, ["init", str(tmp_path)])
    assert init.exit_code == 0, init.stdout
    created = runner.invoke(
        app,
        [
            "change",
            "create",
            "--path",
            str(tmp_path),
            "--title",
            "health",
            "--demand",
            "Add health",
            "--what",
            "GET /health returns 200",
            "--done",
            "GET /health returns 200 with pytest test",
        ],
    )
    assert created.exit_code == 0, created.stdout


def _executed(subject: str, *, evidence_type: str = "test_result") -> Evidence:
    return Evidence(
        id="C-0001/E-0001",
        type=evidence_type,
        subject=subject,
        source="pytest",
        producer="test",
        provenance=EvidenceProvenance.EXECUTED,
        command=["pytest"],
        exit_code=0,
        relations=[Relation(type=RelationType.SUPPORTS, target_id="claim")],
    )


def test_self_reported_test_result_is_not_satisfied(tmp_path: Path) -> None:
    """The old trust-me repro must not exit 0."""
    _init_health(tmp_path)
    added = runner.invoke(
        app,
        [
            "evidence",
            "add",
            "--path",
            str(tmp_path),
            "-c",
            "C-0001",
            "-t",
            "test_result",
            "-s",
            "/health",
            "--source",
            "trust me",
            "--claim",
            _CLAIM,
        ],
    )
    assert added.exit_code == 0, added.stdout
    assert "provenance=self_reported" in added.stdout

    verified = runner.invoke(app, ["verify", "C-0001", "--path", str(tmp_path)])
    assert verified.exit_code != 0
    assert "UNVERIFIED" in verified.stdout
    assert '"verdict": "SATISFIED"' not in verified.stdout
    assert "C-0001/E-001" in verified.stdout


def test_allow_self_reported_flag_and_config(tmp_path: Path) -> None:
    _init_health(tmp_path)
    added = runner.invoke(
        app,
        [
            "evidence",
            "add",
            "--path",
            str(tmp_path),
            "-c",
            "C-0001",
            "-t",
            "test_result",
            "-s",
            "/health",
            "--source",
            "trust me",
            "--claim",
            _CLAIM,
        ],
    )
    assert added.exit_code == 0, added.stdout

    flagged = runner.invoke(
        app,
        [
            "verify",
            "C-0001",
            "--path",
            str(tmp_path),
            "--allow-self-reported",
        ],
    )
    assert flagged.exit_code == 0, flagged.stdout
    assert '"verdict": "SATISFIED"' in flagged.stdout
    assert "self-reported(allowed)" in flagged.stdout

    strict = runner.invoke(app, ["verify", "C-0001", "--path", str(tmp_path)])
    assert strict.exit_code != 0

    repo = FileRepository(tmp_path)
    data, rev = repo.load_config()
    data["assurance"] = {"allow_self_reported": True}
    repo.save_config(data, expected=rev)
    from_config = runner.invoke(app, ["verify", "C-0001", "--path", str(tmp_path)])
    assert from_config.exit_code == 0, from_config.stdout
    assert '"verdict": "SATISFIED"' in from_config.stdout


def test_evidence_run_exit_zero_satisfies(tmp_path: Path) -> None:
    _init_health(tmp_path)
    code = "import sys; sys.stdout.write('OUT'); sys.stderr.write('ERR'); sys.exit(0)"
    ran = runner.invoke(
        app,
        [
            "evidence",
            "run",
            "--path",
            str(tmp_path),
            "-c",
            "C-0001",
            "-t",
            "test_result",
            "-s",
            "/health",
            "--claim",
            _CLAIM,
            "--",
            sys.executable,
            "-c",
            code,
        ],
    )
    assert ran.exit_code == 0, ran.stdout
    assert "provenance=executed" in ran.stdout
    assert "exit_code=0" in ran.stdout

    evidence = EvidenceService(tmp_path).list_for_change("C-0001")
    assert len(evidence) == 1
    ev = evidence[0]
    assert ev.provenance is EvidenceProvenance.EXECUTED
    assert ev.exit_code == 0
    assert ev.command == [sys.executable, "-c", code]
    assert ev.started_at is not None and ev.ended_at is not None
    assert ev.duration_ms is not None and ev.duration_ms >= 0
    assert ev.output_sha256
    assert ev.output_artifact
    artifact = tmp_path / ev.output_artifact
    payload = artifact.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == ev.output_sha256
    assert b"OUT" in payload and b"ERR" in payload
    assert ev.output_tail is not None and "OUT" in ev.output_tail and "ERR" in ev.output_tail

    verified = runner.invoke(app, ["verify", "C-0001", "--path", str(tmp_path)])
    assert verified.exit_code == 0, verified.stdout
    assert '"verdict": "SATISFIED"' in verified.stdout
    assert "status=executed" in verified.stdout


def test_evidence_run_exit_one_is_failing(tmp_path: Path) -> None:
    _init_health(tmp_path)
    ran = runner.invoke(
        app,
        [
            "evidence",
            "run",
            "--path",
            str(tmp_path),
            "-c",
            "C-0001",
            "-t",
            "test_result",
            "-s",
            "/health",
            "--claim",
            _CLAIM,
            "--",
            sys.executable,
            "-c",
            "import sys; sys.exit(1)",
        ],
    )
    assert ran.exit_code == 1, ran.stdout
    ev = EvidenceService(tmp_path).list_for_change("C-0001")[0]
    assert ev.exit_code == 1
    assert ev.timed_out is False
    assert ev.provenance is EvidenceProvenance.EXECUTED

    verified = runner.invoke(app, ["verify", "C-0001", "--path", str(tmp_path)])
    assert verified.exit_code != 0
    assert '"verdict": "SATISFIED"' not in verified.stdout
    assert "failing(exit 1)" in verified.stdout


def test_evidence_run_timeout(tmp_path: Path) -> None:
    _init_health(tmp_path)
    ev = EvidenceService(tmp_path).run(
        change_id="C-0001",
        evidence_type="test_result",
        subject="/health",
        command=[sys.executable, "-c", "import time; time.sleep(30)"],
        timeout_seconds=1.0,
        supports_claim_id=_CLAIM,
    )
    assert ev.timed_out is True
    assert ev.exit_code is None
    assert ev.provenance is EvidenceProvenance.EXECUTED
    assert ev.output_tail is not None and "timed out" in ev.output_tail
    result = evaluate_change_assurance(tmp_path, "C-0001", allow_self_reported=False)
    assert result.verdict is not AssuranceVerdict.SATISFIED
    assert any("failing(timeout)" in line for line in result.evidence_labels)


def test_output_tail_is_bounded(tmp_path: Path) -> None:
    _init_health(tmp_path)
    ev = EvidenceService(tmp_path).run(
        change_id="C-0001",
        evidence_type="build_result",
        subject="/health",
        command=[sys.executable, "-c", "print('x' * 20000)"],
        supports_claim_id=_CLAIM,
    )
    assert ev.output_tail is not None
    assert len(ev.output_tail) <= OUTPUT_TAIL_MAX_CHARS
    assert ev.output_artifact is not None
    full = (tmp_path / ev.output_artifact).read_text(encoding="utf-8")
    assert len(full) > OUTPUT_TAIL_MAX_CHARS


def test_legacy_evidence_json_loads(tmp_path: Path) -> None:
    _init_health(tmp_path)
    legacy = {
        "schema_version": 1,
        "id": "C-0001/E-0009",
        "type": "test_result",
        "subject": "/health",
        "source": "trust me",
        "producer": "agent",
        "observed_at": "2026-01-01T00:00:00Z",
        "subject_state": "passing",
        "relations": [{"type": "SUPPORTS", "target_id": _CLAIM}],
    }
    path = FileRepository(tmp_path).paths.evidence_json("C-0001/E-0009")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(legacy), encoding="utf-8")

    loaded, _ = FileRepository(tmp_path).load_evidence("C-0001/E-0009")
    assert loaded.provenance is EvidenceProvenance.SELF_REPORTED
    assert loaded.command is None
    assert loaded.exit_code is None
    assert loaded.git_commit is None
    assert loaded.timed_out is False
    assert loaded.output_sha256 is None
    assert loaded.source == "trust me"


def test_subject_slash_does_not_match_health() -> None:
    claim = Claim(
        id="claim",
        statement="GET /health returns 200",
        required_evidence_types=["test_result"],
        subject="/health",
    )
    result = evaluate_assurance(claims=[claim], evidence=[_executed("/")])
    assert result.verdict is not AssuranceVerdict.SATISFIED
    assert not subjects_match("/", "/health")
    assert subjects_match("/Health/", "/health")
    assert subjects_match("  /health/  ", "/health")
    assert evidence_subject_matches_claim("docs/health.md", "/health.md")
    assert not evidence_subject_matches_claim("/", "/health")
    assert not evidence_subject_matches_claim("/health", "/")

    matched = evaluate_assurance(claims=[claim], evidence=[_executed("/Health/")])
    assert matched.verdict is AssuranceVerdict.SATISFIED


def test_review_result_stays_self_reported_and_can_satisfy() -> None:
    evidence = Evidence(
        id="C-0001/E-0001",
        type="review_result",
        subject="notes",
        source="human",
        producer="reviewer",
        relations=[Relation(type=RelationType.SUPPORTS, target_id="claim")],
    )
    claim = Claim(
        id="claim",
        statement="Independent review of the change",
        required_evidence_types=["review_result"],
        subject="notes",
    )
    result = evaluate_assurance(claims=[claim], evidence=[evidence])
    assert result.verdict is AssuranceVerdict.SATISFIED
    assert evidence.provenance is EvidenceProvenance.SELF_REPORTED
    assert any("status=self-reported" in line for line in result.evidence_labels)
    assert "UNVERIFIED" not in " ".join(result.evidence_labels)


def test_non_git_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    _init_health(tmp_path)
    ran = runner.invoke(
        app,
        [
            "evidence",
            "run",
            "--path",
            str(tmp_path),
            "-c",
            "C-0001",
            "-t",
            "test_result",
            "-s",
            "/health",
            "--claim",
            _CLAIM,
            "--",
            sys.executable,
            "-c",
            "import sys; sys.exit(0)",
        ],
    )
    assert ran.exit_code == 0, ran.stdout
    assert "not a git work tree" in ran.stdout
    ev = EvidenceService(tmp_path).list_for_change("C-0001")[0]
    assert ev.git_commit is None
    assert ev.worktree_dirty is None
    verified = runner.invoke(app, ["verify", "C-0001", "--path", str(tmp_path)])
    assert verified.exit_code == 0, verified.stdout


def _git_commit(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=root,
        check=True,
        capture_output=True,
    )


def test_stale_commit_warns_without_failing(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "evidence@retornatus.local"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Evidence Test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    (tmp_path / "README").write_text("base\n", encoding="utf-8")
    _git_commit(tmp_path, "base")
    _init_health(tmp_path)
    _git_commit(tmp_path, "retornatus init")

    ran = runner.invoke(
        app,
        [
            "evidence",
            "run",
            "--path",
            str(tmp_path),
            "-c",
            "C-0001",
            "-t",
            "test_result",
            "-s",
            "/health",
            "--claim",
            _CLAIM,
            "--",
            sys.executable,
            "-c",
            "import sys; sys.exit(0)",
        ],
    )
    assert ran.exit_code == 0, ran.stdout
    ev = EvidenceService(tmp_path).list_for_change("C-0001")[0]
    assert ev.git_commit
    assert ev.worktree_dirty is False

    (tmp_path / "README").write_text("changed\n", encoding="utf-8")
    _git_commit(tmp_path, "later")

    verified = runner.invoke(app, ["verify", "C-0001", "--path", str(tmp_path)])
    assert verified.exit_code == 0, verified.stdout
    assert '"verdict": "SATISFIED"' in verified.stdout
    assert "stale snapshot; not a failure" in verified.stdout
    assert "WARN" in verified.stdout
