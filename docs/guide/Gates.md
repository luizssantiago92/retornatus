# Gates

Gates are mechanical brakes. **Non-zero exit = STOP.**

They do not replace judgment; they prevent pretending success when structure or proof is missing.

## Gate catalog

| Command | Stops when |
| --- | --- |
| `retornatus gate contract <C-id>` | No active Contract, empty WHAT, or no DONE criteria |
| `retornatus gate skill-research <S-id>` | RESEARCH lacks sources / PROCEDURE blank |
| `retornatus gate evidence <C-id>` | No Evidence artifacts for the Change |
| `retornatus gate assurance <C-id>` | Assurance is not `SATISFIED` |
| `retornatus gate policy <A-id>` | Policy is `DENY` or `REQUIRE_HUMAN` |
| `retornatus verify <C-id>` | Same family as assurance over Contract DONE Claims |

Related:

```bash
retornatus policy check --action <A-id>
retornatus policy check --effect "…"
retornatus run <A-id> --strict-policy
```

## Assurance verdicts

| Verdict | Meaning |
| --- | --- |
| `SATISFIED` | Each required Claim has bound, fresh, type-appropriate Evidence |
| `NOT_SATISFIED` | Evidence exists but wrong claim/subject/type or stale |
| `INCONCLUSIVE` | Required Evidence missing or unbound |

> Agent conclusion ≠ Evidence. A green test suite is evidence of tests — not automatic proof of every Claim unless bound correctly.

## Process vs brakes

| | Process (hub skill) | Brakes (gates) |
| --- | --- | --- |
| Who checks | Agent follows the skill | CLI exit codes |
| Incomplete work | Agent *should* stop | Agent **cannot** claim success via gate |
| Best for | Learning the method | Teams that need proof between approvals |

## Governed bypass

Some gates can be skipped only as a recorded decision, e.g.:

```bash
retornatus skill activate S-0001 --force --reason "Emergency hotfix; research deferred"
```

Bypass without reason/authority is rejected. See [Governance](Governance.md).

## Guarantees (product level)

| Guarantee | Mechanism |
| --- | --- |
| Contract before build | `gate contract` + Situation sufficiency |
| Research before specialized execution | `gate skill-research` |
| Evidence before done | Claim-bound Evidence + `verify` |
| Continuity after crash | Canonical files + `wake` |
| No silent Rule authority | Human Decision required |
| Policy visibility | `gate policy` / `--strict-policy` |
