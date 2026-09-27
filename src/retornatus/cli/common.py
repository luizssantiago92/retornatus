"""Shared CLI helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import typer

from retornatus.application.change.workflow import TaskSpec


def configure_stdio() -> None:
    # Windows consoles often default to a legacy code page; keep UTF-8 help/status readable.
    # Use getattr so mypy accepts TextIO (reconfigure exists on TextIOWrapper only).
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                pass


def resolve_root(path: Path | None) -> Path:
    """Project root from ``--path`` or the current directory, fully resolved."""
    return (path or Path.cwd()).resolve()


def parse_task_specs(
    tasks: list[str] | None,
    depends: list[str] | None,
    resources: list[str] | None,
) -> list[TaskSpec] | None:
    """
    Build TaskSpecs from CLI flags.

    --task descriptions are independent by default.
    --depends ``1:0`` means task index 1 depends on task index 0.
    --resource ``0:app/main.py`` assigns a resource key to task index 0.
    """
    if not tasks:
        return None
    specs = [TaskSpec(description=t) for t in tasks]
    for item in depends or []:
        if ":" not in item:
            raise typer.BadParameter(f"Invalid --depends {item!r}; expected INDEX:DEP[,DEP]")
        left, right = item.split(":", 1)
        try:
            idx = int(left)
            dep_indices = [int(x) for x in right.split(",") if x.strip() != ""]
        except ValueError as exc:
            raise typer.BadParameter(f"Invalid --depends {item!r}") from exc
        if idx < 0 or idx >= len(specs):
            raise typer.BadParameter(f"--depends index out of range: {idx}")
        specs[idx].depends_on_indices = dep_indices
    for item in resources or []:
        if ":" not in item:
            raise typer.BadParameter(
                f"Invalid --resource {item!r}; expected INDEX:resource/path"
            )
        left, right = item.split(":", 1)
        try:
            idx = int(left)
        except ValueError as exc:
            raise typer.BadParameter(f"Invalid --resource {item!r}") from exc
        if idx < 0 or idx >= len(specs):
            raise typer.BadParameter(f"--resource index out of range: {idx}")
        existing = list(specs[idx].resources or [])
        existing.append(right)
        specs[idx].resources = existing
    return specs
