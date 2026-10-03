"""Inject the active Change finish line at session start.

The text is computed in this process. There is no subprocess back into the
CLI. No active Change, a disabled ``[hooks] session_context``, and every
internal error print nothing on stdout and exit 0, so a hook cannot trap
the session.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from retornatus.application.agent_hooks.config import HOSTS
from retornatus.application.agent_hooks.stop import (
    evidence_command_for_claim,
    locate_project,
)
from retornatus.application.assurance.independent import evaluate_change_assurance
from retornatus.application.assurance.settings import load_project_config
from retornatus.application.governance.scope import change_resources
from retornatus.application.report.envelope import verify_document
from retornatus.bootstrap.hooks import active_change_ids

CONTEXT_BYTE_CAP = 2048
_TRUNCATION_MARK = "\n…(truncated)\n"
_SCOPE_SHOWN = 12


@dataclass(frozen=True)
class SessionResponse:
    """What the session-start command writes. Exit 0 is success and fail-open."""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0


def handle_session_start(
    host: str,
    raw_stdin: str,
    *,
    start: Path,
    walk: bool,
) -> SessionResponse:
    """Read one host payload and return context JSON, or nothing."""
    try:
        return _handle_session_start(host, raw_stdin, start=start, walk=walk)
    except Exception as exc:
        return _fail_open(f"{type(exc).__name__}: {exc}")


def session_context_enabled(root: Path) -> bool:
    """True unless ``[hooks] session_context`` is boolean false.

    A missing table or a missing key keeps the default, true.
    A non-boolean value is an error so the hook fails open.
    """
    hooks = load_project_config(root).get("hooks")
    if hooks is None:
        return True
    if not isinstance(hooks, dict):
        raise ValueError("Invalid [hooks]: expected a table")
    if "session_context" not in hooks:
        return True
    raw = hooks["session_context"]
    if isinstance(raw, bool):
        return raw
    raise ValueError("Invalid [hooks] session_context: expected true or false")


def cap_utf8(text: str, limit: int = CONTEXT_BYTE_CAP) -> str:
    """Keep ``text`` within ``limit`` UTF-8 bytes, marking a cut."""
    raw = text.encode("utf-8")
    if len(raw) <= limit:
        return text
    marker = _TRUNCATION_MARK.encode("utf-8")
    if len(marker) >= limit:
        return marker[:limit].decode("utf-8", errors="ignore")
    budget = limit - len(marker)
    clipped = raw[:budget].decode("utf-8", errors="ignore")
    return clipped + _TRUNCATION_MARK


def _handle_session_start(
    host: str,
    raw_stdin: str,
    *,
    start: Path,
    walk: bool,
) -> SessionResponse:
    name = host.strip().casefold()
    if name not in HOSTS:
        return _fail_open(f"unknown host {host!r}")
    _payload, parsed = _parse_payload(raw_stdin)
    if not parsed:
        return _fail_open("invalid JSON on stdin")
    root = locate_project(start, walk=walk)
    if root is None:
        return SessionResponse()
    if not session_context_enabled(root):
        return SessionResponse()
    context = render_session_context(root)
    if not context:
        return SessionResponse()
    return SessionResponse(stdout=_host_stdout(name, context))


def render_session_context(root: Path) -> str:
    """Plain-text finish line for every active Change, capped at 2 KB.

    A pending skill candidate adds one line. That line does not block the
    session, and it is omitted when ``[adaptation.skill_candidates]`` is off.
    """
    change_ids = active_change_ids(root)
    text = ""
    if change_ids:
        blocks = [_change_block(root, change_id) for change_id in change_ids]
        text = "Retornatus active Change context:\n" + "\n\n".join(blocks)
    notice = _skill_candidate_notice(root)
    if notice:
        text = f"{text}\n{notice}" if text else notice
    if not text:
        return ""
    return cap_utf8(text)


def _change_block(root: Path, change_id: str) -> str:
    from retornatus.infrastructure.persistence.repository import FileRepository

    repo = FileRepository(root)
    change, _ = repo.load_change(change_id)
    contract, _ = repo.load_contract(change_id)
    result = evaluate_change_assurance(root, change_id)
    document = verify_document(root, change_id, result)
    verdict = str(document.get("verdict") or "INCONCLUSIVE")
    title = " ".join(change.title.split())
    goal = " ".join(contract.what.split())
    lines = [
        f"{change_id} {title} — {verdict}",
        f"goal: {goal}",
        f"scope: {_scope_summary(root, change_id)}",
    ]
    claims = document.get("claims")
    unproven: list[dict[str, Any]] = []
    if isinstance(claims, list):
        unproven = [claim for claim in claims if isinstance(claim, dict) and claim.get("status") != "SATISFIED"]
    if not unproven:
        lines.append("unproven: none")
    else:
        for claim in unproven:
            command = evidence_command_for_claim(root, change_id, claim)
            lines.append(f"unproven: {claim.get('id')} ({claim.get('status')}). Next: {command}")
    return "\n".join(lines)


def _scope_summary(root: Path, change_id: str) -> str:
    seen: list[str] = []
    for resource in change_resources(root, change_id):
        text = resource.strip()
        if text and text not in seen:
            seen.append(text)
    if not seen:
        return "(none declared)"
    shown = seen[:_SCOPE_SHOWN]
    extra = len(seen) - len(shown)
    summary = ", ".join(shown)
    if extra:
        summary += f" +{extra} more"
    return summary


def _host_stdout(host: str, context: str) -> str:
    if host == "cursor":
        body: dict[str, Any] = {"additional_context": context}
    else:
        body = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        }
    return json.dumps(body, ensure_ascii=False) + "\n"


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


def _skill_candidate_notice(root: Path) -> str:
    try:
        from retornatus.application.adaptation.skill_candidates import pending_notice

        return pending_notice(root)
    except Exception:
        return ""


def _fail_open(detail: str) -> SessionResponse:
    line = detail.replace("\n", " ").strip()
    return SessionResponse(stderr=f"retornatus hook session-start: fail-open ({line})\n")
