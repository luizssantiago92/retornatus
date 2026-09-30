"""Sticky pull-request comment projected from verdict JSON.

The function does not evaluate Assurance or gates. It folds ``verdict`` fields
that ``verify`` and ``gate --json`` already printed, then lays out markdown.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from retornatus.domain.errors import UsageError

MARKER = "<!-- retornatus-verdict -->"
MAX_COMMENT_CHARS = 60_000
_VERDICTS = frozenset({"SATISFIED", "NOT_SATISFIED", "INCONCLUSIVE"})


def combined_verdict(
    verify_documents: Sequence[Mapping[str, Any]],
    gate_documents: Sequence[Mapping[str, Any]],
    *,
    omission: bool = False,
) -> str:
    """Fold JSON verdicts. Empty input is ``INCONCLUSIVE``, not a pass."""
    if omission:
        return "NOT_SATISFIED"
    if not verify_documents and not gate_documents:
        return "INCONCLUSIVE"
    if any(_gate_failed(document) for document in gate_documents):
        return "NOT_SATISFIED"
    states = [_verify_state(document) for document in verify_documents]
    if any(state == "NOT_SATISFIED" for state in states):
        return "NOT_SATISFIED"
    if any(state != "SATISFIED" for state in states):
        return "INCONCLUSIVE"
    return "SATISFIED"


def render_ci_comment(
    *,
    verify_documents: Sequence[Mapping[str, Any]],
    gate_documents: Sequence[Mapping[str, Any]],
    overview_markdown: Sequence[str] = (),
    notes: Sequence[str] = (),
    omission: bool = False,
) -> tuple[str, str]:
    """Return ``(markdown, verdict)``. The marker is the first line."""
    verdict = combined_verdict(
        verify_documents,
        gate_documents,
        omission=omission,
    )
    lines = [
        MARKER,
        "",
        f"## Retornatus verdict: `{verdict}`",
        "",
        _summary_line(verdict, verify_documents, gate_documents),
        "",
        "One comment for this pull request. Claim and gate tables are the JSON "
        "from `verify` and `gate`. Narrative sections are `change overview --format pr` "
        "without that overview's gate list.",
    ]
    note_lines = [note.strip() for note in notes if note.strip()]
    if note_lines:
        lines.extend(["", "### Notes", ""])
        lines.extend(f"- { _cell(note) }" for note in note_lines)
    rationales = _rationales(verify_documents)
    if rationales:
        lines.extend(["", "### Verify", ""])
        lines.extend(rationales)
    lines.extend(_diagnostics(verify_documents))
    for section in overview_markdown:
        text = _without_overview_gates(section)
        if text:
            lines.extend(["", text])
    lines.extend(["", "### Claim results", ""])
    lines.extend(_claims_table(verify_documents))
    lines.extend(["", "### Gate results", ""])
    lines.extend(_gates_table(gate_documents))
    body = _cap("\n".join(lines) + "\n")
    return body, verdict


def load_json_documents(paths: Sequence[Path]) -> list[dict[str, Any]]:
    """Read verdict envelopes. A non-object document is a usage error."""
    documents: list[dict[str, Any]] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise UsageError(f"JSON document must be an object: {path}")
        documents.append(payload)
    return documents


def comment_bundle(
    verify_documents: Sequence[Mapping[str, Any]],
    gate_documents: Sequence[Mapping[str, Any]],
    verdict: str,
) -> dict[str, Any]:
    """JSON file the action exposes as its ``json`` output."""
    if verdict not in _VERDICTS:
        raise UsageError(f"Unknown verdict: {verdict}")
    return {
        "kind": "ci-comment",
        "verdict": verdict,
        "verify": [dict(document) for document in verify_documents],
        "gates": [dict(document) for document in gate_documents],
    }


def change_ids(
    verify_documents: Sequence[Mapping[str, Any]],
    gate_documents: Sequence[Mapping[str, Any]],
) -> list[str]:
    """Change ids in first-seen order, skipping nulls."""
    seen: list[str] = []
    for document in (*verify_documents, *gate_documents):
        change_id = document.get("change_id")
        if isinstance(change_id, str) and change_id and change_id not in seen:
            seen.append(change_id)
    return seen


def _gate_failed(document: Mapping[str, Any]) -> bool:
    if document.get("passed") is False:
        return True
    return document.get("verdict") == "FAIL"


def _verify_state(document: Mapping[str, Any]) -> str:
    verdict = document.get("verdict")
    if isinstance(verdict, str) and verdict:
        return verdict
    return ""


def _summary_line(
    verdict: str,
    verify_documents: Sequence[Mapping[str, Any]],
    gate_documents: Sequence[Mapping[str, Any]],
) -> str:
    """One mobile-friendly line: verdict, claims satisfied, gates passed."""
    satisfied, claims = _claim_counts(verify_documents)
    passed, gates = _gate_counts(gate_documents)
    return (
        f"**{verdict}** — {_count_phrase(satisfied, claims, 'claim', 'satisfied')}, "
        f"{_count_phrase(passed, gates, 'gate', 'passed')}."
    )


def _claim_counts(documents: Sequence[Mapping[str, Any]]) -> tuple[int, int]:
    satisfied = 0
    total = 0
    for document in documents:
        claims = document.get("claims")
        if not isinstance(claims, list):
            continue
        for claim in claims:
            if not isinstance(claim, Mapping):
                continue
            total += 1
            if claim.get("status") == "SATISFIED":
                satisfied += 1
    return satisfied, total


def _gate_counts(documents: Sequence[Mapping[str, Any]]) -> tuple[int, int]:
    passed = sum(
        1
        for document in documents
        if document.get("verdict") == "PASS" or document.get("passed") is True
    )
    return passed, len(documents)


def _count_phrase(done: int, total: int, noun: str, verb: str) -> str:
    if total == 0:
        return f"0 {noun}s {verb}"
    label = noun if total == 1 else f"{noun}s"
    return f"{done}/{total} {label} {verb}"


def _diagnostics(documents: Sequence[Mapping[str, Any]]) -> list[str]:
    """Collapsed per-evidence labels and warnings. The verify line stays short."""
    warnings: list[str] = []
    labels: list[str] = []
    for document in documents:
        warnings.extend(_strings(document.get("warnings")))
        labels.extend(_strings(document.get("evidence_labels")))
    if not warnings and not labels:
        return []
    stale = [item for item in warnings if "stale snapshot" in item]
    other = [item for item in warnings if "stale snapshot" not in item]
    summary = _diagnostic_summary(stale, other, labels)
    lines = ["", "<details>", f"<summary>{summary}</summary>", ""]
    for item in (*stale, *other):
        lines.append(f"- {_cell(item)}")
    if labels:
        if warnings:
            lines.append("")
        lines.extend(["Evidence:", ""])
        lines.extend(f"- {_cell(label)}" for label in labels)
    lines.extend(["", "</details>"])
    return lines


def _diagnostic_summary(
    stale: Sequence[str],
    other: Sequence[str],
    labels: Sequence[str],
) -> str:
    if stale:
        count = len(stale)
        noun = "snapshot predates" if count == 1 else "snapshots predate"
        return f"{count} evidence {noun} HEAD (expected in CI merge refs)"
    if other:
        count = len(other)
        word = "warning" if count == 1 else "warnings"
        return f"{count} {word}"
    if labels:
        return "Evidence details"
    return "Details"


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _without_overview_gates(markdown: str) -> str:
    """Drop ``### Gates`` from overview text. JSON ``### Gate results`` remains."""
    kept: list[str] = []
    skipping = False
    for line in markdown.splitlines():
        heading = line.startswith("### ") or line.startswith("## ")
        if skipping:
            if heading:
                skipping = False
            else:
                continue
        if line.strip() == "### Gates":
            skipping = True
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def _rationales(documents: Sequence[Mapping[str, Any]]) -> list[str]:
    lines: list[str] = []
    for document in documents:
        change_id = document.get("change_id")
        label = change_id if isinstance(change_id, str) and change_id else "verify"
        state = _verify_state(document) or "—"
        rationale = document.get("rationale")
        if isinstance(rationale, str) and rationale.strip():
            lines.append(f"- **{_cell(label)}** `{state}` — {_cell(rationale)}")
        else:
            lines.append(f"- **{_cell(label)}** `{state}`")
    return lines


