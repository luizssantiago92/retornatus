"""Packaged config presets for `retornatus init`."""

from __future__ import annotations

import os
import subprocess
import tomllib
import zipfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from retornatus import __version__
from retornatus.bootstrap.gitignore import GITIGNORE_BEGIN, gitignore_block
from retornatus.bootstrap.init import DIRECTORY_TREE, initialize_project
from retornatus.bootstrap.presets import (
    list_presets,
    render_config,
    render_preset_document,
    resolve_preset,
)
from retornatus.cli.main import app
from retornatus.domain.errors import UsageError

runner = CliRunner()
ROOT = Path(__file__).resolve().parents[1]


def _combined(result: object) -> str:
    stdout = getattr(result, "stdout", "") or ""
    stderr = getattr(result, "stderr", "") or ""
    output = getattr(result, "output", "") or ""
    return f"{stdout}\n{stderr}\n{output}"


def test_python_preset_renders_valid_config() -> None:
    preset = resolve_preset("python")
    text = render_config(preset)
    data = tomllib.loads(text)

    assert data["schema_version"] == 1
    assert data["retornatus"]["version"] == __version__
    assert data["project"]["initialized"] is True
    assert data["project"]["preset"] == "python"
    assert data["governance"]["scope"]["code_globs"] == ["src/**", "app/**", "tests/**"]
    checks = data["assurance"]["required_checks"]
    assert [item["name"] for item in checks] == ["pytest", "ruff", "mypy"]
    assert checks[0]["run"] == ["uv", "run", "pytest", "-q"]
    assert checks[0]["types"] == ["test_result"]
    assert checks[1]["run"] == ["uv", "run", "ruff", "check", "src", "app", "tests"]
    assert checks[1]["types"] == ["lint_result"]
    assert checks[2]["run"] == ["uv", "run", "mypy"]
    assert "surfaces" not in data


def test_python_platform_extends_python() -> None:
    base = resolve_preset("python")
    platform = resolve_preset("python-platform")

    assert platform.extends == "python"
    assert [check.name for check in platform.required_checks] == [
        check.name for check in base.required_checks
    ]
    assert [check.run for check in platform.required_checks] == [
        check.run for check in base.required_checks
    ]
    assert platform.code_globs == base.code_globs

    text = render_config(platform)
    data = tomllib.loads(text)
    assert data["project"]["preset"] == "python-platform"
    assert [item["name"] for item in data["assurance"]["required_checks"]] == [
        "pytest",
        "ruff",
        "mypy",
    ]
    assert data["surfaces"]["ship"]["globs"] == [
        "**/Dockerfile",
        "**/docker-compose*.y*ml",
        "**/*.tf",
        "**/terraform/**",
        "**/charts/**",
        "**/helm/**",
        "**/.github/workflows/**",
    ]
    assert "checks" not in data["surfaces"]["ship"]
    assert data["surfaces"]["ship"]["note_subject"] == "ship rollback"
    assert data["surfaces"]["ai"]["globs"] == [
        "**/prompts/**",
        "**/mcp/**",
        "**/evals/**",
        "**/tests/eval/**",
        "**/*llm*",
        "**/*rag*",
        "**/*embed*",
    ]
    assert data["surfaces"]["ai"]["run"] == [
        "uv",
        "run",
        "pytest",
        "tests/eval",
        "-m",
        "not live",
    ]
    assert data["surfaces"]["ai"]["note_subject"] == "ai fallback"
    assert 'name = "compose"' in text
    assert '"docker", "compose", "config", "--quiet"' in text
    assert '"terraform", "validate"' in text
    assert '"helm", "template", "."' in text
    assert '"actionlint"' in text
    assert [check.name for check in platform.ship_checks] == [
        "docker",
        "compose",
        "terraform",
        "helm",
        "workflows",
    ]


