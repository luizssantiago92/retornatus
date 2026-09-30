"""CLI command group: preset."""

from __future__ import annotations

import typer

from retornatus.bootstrap.presets import list_presets, render_preset_document
from retornatus.cli.groups import preset_app


@preset_app.command("list")
def preset_list() -> None:
    """List packaged config presets."""
    for name, summary in list_presets():
        typer.echo(f"{name}: {summary}")


@preset_app.command("show")
def preset_show(
    name: str = typer.Argument(..., help="Preset name (for example python-platform)."),
) -> None:
    """Print the config a preset would write."""
    text = render_preset_document(name)
    typer.echo(text, nl=not text.endswith("\n"))
