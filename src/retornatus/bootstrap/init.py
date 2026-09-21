"""Initialize a minimal `.retornatus/` project tree (PRD §52 / M0)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from retornatus.constants import RETORNATUS_DIR

import tomli_w

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
        "version": "0.5.0",
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


def find_project_root(start: Path | None = None) -> Path:
    """Resolve the working directory used for Retornatus operations."""
    return (start or Path.cwd()).resolve()


def is_initialized(root: Path) -> bool:
    """Return True when a Retornatus config already exists under root."""
    return (root / RETORNATUS_DIR / "config.toml").is_file()


def initialize_project(root: Path | None = None, *, force: bool = False) -> InitResult:
    """
    Create a valid minimal Retornatus project under ``root``.

    Acceptance (PRD M0): ``retornatus init`` creates a valid minimal project.
    """
    project_root = find_project_root(root)
    retornatus_dir = project_root / RETORNATUS_DIR

    if is_initialized(project_root) and not force:
        return InitResult(
            root=project_root,
            retornatus_dir=retornatus_dir,
            created=False,
            already_initialized=True,
        )

    retornatus_dir.mkdir(parents=True, exist_ok=True)

    for relative in DIRECTORY_TREE:
        (retornatus_dir / relative).mkdir(parents=True, exist_ok=True)

    config_path = retornatus_dir / "config.toml"
    config_path.write_bytes(tomli_w.dumps(DEFAULT_CONFIG).encode("utf-8"))

    project_md = retornatus_dir / "project" / "project.md"
    if not project_md.exists() or force:
        project_md.write_text(DEFAULT_PROJECT_MD, encoding="utf-8")

    return InitResult(
        root=project_root,
        retornatus_dir=retornatus_dir,
        created=True,
        already_initialized=False,
    )
