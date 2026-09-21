"""Adaptation: Learning, Graduation, Rule Candidates, Human Decisions (PRD M9)."""

from __future__ import annotations

from pathlib import Path

from retornatus.domain.enums import (
    AuthorityCategory,
    DecisionKind,
    RuleApplicationMode,
)
from retornatus.domain.ids import format_project_id
from retornatus.domain.models import Authority, Decision, LearningMetadata, Rule
from retornatus.domain.relations import Relation, RelationType
from retornatus.infrastructure.persistence.repository import FileRepository


class HumanAuthorityError(ValueError):
    """Raised when a HUMAN boundary is crossed without a valid Decision."""


class AdaptationService:
    def __init__(self, root: Path) -> None:
        self.repo = FileRepository(root)

    def next_learning_id(self) -> str:
        existing = self.repo.list_learnings()
        nums = []
        for item in existing:
            try:
                nums.append(int(item.id.split("-", 1)[1]))
            except (IndexError, ValueError):
                continue
        return format_project_id("L", max(nums, default=0) + 1)

    def next_rule_id(self) -> str:
        existing = self.repo.list_rules()
        nums = []
        for item in existing:
            try:
                nums.append(int(item.id.split("-", 1)[1]))
            except (IndexError, ValueError):
                continue
        return format_project_id("R", max(nums, default=0) + 1)

    def next_decision_id(self) -> str:
        existing = self.repo.list_decisions()
        nums = []
        for item in existing:
            try:
                nums.append(int(item.id.split("-", 1)[1]))
            except (IndexError, ValueError):
                continue
        return format_project_id("D", max(nums, default=0) + 1)

    def record_learning(
        self,
        *,
        title: str,
        body: str,
        summary: str | None = None,
        tags: list[str] | None = None,
        related_ids: list[str] | None = None,
    ) -> LearningMetadata:
        meta = LearningMetadata(
            id=self.next_learning_id(),
            title=title,
            summary=summary,
            tags=tags or [],
            relations=[
                Relation(type=RelationType.RELEVANT_TO, target_id=rid)
                for rid in (related_ids or [])
            ],
        )
        self.repo.save_learning(meta, body)
        return meta

    def propose_rule_candidate(
        self,
        *,
        statement: str,
        applicability: str,
        from_learning_id: str | None = None,
    ) -> Rule:
        """
        Graduation produces a Rule Candidate — never auto-activates (PRD §40–§41).
        """
        relations = []
        if from_learning_id:
            relations.append(
                Relation(type=RelationType.DERIVED_FROM, target_id=from_learning_id)
            )
        candidate = Rule(
            id=self.next_rule_id(),
            statement=statement,
            applicability=applicability,
            active=False,
            authority=Authority(
                category=AuthorityCategory.HUMAN,
                rationale="Rule candidate awaiting human validation",
            ),
            modes=[RuleApplicationMode.INSTRUCTIONAL],
            relations=relations,
        )
        self.repo.save_rule(candidate)
        return candidate

    def record_human_decision(
        self,
        *,
        kind: DecisionKind,
        subject_id: str,
        summary: str,
        confirmation_token: str,
        rationale: str | None = None,
    ) -> Decision:
        """
        Record a HUMAN Decision artifact.

        For rule activation / bypass, confirmation_token must equal subject_id.
        This is a distinct intentional act from proposing a Rule Candidate.
        """
        decision = Decision(
            id=self.next_decision_id(),
            kind=kind,
            subject_id=subject_id,
            summary=summary,
            authority=Authority(
                category=AuthorityCategory.HUMAN,
                rationale=rationale or "Human decision boundary",
            ),
            confirmation_token=confirmation_token,
            relations=[
                Relation(type=RelationType.APPLIES_TO, target_id=subject_id),
            ],
        )
        self.repo.save_decision(decision)
        return decision

    def activate_rule(self, rule_id: str, *, human_decision_id: str) -> Rule:
        """
        HUMAN BOUNDARY: Rule Candidate → Active Rule.

        Requires a Decision (APPROVE_RULE_ACTIVATION) for this rule_id.
        Setting authority=HUMAN on the Rule alone is insufficient.
        """
        rule, rev = self.repo.load_rule(rule_id)
        try:
            decision, _ = self.repo.load_decision(human_decision_id)
        except FileNotFoundError as exc:
            raise HumanAuthorityError(
                f"Human Decision {human_decision_id} not found"
            ) from exc

        if decision.authority.category != AuthorityCategory.HUMAN:
            raise HumanAuthorityError("Decision must carry HUMAN authority")
        if decision.kind is not DecisionKind.APPROVE_RULE_ACTIVATION:
            raise HumanAuthorityError(
                f"Decision kind must be APPROVE_RULE_ACTIVATION, got {decision.kind}"
            )
        if decision.subject_id != rule_id:
            raise HumanAuthorityError(
                f"Decision subject {decision.subject_id} does not match rule {rule_id}"
            )
        if decision.confirmation_token != rule_id:
            raise HumanAuthorityError("Decision confirmation_token mismatch")

        activated = rule.model_copy(
            update={
                "active": True,
                "authority": Authority(
                    category=AuthorityCategory.HUMAN,
                    rationale=f"Activated via {human_decision_id}",
                ),
                "relations": list(rule.relations)
                + [Relation(type=RelationType.DERIVED_FROM, target_id=human_decision_id)],
            }
        )
        self.repo.save_rule(activated, expected=rev)
        return activated
