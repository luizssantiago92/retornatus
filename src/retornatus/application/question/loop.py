"""Finding → Question → Action loop (PRD M7)."""

from __future__ import annotations

from pathlib import Path

from retornatus.domain.enums import (
    ActionOriginKind,
    AuthorityCategory,
    QuestionLifecycle,
)
from retornatus.domain.ids import format_owned_id
from retornatus.domain.models import (
    Action,
    Authority,
    Finding,
    Question,
    Resolution,
)
from retornatus.domain.relations import Relation, RelationType
from retornatus.infrastructure.persistence.repository import FileRepository


class QuestionLoop:
    def __init__(self, root: Path) -> None:
        self.repo = FileRepository(root)

    def record_finding(
        self,
        *,
        change_id: str,
        observation: str,
        number: int = 1,
        source: str | None = None,
    ) -> Finding:
        finding = Finding(
            id=format_owned_id(change_id, "F", number),
            observation=observation,
            source=source,
        )
        self.repo.save_finding(finding)
        return finding

    def open_question(
        self,
        *,
        change_id: str,
        statement: str,
        finding_ids: list[str],
        number: int = 1,
    ) -> Question:
        if not finding_ids:
            raise ValueError("A Question must be grounded in at least one Finding")
        question = Question(
            id=format_owned_id(change_id, "Q", number),
            statement=statement,
            grounded_in=finding_ids,
            relations=[
                Relation(type=RelationType.GROUNDED_IN, target_id=fid)
                for fid in finding_ids
            ],
        )
        self.repo.save_question(question)
        return question

    def action_for_question(
        self,
        *,
        change_id: str,
        question_id: str,
        objective: str,
        success_conditions: list[str],
        action_number: int = 2,
    ) -> Action:
        action = Action(
            id=format_owned_id(change_id, "A", action_number),
            origin_kind=ActionOriginKind.QUESTION,
            origin_ref=question_id,
            objective=objective,
            success_conditions=success_conditions,
            authority=Authority(
                category=AuthorityCategory.DELEGATED,
                rationale="resolve question",
            ),
            relations=[
                Relation(type=RelationType.RESOLVES, target_id=question_id),
            ],
        )
        self.repo.save_action(action)
        return action

    def resolve_question(
        self,
        question_id: str,
        *,
        summary: str,
        evidence_ids: list[str] | None = None,
    ) -> Question:
        question, rev = self.repo.load_question(question_id)
        if question.lifecycle == QuestionLifecycle.RESOLVED:
            return question
        updated = question.model_copy(
            update={
                "lifecycle": QuestionLifecycle.RESOLVED,
                "resolution": Resolution(
                    summary=summary,
                    evidence_ids=evidence_ids or [],
                ),
            }
        )
        self.repo.save_question(updated, expected=rev)
        return updated

    def reopen_question(self, question_id: str) -> Question:
        question, rev = self.repo.load_question(question_id)
        updated = question.model_copy(
            update={"lifecycle": QuestionLifecycle.OPEN, "resolution": None}
        )
        self.repo.save_question(updated, expected=rev)
        return updated
