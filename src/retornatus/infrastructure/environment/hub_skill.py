"""Bundled Retornatus hub skill text (native Cursor/Claude progressive disclosure)."""

from __future__ import annotations

from pathlib import Path


def _hub_skill_text() -> str:
    packaged = Path(__file__).resolve().parent / "hub" / "SKILL.md"
    if packaged.is_file():
        return packaged.read_text(encoding="utf-8")
    # Fallback if wheel layout omits the markdown file
    return (
        "---\nname: retornatus\ndescription: Retornatus hub skill\n---\n\n"
        "# Retornatus Hub\n\nSee package docs.\n"
    )


def install_hub_skill(root: Path) -> Path:
    """Install the Retornatus hub skill into `.cursor/skills/retornatus/`."""
    dest_dir = root.resolve() / ".cursor" / "skills" / "retornatus"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "SKILL.md"
    dest.write_text(_hub_skill_text(), encoding="utf-8")
    return dest
