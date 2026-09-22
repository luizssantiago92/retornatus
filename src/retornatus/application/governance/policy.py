"""Policy evaluation against Rules, Authority, Boundaries (PRD §35 / M10)."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import Field

from retornatus.domain.base import DomainModel
from retornatus.domain.enums import AuthorityCategory
from retornatus.domain.models import Authority, Boundaries, Rule
from retornatus.infrastructure.persistence.repository import FileRepository


class PolicyVerdict(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_HUMAN = "REQUIRE_HUMAN"


class PolicyDecision(DomainModel):
    verdict: PolicyVerdict
    rationale: str = Field(min_length=1)
    matched_rule_ids: list[str] = Field(default_factory=list)
    effect: str | None = None


def evaluate_policy(
    *,
    effect: str,
    rules: list[Rule],
    authority: Authority,
    boundaries: Boundaries | None = None,
) -> PolicyDecision:
    """Evaluate a proposed governed effect."""
    boundaries = boundaries or Boundaries()
    effect_l = effect.lower()
    matched: list[str] = []

    for boundary in boundaries.items:
        if boundary.realization.value == "ENFORCED" and boundary.name.lower() in effect_l:
            return PolicyDecision(
                verdict=PolicyVerdict.DENY,
                rationale=f"Enforced boundary blocks effect: {boundary.name}",
                effect=effect,
            )

    for rule in rules:
        if not rule.active:
            continue
        if rule.applicability.lower() in effect_l or effect_l in rule.statement.lower():
            matched.append(rule.id)
            # Deny-style rules: statement starting with "must not" / "do not"
            stmt = rule.statement.lower()
            if stmt.startswith("must not") or stmt.startswith("do not"):
                return PolicyDecision(
                    verdict=PolicyVerdict.DENY,
                    rationale=f"Denied by rule {rule.id}",
                    matched_rule_ids=matched,
                    effect=effect,
                )

    if authority.category == AuthorityCategory.HUMAN:
        return PolicyDecision(
            verdict=PolicyVerdict.REQUIRE_HUMAN,
            rationale="Authority requires human judgment",
            matched_rule_ids=matched,
            effect=effect,
        )

    if matched and authority.category == AuthorityCategory.RULED:
        return PolicyDecision(
            verdict=PolicyVerdict.ALLOW,
            rationale="Allowed under applicable rules",
            matched_rule_ids=matched,
            effect=effect,
        )

    return PolicyDecision(
        verdict=PolicyVerdict.ALLOW,
        rationale="No denying rule matched; delegated authority",
        matched_rule_ids=matched,
        effect=effect,
    )


def evaluate_action_policy(root: Path, action_id: str) -> PolicyDecision:
    """
    Evaluate Policy for an Action's objective using active Rules + Action Authority.

    Includes isolation Boundaries so ENFORCED host constraints can DENY.
    """
    from retornatus.application.execution.isolation import (
        enrich_capabilities,
        isolation_boundaries,
    )
    from retornatus.infrastructure.environment.adapters import detect_environment

    repo = FileRepository(root)
    action, _ = repo.load_action(action_id)
    _, caps = detect_environment(root)
    caps = enrich_capabilities(root, caps)
    boundaries = Boundaries(items=list(isolation_boundaries(root, caps)))
    return evaluate_policy(
        effect=action.objective,
        rules=repo.list_rules(),
        authority=action.authority,
        boundaries=boundaries,
    )