def test_fastapi_extends_python_platform_and_python() -> None:
    base = resolve_preset("python")
    platform = resolve_preset("python-platform")
    fastapi = resolve_preset("fastapi")

    assert fastapi.extends == "python-platform"
    assert [check.name for check in fastapi.required_checks] == [
        check.name for check in base.required_checks
    ]
    assert [check.run for check in fastapi.required_checks] == [
        check.run for check in base.required_checks
    ]
    assert fastapi.code_globs == (
        "src/**",
        "app/**",
        "tests/**",
        "routers/**",
        "api/**",
        "schemas/**",
        "alembic/**",
    )
    assert fastapi.ship_globs == platform.ship_globs + ("alembic/**", "**/alembic/**")
    assert [check.name for check in fastapi.ship_checks] == [
        *[check.name for check in platform.ship_checks],
        "alembic",
    ]
    alembic = fastapi.ship_checks[-1]
    assert alembic.optional is True
    assert alembic.suggested is True
    assert alembic.run == ("uv", "run", "alembic", "check")
    assert all(not check.optional for check in platform.ship_checks)
    assert fastapi.ai_globs == platform.ai_globs
    assert fastapi.ai_run == platform.ai_run
    assert fastapi.ship_note_subject == "ship rollback"
    assert [item.name for item in fastapi.suggestions] == ["httpx", "openapi", "alembic-sql"]

    text = render_config(fastapi)
    data = tomllib.loads(text)
    assert data["schema_version"] == 1
    assert data["project"]["preset"] == "fastapi"
    assert data["project"]["initialized"] is True
    assert [item["name"] for item in data["assurance"]["required_checks"]] == [
        "pytest",
        "ruff",
        "mypy",
    ]
    assert "alembic/**" in data["governance"]["scope"]["code_globs"]
    assert "**/alembic/**" in data["surfaces"]["ship"]["globs"]
    assert "checks" not in data["surfaces"]["ship"]
    assert "suggestions" not in data
    assert "# optional = true" in text
    assert '"uv", "run", "alembic", "check"' in text
    assert '"uv", "run", "alembic", "upgrade", "head", "--sql"' in text
    assert "httpx TestClient" in text
    assert "app.openapi()" in text
    assert '"docker", "build", "."' in text


def test_extends_appends_globs_and_ship_checks() -> None:
    def reader(name: str) -> dict[str, object]:
        if name == "base":
            return {
                "name": "base",
                "summary": "Base",
                "governance": {"scope": {"code_globs": ["src/**"]}},
                "surfaces": {
                    "ship": {
                        "globs": ["**/Dockerfile"],
                        "checks": [
                            {
                                "name": "docker",
                                "globs": ["**/Dockerfile"],
                                "run": ["docker", "build", "."],
                            }
                        ],
                    }
                },
            }
        if name == "child":
            return {
                "name": "child",
                "summary": "Child",
                "extends": "base",
                "governance": {"scope": {"code_globs": ["app/**"]}},
                "surfaces": {
                    "ship": {
                        "globs": ["alembic/**"],
                        "checks": [
                            {
                                "name": "alembic",
                                "optional": True,
                                "globs": ["alembic/**"],
                                "run": ["uv", "run", "alembic", "check"],
                            }
                        ],
                    }
                },
            }
        raise FileNotFoundError(name)

    child = resolve_preset("child", reader=reader)
    assert child.code_globs == ("src/**", "app/**")
    assert child.ship_globs == ("**/Dockerfile", "alembic/**")
    assert [check.name for check in child.ship_checks] == ["docker", "alembic"]
    assert child.ship_checks[0].optional is False
    assert child.ship_checks[1].optional is True


def test_list_presets_and_show() -> None:
    catalog = list_presets()
    assert [name for name, _summary in catalog] == ["fastapi", "python", "python-platform"]
    shown = render_preset_document("python-platform")
    assert shown.startswith("# preset: python-platform\n# extends: python\n")
    assert tomllib.loads(shown)["project"]["preset"] == "python-platform"
    fastapi = render_preset_document("fastapi")
    assert fastapi.startswith("# preset: fastapi\n# extends: python-platform\n")
    assert tomllib.loads(fastapi)["project"]["preset"] == "fastapi"


def test_unknown_preset_lists_available_names() -> None:
    with pytest.raises(UsageError, match="python-platform") as caught:
        resolve_preset("nope")
    assert "python" in str(caught.value)
    assert "Available presets" in str(caught.value)


def test_extend_cycle_is_an_error() -> None:
    def reader(name: str) -> dict[str, object]:
        if name == "a":
            return {"name": "a", "summary": "A", "extends": "b"}
        if name == "b":
            return {"name": "b", "summary": "B", "extends": "a"}
        raise FileNotFoundError(name)

    with pytest.raises(UsageError, match="cycle"):
        resolve_preset("a", reader=reader)


def test_no_preset_path_is_unchanged(tmp_path: Path) -> None:
    result = initialize_project(tmp_path)

    assert result.created is True
    assert result.preset is None
    assert result.config_written is True
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert text == gitignore_block()
    assert text.count(GITIGNORE_BEGIN) == 1
    with (tmp_path / ".retornatus" / "config.toml").open("rb") as handle:
        config = tomllib.load(handle)
    assert set(config) == {"schema_version", "retornatus", "project"}
    assert "preset" not in config["project"]
    assert "surfaces" not in config
    for relative in DIRECTORY_TREE:
        assert (tmp_path / ".retornatus" / relative).is_dir()


