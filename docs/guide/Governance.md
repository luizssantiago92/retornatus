# Governance

Governance in Retornatus is **local and explicit**: Authority, Boundaries, Rules, Policy, and Human Decisions.

## Authority

Actions carry Authority (e.g. DELEGATED for routine work, HUMAN when judgment is required). Policy uses Authority when evaluating effects.

## Boundaries

Describe operational scope (filesystem root, isolation hints). Many are **advisory** — the host realizes worktrees/sandboxes. Retornatus records and projects; it does not replace the host sandbox.

## Rules

```text
Learning → Rule Candidate (inactive)
        → Human Decision (APPROVE_RULE_ACTIVATION)
        → Active Rule
```

```bash
retornatus rule propose --statement "Do not commit secrets" --applicability "commit secrets"
retornatus decision record --kind APPROVE_RULE_ACTIVATION \
  --subject R-0001 --summary "Approve" --confirm R-0001
retornatus rule activate R-0001 --decision D-0001
```

Setting `authority=HUMAN` on a Rule object is **not** enough — activation requires a Decision artifact whose subject and confirmation match the Rule id.

Active Rules are projected into Environment bridges (Cursor / CLAUDE.md / AGENTS.md). Canonical truth remains under `.retornatus/`.

## Policy

```bash
retornatus policy check --effect "commit secrets to repo"
retornatus policy check --action C-0001/A-001
retornatus gate policy C-0001/A-001
retornatus run C-0001/A-001 --strict-policy
```

Verdicts: `ALLOW` · `DENY` · `REQUIRE_HUMAN`.

Deny-style Rules typically start with “Do not” / “Must not” and match via applicability.

## Bypass

Skipping a gate without a durable Bypass + authority is rejected. Example: Skill research bypass with `--force --reason`.

## Git blast radius

Structural gates are not enough — see **[Git governance](Git-governance.md)** for tiers:

| Tier | Meaning |
| --- | --- |
| **0 — Local** | Commits on the machine |
| **1 — Share** | Push / PR — only when the human asks |
| **2 — External** | Merge, deploy, **PyPI publish** — **owner-only** in this project |

Cursor bridge: `.cursor/rules/git-governance.mdc`.

## Design stance

> Learning informs; Rules constrain. Recurrence never creates authority automatically.

Details: PRD §§31–35, §48.
