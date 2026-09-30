"""CLI error handling, receipt commands, and path containment."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app
from retornatus.domain.errors import InvalidIdentifierError, PathEscapeError
from retornatus.infrastructure.index.sqlite_index import RetornatusIndex
from retornatus.infrastructure.persistence.paths import RetornatusPaths

runner = CliRunner()


def _init(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    root.mkdir()
    initialize_project(root)
    return root


def test_help_preserves_command_names() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in (
        "init",
        "wake",
        "status",
        "doctor",
        "inspect",
        "search",
        "verify",
        "run",
        "project-init",
        "integrate",
        "change",
        "skill",
        "gate",
        "evidence",
        "finding",
        "question",
        "loop",
        "decision",
        "rule",
        "policy",
        "assurance",
        "execution",
        "task",
        "lesson",
        "ops",
        "intake",
        "action",
        "receipt",
    ):
        assert name in result.stdout
    receipt = runner.invoke(app, ["receipt", "--help"])
    assert receipt.exit_code == 0
    assert "keygen" in receipt.stdout
    assert "sign" in receipt.stdout
    assert "verify" in receipt.stdout
    for group in ("change", "gate", "evidence", "task", "ops", "skill"):
        listed = runner.invoke(app, [group, "--help"])
        assert listed.exit_code == 0, listed.output


def test_verify_rejects_path_traversal(tmp_path: Path) -> None:
    root = _init(tmp_path)
    result = runner.invoke(app, ["verify", "../../../tmp", "--path", str(root)])
    assert result.exit_code == 2
    assert "Invalid Change id" in result.output
    assert "Traceback" not in result.output
    assert "FileNotFoundError" not in result.output


def test_verify_entrypoint_has_no_rich_traceback(tmp_path: Path) -> None:
    root = _init(tmp_path)
    env = os.environ.copy()
    src = str(Path(__file__).resolve().parents[1] / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from retornatus.cli.main import entrypoint; "
            "sys.argv = ['retornatus', 'verify', '../../../tmp', '--path', sys.argv[1]]; "
            "entrypoint()",
            str(root),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    combined = proc.stdout + proc.stderr
    assert proc.returncode == 2
    assert "Invalid Change id" in combined
    assert "Traceback" not in combined
    assert "FileNotFoundError" not in combined


def test_gate_keeps_exit_code_for_real_checks(tmp_path: Path) -> None:
    root = _init(tmp_path)
    missing = runner.invoke(app, ["gate", "contract", "C-9999", "--path", str(root)])
    assert missing.exit_code == 1
    assert "Traceback" not in missing.output
    bad = runner.invoke(app, ["gate", "contract", "../../../tmp", "--path", str(root)])
    assert bad.exit_code == 2
    assert "Invalid Change id" in bad.output
    assert "Traceback" not in bad.output


def test_search_punctuation_does_not_crash(tmp_path: Path) -> None:
    root = _init(tmp_path)
    for query in ('foo"', "health-check", "C-0001"):
        result = runner.invoke(app, ["search", query, "--path", str(root)])
        assert result.exit_code == 0, result.output
        assert "OperationalError" not in result.output
        assert "Traceback" not in result.output
    empty = runner.invoke(app, ["search", "   ", "--path", str(root)])
    assert empty.exit_code == 2
    assert "empty" in empty.output.lower()
    assert "Traceback" not in empty.output
    hits = RetornatusIndex(root).search('foo"')
    assert hits == []
    assert RetornatusIndex(root).search("health-check") == []


def test_bad_signing_key_is_a_clean_cli_error(tmp_path: Path) -> None:
    root = _init(tmp_path)
    result = runner.invoke(
        app,
        ["receipt", "sign", "--change", "C-0001", "--path", str(root)],
        env={"RETORNATUS_SIGNING_KEY": "abc", "XDG_CONFIG_HOME": str(tmp_path / "xdg")},
    )
    assert result.exit_code == 2
    assert "odd length" in result.output
    assert "Traceback" not in result.output
    assert "ValueError" not in result.output


def test_receipt_keygen_sign_and_verify(tmp_path: Path) -> None:
    root = _init(tmp_path)
    xdg = str(tmp_path / "xdg")
    created = runner.invoke(
        app,
        [
            "change",
            "create",
            "--title",
            "Receipt",
            "--demand",
            "Sign verify results",
            "--what",
            "Receipts verify from a clone",
            "--done",
            "pytest covers receipt verify",
            "--situation",
            "Ed25519 public key is committed",
            "--path",
            str(root),
        ],
    )
    assert created.exit_code == 0, created.output
    keygen = runner.invoke(
        app,
        ["receipt", "keygen", "--path", str(root)],
        env={"XDG_CONFIG_HOME": xdg},
    )
    assert keygen.exit_code == 0, keygen.output
    assert "public_key:" in keygen.output
    assert "BEGIN PRIVATE KEY" not in keygen.output
    project_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in root.rglob("*")
        if path.is_file()
    )
    assert "BEGIN PRIVATE KEY" not in project_text

    signed = runner.invoke(
        app,
        ["receipt", "sign", "--change", "C-0001", "--path", str(root)],
        env={"XDG_CONFIG_HOME": xdg},
    )
    assert signed.exit_code == 0, signed.output
    receipt_line = next(
        line for line in signed.output.splitlines() if line.startswith("receipt:")
    )
    receipt_path = receipt_line.split(": ", 1)[1]
    checked = runner.invoke(
        app,
        ["receipt", "verify", receipt_path, "--path", str(root)],
        env={"XDG_CONFIG_HOME": str(tmp_path / "no-keys")},
    )
    assert checked.exit_code == 0, checked.output
    assert '"portable": true' in checked.output
    assert '"legacy_hmac": false' in checked.output

    payload = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
    payload["verdict"] = "TAMPERED"
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(payload), encoding="utf-8")
    failed = runner.invoke(app, ["receipt", "verify", str(tampered), "--path", str(root)])
    assert failed.exit_code == 1
    assert "signature mismatch" in failed.output
    assert "Traceback" not in failed.output

    verified = runner.invoke(
        app,
        ["verify", "C-0001", "--receipt", "--path", str(root)],
        env={"XDG_CONFIG_HOME": xdg},
    )
    assert verified.exit_code == 1
    assert "receipt:" in verified.output
    assert "Traceback" not in verified.output


def test_keygen_warns_when_pem_is_tracked_and_stays_outside(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "keygen@retornatus.local"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Keygen Test"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    initialize_project(root)
    leaked = root / "leak.pem"
    leaked.write_text("not-a-real-key\n", encoding="utf-8")
    subprocess.run(["git", "add", "-f", "--", "leak.pem"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "tracked pem"], cwd=root, check=True, capture_output=True)
    xdg = tmp_path / "xdg"

    result = runner.invoke(
        app,
        ["receipt", "keygen", "--path", str(root)],
        env={"XDG_CONFIG_HOME": str(xdg)},
    )

    assert result.exit_code == 0, result.output
    blob = f"{result.stdout}\n{result.stderr or ''}\n{result.output}"
    assert "warning: private key file is tracked by git: leak.pem" in blob
    assert "BEGIN PRIVATE KEY" not in blob
    assert "The private key is outside the repository." in blob
    private_files = list((xdg / "retornatus" / "keys").glob("*.pem"))
    assert len(private_files) == 1
    private = private_files[0].resolve()
    assert root.resolve() not in private.parents
    assert list(root.rglob("*.pem")) == [leaked]
    assert not list(root.rglob("*.key"))


def test_change_dir_rejects_traversal(tmp_path: Path) -> None:
    root = _init(tmp_path)
    paths = RetornatusPaths(root)
    with pytest.raises(InvalidIdentifierError, match="Invalid Change id"):
        paths.change_dir("../../../tmp")
    with pytest.raises(InvalidIdentifierError):
        paths.action_json("C-0001/../../../tmp")
    outside = tmp_path / "outside"
    with pytest.raises(PathEscapeError, match="outside"):
        paths._inside(outside)
    assert paths.change_dir("C-0002").is_relative_to(paths.retornatus)