def test_preset_init_writes_config_and_gitignore(tmp_path: Path) -> None:
    result = initialize_project(tmp_path, preset="python")

    assert result.created is True
    assert result.config_written is True
    assert GITIGNORE_BEGIN in (tmp_path / ".gitignore").read_text(encoding="utf-8")
    with (tmp_path / ".retornatus" / "config.toml").open("rb") as handle:
        config = tomllib.load(handle)
    assert config["project"]["preset"] == "python"
    assert (tmp_path / ".retornatus" / "project" / "project.md").is_file()


def test_existing_config_is_not_overwritten_without_force_config(tmp_path: Path) -> None:
    initialize_project(tmp_path, preset="python")
    config = tmp_path / ".retornatus" / "config.toml"
    original = config.read_text(encoding="utf-8")

    refused = initialize_project(tmp_path, preset="python-platform")
    forced = initialize_project(tmp_path, preset="python-platform", force=True)

    assert refused.config_preserved is True
    assert forced.config_preserved is True
    assert config.read_text(encoding="utf-8") == original

    replaced = initialize_project(tmp_path, preset="python-platform", force_config=True)
    assert replaced.config_written is True
    assert replaced.config_preserved is False
    with config.open("rb") as handle:
        data = tomllib.load(handle)
    assert data["project"]["preset"] == "python-platform"
    assert config.read_text(encoding="utf-8").count(GITIGNORE_BEGIN) == 0
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8").count(GITIGNORE_BEGIN) == 1


def test_cli_list_presets_does_not_write(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--list-presets", str(tmp_path)])

    assert result.exit_code == 0, _combined(result)
    blob = _combined(result)
    assert "fastapi:" in blob
    assert "python:" in blob
    assert "python-platform:" in blob
    assert not (tmp_path / ".retornatus").exists()
    assert not (tmp_path / ".gitignore").exists()


def test_cli_unknown_preset_exits_with_the_list(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--preset", "nope", str(tmp_path)])

    assert result.exit_code == 2, _combined(result)
    blob = _combined(result)
    assert "Unknown preset 'nope'" in blob
    assert "python-platform" in blob
    assert not (tmp_path / ".retornatus").exists()
    assert not (tmp_path / ".gitignore").exists()


def test_cli_refuses_overwrite_and_preset_show(tmp_path: Path) -> None:
    first = runner.invoke(app, ["init", "--preset", "python", str(tmp_path)])
    assert first.exit_code == 0, _combined(first)
    original = (tmp_path / ".retornatus" / "config.toml").read_text(encoding="utf-8")

    second = runner.invoke(app, ["init", "--preset", "python-platform", str(tmp_path)])
    assert second.exit_code == 1, _combined(second)
    assert "--force-config" in _combined(second)
    assert (tmp_path / ".retornatus" / "config.toml").read_text(encoding="utf-8") == original

    listed = runner.invoke(app, ["preset", "list"])
    assert listed.exit_code == 0, _combined(listed)
    assert "python-platform:" in listed.stdout

    shown = runner.invoke(app, ["preset", "show", "python"])
    assert shown.exit_code == 0, _combined(shown)
    assert "uv" in shown.stdout
    missing = runner.invoke(app, ["preset", "show", "missing"])
    assert missing.exit_code == 2
    assert "Available presets" in _combined(missing)


def test_preset_toml_is_readable_from_an_installed_wheel(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    built = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(dist)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert built.returncode == 0, built.stderr
    wheels = list(dist.glob("*.whl"))
    assert len(wheels) == 1
    with zipfile.ZipFile(wheels[0]) as archive:
        names = set(archive.namelist())
    assert "retornatus/bootstrap/presets/python.toml" in names
    assert "retornatus/bootstrap/presets/python-platform.toml" in names
    assert "retornatus/bootstrap/presets/fastapi.toml" in names

    venv = tmp_path / "venv"
    assert subprocess.run(["uv", "venv", str(venv)], check=False, cwd=ROOT).returncode == 0
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    installed = subprocess.run(
        ["uv", "pip", "install", "--python", str(python), str(wheels[0])],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert installed.returncode == 0, installed.stderr
    script = (
        "from importlib.resources import files\n"
        "root = files('retornatus.bootstrap.presets')\n"
        "python_toml = root.joinpath('python.toml').read_text(encoding='utf-8')\n"
        "platform = root.joinpath('python-platform.toml').read_text(encoding='utf-8')\n"
        "fastapi = root.joinpath('fastapi.toml').read_text(encoding='utf-8')\n"
        "assert 'name = \"python\"' in python_toml\n"
        "assert 'extends = \"python\"' in platform\n"
        "assert 'extends = \"python-platform\"' in fastapi\n"
    )
    ran = subprocess.run(
        [str(python), "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert ran.returncode == 0, ran.stderr
