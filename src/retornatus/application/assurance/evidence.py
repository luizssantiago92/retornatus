"""Evidence recording helpers — bind Evidence to Claims."""

from __future__ import annotations

import shlex
from pathlib import Path

from retornatus.application.assurance.execute import (
    DEFAULT_COMMAND_TIMEOUT_SECONDS,
    CommandCapture,
    capture_command,
)
from retornatus.application.assurance.subject_state import capture_subject_state
from retornatus.domain.enums import EvidenceProvenance
from retornatus.domain.ids import format_owned_id
from retornatus.domain.models import Evidence
from retornatus.domain.relations import Relation, RelationType
from retornatus.infrastructure.persistence.atomic import atomic_write_bytes
from retornatus.infrastructure.persistence.repository import FileRepository


class EvidenceService:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.repo = FileRepository(self.root)

    def next_evidence_number(self, change_id: str) -> int:
        evidence_dir = self.repo.paths.change_dir(change_id) / "evidence"
        if not evidence_dir.is_dir():
            return 1
        nums: list[int] = []
        for path in evidence_dir.glob("E-*.json"):
            try:
                nums.append(int(path.stem.split("-", 1)[1]))
            except (IndexError, ValueError):
                continue
        return max(nums, default=0) + 1

    def add(
        self,
        *,
        change_id: str,
        evidence_type: str,
        subject: str,
        source: str,
        producer: str,
        subject_state: str | None = None,
        supports_action_id: str | None = None,
        supports_claim_id: str | None = None,
        challenges_claim_id: str | None = None,
        capture_git: bool = False,
    ) -> Evidence:
        """
        Record Evidence.

        ``subject_state`` wins when provided. With ``capture_git=True`` and no
        explicit state, records ``commit:<HEAD>`` when git is available.
        """
        eid = format_owned_id(change_id, "E", self.next_evidence_number(change_id))
        relations: list[Relation] = []
        if supports_action_id:
            relations.append(Relation(type=RelationType.SUPPORTS, target_id=supports_action_id))
        if supports_claim_id:
            relations.append(Relation(type=RelationType.SUPPORTS, target_id=supports_claim_id))
        if challenges_claim_id:
            relations.append(Relation(type=RelationType.CHALLENGES, target_id=challenges_claim_id))

        final_state: str | None
        if subject_state is not None:
            final_state = subject_state
        elif capture_git:
            final_state = capture_subject_state(self.root, use_git=True, subject=subject)
        else:
            final_state = None

        evidence = Evidence(
            id=eid,
            type=evidence_type,
            subject=subject,
            source=source,
            producer=producer,
            subject_state=final_state,
            provenance=EvidenceProvenance.SELF_REPORTED,
            relations=relations,
        )
        self.repo.save_evidence(evidence)
        return evidence

    def run(
        self,
        *,
        change_id: str,
        evidence_type: str,
        subject: str,
        command: list[str],
        source: str | None = None,
        producer: str = "retornatus",
        timeout_seconds: float = DEFAULT_COMMAND_TIMEOUT_SECONDS,
        subject_state: str | None = None,
        supports_action_id: str | None = None,
        supports_claim_id: str | None = None,
        challenges_claim_id: str | None = None,
        capture_git: bool = False,
    ) -> Evidence:
        """Execute ``command`` and record the capture as Evidence.

        A non-zero exit, a timeout, or a failure to start the process is still
        persisted. Assurance must not treat that record as passing.
        ``provenance`` is always ``executed``. ``git_commit`` / ``worktree_dirty``
        describe HEAD before the command; they are None outside git.
        ``capture_git`` only fills ``subject_state`` (the freshness field), the
        same way ``add(..., capture_git=True)`` does.
        """
        capture = capture_command(
            self.root,
            command,
            timeout_seconds=timeout_seconds,
        )
        return self.record_executed(
            change_id=change_id,
            evidence_type=evidence_type,
            subject=subject,
            capture=capture,
            source=source,
            producer=producer,
            subject_state=subject_state,
            supports_action_id=supports_action_id,
            supports_claim_id=supports_claim_id,
            challenges_claim_id=challenges_claim_id,
            capture_git=capture_git,
        )

    def record_executed(
        self,
        *,
        change_id: str,
        evidence_type: str,
        subject: str,
        capture: CommandCapture,
        source: str | None = None,
        producer: str = "retornatus",
        subject_state: str | None = None,
        supports_action_id: str | None = None,
        supports_claim_id: str | None = None,
        challenges_claim_id: str | None = None,
        capture_git: bool = False,
    ) -> Evidence:
        """Persist an already-captured command as executed Evidence.

        Callers that run several checks capture first, then record, so later
        evidence files do not dirty the snapshot of an earlier command.
        """
        eid = format_owned_id(change_id, "E", self.next_evidence_number(change_id))
        relations: list[Relation] = []
        if supports_action_id:
            relations.append(Relation(type=RelationType.SUPPORTS, target_id=supports_action_id))
        if supports_claim_id:
            relations.append(Relation(type=RelationType.SUPPORTS, target_id=supports_claim_id))
        if challenges_claim_id:
            relations.append(Relation(type=RelationType.CHALLENGES, target_id=challenges_claim_id))

        artifact_path = self.repo.paths.evidence_output(eid)
        atomic_write_bytes(artifact_path, capture.output_bytes)
        output_artifact = artifact_path.resolve().relative_to(self.root).as_posix()

        if subject_state is not None:
            final_state: str | None = subject_state
        elif capture_git:
            final_state = capture_subject_state(self.root, use_git=True, subject=subject)
        else:
            final_state = None

        evidence = Evidence(
            id=eid,
            type=evidence_type,
            subject=subject,
            source=source if source else shlex.join(capture.argv),
            producer=producer,
            subject_state=final_state,
            provenance=EvidenceProvenance.EXECUTED,
            command=list(capture.argv),
            exit_code=capture.exit_code,
            started_at=capture.started_at,
            ended_at=capture.ended_at,
            duration_ms=capture.duration_ms,
            output_sha256=capture.output_sha256,
            output_tail=capture.output_tail,
            output_artifact=output_artifact,
            git_commit=capture.git_commit,
            worktree_dirty=capture.worktree_dirty,
            timed_out=capture.timed_out,
            relations=relations,
        )
        self.repo.save_evidence(evidence)
        return evidence

    def list_for_change(self, change_id: str) -> list[Evidence]:
        evidence_dir = self.repo.paths.change_dir(change_id) / "evidence"
        if not evidence_dir.is_dir():
            return []
        items: list[Evidence] = []
        for path in sorted(evidence_dir.glob("E-*.json")):
            ev, _ = self.repo.load_evidence(f"{change_id}/{path.stem}")
            items.append(ev)
        return items
