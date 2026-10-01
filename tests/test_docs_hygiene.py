"""Hub copies, config version warning, and the docs hygiene fixes."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from typer.testing import CliRunner

from retornatus import __version__
from retornatus.bootstrap.doctor import run_doctor
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app

ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()

_OG_IMAGE = "https://luizssantiago92.github.io/retornatus/assets/retornatus-mascot-square.webp"
_LICENSE_URL = "https://github.com/luizssantiago92/retornatus/blob/main/LICENSE"


def _github_anchor(heading: str) -> str:
    """GitHub heading slug: drop punctuation, then turn each space into a hyphen."""
    kept = "".join(ch if (ch.isalnum() or ch in "-_ ") else "" for ch in heading.lower())
    return "#" + kept.replace(" ", "-")


def _section(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    return text[begin : text.index(end, begin)]


def _render_credits() -> str:
    script = ROOT / "scripts" / "build_docs_html.py"
    spec = importlib.util.spec_from_file_location("build_docs_html", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.render_one("credits-and-lineage.md", "credits.html")


def _write_version(root: Path, version_line: str) -> None:
    config = root / ".retornatus" / "config.toml"
    lines = config.read_text(encoding="utf-8").splitlines()
    replaced = [version_line if line.startswith("version = ") else line for line in lines]
    config.write_text("\n".join(replaced) + "\n", encoding="utf-8")


def test_repo_hub_copy_matches_packaged_hub() -> None:
    packaged = (ROOT / "src" / "retornatus" / "infrastructure" / "environment" / "hub" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    copied = (ROOT / ".cursor" / "skills" / "retornatus" / "SKILL.md").read_text(encoding="utf-8")
    assert copied == packaged
    assert "portable HMAC" not in packaged
    assert "Ed25519 receipt (public key in `.retornatus/keys/`)" in packaged


def test_repo_config_version_matches_installed_release() -> None:
    text = (ROOT / ".retornatus" / "config.toml").read_text(encoding="utf-8")
    assert f'version = "{__version__}"' in text


def test_doctor_warns_when_config_version_differs(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    matched = run_doctor(tmp_path)
    assert not any("differs from installed" in warning for warning in matched.warnings)

    _write_version(tmp_path, f'version = "  {__version__}  "')
    padded = run_doctor(tmp_path)
    assert not any("differs from installed" in warning for warning in padded.warnings)

    _write_version(tmp_path, 'version = "0.8.0"')
    drifted = run_doctor(tmp_path)
    assert any(
        "0.8.0" in warning and __version__ in warning and "differs from installed" in warning
        for warning in drifted.warnings
    )
    cli = runner.invoke(app, ["doctor", "--path", str(tmp_path)])
    assert cli.exit_code == 0, cli.stdout
    assert "differs from installed" in cli.stdout

    _write_version(tmp_path, "version = 1")
    numeric = run_doctor(tmp_path)
    assert any("version 1 differs from installed" in warning for warning in numeric.warnings)

    config = tmp_path / ".retornatus" / "config.toml"
    config.write_text("schema_version = 1\n\n[project]\ninitialized = true\n", encoding="utf-8")
    missing = run_doctor(tmp_path)
    assert any("version None differs from installed" in warning for warning in missing.warnings)


def test_readme_anchor_matches_em_dash_heading() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    heading_line = next(line for line in readme.splitlines() if line.startswith("## What you get"))
    heading = heading_line.removeprefix("## ").strip()
    assert "\u2014" in heading
    anchor = _github_anchor(heading)
    assert anchor == "#what-you-get--and-why-it-helps"
    assert f"]({anchor})" in readme
    assert "](#what-you-get-and-why-it-helps)" not in readme


def test_readme_news_does_not_pin_a_package_version() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "What\u2019s new (1.4.0)" not in readme
    assert "What\u2019s new (1.3.0)" not in readme
    assert "What\u2019s new (1.2" not in readme
    assert "What\u2019s new (1.1" not in readme
    section = _section(readme, "## What\u2019s new", "\n## ")
    assert "retornatus==" not in section
    assert "current release" in section
    assert "1.5" in section
    assert "1.9.0" in section
    assert "hook file-edit" in section
    assert "hook subagent-stop" in section
    assert "scope_mode" in section
    changelog = "https://github.com/luizssantiago92/retornatus/blob/main/CHANGELOG.md"
    assert changelog in section
    assert 150 <= len(readme.splitlines()) <= 200


def test_credits_license_and_prd_link_text() -> None:
    source = (ROOT / "docs" / "credits-and-lineage.md").read_text(encoding="utf-8")
    assert "prd/PRD.md" not in source
    assert "[`docs/archive/PRD.md`](archive/PRD.md)" in source
    assert "../LICENSE" not in source
    assert _LICENSE_URL in source

    html = _render_credits()
    assert 'href="guide/license.html"' not in html
    assert f'href="{_LICENSE_URL}"' in html
    assert "prd/PRD.md" not in html
    assert "docs/archive/PRD.md" in html


def test_landing_og_image_and_news_mention_presets() -> None:
    html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    assert f'property="og:image" content="{_OG_IMAGE}"' in html
    news = _section(html, 'id="news"', "</section>")
    assert "1.9.0" in news
    assert "subagent-stop hook" in news
    assert "scope warning hook" in news
    assert "SessionStart" in news
    assert "agent hooks" in news
    assert "init presets" in news
    for name in ("python", "python-platform", "fastapi", "django", "rag"):
        assert name in news


def test_changelog_unreleased_contains_hygiene_notes() -> None:
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    unreleased = log.split("## [1.4.1]", 1)[0]
    assert "Ed25519 receipt" in unreleased
    assert "differs from the installed package" in unreleased
    assert "docs/archive/PRD.md" in unreleased
    assert _OG_IMAGE.split("https://", 1)[1].split("/", 1)[0] in unreleased
    assert "current release" in unreleased


def test_cli_reference_mentions_config_version_warning() -> None:
    cli = (ROOT / "docs" / "guide" / "CLI.md").read_text(encoding="utf-8")
    assert "differs from the installed package" in cli
