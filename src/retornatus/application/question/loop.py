"""Finding → Question → Action loop (PRD M7). Resolution is established, not claimed."""

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


class ResolutionIncompleteError(ValueError):
    """Raised when Resolution lacks Evidence required to establish the outcome."""


def _requires_evidence(statement: str) -> bool:
    """Verifiable outcome Questions need Evidence — not bare self-report."""
    s = statement.lower()
    markers = (
        "fix",
        "broken",
        "fail",
        "pass",
        "evidence",
        "verify",
        "how do we establish",
        "assurance",
        "bug",
        "error",
        "regress",
        "implement",
        "work",
    )
    return any(m in s for m in markers)


class QuestionLoop:
    def __init__(self, root: Path) -> None:
        self.repo = FileRepository(root)

    def next_finding_number(self, change_id: str) -> int:
        findings_dir = self.repo.paths.change_dir(change_id) / "findings"
        if not findings_dir.is_dir():
            return 1
        nums: list[int] = []
        for path in findings_dir.glob("F-*.json"):
            try:
                nums.append(int(path.stem.split("-", 1)[1]))
            except (IndexError, ValueError):
                continue
        return max(nums, default=0) + 1

    def next_question_number(self, change_id: str) -> int:
        questions_dir = self.repo.paths.change_dir(change_id) / "questions"
        if not questions_dir.is_dir():
            return 1
        nums: list[int] = []
        for path in questions_dir.glob("Q-*.json"):
            try:
                nums.append(int(path.stem.split("-", 1)[1]))
            except (IndexError, ValueError):
                continue
        return max(nums, default=0) + 1

    def next_action_number(self, change_id: str) -> int:
        actions_dir = self.repo.paths.change_dir(change_id) / "actions"
        if not actions_dir.is_dir():
            return 1
        nums: list[int] = []
        for path in actions_dir.glob("A-*.json"):
            try:
                nums.append(int(path.stem.split("-", 1)[1]))
            except (IndexError, ValueError):
                continue
        return max(nums, default=0) + 1

    def record_finding(
        self,
        *,
        change_id: str,
        observation: str,
        number: int | None = None,
        source: str | None = None,
    ) -> Finding:
        n = number if number is not None else self.next_finding_number(change_id)
        finding = Finding(
            id=format_owned_id(change_id, "F", n),
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
        number: int | None = None,
    ) -> Question:
        if not finding_ids:
            raise ValueError("A Question must be grounded in at least one Finding")
        n = number if number is not None else self.next_question_number(change_id)
        question = Question(
            id=format_owned_id(change_id, "Q", n),
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
        action_number: int | None = None,
    ) -> Action:
        n = action_number if action_number is not None else self.next_action_number(change_id)
        action = Action(
            id=format_owned_id(change_id, "A", n),
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
        require_evidence: bool | None = None,
    ) -> Question:
        question, rev = self.repo.load_question(question_id)
        if question.lifecycle == QuestionLifecycle.RESOLVED:
            return question

        ids = list(evidence_ids or [])
        needs_proof = (
            require_evidence
            if require_evidence is not None
            else _requires_evidence(question.statement)
        )
        if needs_proof and not ids:
            raise ResolutionIncompleteError(
                "Resolution requires attributable Evidence for this verifiable Question "
                f"({question_id}); summary alone is not establishment"
            )

        # Validate Evidence artifacts exist when cited
        for eid in ids:
            try:
                self.repo.load_evidence(eid)
            except FileNotFoundError as exc:
                raise ResolutionIncompleteError(
                    f"Resolution cites missing Evidence: {eid}"
                ) from exc

        updated = question.model_copy(
            update={
                "lifecycle": QuestionLifecycle.RESOLVED,
                "resolution": Resolution(
                    summary=summary,
                    evidence_ids=ids,
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
