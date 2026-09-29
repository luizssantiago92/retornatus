"""Coverage for verify receipts and Action attempt budgets."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import shutil
import warnings
from pathlib import Path

import pytest

from retornatus.application.assurance.evaluate import (
    AssuranceResult,
    AssuranceVerdict,
)
from retornatus.application.assurance.receipt import (
    ALG_HMAC,
    RECEIPT_SCHEMA_V1,
    canonical_bytes,
    generate_keypair,
    keygen,
    load_and_verify_receipt,
    parse_private_key,
    private_key_pem,
    verify_receipt_dict,
    write_private_key,
    write_verify_receipt,
)
from retornatus.application.change.tasks import TaskService
from retornatus.application.change.workflow import ChangeWorkflow
from retornatus.application.governance.gates import gate_budget
from retornatus.bootstrap.init import initialize_project
from retornatus.domain.errors import SigningKeyError


def _project(tmp: Path) -> Path:
    initialize_project(tmp)
    return tmp


def _result() -> AssuranceResult:
    return AssuranceResult(
        verdict=AssuranceVerdict.SATISFIED,
        rationale="all claims supported",
        claim_results={"done:1": "SATISFIED"},
        evidence_ids=["C-0001/E-001"],
    )


def _use_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.delenv("RETORNATUS_SIGNING_KEY", raising=False)
    monkeypatch.delenv("RETORNATUS_SIGNING_KEY_PATH", raising=False)
    monkeypatch.delenv("RETORNATUS_RECEIPT_KEY", raising=False)


def test_receipt_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _use_config(monkeypatch, tmp_path)
    root = _project(tmp_path / "proj")
    keygen(root)
    path = write_verify_receipt(root, "C-0001", _result())
    assert path.is_file()
    ok, msg, data = load_and_verify_receipt(root, path)
    assert ok, msg
    assert msg == "ok"
    assert data["change_id"] == "C-0001"
    assert data["verdict"] == "SATISFIED"
    assert data["alg"] == "Ed25519"
    assert (root / ".retornatus" / "keys" / f"{data['key_id']}.pub").is_file()

    tampered = dict(data)
    tampered["verdict"] = "NOT_SATISFIED"
    bad, reason = verify_receipt_dict(root, tampered)
    assert bad is False
    assert reason == "signature mismatch"


def test_wrong_public_key_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _use_config(monkeypatch, tmp_path)
    root = _project(tmp_path / "proj")
    keygen(root)
    path = write_verify_receipt(root, "C-0001", _result())
    ok, _, data = load_and_verify_receipt(root, path)
    assert ok
    other = tmp_path / "other"
    other.mkdir()
    _project(other)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-other"))
    keygen(other)
    foreign = next((other / ".retornatus" / "keys").glob("*.pub"))
    target = root / ".retornatus" / "keys" / f"{data['key_id']}.pub"
    target.write_bytes(foreign.read_bytes())
    bad, reason = verify_receipt_dict(root, data)
    assert bad is False
    assert "does not match" in reason


def test_verify_from_clone_with_public_key_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_config(monkeypatch, tmp_path)
    origin = _project(tmp_path / "origin")
    keygen(origin)
    receipt = write_verify_receipt(origin, "C-0001", _result())

    clone = tmp_path / "clone"
    keys = clone / ".retornatus" / "keys"
    keys.mkdir(parents=True)
    shutil.copy(receipt, clone / "receipt.json")
    for pub in (origin / ".retornatus" / "keys").glob("*.pub"):
        shutil.copy(pub, keys / pub.name)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "empty-xdg"))
    monkeypatch.delenv("RETORNATUS_SIGNING_KEY", raising=False)

    ok, msg, _ = load_and_verify_receipt(clone, clone / "receipt.json")
    assert ok, msg
    assert msg == "ok"
    private_bits = [
        p
        for p in clone.rglob("*")
        if p.is_file() and "PRIVATE KEY" in p.read_text(encoding="utf-8", errors="ignore")
    ]
    assert private_bits == []


def test_env_signing_key_is_not_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    xdg = tmp_path / "xdg"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    monkeypatch.delenv("RETORNATUS_SIGNING_KEY_PATH", raising=False)
    root = _project(tmp_path / "proj")
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    pem = private_key_pem(Ed25519PrivateKey.generate())
    monkeypatch.setenv("RETORNATUS_SIGNING_KEY", pem)
    write_verify_receipt(root, "C-0001", _result())
    assert list(xdg.rglob("*")) == []
    for path in root.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "BEGIN PRIVATE KEY" not in text
    runtime_key = root / ".retornatus" / "runtime" / "receipt.key"
    assert not runtime_key.exists()


def test_bad_signing_key_input(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RETORNATUS_SIGNING_KEY", raising=False)
    with pytest.raises(SigningKeyError, match="odd length"):
        parse_private_key("abc")
    with pytest.raises(SigningKeyError, match="empty"):
        parse_private_key("   ")
    with pytest.raises(SigningKeyError, match="PEM, base64, or even-length hex"):
        parse_private_key("!!!")
    with pytest.raises(SigningKeyError, match="32 bytes"):
        parse_private_key("aa")


def test_private_key_file_is_created_at_mode_0600(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mode 0600 comes from os.open, not from a later chmod.

    umask 0 would make a normal write world-readable. chmod is forced to fail
    so a write-then-chmod implementation cannot hide that window.
    """
    _use_config(monkeypatch, tmp_path)
    root = _project(tmp_path / "proj")

    def _chmod_fails(*_args: object, **_kwargs: object) -> None:
        raise OSError("chmod disabled")

    monkeypatch.setattr(os, "chmod", _chmod_fails)
    private_key = generate_keypair()
    if os.name == "nt":
        path = write_private_key(root, private_key)
        again = write_private_key(root, private_key)
        assert again == path
        assert path.is_file()
        assert "BEGIN PRIVATE KEY" in path.read_text(encoding="utf-8")
        return

    previous = os.umask(0)
    try:
        path = write_private_key(root, private_key)
        again = write_private_key(root, private_key)
    finally:
        os.umask(previous)
    assert again == path
    assert path.stat().st_mode & 0o777 == 0o600
    pem = path.read_text(encoding="utf-8")
    assert pem.startswith("-----BEGIN PRIVATE KEY-----")
    assert pem.endswith("\n")
    leftovers = [
        child
        for child in path.parent.iterdir()
        if child.name.startswith(f".{path.name}.") and child.suffix == ".tmp"
    ]
    assert leftovers == []


