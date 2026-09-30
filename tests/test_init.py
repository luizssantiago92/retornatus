"""Tests for `retornatus init` (M0 acceptance)."""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

import pytest
from typer.testing import CliRunner

from retornatus import __version__
from retornatus.bootstrap.gitignore import (
    GITIGNORE_BEGIN,
    GITIGNORE_END,
    gitignore_block,
    tracked_private_key_files,
    tracked_private_key_warnings,
)
from retornatus.bootstrap.init import (
    DIRECTORY_TREE,
    initialize_project,
    is_initialized,
)
from retornatus.cli.main import app

runner = CliRunner()


def test_initialize_creates_minimal_tree(tmp_path: Path) -> None:
    result = initialize_project(tmp_path)

    assert result.created is True
    assert result.already_initialized is False
    assert is_initialized(tmp_path)

    retornatus = tmp_path / ".retornatus"
    assert (retornatus / "config.toml").is_file()
    assert (retornatus / "project" / "project.md").is_file()

    for relative in DIRECTORY_TREE:
        assert (retornatus / relative).is_dir()

    with (retornatus / "config.toml").open("rb") as handle:
        config = tomllib.load(handle)

    assert config["schema_version"] == 1
    assert config["project"]["initialized"] is True
    assert config["retornatus"]["version"] == __version__


def test_initialize_is_idempotent_without_force(tmp_path: Path) -> None:
    first = initialize_project(tmp_path)
    second = initialize_project(tmp_path)

    assert first.created is True
    assert second.created is False
    assert second.already_initialized is True


