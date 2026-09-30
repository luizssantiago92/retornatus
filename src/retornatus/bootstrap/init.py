"""Initialize a minimal `.retornatus/` project tree (PRD §52 / M0)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import tomli_w

from retornatus import __version__
from retornatus.bootstrap.gitignore import (
    ensure_retornatus_gitignore,
    tracked_private_key_files,
)
from retornatus.bootstrap.presets import render_config, resolve_preset
from retornatus.constants import RETORNATUS_DIR

SCHEMA_VERSION = 1

DIRECTORY_TREE: tuple[str, ...] = (
    "project/decisions",
    "changes",
    "governance/rules",
    "governance/bypasses",
    "adaptation/learnings",
    "adaptation/skills",
    "index",
    "runtime/locks",
    "runtime/executions",
    "runtime/cache",
)

DEFAULT_CONFIG: dict[str, object] = {
    "schema_version": SCHEMA_VERSION,
    "retornatus": {
        "version": __version__,
    },
    "project": {
        "initialized": True,
    },
}

DEFAULT_PROJECT_MD = """# Project

Retornatus project continuity notes live here.

Agents and humans express intent. Retornatus owns structure.
"""


@dataclass(frozen=True)
class InitResult:
    """Outcome of `retornatus init`."""

    root: Path
    retornatus_dir: Path
    created: bool
    already_initialized: bool
    gitignore_updated: bool = False
    tracked_private_keys: tuple[str, ...] = ()
    preset: str | None = None
    config_written: bool = False
    config_preserved: bool = False


def find_project_root(start: Path | None = None) -> Path:
    """Resolve the working directory used for Retornatus operations."""
    return (start or Path.cwd()).resolve()


def is_initialized(root: Path) -> bool:
    """Return True when a Retornatus config already exists under root."""
    return (root / RETORNATUS_DIR / "config.toml").is_file()


def initialize_project(
    root: Path | None = None,
    *,
    force: bool = False,
    preset: str | None = None,
    force_config: bool = False,
) -> InitResult:
    """
    Create a valid minimal Retornatus project under ``root``.

    Acceptance (PRD M0): ``retornatus init`` creates a valid minimal project.
    ``preset`` writes a packaged config. An existing config is kept unless
    ``force_config`` is set. ``force`` without a preset still rewrites the
    minimal config, which is the historical behavior.
    """
    project_root = find_project_root(root)
    retornatus_dir = project_root / RETORNATUS_DIR
    selected = preset.strip() if isinstance(preset, str) and preset.strip() else None
    # Resolve before any write so an unknown preset leaves the tree alone.
    rendered = render_config(resolve_preset(selected)) if selected else None
    gitignore_updated = ensure_retornatus_gitignore(project_root)
    tracked = tuple(tracked_private_key_files(project_root))
    exists = is_initialized(project_root)

    if selected and exists and not force_config:
        return InitResult(
            root=project_root,
            retornatus_dir=retornatus_dir,
            created=False,
            already_initialized=True,
            gitignore_updated=gitignore_updated,
            tracked_private_keys=tracked,
            preset=selected,
            config_written=False,
            config_preserved=True,
        )

    if not selected and exists and not force:
        return InitResult(
            root=project_root,
            retornatus_dir=retornatus_dir,
            created=False,
            already_initialized=True,
            gitignore_updated=gitignore_updated,
            tracked_private_keys=tracked,
        )

    retornatus_dir.mkdir(parents=True, exist_ok=True)

    for relative in DIRECTORY_TREE:
        (retornatus_dir / relative).mkdir(parents=True, exist_ok=True)

    config_path = retornatus_dir / "config.toml"
    if rendered is None:
        config_path.write_bytes(tomli_w.dumps(DEFAULT_CONFIG).encode("utf-8"))
    else:
        config_path.write_text(rendered, encoding="utf-8")

    project_md = retornatus_dir / "project" / "project.md"
    if not project_md.exists() or force:
        project_md.write_text(DEFAULT_PROJECT_MD, encoding="utf-8")

    # ``--force`` without a preset still reports a fresh init, as before.
    recreated = not exists or (selected is None and force)
    return InitResult(
        root=project_root,
        retornatus_dir=retornatus_dir,
        created=recreated,
        already_initialized=exists and not recreated,
        gitignore_updated=gitignore_updated,
        tracked_private_keys=tracked,
        preset=selected,
        config_written=True,
        config_preserved=False,
    )
