"""Change workflow: Demand → Situation → Contract → Action (PRD M3)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from retornatus.application.change.readiness import DependencyCycleError, assert_acyclic
from retornatus.application.change.situation import (
    SituationAssessment,
    assess_situation,
    load_project_context_snippet,
)
from retornatus.domain.enums import (
    ActionOriginKind,
    AuthorityCategory,
    DemandKind,
    TaskLifecycle,
)
from retornatus.domain.ids import format_change_id, format_owned_id
from retornatus.domain.models import (
    Action,
    Authority,
    Change,
    Contract,
    Demand,
    Task,
)
from retornatus.infrastructure.persistence.repository import FileRepository


@dataclass
class TaskSpec:
    """Explicit Task declaration — dependencies are never invented from list order."""

    description: str
    depends_on_indices: list[int] | None = None  # 0-based indices into the same list
    resources: list[str] | None = None


@dataclass
class ChangeWorkflowResult:
    change: Change
    contract: Contract
    action: Action | None
    situation_assessment: SituationAssessment | None = None


class ChangeWorkflow:
    """Application service owning Change structural integrity."""

    def __init__(self, root: Path) -> None:
        self.repo = FileRepository(root)

    def next_change_id(self) -> str:
        existing = self.repo.list_change_ids()
        numbers = []
        for cid in existing:
            try:
                numbers.append(int(cid.split("-", 1)[1]))
            except (IndexError, ValueError):
                continue
        nxt = max(numbers, default=0) + 1
        return format_change_id(nxt)

    def elicit_situation(
        self,
        *,
        demand_statement: str,
        situation: str | None = None,
        what: str | None = None,
        done_criteria: list[str] | None = None,
        constraints: list[str] | None = None,
    ) -> SituationAssessment:
        """Governed elicitation — inspect project context; ask only material questions."""
        project_context = load_project_context_snippet(self.repo.paths.root)
        return assess_situation(
            demand=demand_statement,
            situation=situation,
            what=what,
            done_criteria=done_criteria,
            constraints=constraints,
            project_context=project_context,
        )

    def create_change(
        self,
        *,
        title: str,
        demand_statement: str,
        demand_kind: DemandKind = DemandKind.OTHER,
        situation: str,
        what: str,
        done_criteria: list[str],
        constraints: list[str] | None = None,
        activate_contract: bool = True,
        action_objective: str | None = None,
        tasks: list[str] | None = None,
        task_specs: list[TaskSpec] | None = None,
        require_sufficient_situation: bool = False,
    ) -> ChangeWorkflowResult:
        assessment = self.elicit_situation(
            demand_statement=demand_statement,
            situation=situation,
            what=what,
            done_criteria=done_criteria,
            constraints=constraints,
        )
        if require_sufficient_situation and not assessment.sufficient_for_contract:
            raise ValueError(
                f"Situation insufficient for Contract: {assessment.rationale}"
            )
        if activate_contract and not assessment.sufficient_for_contract:
            # Soft guard: refuse activation when elicitation says not ready
            activate_contract = False

        change_id = self.next_change_id()
        change = Change(
            id=change_id,
            title=title,
            demand=Demand(statement=demand_statement, kind=demand_kind),
        )
        self.repo.save_change(change)

        situation_body = assessment.to_markdown(
            demand=demand_statement,
            project_notes=load_project_context_snippet(self.repo.paths.root) or None,
        )
        if situation and situation.strip() and "pending detailed analysis" not in situation.lower():
            situation_body = situation_body + "\n## Agent narrative\n\n" + situation.strip() + "\n"
        self.repo.save_situation(change_id, situation_body)

        contract = Contract(
            change_id=change_id,
            version=1,
            what=what,
            constraints=constraints or [],
            done_criteria=done_criteria,
        )
        if activate_contract:
            contract = contract.activate()
            change = change.model_copy(update={"active_contract_version": contract.version})
            _, rev = self.repo.load_change(change_id)
            self.repo.save_change(change, expected=rev)

        self.repo.save_contract(contract)

        action: Action | None = None
        if action_objective:
            action = self.create_action(
                change_id=change_id,
                objective=action_objective,
                success_conditions=done_criteria,
                task_descriptions=tasks,
                task_specs=task_specs,
            )

        return ChangeWorkflowResult(
            change=change,
            contract=contract,
            action=action,
            situation_assessment=assessment,
        )

    def create_action(
        self,
        *,
        change_id: str,
        objective: str,
        success_conditions: list[str],
        task_descriptions: list[str] | None = None,
        task_specs: list[TaskSpec] | None = None,
        origin_kind: ActionOriginKind = ActionOriginKind.CONTRACT,
        origin_ref: str = "contract@v1",
        authority: Authority | None = None,
        action_number: int = 1,
    ) -> Action:
        action_id = format_owned_id(change_id, "A", action_number)
        embedded: list[Task] = []

        if task_specs:
            # Explicit dependencies only — never invent sequential chains
            for i, spec in enumerate(task_specs, start=1):
                deps: list[str] = []
                for dep_idx in spec.depends_on_indices or []:
                    if dep_idx < 0 or dep_idx >= len(task_specs):
                        raise ValueError(f"Invalid depends_on index {dep_idx}")
                    if dep_idx == i - 1:
                        raise ValueError("Task cannot depend on itself")
                    deps.append(format_owned_id(change_id, "T", dep_idx + 1))
                embedded.append(
                    Task(
                        id=format_owned_id(change_id, "T", i),
                        description=spec.description,
                        lifecycle=TaskLifecycle.PENDING,
                        depends_on=deps,
                        resources=list(spec.resources or []),
                    )
                )
        elif task_descriptions:
            # Independent PENDING tasks — declaration order is NOT dependency
            for i, desc in enumerate(task_descriptions, start=1):
                embedded.append(
                    Task(
                        id=format_owned_id(change_id, "T", i),
                        description=desc,
                        lifecycle=TaskLifecycle.PENDING,
                    )
                )

        try:
            assert_acyclic(embedded)
        except DependencyCycleError:
            raise

        action = Action(
            id=action_id,
            origin_kind=origin_kind,
            origin_ref=origin_ref,
            objective=objective,
            success_conditions=success_conditions,
            authority=authority
            or Authority(category=AuthorityCategory.DELEGATED, rationale="routine"),
            tasks=embedded,
        )
        self.repo.save_action(action)
        return action

    def derived_status(self, change_id: str) -> str:
        """Human-readable projection (PRD §44) — not durable truth."""
        change, _ = self.repo.load_change(change_id)
        try:
            contract, _ = self.repo.load_contract(change_id)
        except FileNotFoundError:
            return f"{change_id}: demand understood, no contract"
        if not contract.active:
            return f"{change_id}: contract draft v{contract.version}"
        return f"{change_id}: contract v{contract.version} active — {change.title}"
