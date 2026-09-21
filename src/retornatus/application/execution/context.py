"""Execution context assembly (PRD M5) — assembled, not inherited."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pydantic import Field

from retornatus.application.adaptation.skills import SkillService
from retornatus.application.change.situation import load_project_context_snippet
from retornatus.application.execution.isolation import (
    capability_flag_list,
    enrich_capabilities,
    isolation_boundaries,
)
from retornatus.domain.base import DomainModel
from retornatus.domain.enums import BoundaryRealization
from retornatus.domain.ids import change_id_of
from retornatus.domain.models import (
    Action,
    Authority,
    Boundaries,
    Boundary,
    LearningMetadata,
    Rule,
    Skill,
)
from retornatus.infrastructure.environment.adapters import detect_environment
from retornatus.infrastructure.persistence.repository import FileRepository


class ExecutionContext(DomainModel):
    """Stable assembled context for a bounded execution."""

    action_id: str
    assembled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    objective: str
    success_conditions: list[str] = Field(default_factory=list)
    contract_what: str | None = None
    contract_constraints: list[str] = Field(default_factory=list)
    contract_done: list[str] = Field(default_factory=list)
    authority: Authority
    boundaries: Boundaries = Field(default_factory=Boundaries)
    applicable_rules: list[Rule] = Field(default_factory=list)
    relevant_learnings: list[LearningMetadata] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    skill_ids: list[str] = Field(default_factory=list)
    capability_requirements: list[str] = Field(default_factory=list)
    environment_capabilities: list[str] = Field(default_factory=list)
    project_context_excerpt: str | None = None
    independent_assurance: bool = False


def _tokens(*parts: str | None) -> set[str]:
    text = " ".join(p for p in parts if p).lower()
    return {t for t in re_split(text) if len(t) > 2}


def re_split(text: str) -> list[str]:
    import re

    return re.findall(r"[a-z0-9_/-]+", text.lower())


def _rule_applies(rule: Rule, haystack: set[str]) -> bool:
    """Applicability-aware inclusion — unrelated Rules must not enter context."""
    app_tokens = _tokens(rule.applicability, rule.statement)
    if not app_tokens:
        return False
    # overlap OR applicability phrase contained in objective/scope text
    if app_tokens & haystack:
        return True
    app = rule.applicability.lower().strip()
    joined = " ".join(haystack)
    if app and (app in joined or any(tok in app for tok in haystack if len(tok) > 4)):
        return True
    # Broad applicability markers
    if app in {"all", "all changes", "*", "global"}:
        return True
    return False


def _learning_relevant(learning: LearningMetadata, haystack: set[str]) -> bool:
    learn_tokens = _tokens(
        learning.title,
        learning.summary,
        " ".join(learning.tags),
    )
    return bool(learn_tokens & haystack) or any(
        r.target_id for r in learning.relations if r.target_id in haystack
    )


def assemble_execution_context(
    root: Path,
    action_id: str,
    *,
    skill_ids: list[str] | None = None,
    capability_requirements: list[str] | None = None,
    query: str | None = None,
    independent_assurance: bool = False,
) -> ExecutionContext:
    """
    Select relevant context for an Action — sufficient, not comprehensive.

    Context assembled, not inherited. Context follows responsibility.
    When independent_assurance=True, omit author-linked Skill bodies' conclusions
    by assembling a fresh context without carrying prior Assurance rationale.
    """
    repo = FileRepository(root)
    action, _ = repo.load_action(action_id)
    change_id = change_id_of(action_id)

    contract_what = None
    contract_constraints: list[str] = []
    contract_done: list[str] = []
    try:
        contract, _ = repo.load_contract(change_id)
        contract_what = contract.what
        contract_constraints = list(contract.constraints)
        contract_done = list(contract.done_criteria)
    except FileNotFoundError:
        pass

    haystack = _tokens(
        action.objective,
        action.scope,
        " ".join(action.success_conditions),
        contract_what,
        " ".join(contract_done),
        query,
        change_id,
        action_id,
    )

    rules = [
        r
        for r in repo.list_rules()
        if r.active and _rule_applies(r, haystack)
    ]

    learnings = repo.list_learnings()
    if query:
        q = query.lower()
        learnings = [
            L
            for L in learnings
            if q in L.title.lower()
            or (L.summary and q in L.summary.lower())
            or any(q in t.lower() for t in L.tags)
        ]
    else:
        relevant = [L for L in learnings if _learning_relevant(L, haystack)]
        learnings = relevant[:5] if relevant else []

    # Independent Assurance: do not inherit author conclusions via learnings
    if independent_assurance:
        learnings = []

    skill_service = SkillService(root)
    skills = skill_service.resolve_for_action(action_id)
    if skill_ids:
        for sid in skill_ids:
            try:
                skill, _, _ = repo.load_skill(sid)
            except FileNotFoundError:
                continue
            if skill.id not in {s.id for s in skills}:
                skills.append(skill)
    if query and not skills:
        skills = skill_service.resolve_relevant(query)

    _, capabilities = detect_environment(root)
    capabilities = enrich_capabilities(root, capabilities)
    env_caps = capability_flag_list(capabilities)

    boundaries = Boundaries(
        items=[
            Boundary(
                name="repository-root",
                kind="filesystem",
                realization=BoundaryRealization.ADVISORY,
                description=str(root.resolve()),
            ),
            *isolation_boundaries(root, capabilities),
        ]
    )
    if independent_assurance:
        boundaries.items.append(
            Boundary(
                name="independent-assurance",
                kind="execution scope",
                realization=BoundaryRealization.ADVISORY,
                description="Fresh Assurance Execution — do not inherit author conclusions",
            )
        )

    project_excerpt = load_project_context_snippet(root, max_chars=1200) or None

    return ExecutionContext(
        action_id=action.id,
        objective=action.objective,
        success_conditions=action.success_conditions,
        contract_what=contract_what,
        contract_constraints=contract_constraints,
        contract_done=contract_done,
        authority=action.authority,
        boundaries=boundaries,
        applicable_rules=rules,
        relevant_learnings=learnings,
        skills=skills,
        skill_ids=[s.id for s in skills],
        capability_requirements=capability_requirements or [],
        environment_capabilities=env_caps,
        project_context_excerpt=project_excerpt,
        independent_assurance=independent_assurance,
    )


def assemble_assurance_context(root: Path, action_id: str) -> ExecutionContext:
    """Fresh ExecutionContext for independent Assurance review."""
    return assemble_execution_context(
        root,
        action_id,
        independent_assurance=True,
        capability_requirements=["review", "assurance"],
    )
