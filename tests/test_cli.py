"""CLI smoke tests for M0."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from retornatus.cli.main import app

runner = CliRunner()


def test_help_lists_intentions() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.stdout
    assert "wake" in result.stdout
    assert "Govern the work" in result.stdout


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "retornatus" in result.stdout


def test_cli_import_prints_package_version() -> None:
    """Importing the CLI must succeed and --version must print __version__."""
    import retornatus.cli.main as cli_main
    from retornatus import __version__

    assert cli_main.app is app
    result = runner.invoke(cli_main.app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout
    assert result.stdout.strip() == f"retornatus {__version__}"


def test_init_command(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert "Initialized Retornatus" in result.stdout
    assert (tmp_path / ".retornatus" / "config.toml").is_file()


def test_init_already_initialized(tmp_path: Path) -> None:
    runner.invoke(app, ["init", str(tmp_path)])
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert "Already initialized" in result.stdout
