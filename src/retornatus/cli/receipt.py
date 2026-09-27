"""Ed25519 receipt commands."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from retornatus.application.assurance.receipt import (
    is_legacy_message,
    keygen,
    load_and_verify_receipt,
    load_signing_key,
    write_verify_receipt,
)
from retornatus.application.assurance.settings import allow_self_reported_enabled
from retornatus.cli.common import resolve_root
from retornatus.cli.groups import receipt_app

_LEGACY_WARNING = (
    "warning: HMAC receipt is deprecated and not portable (legacy_hmac). "
    "Keep the private key out of the agent environment and use Ed25519."
)


def _echo_verification(ok: bool, message: str, data: dict[str, object]) -> None:
    legacy = is_legacy_message(message)
    if legacy:
        typer.echo(_LEGACY_WARNING, err=True)
    typer.echo(
        json.dumps(
            {
                "ok": ok,
                "message": message,
                "change_id": data.get("change_id"),
                "verdict": data.get("verdict"),
                "alg": data.get("alg"),
                "key_id": data.get("key_id"),
                "portable": bool(ok and not legacy),
                "legacy_hmac": legacy,
            },
            indent=2,
        )
    )


@receipt_app.command("keygen")
def receipt_keygen_cmd(
    path: Path | None = typer.Option(None, "--path", "-p"),
    print_private: bool = typer.Option(
        False,
        "--print",
        help=(
            "Print the private key for a CI secret instead of writing it to the "
            "user config directory. The public key is still written into the repo."
        ),
    ),
) -> None:
    """Create an Ed25519 key. The private key stays outside the repository."""
    root = resolve_root(path)
    key_id, public_path, private_path, pem = keygen(root, print_private=print_private)
    typer.echo(f"key_id: {key_id}")
    typer.echo(f"public_key: {public_path}")
    if private_path is None:
        typer.echo(
            "private_key: printed below — store as RETORNATUS_SIGNING_KEY "
            "(GitHub secret). Do not commit it and do not expose it to the agent."
        )
        typer.echo(pem, nl=False)
        return
    typer.echo(f"private_key: {private_path}")
    typer.echo("The private key is outside the repository. Commit only the public key.")


@receipt_app.command("sign")
def receipt_sign_cmd(
    change_id: str = typer.Option(..., "--change", "-c", help="Change id to sign."),
    path: Path | None = typer.Option(None, "--path", "-p"),
    no_git: bool = typer.Option(
        False,
        "--no-git",
        help="Do not derive subject freshness from git HEAD.",
    ),
    allow_self_reported: bool = typer.Option(
        False,
        "--allow-self-reported",
        help="Count self-reported test/build/lint evidence as satisfying.",
    ),
) -> None:
    """Sign the current Assurance result (Ed25519) and write a receipt."""
    from retornatus.application.assurance.independent import evaluate_change_assurance

    root = resolve_root(path)
    load_signing_key(root)
    allowed = allow_self_reported or allow_self_reported_enabled(root)
    result = evaluate_change_assurance(
        root,
        change_id,
        use_git_state=not no_git,
        allow_self_reported=allowed,
    )
    out = write_verify_receipt(root, change_id, result)
    typer.echo(f"verdict: {result.verdict.value}")
    typer.echo(f"receipt: {out}")


@receipt_app.command("verify")
def receipt_verify_cmd(
    receipt_path: Path = typer.Argument(..., help="Path to receipt JSON."),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Verify a receipt with the committed public key.

    Legacy HMAC receipts are checked only when a local HMAC key exists and are
    reported as ``legacy_hmac`` (not portable).
    """
    ok, message, data = load_and_verify_receipt(resolve_root(path), receipt_path)
    _echo_verification(ok, message, data)
    raise typer.Exit(code=0 if ok else 1)
