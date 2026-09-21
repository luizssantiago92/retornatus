"""Change workflow: Demand → Situation → Contract → Action (PRD M3)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
class ChangeWorkflowResult:
    change: Change
    contract: Contract
    action: Action | None


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
    ) -> ChangeWorkflowResult:
        change_id = self.next_change_id()
        change = Change(
            id=change_id,
            title=title,
            demand=Demand(statement=demand_statement, kind=demand_kind),
        )
        self.repo.save_change(change)
        self.repo.save_situation(change_id, situation)

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
            # reload revision for update
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
            )

        return ChangeWorkflowResult(change=change, contract=contract, action=action)

    def create_action(
        self,
        *,
        change_id: str,
        objective: str,
        success_conditions: list[str],
        task_descriptions: list[str] | None = None,
        origin_kind: ActionOriginKind = ActionOriginKind.CONTRACT,
        origin_ref: str = "contract@v1",
        authority: Authority | None = None,
        action_number: int = 1,
    ) -> Action:
        action_id = format_owned_id(change_id, "A", action_number)
        embedded: list[Task] = []
        # Tasks only when needed (PRD §14)
        if task_descriptions and len(task_descriptions) > 1:
            for i, desc in enumerate(task_descriptions, start=1):
                deps = [format_owned_id(change_id, "T", i - 1)] if i > 1 else []
                embedded.append(
                    Task(
                        id=format_owned_id(change_id, "T", i),
                        description=desc,
                        lifecycle=TaskLifecycle.PENDING,
                        depends_on=deps,
                    )
                )
        elif task_descriptions and len(task_descriptions) == 1:
            # Single task still optional — embed only if explicitly requested list
            embedded.append(
                Task(
                    id=format_owned_id(change_id, "T", 1),
                    description=task_descriptions[0],
                    lifecycle=TaskLifecycle.PENDING,
                )
            )

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
