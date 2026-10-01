"""Public README, guide, and landing page present the init presets."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESETS = ("python", "python-platform", "fastapi", "django", "rag", "worker")
# Bytes of the two mascot WebPs that remain after the neon cutout was removed.
_ASSET_BUDGET = 49_268 + 63_046


def test_readme_presets_section_names_each_preset() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    start = text.index("## Presets")
    next_heading = text.index("\n## ", start + 1)
    section = text[start:next_heading]
    for name in PRESETS:
        assert f"`{name}`" in section
    assert "retornatus init --preset fastapi" in section
    assert "retornatus init --list-presets" in section
    assert "docs/guide/Presets.md" in section
    assert "exited 0" in section


def test_guide_hub_cli_and_overview_cover_presets() -> None:
    hub = (ROOT / "docs/guide/index.html").read_text(encoding="utf-8")
    assert 'href="presets.html"' in hub
    guide_index = (ROOT / "docs/guide/README.md").read_text(encoding="utf-8")
    assert "[Presets](Presets.md)" in guide_index
    cli = (ROOT / "docs/guide/CLI.md").read_text(encoding="utf-8")
    assert "init --preset" in cli
    assert "init --list-presets" in cli
    assert "--force-config" in cli
    assert "preset show" in cli
    overview = (ROOT / "docs/guide/Overview.md").read_text(encoding="utf-8")
    assert "## Init presets" in overview
    for name in PRESETS:
        assert f"`{name}`" in overview


def test_landing_hero_uses_readme_card_and_lists_presets() -> None:
    html = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    assert 'src="assets/retornatus-mascot-readme.webp"' in html
    assert 'id="presets"' in html
    assert "retornatus init --preset fastapi" in html
    for name in PRESETS:
        assert f"<h3>{name}</h3>" in html
    square = "assets/retornatus-mascot-square.webp"
    assert f'href="{square}"' in html
    css = (ROOT / "docs/site.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion: reduce" in css
    assert ".mascot-card" in css


def test_neon_cutout_is_gone_from_live_files_and_assets_shrunk() -> None:
    neon = ROOT / "docs/assets/retornatus-mascot-neon.webp"
    assert not neon.exists()
    live_roots = [
        ROOT / "README.md",
        ROOT / "CHANGELOG.md",
        ROOT / "pyproject.toml",
        ROOT / "docs",
        ROOT / "scripts",
        ROOT / "tests",
        ROOT / ".github",
    ]
    hits: list[str] = []
    for root in live_roots:
        paths = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file()]
        for path in paths:
            if path.name == "test_public_preset_docs.py":
                continue
            if path.suffix.lower() in {".webp", ".png", ".jpg", ".jpeg", ".gif"}:
                if path.name == "retornatus-mascot-neon.webp":
                    hits.append(str(path))
                continue
            try:
                body = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if "retornatus-mascot-neon.webp" in body:
                hits.append(str(path.relative_to(ROOT)))
    # The changelog records the removal. It must not describe the file as the live hero.
    changelog_hits = [item for item in hits if item == "CHANGELOG.md"]
    other_hits = [item for item in hits if item != "CHANGELOG.md"]
    assert other_hits == []
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    unreleased = changelog.split("## [1.4.1]", 1)[0]
    assert "retornatus-mascot-neon.webp` is removed" in unreleased
    hero = "docs site hero uses the same static card as the README, `docs/assets/retornatus-mascot-readme.webp`"
    assert hero in unreleased
    assert "docs site hero uses `docs/assets/retornatus-mascot-neon.webp`" not in unreleased
    assert changelog_hits == ["CHANGELOG.md"]
    assets = list((ROOT / "docs/assets").glob("*.webp"))
    assert {path.name for path in assets} == {
        "retornatus-mascot-readme.webp",
        "retornatus-mascot-square.webp",
    }
    assert sum(path.stat().st_size for path in assets) <= _ASSET_BUDGET