def _claims_table(documents: Sequence[Mapping[str, Any]]) -> list[str]:
    rows: list[tuple[str, str, str]] = []
    for document in documents:
        claims = document.get("claims")
        if not isinstance(claims, list):
            continue
        for claim in claims:
            if not isinstance(claim, Mapping):
                continue
            rows.append((_claim_label(claim), _status(claim), _evidence_ids(claim)))
    if not rows:
        return ["_No claims in the verify output._"]
    lines = [
        "| Claim | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    for claim, status, evidence in rows:
        lines.append(f"| {_cell(claim)} | {_cell(status)} | {_cell(evidence)} |")
    return lines


def _gates_table(documents: Sequence[Mapping[str, Any]]) -> list[str]:
    if not documents:
        return ["_No gate results._"]
    lines = [
        "| Gate | Change | Result | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for document in documents:
        gate = document.get("gate")
        gate_label = gate if isinstance(gate, str) and gate else "gate"
        change_id = document.get("change_id")
        change = change_id if isinstance(change_id, str) and change_id else "—"
        if document.get("verdict") == "PASS" or document.get("passed") is True:
            result = "PASS"
        elif _gate_failed(document):
            result = "FAIL"
        else:
            raw = document.get("verdict")
            result = raw if isinstance(raw, str) and raw else "—"
        lines.append(
            f"| {_cell(gate_label)} | {_cell(change)} | {result} | {_cell(_detail(document))} |"
        )
    return lines


def _claim_label(claim: Mapping[str, Any]) -> str:
    claim_id = claim.get("id")
    ident = claim_id if isinstance(claim_id, str) and claim_id else "claim"
    statement = claim.get("statement")
    text = statement.strip() if isinstance(statement, str) else ""
    if text:
        return f"`{ident}` {text}"
    return f"`{ident}`"


def _status(claim: Mapping[str, Any]) -> str:
    status = claim.get("status")
    if isinstance(status, str) and status:
        return status
    return "—"


def _evidence_ids(claim: Mapping[str, Any]) -> str:
    evidence = claim.get("evidence")
    if not isinstance(evidence, list):
        return "—"
    ids: list[str] = []
    for item in evidence:
        if isinstance(item, Mapping):
            evidence_id = item.get("id")
            if isinstance(evidence_id, str) and evidence_id:
                ids.append(f"`{evidence_id}`")
    return ", ".join(ids) if ids else "—"


def _detail(document: Mapping[str, Any]) -> str:
    for key in ("errors", "findings", "warnings"):
        value = document.get(key)
        if not isinstance(value, list):
            continue
        parts = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        if parts:
            return "; ".join(parts)
    return "—"


def _cell(value: str) -> str:
    """One table cell. Pipes would split the row; angle brackets stay literal."""
    text = " ".join(value.split())
    text = text.replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;")
    if len(text) > 180:
        text = text[:177] + "..."
    return text or "—"


def _cap(body: str) -> str:
    if len(body) <= MAX_COMMENT_CHARS:
        return body
    note = "\n\n_Comment truncated to fit the GitHub comment size limit._\n"
    keep = MAX_COMMENT_CHARS - len(note)
    return body[:keep] + note
