"""Omission gate exemption for dependency-bot pull requests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from retornatus.application.governance.gates import GateName
from retornatus.application.governance.omission import (
    DEFAULT_BOT_AUTHORS,
    DEFAULT_BOT_PATHS,
    BotExemptionSettings,
    assess_omission,
    evaluate_bot_exemption,
    load_bot_exemption,
    normalize_author,
    path_counts_as_code,
)
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app
from retornatus.domain.errors import UsageError
from retornatus.infrastructure.persistence.repository import FileRepository

runner = CliRunner()
ROOT = Path(__file__).resolve().parents[1]
_SCHEMA = json.loads((ROOT / "schemas" / "verdict-v1.schema.json").read_text(encoding="utf-8"))


def _git(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "omission@retornatus.local"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Omission Test"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    (root / "README").write_text("base\n", encoding="utf-8")
    _commit(root, "base")


def _commit(root: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", message], cwd=root, check=True, capture_output=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _defaults() -> BotExemptionSettings:
    return BotExemptionSettings(True, DEFAULT_BOT_AUTHORS, DEFAULT_BOT_PATHS)


def _write_exemption(root: Path, table: dict[str, object]) -> None:
    repo = FileRepository(root)
    data, rev = repo.load_config()
    governance = data.get("governance")
    if not isinstance(governance, dict):
        governance = {}
    governance["omission"] = {"bot_exemption": table}
    data["governance"] = governance
    repo.save_config(data, expected=rev)


def test_schema_gate_enum_includes_omission() -> None:
    assert set(_SCHEMA["properties"]["gate"]["enum"]) == {item.value for item in GateName}
    assert "omission" in _SCHEMA["properties"]["gate"]["enum"]


def test_code_paths_match_the_historical_patterns() -> None:
    assert path_counts_as_code("src/app.py")
    assert path_counts_as_code("src/pkg/mod.py")
    assert path_counts_as_code("tests/test_app.py")
    assert path_counts_as_code("scripts/github_action.sh")
    assert path_counts_as_code("templates/ci/retornatus-pr.yml")
    assert path_counts_as_code("pyproject.toml")
    assert path_counts_as_code("uv.lock")
    assert path_counts_as_code("./src/app.py")
    assert not path_counts_as_code("src2/app.py")
    assert not path_counts_as_code("README.md")
    assert not path_counts_as_code(".github/workflows/ci.yml")
    assert not path_counts_as_code("pkg/pyproject.toml")


@pytest.mark.parametrize(
    "path",
    [
        "pyproject.toml",
        "services/api/pyproject.toml",
        "uv.lock",
        "pkg/uv.lock",
        "poetry.lock",
        "requirements.txt",
        "requirements-dev.txt",
        "apps/api/requirements.txt",
        "package.json",
        "frontend/package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "Cargo.toml",
        "crates/foo/Cargo.lock",
        "go.mod",
        "go.sum",
        ".github/workflows/ci.yml",
        ".github/workflows/ci.yaml",
        ".github/workflows/dependabot.yml",
        "./pyproject.toml",
        "pkg\\uv.lock",
    ],
)
def test_default_allow_list_matches_manifests(path: str) -> None:
    decision = evaluate_bot_exemption([path], author="dependabot[bot]", settings=_defaults())
    assert decision.exempted, path
    assert "dependabot[bot]" in decision.notice
    assert "exempted" in decision.notice
    assert "allow-list" in decision.notice


@pytest.mark.parametrize(
    "path",
    [
        "src/app.py",
        "src/pkg/mod.py",
        "requirements.txt.bak",
        "my-requirements.txt",
        "requirements/base.txt",
        "pyproject.toml.bak",
        "notpyproject.toml",
        "package.json.new",
        "yarn.lock.bak",
        ".github/workflows/nested/ci.yml",
        ".github/workflows/ci.yml.txt",
        ".github/workflows/ci.YML",
        ".github/workflow/ci.yml",
        "github/workflows/ci.yml",
        "README.md",
        "docs/guide/Gates.md",
    ],
)
def test_default_allow_list_rejects_other_paths(path: str) -> None:
    decision = evaluate_bot_exemption([path], author="renovate[bot]", settings=_defaults())
    assert not decision.exempted, path
    assert decision.notice == ""


def test_bot_with_only_manifests_is_exempt_and_names_the_files() -> None:
    decision = evaluate_bot_exemption(
        ["pyproject.toml", "uv.lock"],
        author=" dependabot[bot] ",
        settings=_defaults(),
    )
    assert decision.exempted
    assert "pyproject.toml" in decision.notice
    assert "uv.lock" in decision.notice


def test_bot_with_a_source_file_is_not_exempt() -> None:
    decision = evaluate_bot_exemption(
        ["pyproject.toml", "src/app.py"],
        author="dependabot[bot]",
        settings=_defaults(),
    )
    assert not decision.exempted


def test_human_with_only_manifests_is_not_exempt() -> None:
    decision = evaluate_bot_exemption(
        ["pyproject.toml", "uv.lock"],
        author="octocat",
        settings=_defaults(),
    )
    assert not decision.exempted


def test_author_match_is_exact() -> None:
    settings = _defaults()
    assert not evaluate_bot_exemption(["uv.lock"], author="dependabot", settings=settings).exempted
    assert not evaluate_bot_exemption(["uv.lock"], author="Dependabot[bot]", settings=settings).exempted
    assert not evaluate_bot_exemption(["uv.lock"], author="not-dependabot[bot]", settings=settings).exempted
    assert not evaluate_bot_exemption(["uv.lock"], author="", settings=settings).exempted
    assert evaluate_bot_exemption(["uv.lock"], author="renovate[bot]", settings=settings).exempted


def test_disabled_config_is_not_exempt() -> None:
    settings = BotExemptionSettings(False, DEFAULT_BOT_AUTHORS, DEFAULT_BOT_PATHS)
    decision = evaluate_bot_exemption(["pyproject.toml"], author="dependabot[bot]", settings=settings)
    assert not decision.exempted


def test_empty_file_list_is_not_exempt() -> None:
    decision = evaluate_bot_exemption([], author="dependabot[bot]", settings=_defaults())
    assert not decision.exempted


def test_custom_authors_and_paths_replace_the_defaults() -> None:
    settings = BotExemptionSettings(True, ("my-bot",), ("src/vendor.py",))
    assert evaluate_bot_exemption(["src/vendor.py"], author="my-bot", settings=settings).exempted
    assert not evaluate_bot_exemption(["src/vendor.py"], author="dependabot[bot]", settings=settings).exempted
    assert not evaluate_bot_exemption(["pyproject.toml"], author="my-bot", settings=settings).exempted
    assert not evaluate_bot_exemption(["src/vendor.py", "src/app.py"], author="my-bot", settings=settings).exempted


def test_notice_truncates_a_long_file_list() -> None:
    paths = [f"requirements-{index}.txt" for index in range(13)]
    decision = evaluate_bot_exemption(paths, author="dependabot[bot]", settings=_defaults())
    assert decision.exempted
    assert "+1 more" in decision.notice
    assert "requirements-12.txt" not in decision.notice


def test_author_control_characters_and_length_are_rejected() -> None:
    with pytest.raises(UsageError, match="control"):
        normalize_author("dependabot[bot]\n")
    with pytest.raises(UsageError, match="too long"):
        normalize_author("a" * 257)
    assert normalize_author("  renovate[bot]  ") == "renovate[bot]"


def test_missing_table_uses_defaults(tmp_path: Path) -> None:
    settings = load_bot_exemption(tmp_path)
    assert settings.enabled is True
    assert settings.authors == DEFAULT_BOT_AUTHORS
    assert settings.paths == DEFAULT_BOT_PATHS


def test_scope_table_does_not_disable_the_exemption(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    repo = FileRepository(tmp_path)
    data, rev = repo.load_config()
    data["governance"] = {"scope": {"denied_globs": ["**/.env"]}}
    repo.save_config(data, expected=rev)
    settings = load_bot_exemption(tmp_path)
    assert settings.enabled is True
    assert "dependabot[bot]" in settings.authors


def test_explicit_enabled_false_and_replacement_lists(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    _write_exemption(tmp_path, {"enabled": False, "authors": ["my-bot"], "paths": ["notes.lock"]})
    settings = load_bot_exemption(tmp_path)
    assert settings.enabled is False
    assert settings.authors == ("my-bot",)
    assert settings.paths == ("notes.lock",)


@pytest.mark.parametrize(
    ("governance", "match"),
    [
        ("nope", r"\[governance\]"),
        ({"omission": "nope"}, r"governance\.omission\]"),
        ({"omission": {"bot_exemption": "nope"}}, "bot_exemption"),
        ({"omission": {"bot_exemption": {"enabled": "yes"}}}, "enabled"),
        ({"omission": {"bot_exemption": {"authors": "dependabot[bot]"}}}, "authors"),
        ({"omission": {"bot_exemption": {"paths": [""]}}}, "empty"),
        ({"omission": {"bot_exemption": {"authors": ["bad\nname"]}}}, "control"),
        ({"omission": {}}, ""),
    ],
)
def test_exemption_config_shapes(tmp_path: Path, governance: object, match: str) -> None:
    initialize_project(tmp_path)
    repo = FileRepository(tmp_path)
    data, rev = repo.load_config()
    data["governance"] = governance
    repo.save_config(data, expected=rev)
    if match:
        with pytest.raises(UsageError, match=match):
            load_bot_exemption(tmp_path)
        return
    settings = load_bot_exemption(tmp_path)
    assert settings.authors == DEFAULT_BOT_AUTHORS


def test_assess_skips_when_a_change_id_was_supplied(tmp_path: Path) -> None:
    report = assess_omission(tmp_path, declared_change="C-0041")
    assert report.passed
    assert "skipped" in report.messages[0]


def test_assess_fails_outside_a_work_tree(tmp_path: Path) -> None:
    report = assess_omission(tmp_path)
    assert not report.passed
    assert "work tree" in report.messages[0]


def test_gate_exempts_a_bot_manifest_diff(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (tmp_path / "uv.lock").write_text("# lock\n", encoding="utf-8")
    base = _commit(tmp_path, "manifests")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\nversion = '2'\n", encoding="utf-8")
    (tmp_path / "uv.lock").write_text("# lock\nversion = 2\n", encoding="utf-8")
    _commit(tmp_path, "bump")
    result = runner.invoke(
        app,
        [
            "gate",
            "omission",
            "--base",
            base,
            "--pr-author",
            "dependabot[bot]",
            "--path",
            str(tmp_path),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.stderr
    document = json.loads(result.stdout)
    assert document["gate"] == "omission"
    assert document["passed"] is True
    assert document["verdict"] == "PASS"
    assert document["errors"] == []
    assert document["warnings"]
    assert document["warnings"][0].startswith("WARN ")
    assert "exempted" in document["warnings"][0]
    assert "dependabot[bot]" in document["warnings"][0]


def test_gate_fails_a_bot_that_touches_source(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    source = tmp_path / "src" / "pkg" / "app.py"
    source.parent.mkdir(parents=True)
    source.write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    base = _commit(tmp_path, "base-code")
    source.write_text("value = 2\n", encoding="utf-8")
    _commit(tmp_path, "edit")
    result = runner.invoke(
        app,
        ["gate", "omission", "--base", base, "--pr-author", "dependabot[bot]", "--path", str(tmp_path)],
    )
    assert result.exit_code == 1, result.stdout
    assert "no .retornatus Change was touched" in result.stdout
    assert "exempted" not in result.stdout


def test_gate_fails_a_human_manifest_diff(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    (tmp_path / "uv.lock").write_text("# lock\n", encoding="utf-8")
    base = _commit(tmp_path, "lock")
    (tmp_path / "uv.lock").write_text("# lock\nchanged\n", encoding="utf-8")
    _commit(tmp_path, "bump")
    result = runner.invoke(
        app,
        ["gate", "omission", "--base", base, "--pr-author", "octocat", "--path", str(tmp_path)],
    )
    assert result.exit_code == 1, result.stdout
    assert "exempted" not in result.stdout


def test_gate_fails_when_the_exemption_is_disabled(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    _write_exemption(tmp_path, {"enabled": False})
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    base = _commit(tmp_path, "manifest")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\nversion = '2'\n", encoding="utf-8")
    _commit(tmp_path, "bump")
    result = runner.invoke(
        app,
        ["gate", "omission", "--base", base, "--pr-author", "dependabot[bot]", "--path", str(tmp_path)],
    )
    assert result.exit_code == 1, result.stdout
    assert "exempted" not in result.stdout


def test_gate_honors_custom_authors_and_paths(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    _write_exemption(tmp_path, {"authors": ["my-bot"], "paths": ["src/vendor.py"]})
    vendor = tmp_path / "src" / "vendor.py"
    vendor.parent.mkdir()
    vendor.write_text("value = 1\n", encoding="utf-8")
    base = _commit(tmp_path, "vendor")
    vendor.write_text("value = 2\n", encoding="utf-8")
    _commit(tmp_path, "bump")
    allowed = runner.invoke(
        app,
        ["gate", "omission", "--base", base, "--pr-author", "my-bot", "--path", str(tmp_path)],
    )
    assert allowed.exit_code == 0, allowed.stdout
    assert "exempted" in allowed.stdout
    denied = runner.invoke(
        app,
        ["gate", "omission", "--base", base, "--pr-author", "dependabot[bot]", "--path", str(tmp_path)],
    )
    assert denied.exit_code == 1, denied.stdout


def test_gate_ignores_a_workflow_only_diff(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    workflow = tmp_path / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("name: CI\n", encoding="utf-8")
    base = _commit(tmp_path, "workflow")
    workflow.write_text("name: CI\non: push\n", encoding="utf-8")
    _commit(tmp_path, "bump")
    result = runner.invoke(
        app,
        ["gate", "omission", "--base", base, "--pr-author", "dependabot[bot]", "--path", str(tmp_path)],
    )
    assert result.exit_code == 0, result.stdout
    assert "not triggered" in result.stdout
    assert "exempted" not in result.stdout


def test_gate_exempts_a_bot_that_bumps_a_workflow_and_a_lockfile(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    workflow = tmp_path / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("name: CI\n", encoding="utf-8")
    (tmp_path / "uv.lock").write_text("# lock\n", encoding="utf-8")
    base = _commit(tmp_path, "both")
    workflow.write_text("name: CI\non: push\n", encoding="utf-8")
    (tmp_path / "uv.lock").write_text("# lock\nv2\n", encoding="utf-8")
    _commit(tmp_path, "bump")
    result = runner.invoke(
        app,
        ["gate", "omission", "--base", base, "--pr-author", "renovate[bot]", "--path", str(tmp_path)],
    )
    assert result.exit_code == 0, result.stdout
    assert "exempted" in result.stdout


def test_gate_fails_when_a_bot_also_edits_the_readme(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    base = _commit(tmp_path, "manifest")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\nversion = '2'\n", encoding="utf-8")
    (tmp_path / "README").write_text("edited by the bot\n", encoding="utf-8")
    _commit(tmp_path, "mixed")
    result = runner.invoke(
        app,
        ["gate", "omission", "--base", base, "--pr-author", "dependabot[bot]", "--path", str(tmp_path)],
    )
    assert result.exit_code == 1, result.stdout


def test_gate_passes_when_a_change_is_in_the_diff(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("value = 1\n", encoding="utf-8")
    base = _commit(tmp_path, "app")
    change = tmp_path / ".retornatus" / "changes" / "C-0007" / "situation.md"
    change.parent.mkdir(parents=True)
    change.write_text("situation\n", encoding="utf-8")
    (change.parent / "contract.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "src" / "app.py").write_text("value = 2\n", encoding="utf-8")
    _commit(tmp_path, "with change")
    result = runner.invoke(
        app,
        ["gate", "omission", "--base", base, "--pr-author", "octocat", "--path", str(tmp_path)],
    )
    assert result.exit_code == 0, result.stdout
    assert "Change is in the diff" in result.stdout


def test_gate_does_not_treat_a_loose_change_file_as_a_change(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    changes = tmp_path / ".retornatus" / "changes"
    changes.mkdir(parents=True, exist_ok=True)
    (tmp_path / "uv.lock").write_text("# lock\n", encoding="utf-8")
    base = _commit(tmp_path, "loose")
    (changes / "C-0007").write_text("not a directory\n", encoding="utf-8")
    note = changes / "C-x" / "note.md"
    note.parent.mkdir()
    note.write_text("not an id\n", encoding="utf-8")
    other = changes / "NOPE" / "note.md"
    other.parent.mkdir()
    other.write_text("not a change id\n", encoding="utf-8")
    (tmp_path / "uv.lock").write_text("# lock\nv2\n", encoding="utf-8")
    _commit(tmp_path, "bump")
    result = runner.invoke(
        app,
        ["gate", "omission", "--base", base, "--pr-author", "octocat", "--path", str(tmp_path)],
    )
    assert result.exit_code == 1, result.stdout


def test_declared_change_skips_omission_even_for_a_human(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("value = 1\n", encoding="utf-8")
    base = _commit(tmp_path, "app")
    (tmp_path / "src" / "app.py").write_text("value = 2\n", encoding="utf-8")
    _commit(tmp_path, "edit")
    result = runner.invoke(
        app,
        [
            "gate",
            "omission",
            "--base",
            base,
            "--change",
            "C-0041",
            "--pr-author",
            "octocat",
            "--path",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "skipped" in result.stdout


def test_gate_rejects_a_spoofed_author_flag(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    result = runner.invoke(
        app,
        ["gate", "omission", "--pr-author", "dependabot[bot]\n", "--path", str(tmp_path)],
    )
    assert result.exit_code == 2
    assert "control" in result.stderr


def test_gate_usage_error_when_base_and_staged_are_combined(tmp_path: Path) -> None:
    _git(tmp_path)
    result = runner.invoke(
        app,
        ["gate", "omission", "--base", "HEAD", "--staged", "--path", str(tmp_path)],
    )
    assert result.exit_code == 2, result.stderr


def test_staged_manifest_diff_can_be_exempt(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    (tmp_path / "uv.lock").write_text("# lock\n", encoding="utf-8")
    _commit(tmp_path, "lock")
    (tmp_path / "uv.lock").write_text("# lock\nv2\n", encoding="utf-8")
    subprocess.run(["git", "add", "uv.lock"], cwd=tmp_path, check=True, capture_output=True)
    result = runner.invoke(
        app,
        ["gate", "omission", "--staged", "--pr-author", "dependabot[bot]", "--path", str(tmp_path)],
    )
    assert result.exit_code == 0, result.stdout
    assert "exempted" in result.stdout


def test_action_reads_the_author_from_the_event_payload() -> None:
    action = (ROOT / "action.yml").read_text(encoding="utf-8")
    script = (ROOT / "scripts" / "github_action.sh").read_text(encoding="utf-8")
    assert "PR_AUTHOR: ${{ github.event.pull_request.user.login }}" in action
    assert "pull_request.title" not in action
    assert "pull_request.body" not in action
    assert "commits" not in action.split("PR_AUTHOR", 1)[1].split("run:", 1)[0]
    assert "gate omission" in script
    assert '--pr-author "$PR_AUTHOR"' in script
    assert "pull_request.title" not in script
    assert "pull_request.body" not in script
    assert "git log" not in script
    assert "::warning::" in script


def test_guides_name_the_config_and_how_to_disable_it() -> None:
    gates = (ROOT / "docs" / "guide" / "Gates.md").read_text(encoding="utf-8")
    action = (ROOT / "docs" / "guide" / "GitHub-Action.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    template = (ROOT / "templates" / "ci" / "retornatus-pr.yml").read_text(encoding="utf-8")
    assert "[governance.omission.bot_exemption]" in gates
    assert "enabled = false" in gates
    assert "dependabot[bot]" in gates
    assert "renovate[bot]" in gates
    assert "pull_request.user.login" in action
    assert "gate omission" in action
    assert "bot_exemption" in readme
    assert "gate omission" in readme
    unreleased, _, _rest = changelog.partition("## [1.9.1]")
    assert "gate omission" in unreleased
    assert "bot_exemption" in unreleased
    assert "bot_exemption" in template
