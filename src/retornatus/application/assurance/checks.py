"""Execute owner-declared required checks and record Evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from retornatus.application.assurance.evaluate import (
    EXECUTION_EVIDENCE_TYPES,
    Claim,
    build_claims_from_contract,
)
from retornatus.application.assurance.evidence import EvidenceService
from retornatus.application.assurance.execute import (
    DEFAULT_COMMAND_TIMEOUT_SECONDS,
    capture_command,
)
from retornatus.application.assurance.settings import RequiredCheck, load_required_checks
from retornatus.domain.errors import UsageError
from retornatus.domain.models import Evidence
from retornatus.infrastructure.persistence.repository import FileRepository


@dataclass
class RequiredCheckRun:
    """Evidence recorded for one ``checks run`` / ``verify --run-checks``."""

    evidence: list[Evidence] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return bool(self.evidence) and all(item.exit_code == 0 and not item.timed_out for item in self.evidence)


def run_required_checks(
    root: Path,
    change_id: str,
    *,
    timeout_seconds: float = DEFAULT_COMMAND_TIMEOUT_SECONDS,
) -> RequiredCheckRun:
    """Run each required check once, then record Evidence for matching claims.

    Captures happen before any Evidence file is written so the git snapshot
    describes the tree the commands actually ran against.
    """
    checks = load_required_checks(root)
    if not checks:
        raise UsageError(
            "No [assurance] required_checks in .retornatus/config.toml. "
            'Example: required_checks = [{name="tests", run=["pytest", "-q"]}]'
        )
    repo = FileRepository(root)
    try:
        contract, _ = repo.load_contract(change_id)
    except FileNotFoundError as exc:
        raise UsageError(f"No contract for {change_id}") from exc
    claims = build_claims_from_contract(contract)
    planned = [(check, _targets_for_check(check, claims)) for check in checks]
    captures = [capture_command(root, list(check.run), timeout_seconds=timeout_seconds) for check, _targets in planned]
    service = EvidenceService(root)
    outcome = RequiredCheckRun()
    for (check, targets), capture in zip(planned, captures, strict=True):
        if not targets:
            evidence_type = next(iter(check.types), "test_result")
            outcome.notes.append(f"check {check.name}: no execution claim matched; recorded unbound {evidence_type}")
            outcome.evidence.append(
                service.record_executed(
                    change_id=change_id,
                    evidence_type=evidence_type,
                    subject=check.name,
                    capture=capture,
                    source=check.name,
                    capture_git=True,
                )
            )
            continue
        for evidence_type, subject, claim_id in targets:
            outcome.evidence.append(
                service.record_executed(
                    change_id=change_id,
                    evidence_type=evidence_type,
                    subject=subject,
                    capture=capture,
                    source=check.name,
                    supports_claim_id=claim_id,
                    capture_git=True,
                )
            )
    return outcome


def _targets_for_check(
    check: RequiredCheck,
    claims: list[Claim],
) -> list[tuple[str, str, str]]:
    targets: list[tuple[str, str, str]] = []
    for claim in claims:
        execution_types = [
            evidence_type
            for evidence_type in claim.required_evidence_types
            if evidence_type in EXECUTION_EVIDENCE_TYPES
        ]
        if not execution_types:
            continue
        if check.types:
            matched = [evidence_type for evidence_type in execution_types if evidence_type in check.types]
            if not matched:
                continue
            evidence_type = matched[0]
        else:
            evidence_type = execution_types[0]
        subject = claim.subject or check.name
        targets.append((evidence_type, subject, claim.id))
    return targets