def test_force_recreates_config(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    config = tmp_path / ".retornatus" / "config.toml"
    config.write_text("schema_version = 0\n", encoding="utf-8")

    result = initialize_project(tmp_path, force=True)

    assert result.created is True
    with config.open("rb") as handle:
        data = tomllib.load(handle)
    assert data["schema_version"] == 1
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8").count(GITIGNORE_BEGIN) == 1


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _git_repo(root: Path) -> None:
    assert _git(root, "init").returncode == 0
    assert _git(root, "config", "user.email", "init@retornatus.local").returncode == 0
    assert _git(root, "config", "user.name", "Init Test").returncode == 0


def _ignored(root: Path, relative: str) -> bool:
    completed = _git(root, "check-ignore", "--no-index", "-q", "--", relative)
    assert completed.returncode in (0, 1), completed.stderr
    return completed.returncode == 0


def _combined(result: object) -> str:
    stdout = getattr(result, "stdout", "") or ""
    stderr = getattr(result, "stderr", "") or ""
    output = getattr(result, "output", "") or ""
    return f"{stdout}\n{stderr}\n{output}"


def test_fresh_init_gitignore_block_is_idempotent(tmp_path: Path) -> None:
    first = initialize_project(tmp_path)
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")

    assert first.gitignore_updated is True
    assert first.tracked_private_keys == ()
    assert text == gitignore_block()
    assert text.count(GITIGNORE_BEGIN) == 1
    assert text.count(GITIGNORE_END) == 1
    for rule in (
        ".retornatus/index/",
        ".retornatus/runtime/",
        "*.pem",
        "*.key",
        ".env",
        ".env.*",
        "!.env.example",
        "!.retornatus/keys/*.pub",
    ):
        assert rule in text.splitlines()

    second = initialize_project(tmp_path)
    assert second.created is False
    assert second.already_initialized is True
    assert second.gitignore_updated is False
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == text


def test_gitignore_preserves_existing_lines(tmp_path: Path) -> None:
    original = "my-build/\n# keep this\n"
    (tmp_path / ".gitignore").write_bytes(original.encode("utf-8"))

    initialize_project(tmp_path)
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")

    assert text.startswith(original)
    assert "my-build/" in text.splitlines()
    assert "# keep this" in text.splitlines()
    assert text.count(GITIGNORE_BEGIN) == 1
    initialize_project(tmp_path)
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == text


def test_gitignore_preserves_crlf_and_a_line_without_newline(tmp_path: Path) -> None:
    crlf = tmp_path / "crlf"
    lf = tmp_path / "lf"
    crlf.mkdir()
    lf.mkdir()
    original = "keep-me\r\n# user rule\r\n"
    (crlf / ".gitignore").write_bytes(original.encode("utf-8"))
    (lf / ".gitignore").write_bytes(b"keep-me")

    initialize_project(crlf)
    crlf_bytes = (crlf / ".gitignore").read_bytes()
    assert crlf_bytes.startswith(original.encode("utf-8"))
    assert crlf_bytes.count(b"# retornatus-gitignore:begin") == 1
    assert b"*.pem\r\n" in crlf_bytes
    assert initialize_project(crlf).gitignore_updated is False
    assert (crlf / ".gitignore").read_bytes() == crlf_bytes

    initialize_project(lf)
    lf_bytes = (lf / ".gitignore").read_bytes()
    assert lf_bytes.startswith(b"keep-me\n")
    assert b"keep-me#" not in lf_bytes
    assert lf_bytes.count(GITIGNORE_BEGIN.encode()) == 1
    assert initialize_project(lf).gitignore_updated is False
    assert (lf / ".gitignore").read_bytes() == lf_bytes


def test_init_repairs_missing_block_when_already_initialized(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    (tmp_path / ".gitignore").unlink()

    second = initialize_project(tmp_path)

    assert second.already_initialized is True
    assert second.gitignore_updated is True
    assert GITIGNORE_BEGIN in (tmp_path / ".gitignore").read_text(encoding="utf-8")


def test_existing_gitignore_block_is_not_rewritten(tmp_path: Path) -> None:
    custom = "# retornatus-gitignore:begin\ncustom-rule\n# retornatus-gitignore:end\n"
    (tmp_path / ".gitignore").write_text(custom, encoding="utf-8")

    result = initialize_project(tmp_path)

    assert result.gitignore_updated is False
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == custom


def test_check_ignore_keeps_public_keys_and_ignores_secrets(tmp_path: Path) -> None:
    _git_repo(tmp_path)
    initialize_project(tmp_path)
    keys = tmp_path / ".retornatus" / "keys"
    keys.mkdir(parents=True)
    (keys / "abc.pub").write_text("public\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text("EXAMPLE=1\n", encoding="utf-8")
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / ".env.example").write_text("EXAMPLE=1\n", encoding="utf-8")

    assert _ignored(tmp_path, ".retornatus/keys/abc.pub") is False
    assert _ignored(tmp_path, ".retornatus/config.toml") is False
    assert _ignored(tmp_path, ".retornatus/project/project.md") is False
    assert _ignored(tmp_path, ".retornatus/changes/C-0001/change.json") is False
    assert _ignored(tmp_path, ".env.example") is False
    assert _ignored(tmp_path, "app/.env.example") is False

    assert _ignored(tmp_path, ".retornatus/index/retornatus.db") is True
    assert _ignored(tmp_path, ".retornatus/runtime/cache/session") is True
    assert _ignored(tmp_path, ".retornatus/runtime/locks/lock") is True
    assert _ignored(tmp_path, "secret.pem") is True
    assert _ignored(tmp_path, "nested/secret.key") is True
    assert _ignored(tmp_path, ".env") is True
    assert _ignored(tmp_path, ".env.local") is True
    assert _ignored(tmp_path, ".env.production") is True


def test_tracked_private_key_files_skip_public_keys(tmp_path: Path) -> None:
    assert tracked_private_key_files(tmp_path) == []
    _git_repo(tmp_path)
    (tmp_path / "a.PEM").write_text("pem\n", encoding="utf-8")
    (tmp_path / "b.key").write_text("key\n", encoding="utf-8")
    keys = tmp_path / ".retornatus" / "keys"
    keys.mkdir(parents=True)
    (keys / "abc.pub").write_text("public\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ok\n", encoding="utf-8")
    assert _git(tmp_path, "add", "--", "a.PEM", "b.key", ".retornatus/keys/abc.pub", "notes.txt").returncode == 0
    assert _git(tmp_path, "commit", "-m", "keys").returncode == 0

    assert tracked_private_key_files(tmp_path) == ["a.PEM", "b.key"]


def test_init_cli_warns_when_a_private_key_is_tracked(tmp_path: Path) -> None:
    _git_repo(tmp_path)
    (tmp_path / "signing.pem").write_text("not-a-real-key\n", encoding="utf-8")
    assert _git(tmp_path, "add", "--", "signing.pem").returncode == 0
    assert _git(tmp_path, "commit", "-m", "tracked key").returncode == 0

    result = runner.invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 0, _combined(result)
    blob = _combined(result)
    assert "warning: private key file is tracked by git: signing.pem" in blob
    assert "BEGIN PRIVATE KEY" not in blob
    assert "Gitignore: appended Retornatus ignore rules" in blob


def test_gitignore_directory_is_left_alone(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").mkdir()
    result = initialize_project(tmp_path)
    assert result.gitignore_updated is False
    assert (tmp_path / ".gitignore").is_dir()


def test_tracked_private_key_scan_tolerates_git_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import retornatus.bootstrap.gitignore as gitignore_mod

    def _boom(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise OSError("git missing")

    monkeypatch.setattr(gitignore_mod.subprocess, "run", _boom)
    assert tracked_private_key_files(tmp_path) == []

    def _nonzero(*args: object, **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(list(args), 1, stdout=b"", stderr=b"no")

    monkeypatch.setattr(gitignore_mod.subprocess, "run", _nonzero)
    assert tracked_private_key_files(tmp_path) == []
    assert tracked_private_key_warnings([]) == []


def test_repository_gitignore_contains_the_init_block() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / ".gitignore").read_text(encoding="utf-8")
    assert text.count(GITIGNORE_BEGIN) == 1
    assert gitignore_block("\n") in text or gitignore_block("\r\n") in text
