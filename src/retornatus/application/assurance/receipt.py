"""Ed25519 receipts for Assurance verify results.

Threat model
------------
A receipt shows that a holder of the Ed25519 private key signed this verify
result. Anyone with a clone can check that signature using the public key
committed at ``.retornatus/keys/<key-id>.pub`` (``key-id`` is the SHA-256
fingerprint of the raw public key).

The private key is never written inside the repository. Load it from
``RETORNATUS_SIGNING_KEY`` (PEM, base64, or even-length hex) or from the user
config directory (or ``RETORNATUS_SIGNING_KEY_PATH``, which must sit outside
the project). An agent that can read the private key can still sign — keep
that key out of the agent's environment. CI should pass the private key as a
secret and produce receipts there.

Legacy HMAC-SHA256 receipts (schema ``retornatus-receipt/v1``) still verify
when the old local key is available. They are reported as ``legacy_hmac`` and
are not portable. That path is deprecated and does not copy the key to disk.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from retornatus.application.assurance.evaluate import AssuranceResult
from retornatus.domain.errors import ReceiptError, SigningKeyError
from retornatus.domain.ids import validate_change_id
from retornatus.infrastructure.persistence.paths import RetornatusPaths

RECEIPT_SCHEMA = "retornatus-receipt/v2"
RECEIPT_SCHEMA_V1 = "retornatus-receipt/v1"
ALG_ED25519 = "Ed25519"
ALG_HMAC = "HMAC-SHA256"
_KEY_ID = re.compile(r"^[0-9a-f]{64}$")
_HEX = re.compile(r"^[0-9a-fA-F]+$")

_LEGACY_WARNING = (
    "HMAC receipts are deprecated and not portable (legacy_hmac). "
    "Use Ed25519: retornatus receipt keygen. "
    "Keep the private key out of the agent environment."
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def user_config_dir() -> Path:
    """Per-user config directory. Honors ``XDG_CONFIG_HOME`` on every OS."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "retornatus"
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "retornatus"
        return Path.home() / "AppData" / "Roaming" / "retornatus"
    return Path.home() / ".config" / "retornatus"


def private_key_path(key_id: str) -> Path:
    return user_config_dir() / "keys" / f"{key_id}.pem"


def assert_outside_project(root: Path, target: Path) -> None:
    """Refuse to read or write private key material inside the project tree."""
    resolved = target.resolve()
    base = root.resolve()
    if resolved == base or base in resolved.parents:
        raise SigningKeyError(
            "Refusing to store or read a private key inside the project: "
            f"{target}. Use the user config directory or RETORNATUS_SIGNING_KEY."
        )


