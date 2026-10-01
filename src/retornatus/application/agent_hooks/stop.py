"""Decide whether an agent may end its turn.

The decision uses the same Assurance evaluation as ``verify --json``, in this
process. There is no network call and no subprocess back into the CLI.

SATISFIED, no active Change, and a missing ``.retornatus/`` allow the stop.
A question to the user allows the stop when ``[hooks] allow_questions`` is
not false. Anything else asks the host to continue, once. Internal failures
allow the stop and print one line to stderr so a crash cannot trap the agent.
"""

from __future__ import annotations

import json
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from retornatus.application.agent_hooks.config import HOSTS
from retornatus.application.agent_hooks.questions import (
    assistant_message_text,
    is_question_to_user,
)
from retornatus.application.assurance.independent import evaluate_change_assurance
from retornatus.application.assurance.settings import (
    allow_question_stops,
    load_required_checks,
)
from retornatus.application.report.envelope import verify_document
from retornatus.bootstrap.hooks import active_change_ids

_ALLOW_STATUSES = frozenset({"aborted", "error"})


@dataclass(frozen=True)
class StopResponse:
    """What the Stop command writes. Exit 0 is allow and block."""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0


def handle_stop(
    host: str,
    raw_stdin: str,
    *,
    start: Path,
    walk: bool,
) -> StopResponse:
    """Read one host payload and return the allow or block response."""
    try:
        return _handle_stop(host, raw_stdin, start=start, walk=walk)
    except Exception as exc:
        return _fail_open(f"{type(exc).__name__}: {exc}")


def _handle_stop(
    host: str,
    raw_stdin: str,
    *,
    start: Path,
    walk: bool,
) -> StopResponse:
    name = host.strip().casefold()
    if name not in HOSTS:
        return _fail_open(f"unknown host {host!r}")
    payload, parsed = _parse_payload(raw_stdin)
    if not parsed:
        return _fail_open("invalid JSON on stdin")
    if name in {"claude", "codex"} and payload.get("stop_hook_active") is True:
        return StopResponse()
    if name == "cursor" and payload.get("status") in _ALLOW_STATUSES:
        return StopResponse()
    root = locate_project(start, walk=walk)
    if root is None:
        return StopResponse()
    change_ids = active_change_ids(root)
    if not change_ids:
        return StopResponse()
    if allow_question_stops(root) and _message_is_question(name, payload):
        return StopResponse()
    blocking: list[dict[str, Any]] = []
    for change_id in change_ids:
        result = evaluate_change_assurance(root, change_id)
        document = verify_document(root, change_id, result)
        if document.get("verdict") != "SATISFIED":
            blocking.append(document)
    if not blocking:
        return StopResponse()
    reason = " ".join(_reason_for(root, document) for document in blocking)
    body: dict[str, str] = {"followup_message": reason} if name == "cursor" else {"decision": "block", "reason": reason}
    return StopResponse(stdout=json.dumps(body, ensure_ascii=False) + "\n")


def locate_project(start: Path, *, walk: bool) -> Path | None:
    """Directory that contains ``.retornatus``, or None.

    ``walk`` searches parents. An explicit ``--path`` does not walk, so a
    caller can point at one project without inheriting a parent checkout.
    """
    current = start.resolve()
    if (current / ".retornatus").is_dir():
        return current
    if not walk:
        return None
    for candidate in current.parents:
        if (candidate / ".retornatus").is_dir():
            return candidate
    return None


def _message_is_question(host: str, payload: dict[str, Any]) -> bool:
    """True when the documented assistant text asks the user something.

    A missing transcript or a read error is not a question, so the caller
    keeps the Assurance decision.
    """
    try:
        text = assistant_message_text(host, payload)
    except Exception:
        return False
    if not text:
        return False
    return is_question_to_user(text)


def _parse_payload(raw: str) -> tuple[dict[str, Any], bool]:
    """Return ``(object, ok)``. Non-objects count as an empty object."""
    if not raw.strip():
        return {}, True
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}, False
    if isinstance(parsed, dict):
        return parsed, True
    return {}, True


def _fail_open(detail: str) -> StopResponse:
    line = detail.replace("\n", " ").strip()
    return StopResponse(stderr=f"retornatus hook stop: fail-open ({line})\n")


def _reason_for(root: Path, document: dict[str, Any]) -> str:
    change_id = str(document.get("change_id") or "?")
    verdict = str(document.get("verdict") or "NOT_SATISFIED")
    claims = document.get("claims")
    if isinstance(claims, list):
        unproven = [claim for claim in claims if isinstance(claim, dict) and claim.get("status") != "SATISFIED"]
    else:
        unproven = []
    if not unproven:
        rationale = str(document.get("rationale") or "not SATISFIED")
        return f"{change_id} is {verdict}. {rationale}"
    shown = unproven[:8]
    parts = [f"{claim.get('id')} ({claim.get('status')})" for claim in shown]
    more = f" +{len(unproven) - len(shown)} more" if len(unproven) > len(shown) else ""
    nxt = evidence_command_for_claim(root, change_id, shown[0])
    return f"{change_id} is {verdict}. Unproven claims: {', '.join(parts)}{more}. Next: {nxt}"


def evidence_command_for_claim(root: Path, change_id: str, claim: dict[str, Any]) -> str:
    evidence_type = "test_result"
    types = claim.get("required_evidence_types")
    if isinstance(types, list) and types and isinstance(types[0], str) and types[0].strip():
        evidence_type = types[0]
    subject = claim.get("subject")
    if not isinstance(subject, str) or not subject.strip():
        subject = str(claim.get("id") or change_id)
    claim_id = str(claim.get("id") or "")
    argv = _suggest_argv(root, evidence_type)
    command = " ".join(shlex.quote(part) for part in argv)
    return (
        "retornatus evidence run "
        f"-c {shlex.quote(change_id)} "
        f"-t {shlex.quote(evidence_type)} "
        f"-s {shlex.quote(subject)} "
        f"--claim {shlex.quote(claim_id)} "
        f"-- {command}"
    )


def _suggest_argv(root: Path, evidence_type: str) -> list[str]:
    try:
        checks = load_required_checks(root)
    except (OSError, ValueError):
        return ["pytest", "-q"]
    for check in checks:
        if not check.types or evidence_type in check.types:
            return list(check.run)
    return ["pytest", "-q"]
