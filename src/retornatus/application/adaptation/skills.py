"""Skill creation, resolution, evolution, and native export (PRD §39–§40)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from retornatus.domain.enums import AuthorityCategory, SkillSource, SkillStatus
from retornatus.domain.ids import format_project_id
from retornatus.domain.models import Skill
from retornatus.domain.relations import Relation, RelationType
from retornatus.infrastructure.persistence.repository import FileRepository


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:48] or "skill"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_skill_body(
    *,
    title: str,
    specialization: str,
    change_id: str | None,
    action_id: str | None,
    research_seed: str | None = None,
) -> str:
    """
    Canonical Skill body scaffold.

    Retornatus owns structure. The agent (with web tools) fills RESEARCH and
    PROCEDURE with current knowledge — avoiding stale preloaded skill packs.
    """
    seed = research_seed or (
        "Use current web documentation and official sources. Prefer primary docs "
        "over blog summaries. Record sources with URLs and access dates."
    )
    links = []
    if change_id:
        links.append(f"- Change: `{change_id}`")
    if action_id:
        links.append(f"- Action: `{action_id}`")
    related = "\n".join(links) if links else "- (none yet)"

    return f"""# {title}

## Specialization

{specialization}

## Related work

{related}

## RESEARCH (agent must complete before ACTIVE)

> Progressive specialization: research *now* for this need. Do not rely on stale
> global skill packs.

### Research brief

{seed}

### Sources

| Source | URL | Accessed | Notes |
| --- | --- | --- | --- |
| | | | |

### Current best practices (fill after research)

-

### Pitfalls / anti-patterns

-

## PROCEDURE (stable snapshot for Execution)

Step-by-step instructions the agent (and subagents) must follow:

1.
2.
3.

## Checks before claiming done

- [ ]
- [ ]

## Evolution log

