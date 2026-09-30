"""Versioned JSON verdict envelope (schema_version 1).

The document is a projection of data the command already computed.
Gate ``verdict`` is ``PASS`` or ``FAIL``, the same fact as ``GateResult.passed``.
Assurance commands use ``SATISFIED``, ``NOT_SATISFIED``, or ``INCONCLUSIVE``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from retornatus.application.assurance.evaluate import AssuranceResult
from retornatus.application.assurance.evidence import EvidenceService
from retornatus.application.assurance.subject_state import current_git_head
from retornatus.application.governance.gates import GateResult
from retornatus.domain.models import Evidence
from retornatus.domain.relations import RelationType

SCHEMA_VERSION = 1


def utc_now_iso() -> str:
    """UTC timestamp with a ``Z`` suffix and no fractional seconds."""
    return datetime.now(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def partition_gate_messages(
    messages: list[str],
    *,
    passed: bool,
) -> tuple[list[str], list[str]]:
    """Split gate lines into warnings and errors.

    Lines that start with ``WARN`` are warnings. Other lines are errors only
    when the gate failed. A passing note such as ``Contract OK`` stays a
    finding and is not an error.
    """
    warnings = [message for message in messages if message.startswith("WARN")]
    if passed:
        return warnings, []
    errors = [message for message in messages if not message.startswith("WARN")]
    return warnings, errors


def _head(root: Path) -> str | None:
    return current_git_head(root)


def _common(
    *,
    command: str,
    exit_code: int,
    root: Path,
    warnings: list[str],
    errors: list[str],
    verdict: str | None,
    claims: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "command": command,
        "exit_code": exit_code,
        "verdict": verdict,
        "claims": claims,
        "warnings": warnings,
        "errors": errors,
        "head": _head(root),
        "generated_at": utc_now_iso(),
    }


def bound_evidence(claim_id: str, evidence: list[Evidence]) -> list[dict[str, Any]]:
    """Evidence rows whose relations SUPPORT this claim id."""
    rows: list[dict[str, Any]] = []
    for item in evidence:
        supports = any(
            relation.type is RelationType.SUPPORTS and relation.target_id == claim_id
            for relation in item.relations
        )
        if not supports:
            continue
        rows.append(
            {
                "id": item.id,
                "type": item.type,
                "subject": item.subject,
                "provenance": item.provenance.value,
                "exit_code": item.exit_code,
                "git_commit": item.git_commit,
            }
        )
    return rows


def verify_document(
    root: Path,
    change_id: str,
    result: AssuranceResult,
    *,
    receipt_path: str | None = None,
) -> dict[str, Any]:
    """Envelope for ``retornatus verify``."""
    evidence = EvidenceService(root).list_for_change(change_id)
    claims: list[dict[str, Any]] = []
    for claim in result.claims:
        claims.append(
            {
                "id": claim.id,
                "subject": claim.subject,
                "statement": claim.statement,
                "status": result.claim_results.get(claim.id, "INCONCLUSIVE"),
                "required_evidence_types": list(claim.required_evidence_types),
                "evidence": bound_evidence(claim.id, evidence),
            }
        )
    document = _common(
        command="verify",
        exit_code=0 if result.verdict.value == "SATISFIED" else 1,
        root=root,
        warnings=list(result.warnings),
        errors=[],
        verdict=result.verdict.value,
        claims=claims,
    )
    document["change_id"] = change_id
    document["rationale"] = result.rationale
    document["evidence_labels"] = list(result.evidence_labels)
    document["unverified_evidence_ids"] = list(result.unverified_evidence_ids)
    document["receipt"] = receipt_path
    if result.surfaces:
        document["surfaces"] = [dict(item) for item in result.surfaces]
    return document


def gate_document(
    root: Path,
    result: GateResult,
    *,
    change_id: str | None = None,
    action_id: str | None = None,
    skill_id: str | None = None,
) -> dict[str, Any]:
    """Envelope for one ``retornatus gate`` subcommand."""
    warnings, errors = partition_gate_messages(list(result.messages), passed=result.passed)
    document = _common(
        command="gate",
        exit_code=result.exit_code,
        root=root,
        warnings=warnings,
        errors=errors,
        verdict="PASS" if result.passed else "FAIL",
        claims=[],
    )
    document["gate"] = result.name.value
    document["passed"] = result.passed
    document["change_id"] = change_id
    document["action_id"] = action_id
    document["skill_id"] = skill_id
    document["findings"] = list(result.messages)
    return document


def overview_document(root: Path, change_id: str) -> dict[str, Any]:
    """Envelope for ``retornatus change overview`` when the Change exists."""
    from retornatus.application.assurance.evaluate import build_claims_from_contract
    from retornatus.application.change.overview import build_change_overview
    from retornatus.infrastructure.persistence.repository import FileRepository

    overview = build_change_overview(root, change_id)
    evidence = EvidenceService(root).list_for_change(change_id)
    subjects: dict[str, str | None] = {}
    try:
        contract, _ = FileRepository(root).load_contract(change_id)
    except FileNotFoundError:
        contract = None
    if contract is not None:
        for claim in build_claims_from_contract(contract):
            subjects[claim.id] = claim.subject
    claims: list[dict[str, Any]] = []
    for row in overview.claims:
        claims.append(
            {
                "id": row.claim_id,
                "subject": subjects.get(row.claim_id),
                "statement": row.statement,
                "status": row.verdict,
                "required_evidence_types": list(row.required_types),
                "evidence": bound_evidence(row.claim_id, evidence),
            }
        )
    document = _common(
        command="change overview",
        exit_code=0,
        root=root,
        warnings=[],
        errors=[],
        verdict=overview.assurance_verdict,
        claims=claims,
    )
    document["change_id"] = change_id
    document["title"] = overview.title
    document["lane"] = overview.lane
    document["contract_version"] = overview.contract_version
    document["contract_active"] = overview.contract_active
    document["what"] = overview.what
    document["evidence_lines"] = list(overview.evidence_lines)
    document["tasks"] = list(overview.task_lines)
    document["questions"] = list(overview.question_lines)
    document["next"] = overview.next_line
    document["parallelizable"] = list(overview.parallelizable)
    return document


def overview_missing_document(root: Path, change_id: str) -> dict[str, Any]:
    """Envelope when ``change overview`` cannot load the Change."""
    message = f"Change not found: {change_id}"
    document = _common(
        command="change overview",
        exit_code=1,
        root=root,
        warnings=[],
        errors=[message],
        verdict=None,
        claims=[],
    )
    document["change_id"] = change_id
    return document
