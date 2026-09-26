"""Portable HMAC receipts for Assurance verify results.

Lightweight local receipts (not a full Agent Receipts / Ed25519 mesh).
Key material lives under ``.retornatus/runtime/`` (gitignored).
Receipt JSON may be committed under ``.retornatus/assurance/receipts/``.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from retornatus.application.assurance.evaluate import AssuranceResult
from retornatus.infrastructure.persistence.paths import RetornatusPaths

RECEIPT_SCHEMA = "retornatus-receipt/v1"
ALG = "HMAC-SHA256"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_receipt_key(root: Path) -> Path:
    """Return path to local HMAC key, creating one if missing."""
    paths = RetornatusPaths(root)
    key_path = paths.runtime / "receipt.key"
    key_path.parent.mkdir(parents=True, exist_ok=True)
    env_key = os.environ.get("RETORNATUS_RECEIPT_KEY")
    if env_key:
        raw = bytes.fromhex(env_key) if all(c in "0123456789abcdefABCDEF" for c in env_key) and len(env_key) >= 32 else env_key.encode("utf-8")
        key_path.write_bytes(raw)
        key_path.chmod(0o600)
        return key_path
    if not key_path.exists():
        key_path.write_bytes(secrets.token_bytes(32))
        key_path.chmod(0o600)
    return key_path


def _load_key(root: Path) -> bytes:
    return ensure_receipt_key(root).read_bytes()


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
    return {
        "schema": RECEIPT_SCHEMA,
        "alg": ALG,
        "change_id": change_id,
        "verdict": result.verdict.value,
        "rationale": result.rationale,
        "claim_results": dict(sorted(result.claim_results.items())),
        "evidence_ids": list(result.evidence_ids),
        "git_head": git_head,
        "issued_at": _utc_now_iso(),
    }


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    body = {k: v for k, v in payload.items() if k != "signature"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def sign_payload(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    digest = hmac.new(_load_key(root), _canonical_bytes(payload), hashlib.sha256).hexdigest()
    signed = dict(payload)
    signed["signature"] = digest
    return signed


def verify_receipt_dict(root: Path, receipt: dict[str, Any]) -> tuple[bool, str]:
    if receipt.get("schema") != RECEIPT_SCHEMA:
        return False, f"unsupported schema {receipt.get('schema')!r}"
    sig = receipt.get("signature")
    if not isinstance(sig, str) or not sig:
        return False, "missing signature"
    expected = hmac.new(_load_key(root), _canonical_bytes(receipt), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return False, "signature mismatch"
    return True, "ok"


def write_verify_receipt(
    root: Path,
    change_id: str,
    result: AssuranceResult,
) -> Path:
    """Sign and persist a receipt for a verify/assurance evaluation."""
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
    data = json.loads(receipt_path.read_text(encoding="utf-8"))
    ok, msg = verify_receipt_dict(root, data)
    return ok, msg, data
