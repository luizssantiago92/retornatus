"""Governed bypass — Bypass is a governed decision, not absence of governance."""

from __future__ import annotations

from pathlib import Path

from retornatus.domain.enums import AuthorityCategory, DecisionKind
from retornatus.domain.ids import format_project_id
from retornatus.domain.models import Authority, BypassRecord, Decision
from retornatus.domain.relations import Relation, RelationType
from retornatus.infrastructure.persistence.repository import FileRepository


class BypassError(ValueError):
    """Raised when a governance bypass lacks required authority/reason."""


class BypassService:
    def __init__(self, root: Path) -> None:
        self.repo = FileRepository(root)

    def next_bypass_id(self) -> str:
        existing = self.repo.list_bypasses()
        nums: list[int] = []
        for item in existing:
            try:
                nums.append(int(item.id.split("-", 1)[1]))
            except (IndexError, ValueError):
                continue
        return f"B-{max(nums, default=0) + 1:04d}"

    def record_bypass(
        self,
        *,
        gate: str,
        entity_id: str,
        reason: str,
        authority: Authority | None = None,
        decision_id: str | None = None,
    ) -> BypassRecord:
        if not reason or not reason.strip():
            raise BypassError("Governed bypass requires a non-empty reason")
        auth = authority or Authority(
            category=AuthorityCategory.HUMAN,
            rationale="Explicit governance bypass",
        )
        if auth.category not in {AuthorityCategory.HUMAN, AuthorityCategory.DELEGATED}:
            raise BypassError("Bypass authority must be HUMAN or DELEGATED")
        if auth.category == AuthorityCategory.DELEGATED and not (auth.rationale or "").strip():
            raise BypassError("DELEGATED bypass requires rationale")

        decision_ref: str | None = decision_id
        if auth.category == AuthorityCategory.HUMAN and decision_id is None:
            # Create paired Decision so HUMAN boundary is durable
            decision = Decision(
                id=self._next_decision_id(),
                kind=DecisionKind.GOVERNANCE_BYPASS,
                subject_id=entity_id,
                summary=f"Bypass {gate} for {entity_id}: {reason.strip()}",
                authority=auth,
                confirmation_token=entity_id,
                relations=[
                    Relation(type=RelationType.APPLIES_TO, target_id=entity_id),
                ],
            )
            self.repo.save_decision(decision)
            decision_ref = decision.id
        elif decision_id is not None:
            decision_obj, _ = self.repo.load_decision(decision_id)
            if decision_obj.kind is not DecisionKind.GOVERNANCE_BYPASS:
                raise BypassError("decision_id must reference a GOVERNANCE_BYPASS Decision")
            if decision_obj.subject_id != entity_id:
                raise BypassError("Decision subject must match bypassed entity")

        record = BypassRecord(
            id=self.next_bypass_id(),
            gate=gate,
            entity_id=entity_id,
            reason=reason.strip(),
            authority=auth,
            decision_id=decision_ref,
            relations=[
                Relation(type=RelationType.APPLIES_TO, target_id=entity_id),
            ],
        )
        self.repo.save_bypass(record)
        return record

    def _next_decision_id(self) -> str:
        existing = self.repo.list_decisions()
        nums = []
        for item in existing:
            try:
                nums.append(int(item.id.split("-", 1)[1]))
            except (IndexError, ValueError):
                continue
        return format_project_id("D", max(nums, default=0) + 1)
