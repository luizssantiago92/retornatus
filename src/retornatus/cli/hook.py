"""CLI commands: agent Stop, subagent-stop, session-start, and file-edit hooks."""

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


@hook_app.command("subagent-stop")
def hook_subagent_stop(
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
    """Allow or remind a subagent from the host's subagent-stop JSON on stdin.

    Exit 0 either way. A reminder is host JSON on stdout. Failures print one
    diagnostic on stderr and allow the subagent to finish.
    """
    from retornatus.application.agent_hooks.stop import handle_subagent_stop

    raw = sys.stdin.read()
    start = path if path is not None else Path.cwd()
    response = handle_subagent_stop(host, raw, start=start, walk=path is None)
    if response.stderr:
        sys.stderr.write(response.stderr)
    if response.stdout:
        sys.stdout.write(response.stdout)
    raise typer.Exit(code=response.exit_code)


@hook_app.command("session-start")
def hook_session_start(
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
    """Inject active Change context from the host's session-start JSON on stdin.

    Exit 0 always. Context is host JSON on stdout. No active Change prints
    nothing. Failures print one diagnostic on stderr and inject nothing.
    """
    from retornatus.application.agent_hooks.session import handle_session_start

    raw = sys.stdin.read()
    start = path if path is not None else Path.cwd()
    response = handle_session_start(host, raw, start=start, walk=path is None)
    if response.stderr:
        sys.stderr.write(response.stderr)
    if response.stdout:
        sys.stdout.write(response.stdout)
    raise typer.Exit(code=response.exit_code)


@hook_app.command("file-edit")
def hook_file_edit(
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
    """Warn when a file edit leaves the active Change scope.

    Exit 0 always. A warning or a deny is host JSON on stdout. In-scope
    edits, no active Change, and ``.retornatus/`` print nothing. Failures
    print one diagnostic on stderr and allow the edit.
    """
    from retornatus.application.agent_hooks.file_edit import handle_file_edit

    raw = sys.stdin.read()
    start = path if path is not None else Path.cwd()
    response = handle_file_edit(host, raw, start=start, walk=path is None)
    if response.stderr:
        sys.stderr.write(response.stderr)
    if response.stdout:
        sys.stdout.write(response.stdout)
    raise typer.Exit(code=response.exit_code)
