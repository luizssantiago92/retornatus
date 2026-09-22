"""Change workflow: Demand → Situation → Contract → Action (PRD M3)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from retornatus.application.change.readiness import DependencyCycleError, assert_acyclic
from retornatus.application.change.situation import (
    SituationAssessment,
    assess_situation,
    discover_kickoff,
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
        answered_topics: set[str] | None = None,
    ) -> SituationAssessment:
        """Governed requirements elicitation — kickoff + repo; ask only material questions."""
        from retornatus.application.change.situation import collect_repo_signals

        root = self.repo.paths.root
        project_context = load_project_context_snippet(root)
        kickoff_sources, kickoff_facts = discover_kickoff(root)
        return assess_situation(
            demand=demand_statement,
            situation=situation,
            what=what,
            done_criteria=done_criteria,
            constraints=constraints,
            project_context=project_context,
            repo_signals=collect_repo_signals(root),
            kickoff_sources=kickoff_sources,
            kickoff_facts=kickoff_facts,
            answered_topics=answered_topics,
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
        lane: str | None = None,
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
        if lane is None:
            from retornatus.application.change.classify import classify_change

            lane = classify_change(
                demand=demand_statement,
                what=what,
                done_criteria=done_criteria,
                demand_kind=demand_kind,
                task_count=len(task_specs or tasks or []),
                constraint_count=len(constraints or []),
            ).lane.value
        change = Change(
            id=change_id,
            title=title,
            demand=Demand(statement=demand_statement, kind=demand_kind),
            lane=lane,
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
        from retornatus.application.change.status import project_change_status

        return project_change_status(self.repo.paths.root, change_id).render()

    def activate_contract(self, change_id: str) -> Contract:
        """
        Activate a draft Contract after Situation is sufficient.

        Refuses when elicitation still has material gaps.
        """
        change, change_rev = self.repo.load_change(change_id)
        contract, contract_rev = self.repo.load_contract(change_id)
        if contract.active:
            return contract
        assessment = self.elicit_situation(
            demand_statement=change.demand.statement,
            what=contract.what,
            done_criteria=list(contract.done_criteria),
            constraints=list(contract.constraints),
        )
        if not assessment.sufficient_for_contract:
            raise ValueError(
                f"Situation insufficient to activate Contract: {assessment.rationale}"
            )
        if not contract.done_criteria:
            raise ValueError("Contract requires at least one done criterion before activation")
        activated = contract.activate()
        change = change.model_copy(
            update={"active_contract_version": activated.version}
        )
        self.repo.save_change(change, expected=change_rev)
        self.repo.save_contract(activated, expected=contract_rev)
        return activated

    def reopen_contract(
        self,
        change_id: str,
        *,
        what: str,
        done_criteria: list[str],
        constraints: list[str] | None = None,
        situation_note: str | None = None,
        activate: bool = True,
    ) -> Contract:
        """
        Material Contract change: archive active version, reopen Situation, new version.

        Active Contracts are immutable — a new version is required (PRD §12).
        """
        from retornatus.infrastructure.persistence.atomic import atomic_write_bytes
        from retornatus.infrastructure.persistence.serializers import dump_json_model

        change, change_rev = self.repo.load_change(change_id)
        current, _ = self.repo.load_contract(change_id)
        if not current.active:
            raise ValueError("Only an active Contract can be reopened into a new version")

        # Archive immutable snapshot
        archive_path = self.repo.paths.contract_archive_json(change_id, current.version)
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_bytes(archive_path, dump_json_model(current))

        # Append Situation reopen note
        try:
            meta, body, sit_rev = self.repo.load_situation(change_id)
            note = situation_note or (
                f"Material change: reopened from contract v{current.version} → "
                f"v{current.version + 1}"
            )
            new_body = body.rstrip() + f"\n\n## Reopened Situation\n\n{note}\n"
            self.repo.save_markdown(
                self.repo.paths.situation_md(change_id),
                new_body,
                front_matter=meta or {"schema_version": 1, "change_id": change_id},
                expected=sit_rev,
            )
        except FileNotFoundError:
            assessment = self.elicit_situation(
                demand_statement=change.demand.statement,
                what=what,
                done_criteria=done_criteria,
                constraints=constraints,
            )
            self.repo.save_situation(
                change_id,
                assessment.to_markdown(demand=change.demand.statement),
            )

        new_version = current.version + 1
        contract = Contract(
            change_id=change_id,
            version=new_version,
            what=what,
            constraints=constraints if constraints is not None else list(current.constraints),
            done_criteria=done_criteria,
            active=False,
        )
        if activate:
            # Sufficiency check
            assessment = self.elicit_situation(
                demand_statement=change.demand.statement,
                what=what,
                done_criteria=done_criteria,
                constraints=contract.constraints,
            )
            if not assessment.sufficient_for_contract:
                activate = False
            else:
                contract = contract.activate()
                change = change.model_copy(
                    update={"active_contract_version": contract.version}
                )
                self.repo.save_change(change, expected=change_rev)

        # Overwrite active contract.json with new version (prior archived)
        # Must replace existing file — load revision first
        _, contract_rev = self.repo.load_contract(change_id)
        self.repo.save_contract(contract, expected=contract_rev)
        return contract
