"""CLI command: agent Stop hook."""

from __future__ import annotations

import sys
from pathlib import Path

import typer

from retornatus.cli.groups import hook_app


@hook_app.command("stop")
def hook_stop(
    host: str = typer.Option(
        ...,
        "--host",
        help="Agent host: claude, cursor, or codex.",
    ),
    path: Path | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root. Omit to walk up from the working directory.",
    ),
) -> None:
    """Allow or block an agent turn from the host's Stop hook JSON on stdin.

    Exit 0 either way. A block is host JSON on stdout. Failures print one
    diagnostic on stderr and allow the stop.
    """
    from retornatus.application.agent_hooks.stop import handle_stop

    raw = sys.stdin.read()
    start = path if path is not None else Path.cwd()
    response = handle_stop(host, raw, start=start, walk=path is None)
    if response.stderr:
        sys.stderr.write(response.stderr)
    if response.stdout:
        sys.stdout.write(response.stdout)
    raise typer.Exit(code=response.exit_code)