def test_private_key_write_on_windows_mode_and_failed_replace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Windows ignores POSIX mode; a failed replace must not leave the temp file."""
    from retornatus.application.assurance import receipt as receipt_mod

    _use_config(monkeypatch, tmp_path)
    root = _project(tmp_path / "proj")
    path = write_private_key(root, generate_keypair())
    real_name = os.name
    # Path objects already exist. Only the writer consults os.name after this.
    monkeypatch.setattr(receipt_mod.os, "name", "nt")
    receipt_mod._write_private_key_file(path, path.read_text(encoding="utf-8"))
    assert "BEGIN PRIVATE KEY" in path.read_text(encoding="utf-8")
    if real_name != "nt":
        assert path.stat().st_mode & 0o777 == 0o600

    def _replace_fails(src: str, dst: str) -> None:
        raise OSError(f"replace failed {src} -> {dst}")

    monkeypatch.setattr(receipt_mod.os, "replace", _replace_fails)
    with pytest.raises(OSError, match="replace failed"):
        receipt_mod._write_private_key_file(path, "secret\n")
    leftovers = list(path.parent.glob(f".{path.name}.*.tmp"))
    assert leftovers == []
    assert "BEGIN PRIVATE KEY" in path.read_text(encoding="utf-8")


def test_private_key_write_closes_fd_when_open_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from retornatus.application.assurance import receipt as receipt_mod

    _use_config(monkeypatch, tmp_path)
    root = _project(tmp_path / "proj")
    path = write_private_key(root, generate_keypair())

    def _fdopen_fails(*_args: object, **_kwargs: object) -> None:
        raise OSError("fdopen failed")

    monkeypatch.setattr(os, "fdopen", _fdopen_fails)
    with pytest.raises(OSError, match="fdopen failed"):
        receipt_mod._write_private_key_file(path, "secret\n")
    assert list(path.parent.glob(f".{path.name}.*.tmp")) == []


def test_keygen_refuses_private_key_inside_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path / "proj")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(root / "inside-config"))
    monkeypatch.delenv("RETORNATUS_SIGNING_KEY", raising=False)
    with pytest.raises(SigningKeyError, match="inside the project"):
        keygen(root, print_private=False)
    key_id, public_path, private_path, pem = keygen(root, print_private=True)
    assert private_path is None
    assert "BEGIN PRIVATE KEY" in pem
    assert public_path.is_file()
    assert key_id in public_path.name
    assert not any(root.rglob("*.pem"))


def test_legacy_hmac_is_not_portable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_config(monkeypatch, tmp_path)
    root = _project(tmp_path / "proj")
    key = b"legacy-local-key"
    payload = {
        "schema": RECEIPT_SCHEMA_V1,
        "alg": ALG_HMAC,
        "change_id": "C-0001",
        "verdict": "SATISFIED",
        "rationale": "old",
        "claim_results": {},
        "evidence_ids": [],
        "git_head": None,
        "issued_at": "2020-01-01T00:00:00+00:00",
    }
    digest = hmac.new(key, canonical_bytes(payload), hashlib.sha256).hexdigest()
    payload["signature"] = digest
    monkeypatch.setenv("RETORNATUS_RECEIPT_KEY", key.hex())
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ok, msg = verify_receipt_dict(root, payload)
    assert ok
    assert msg == "legacy_hmac"
    assert any(issubclass(item.category, DeprecationWarning) for item in caught)
    assert not (root / ".retornatus" / "runtime" / "receipt.key").exists()

    monkeypatch.delenv("RETORNATUS_RECEIPT_KEY", raising=False)
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        bad, reason = verify_receipt_dict(root, payload)
    assert bad is False
    assert "not portable" in reason

    monkeypatch.setenv("RETORNATUS_RECEIPT_KEY", "abc")
    with pytest.raises(SigningKeyError, match="odd length"):
        verify_receipt_dict(root, payload)


def test_legacy_receipt_file_roundtrip_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path / "proj")
    monkeypatch.delenv("RETORNATUS_RECEIPT_KEY", raising=False)
    receipt = tmp_path / "legacy.json"
    receipt.write_text(
        json.dumps(
            {
                "schema": RECEIPT_SCHEMA_V1,
                "alg": ALG_HMAC,
                "change_id": "C-0001",
                "verdict": "SATISFIED",
                "signature": "00",
            }
        ),
        encoding="utf-8",
    )
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        ok, msg, _ = load_and_verify_receipt(root, receipt)
    assert ok is False
    assert msg.startswith("legacy_hmac")


def test_action_budget_gate(tmp_path: Path) -> None:
    root = _project(tmp_path)
    created = ChangeWorkflow(root).create_change(
        title="Budget demo",
        demand_statement="Add health",
        situation="GET /health should return 200 with tests",
        what="GET /health returns 200",
        done_criteria=["pytest covers GET /health"],
        action_objective="Implement health",
        tasks=["implement"],
    )
    assert created.action is not None
    action_id = created.action.id
    tasks = TaskService(root)
    tasks.set_max_attempts(action_id, 2)
    assert gate_budget(root, action_id).passed

    task_id = created.action.tasks[0].id
    tasks.start(task_id)
    tasks.fail(task_id)
    assert gate_budget(root, action_id).passed

    tasks.reopen(task_id)
    tasks.start(task_id)
    tasks.fail(task_id)
    assert not gate_budget(root, action_id).passed


def test_docs_html_check_script_runs() -> None:
    import subprocess
    import sys

    repo = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(repo / "scripts" / "build_docs_html.py"), "--check"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
