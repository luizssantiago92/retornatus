"""Brownfield project continuity bootstrap (PRD Memory / Wake)."""

from __future__ import annotations

from pathlib import Path

from retornatus.bootstrap.init import initialize_project, is_initialized
from retornatus.infrastructure.persistence.atomic import atomic_write_text
from retornatus.infrastructure.persistence.paths import RetornatusPaths


def project_init(root: Path) -> Path:
    """
    Map a repository into `.retornatus/project/project.md` continuity notes.

    Lightweight brownfield context — not a Spec Guardrails clone of project-init.
    """
    root = root.resolve()
    if not is_initialized(root):
        initialize_project(root)

    paths = RetornatusPaths(root)
    markers: list[str] = []
    for name in (
        "pyproject.toml",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "composer.json",
        "Gemfile",
    ):
        if (root / name).exists():
            markers.append(name)

    readme = ""
    for candidate in ("README.md", "Readme.md", "readme.md"):
        p = root / candidate
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace")
            readme = text.strip().splitlines()[0] if text.strip() else ""
            break

    body = f"""# Project

Retornatus continuity map for `{root.name}`.

## Identity

- Path: `{root}`
- README signal: {readme or "(none)"}

## Detected manifests

{chr(10).join(f"- `{m}`" for m in markers) or "- (none detected)"}

## Conventions

_Agents: update this file when durable project conventions are discovered._

## Stack notes

_Fill during Wake / first Change. Prefer facts from the repo over assumptions._
"""
    atomic_write_text(paths.project_md, body)
    return paths.project_md