| Version | Date | Change |
| --- | --- | --- |
| 1 | {_utc_now().date().isoformat()} | Created as DRAFT specialization skill |
"""


class SkillService:
    """Adaptation surface for Skills — create, activate, evolve, export."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.repo = FileRepository(self.root)

    def next_skill_id(self) -> str:
        nums: list[int] = []
        for skill in self.repo.list_skills():
            try:
                nums.append(int(skill.id.split("-", 1)[1]))
            except (IndexError, ValueError):
                continue
        return format_project_id("S", max(nums, default=0) + 1)

    def create_for_specialization(
        self,
        *,
        specialization: str,
        title: str | None = None,
        description: str | None = None,
        change_id: str | None = None,
        action_id: str | None = None,
        research_seed: str | None = None,
        activate: bool = False,
    ) -> tuple[Skill, str]:
        """
        Create one specialization Skill for the current need.

        Physical contract: one Skill tailored to the specialization (not a
        library of preloaded generic skills). Agent researches and fills body.

        Skills always start as DRAFT. Activation requires research gate
        (or governed bypass) via ``activate()``.
        """
        if activate:
            # Soft: still create DRAFT — callers must activate explicitly
            activate = False
        skill_id = self.next_skill_id()
        name = _slugify(title or specialization)
        resolved_title = title or specialization
        resolved_description = description or (
            f"Use when working on: {specialization}"
        )
        relations: list[Relation] = []
        if change_id:
            relations.append(
                Relation(type=RelationType.APPLIES_TO, target_id=change_id)
            )
        if action_id:
            relations.append(
                Relation(type=RelationType.APPLIES_TO, target_id=action_id)
            )

        skill = Skill(
            id=skill_id,
            name=name,
            title=resolved_title,
            description=resolved_description,
            specialization=specialization,
            status=SkillStatus.DRAFT,
            source=SkillSource.RESEARCHED,
            change_id=change_id,
            action_id=action_id,
            relations=relations,
        )
        body = build_skill_body(
            title=resolved_title,
            specialization=specialization,
            change_id=change_id,
            action_id=action_id,
            research_seed=research_seed,
        )
        self.repo.save_skill(skill, body)
        return skill, body

    def activate(
        self,
        skill_id: str,
        *,
        force: bool = False,
        bypass_reason: str | None = None,
        bypass_authority: AuthorityCategory | None = None,
    ) -> Skill:
        """
        Mark Skill ACTIVE.

        Research gate must pass unless a governed bypass is recorded
        (force + reason + authority).
        """
        from retornatus.application.governance.bypass import BypassError, BypassService
        from retornatus.application.governance.gates import gate_skill_research
        from retornatus.domain.models import Authority

        skill, body, rev = self.repo.load_skill(skill_id)
        if skill.status is SkillStatus.ACTIVE:
            return skill

        gate = gate_skill_research(self.root, skill_id)
        if not gate.passed:
            if not force:
                raise ValueError(
                    "Skill research gate failed: "
                    + "; ".join(gate.messages)
                    + " — fill RESEARCH or use force with reason"
                )
            if not bypass_reason or not bypass_reason.strip():
                raise BypassError(
                    "Governed bypass of skill-research requires --reason"
                )
            BypassService(self.root).record_bypass(
                gate="skill-research",
                entity_id=skill_id,
                reason=bypass_reason,
                authority=Authority(
                    category=bypass_authority or AuthorityCategory.HUMAN,
                    rationale=bypass_reason,
                ),
            )

        updated = skill.model_copy(
            update={"status": SkillStatus.ACTIVE, "updated_at": _utc_now()}
        )
        self.repo.save_skill(updated, body, expected=rev)
        return updated

    def evolve(
        self,
        skill_id: str,
        *,
        note: str,
        from_learning_id: str | None = None,
        body_append: str | None = None,
    ) -> Skill:
        """Skill Evolution — update procedure from validated experience (PRD §40)."""
        skill, body, rev = self.repo.load_skill(skill_id)
        new_version = skill.version + 1
        relations = list(skill.relations)
        if from_learning_id:
            relations.append(
                Relation(type=RelationType.DERIVED_FROM, target_id=from_learning_id)
            )
        stamp = _utc_now().date().isoformat()
        evolution_line = f"| {new_version} | {stamp} | {note} |\n"
        if "| Version | Date | Change |" in body:
            # append after header row block — simple: append section
            new_body = body.rstrip() + "\n" + evolution_line
        else:
            new_body = body.rstrip() + f"\n\n## Evolution log\n\n{evolution_line}"
        if body_append:
            new_body = new_body.rstrip() + "\n\n## Update\n\n" + body_append.strip() + "\n"

        updated = skill.model_copy(
            update={
                "version": new_version,
                "updated_at": _utc_now(),
                "relations": relations,
            }
        )
        self.repo.save_skill(updated, new_body, expected=rev)
        return updated

    def resolve_for_action(self, action_id: str) -> list[Skill]:
        """Skills linked to an Action or its Change — for ExecutionContext."""
        matched: list[Skill] = []
        for skill in self.repo.list_skills():
            if skill.status is SkillStatus.SUPERSEDED:
                continue
            if skill.action_id == action_id:
                matched.append(skill)
                continue
            if any(
                r.target_id == action_id and r.type is RelationType.APPLIES_TO
                for r in skill.relations
            ):
                matched.append(skill)
        return matched

    def resolve_relevant(self, query: str, *, limit: int = 5) -> list[Skill]:
        q = query.lower()
        scored: list[tuple[int, Skill]] = []
        for skill in self.repo.list_skills():
            if skill.status is SkillStatus.SUPERSEDED:
                continue
            hay = " ".join(
                [skill.title, skill.description, skill.specialization, skill.name]
            ).lower()
            score = hay.count(q) if q else 0
            if q and q in hay:
                scored.append((score + 1, skill))
            elif not q and skill.status is SkillStatus.ACTIVE:
                scored.append((1, skill))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [s for _, s in scored[:limit]]

    def export_native(self, skill_id: str, *, target: str = "cursor") -> Path:
        """
        Project Skill into environment-native skill surface (PRD native-first).

        Does not invent a proprietary DSL — writes Agent-Skills-style SKILL.md.
        """
        skill, body, _ = self.repo.load_skill(skill_id)
        if target != "cursor":
            raise ValueError(f"Unsupported native export target: {target}")
        dest_dir = self.root / ".cursor" / "skills" / skill.name
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "SKILL.md"
        # Cursor-friendly front matter + body without Retornatus HTML meta
        front = (
            f"---\n"
            f"name: {skill.name}\n"
            f"description: {skill.description}\n"
            f"---\n\n"
        )
        dest.write_text(front + body, encoding="utf-8")
        return dest
