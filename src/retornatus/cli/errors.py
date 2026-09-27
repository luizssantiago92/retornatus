"""Map domain failures to a CLI message and a documented exit code.

Exit codes (unchanged for gates and ``verify`` verdicts):

* ``0`` — success, gate passed, ``verify`` SATISFIED, receipt signature ok
* ``1`` — gate STOP, ``verify`` not SATISFIED, signature failed, missing artifact
* ``2`` — usage: invalid id, path escape, bad search query, malformed signing key

``typer.Exit`` raised by a command is not rewritten, so gate and verify keep
the codes they already choose.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

import typer
from typer.core import TyperGroup
from typer.exceptions import Abort, Exit, TyperException

from retornatus.domain.errors import UsageError


def translate_cli_error(exc: BaseException) -> tuple[str, int] | None:
    """Return ``(message, exit_code)`` or ``None`` to let Typer handle it."""
    if isinstance(exc, (Exit, Abort, TyperException)):
        return None
    if isinstance(exc, UsageError):
        return (str(exc), 2)
    if isinstance(exc, json.JSONDecodeError):
        return (f"Invalid JSON: {exc.msg}", 2)
    if isinstance(exc, sqlite3.OperationalError):
        return (
            "Search query is not valid for the index. "
            "Use plain words; punctuation is matched literally.",
            2,
        )
    if isinstance(exc, FileNotFoundError):
        target = exc.filename if exc.filename else str(exc)
        text = str(target).strip() or "file"
        return (f"Not found: {text}", 1)
    if isinstance(exc, ValueError) and str(exc).startswith("Invalid "):
        return (str(exc), 2)
    if isinstance(exc, ValueError):
        return (str(exc), 1)
    return None


class GuardedTyperGroup(TyperGroup):
    """Top-level handler: domain errors become a line on stderr, not a traceback."""

    def invoke(self, ctx: typer.Context) -> Any:
        try:
            return super().invoke(ctx)
        except Exception as exc:
            mapped = translate_cli_error(exc)
            if mapped is None:
                raise
            message, code = mapped
            typer.echo(f"error: {message}", err=True)
            raise Exit(code) from exc
