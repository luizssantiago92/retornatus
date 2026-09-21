"""Adaptation: Learning, Graduation, Rule Candidates (PRD M9)."""

from __future__ import annotations

from pathlib import Path

from retornatus.domain.enums import AuthorityCategory, RuleApplicationMode
from retornatus.domain.ids import format_project_id
from retornatus.domain.models import Authority, LearningMetadata, Rule
from retornatus.domain.relations import Relation, RelationType
from retornatus.infrastructure.persistence.repository import FileRepository


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

    def activate_rule(self, rule_id: str) -> Rule:
        """Human validation boundary — activates an existing candidate."""
        rule, rev = self.repo.load_rule(rule_id)
        if rule.authority.category != AuthorityCategory.HUMAN:
            raise ValueError("Only HUMAN-validated rules may become authoritative")
        activated = rule.model_copy(update={"active": True})
        self.repo.save_rule(activated, expected=rev)
        return activated
