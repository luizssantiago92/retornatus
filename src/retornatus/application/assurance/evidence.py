"""Evidence recording helpers — bind Evidence to Claims."""

from __future__ import annotations

from pathlib import Path

from retornatus.domain.ids import format_owned_id
from retornatus.domain.models import Evidence
from retornatus.domain.relations import Relation, RelationType
from retornatus.infrastructure.persistence.repository import FileRepository


class EvidenceService:
    def __init__(self, root: Path) -> None:
        self.repo = FileRepository(root)

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
    ) -> Evidence:
        eid = format_owned_id(change_id, "E", self.next_evidence_number(change_id))
        relations: list[Relation] = []
        if supports_action_id:
            relations.append(
                Relation(type=RelationType.SUPPORTS, target_id=supports_action_id)
            )
        if supports_claim_id:
            relations.append(
                Relation(type=RelationType.SUPPORTS, target_id=supports_claim_id)
            )
        if challenges_claim_id:
            relations.append(
                Relation(type=RelationType.CHALLENGES, target_id=challenges_claim_id)
            )
        evidence = Evidence(
            id=eid,
            type=evidence_type,
            subject=subject,
            source=source,
            producer=producer,
            subject_state=subject_state,
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