def fingerprint_public_key(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return hashlib.sha256(raw).hexdigest()


def _restrict_private_file(path: Path) -> None:
    try:
        path.chmod(0o600)
    except OSError:
        return


def _normalize_key_material(material: str) -> str:
    text = material.strip().lstrip("\ufeff")
    if not text:
        raise SigningKeyError("Signing key is empty")
    if "\\n" in text and "-----BEGIN" in text.replace("\\n", "\n"):
        text = text.replace("\\n", "\n")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _from_pem(data: bytes) -> Ed25519PrivateKey:
    try:
        key = serialization.load_pem_private_key(data, password=None)
    except (ValueError, TypeError) as exc:
        raise SigningKeyError(f"Could not read PEM signing key: {exc}") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise SigningKeyError("Signing key is not an Ed25519 private key")
    return key


def _from_seed(raw: bytes) -> Ed25519PrivateKey:
    if len(raw) != 32:
        raise SigningKeyError(
            f"Ed25519 private key seed must be 32 bytes, got {len(raw)}"
        )
    return Ed25519PrivateKey.from_private_bytes(raw)


def _from_der_or_seed(raw: bytes) -> Ed25519PrivateKey:
    if len(raw) == 32:
        return _from_seed(raw)
    try:
        key = serialization.load_der_private_key(raw, password=None)
    except (ValueError, TypeError) as exc:
        raise SigningKeyError(
            "Signing key must be PEM, base64 (32-byte seed or PKCS8), "
            "or even-length hex"
        ) from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise SigningKeyError("Signing key is not an Ed25519 private key")
    return key


def parse_private_key(material: str) -> Ed25519PrivateKey:
    """Parse PEM, base64, or even-length hex. Odd-length hex is a clean error."""
    text = _normalize_key_material(material)
    if "-----BEGIN" in text:
        return _from_pem(text.encode("utf-8"))
    compact = "".join(text.split())
    if _HEX.fullmatch(compact):
        if len(compact) % 2:
            raise SigningKeyError(
                "Signing key hex has odd length; use even-length hex, base64, or PEM"
            )
        try:
            raw = bytes.fromhex(compact)
        except ValueError as exc:
            raise SigningKeyError("Signing key is not valid hex") from exc
        return _from_seed(raw)
    try:
        raw = base64.b64decode(compact, validate=True)
    except (ValueError, TypeError) as exc:
        raise SigningKeyError(
            "Signing key must be PEM, base64, or even-length hex"
        ) from exc
    if raw.startswith(b"-----BEGIN"):
        return _from_pem(raw)
    return _from_der_or_seed(raw)


def private_key_pem(private_key: Ed25519PrivateKey) -> str:
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    text = pem.decode("ascii")
    if not text.endswith("\n"):
        text += "\n"
    return text


def public_key_pem(public_key: Ed25519PublicKey) -> str:
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    text = pem.decode("ascii")
    if not text.endswith("\n"):
        text += "\n"
    return text


def publish_public_key(root: Path, private_key: Ed25519PrivateKey) -> tuple[str, Path]:
    """Write the public key under ``.retornatus/keys``. Never writes the private key."""
    public_key = private_key.public_key()
    key_id = fingerprint_public_key(public_key)
    path = RetornatusPaths(root).public_key_path(key_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    pem = public_key_pem(public_key)
    if path.is_file() and path.read_text(encoding="utf-8").strip() != pem.strip():
        raise SigningKeyError(
            f"Committed public key {path.name} does not match the signing key"
        )
    path.write_text(pem, encoding="utf-8")
    return key_id, path


def write_private_key(root: Path, private_key: Ed25519PrivateKey) -> Path:
    """Write the private key to the user config dir, never inside ``root``."""
    key_id = fingerprint_public_key(private_key.public_key())
    dest = private_key_path(key_id)
    assert_outside_project(root, dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(private_key_pem(private_key), encoding="utf-8")
    _restrict_private_file(dest)
    return dest


def generate_keypair() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.generate()


def keygen(root: Path, *, print_private: bool = False) -> tuple[str, Path, Path | None, str]:
    """Create a keypair.

    Returns ``(key_id, public_path, private_path_or_none, pem)``.
    ``print_private`` skips the config-dir write; the PEM is still returned
    so the CLI can show it for a CI secret.
    """
    private_key = generate_keypair()
    key_id, public_path = publish_public_key(root, private_key)
    pem = private_key_pem(private_key)
    if print_private:
        return key_id, public_path, None, pem
    private_path = write_private_key(root, private_key)
    return key_id, public_path, private_path, pem


def _load_private_from_path(root: Path, path: Path) -> Ed25519PrivateKey:
    assert_outside_project(root, path)
    if not path.is_file():
        raise SigningKeyError(f"Signing key file not found: {path}")
    return parse_private_key(path.read_text(encoding="utf-8"))


def _keys_matching_repo(root: Path) -> list[tuple[Ed25519PrivateKey, str]]:
    keys_dir = user_config_dir() / "keys"
    if not keys_dir.is_dir():
        return []
    found: list[tuple[Ed25519PrivateKey, str]] = []
    for path in sorted(keys_dir.glob("*.pem")):
        try:
            assert_outside_project(root, path)
            key = parse_private_key(path.read_text(encoding="utf-8"))
        except SigningKeyError:
            continue
        key_id = fingerprint_public_key(key.public_key())
        pub = RetornatusPaths(root).public_key_path(key_id)
        if pub.is_file():
            found.append((key, key_id))
    return found


def load_signing_key(root: Path) -> tuple[Ed25519PrivateKey, str]:
    """Load the private key from the environment or a path outside the project.

    Environment material is never written to disk.
    """
    if "RETORNATUS_SIGNING_KEY" in os.environ:
        material = os.environ["RETORNATUS_SIGNING_KEY"]
        if not material.strip():
            raise SigningKeyError("RETORNATUS_SIGNING_KEY is empty")
        key = parse_private_key(material)
        return key, fingerprint_public_key(key.public_key())

    path_env = os.environ.get("RETORNATUS_SIGNING_KEY_PATH")
    if path_env is not None:
        if not path_env.strip():
            raise SigningKeyError("RETORNATUS_SIGNING_KEY_PATH is empty")
        key = _load_private_from_path(root, Path(path_env))
        return key, fingerprint_public_key(key.public_key())

    matches = _keys_matching_repo(root)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise SigningKeyError(
            "Multiple signing keys match committed public keys. "
            "Set RETORNATUS_SIGNING_KEY to the one this environment should use."
        )
    raise SigningKeyError(
        "No Ed25519 signing key. Run `retornatus receipt keygen` "
        "or set RETORNATUS_SIGNING_KEY. Do not put the private key in the "
        "repository or in the agent's environment."
    )


def load_public_key(root: Path, key_id: str) -> Ed25519PublicKey:
    if _KEY_ID.fullmatch(key_id) is None:
        raise ReceiptError(f"Invalid key id: {key_id!r}")
    path = RetornatusPaths(root).public_key_path(key_id)
    if not path.is_file():
        raise ReceiptError(
            f"Public key {key_id} is not in .retornatus/keys "
            "(verification needs the committed public key)"
        )
    try:
        loaded = serialization.load_pem_public_key(path.read_bytes())
    except (ValueError, TypeError) as exc:
        raise ReceiptError(f"Could not read public key {key_id}: {exc}") from exc
    if not isinstance(loaded, Ed25519PublicKey):
        raise ReceiptError(f"Public key {key_id} is not an Ed25519 key")
    if fingerprint_public_key(loaded) != key_id:
        raise ReceiptError(f"Public key file does not match key id {key_id}")
    return loaded


def _git_head(root: Path) -> str | None:
    head = root / ".git" / "HEAD"
    if not head.is_file():
        return None
    text = head.read_text(encoding="utf-8").strip()
    if text.startswith("ref:"):
        ref = text.split(" ", 1)[1].strip()
        ref_path = root / ".git" / ref
        if ref_path.is_file():
            return ref_path.read_text(encoding="utf-8").strip()
        return ref
    return text or None


def build_payload(
    *,
    change_id: str,
    result: AssuranceResult,
    git_head: str | None,
) -> dict[str, Any]:
    validate_change_id(change_id)
    return {
        "schema": RECEIPT_SCHEMA,
        "alg": ALG_ED25519,
        "change_id": change_id,
        "verdict": result.verdict.value,
        "rationale": result.rationale,
        "claim_results": dict(sorted(result.claim_results.items())),
        "evidence_ids": list(result.evidence_ids),
        "git_head": git_head,
        "issued_at": _utc_now_iso(),
    }


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    body = {k: v for k, v in payload.items() if k != "signature"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def sign_payload(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    private_key, key_id = load_signing_key(root)
    publish_public_key(root, private_key)
    signed = dict(payload)
    signed["schema"] = RECEIPT_SCHEMA
    signed["alg"] = ALG_ED25519
    signed["key_id"] = key_id
    signed.pop("signature", None)
    signature = private_key.sign(canonical_bytes(signed))
    signed["signature"] = base64.b64encode(signature).decode("ascii")
    return signed


def _parse_legacy_key(material: str) -> bytes:
    text = material.strip()
    if not text:
        raise SigningKeyError("RETORNATUS_RECEIPT_KEY is empty")
    if all(c in "0123456789abcdefABCDEF" for c in text):
        if len(text) % 2:
            raise SigningKeyError(
                "RETORNATUS_RECEIPT_KEY hex has odd length; "
                "use even-length hex or raw text"
            )
        try:
            return bytes.fromhex(text)
        except ValueError as exc:
            raise SigningKeyError("RETORNATUS_RECEIPT_KEY is not valid hex") from exc
    return text.encode("utf-8")


def _load_legacy_hmac_key(root: Path) -> bytes | None:
    """In-memory legacy key. Never writes ``RETORNATUS_RECEIPT_KEY`` to disk."""
    env_key = os.environ.get("RETORNATUS_RECEIPT_KEY")
    if env_key is not None:
        return _parse_legacy_key(env_key)
    key_path = RetornatusPaths(root).runtime / "receipt.key"
    if key_path.is_file():
        return key_path.read_bytes()
    return None


def _warn_legacy() -> None:
    warnings.warn(_LEGACY_WARNING, DeprecationWarning, stacklevel=3)


def _verify_legacy_hmac(root: Path, receipt: dict[str, Any]) -> tuple[bool, str]:
    _warn_legacy()
    sig = receipt.get("signature")
    if not isinstance(sig, str) or not sig:
        return False, "legacy_hmac: missing signature (not portable)"
    key = _load_legacy_hmac_key(root)
    if key is None:
        return False, "legacy_hmac: not portable (no local HMAC key)"
    expected = hmac.new(key, canonical_bytes(receipt), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return False, "legacy_hmac: signature mismatch (not portable)"
    return True, "legacy_hmac"


def _is_legacy(receipt: dict[str, Any]) -> bool:
    return receipt.get("alg") == ALG_HMAC or receipt.get("schema") == RECEIPT_SCHEMA_V1


def verify_receipt_dict(root: Path, receipt: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(receipt, dict):
        raise ReceiptError("Receipt JSON must be an object")
    if _is_legacy(receipt):
        return _verify_legacy_hmac(root, receipt)
    schema = receipt.get("schema")
    if schema != RECEIPT_SCHEMA:
        return False, f"unsupported schema {schema!r}"
    alg = receipt.get("alg")
    if alg != ALG_ED25519:
        return False, f"unsupported alg {alg!r}"
    key_id = receipt.get("key_id")
    if not isinstance(key_id, str) or not key_id:
        return False, "missing key_id"
    sig_text = receipt.get("signature")
    if not isinstance(sig_text, str) or not sig_text:
        return False, "missing signature"
    try:
        signature = base64.b64decode(sig_text, validate=True)
        public_key = load_public_key(root, key_id)
    except ReceiptError as exc:
        return False, str(exc)
    try:
        public_key.verify(signature, canonical_bytes(receipt))
    except InvalidSignature:
        return False, "signature mismatch"
    return True, "ok"


def write_verify_receipt(
    root: Path,
    change_id: str,
    result: AssuranceResult,
) -> Path:
    """Sign and persist a receipt for a verify/assurance evaluation."""
    validate_change_id(change_id)
    paths = RetornatusPaths(root)
    out_dir = paths.retornatus / "assurance" / "receipts"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload(
        change_id=change_id,
        result=result,
        git_head=_git_head(root),
    )
    signed = sign_payload(root, payload)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = out_dir / f"{change_id}-{stamp}.json"
    out.write_text(json.dumps(signed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def load_and_verify_receipt(root: Path, receipt_path: Path) -> tuple[bool, str, dict[str, Any]]:
    try:
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReceiptError(f"Invalid JSON: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ReceiptError("Receipt JSON must be an object")
    ok, msg = verify_receipt_dict(root, data)
    return ok, msg, data


def is_legacy_message(message: str) -> bool:
    return message == "legacy_hmac" or message.startswith("legacy_hmac")
