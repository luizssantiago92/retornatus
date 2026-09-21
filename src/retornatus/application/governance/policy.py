"""Policy evaluation against Rules, Authority, Boundaries (PRD §35 / M10)."""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from retornatus.domain.base import DomainModel
from retornatus.domain.enums import AuthorityCategory
from retornatus.domain.models import Authority, Boundaries, Boundary, Rule


class PolicyVerdict(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_HUMAN = "REQUIRE_HUMAN"


class PolicyDecision(DomainModel):
    verdict: PolicyVerdict
    rationale: str = Field(min_length=1)
    matched_rule_ids: list[str] = Field(default_factory=list)


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
                )

    if authority.category == AuthorityCategory.HUMAN:
        return PolicyDecision(
            verdict=PolicyVerdict.REQUIRE_HUMAN,
            rationale="Authority requires human judgment",
            matched_rule_ids=matched,
        )

    if matched and authority.category == AuthorityCategory.RULED:
        return PolicyDecision(
            verdict=PolicyVerdict.ALLOW,
            rationale="Allowed under applicable rules",
            matched_rule_ids=matched,
        )

    return PolicyDecision(
        verdict=PolicyVerdict.ALLOW,
        rationale="No denying rule matched; delegated authority",
        matched_rule_ids=matched,
    )
