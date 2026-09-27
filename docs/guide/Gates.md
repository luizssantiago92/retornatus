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
| `retornatus gate budget <A-id>` | Action `attempt_count` reached `max_attempts` |
| `retornatus verify <C-id>` | Same family as assurance over Contract DONE Claims |

Related:

```bash
retornatus policy check --action <A-id>
retornatus policy check --effect "…"
retornatus run <A-id> --strict-policy
retornatus action budget <A-id> --max 5
retornatus receipt keygen            # public key in-repo; private key outside it
retornatus verify <C-id> --receipt   # Ed25519 receipt (needs the private key)
retornatus receipt verify path/to/receipt.json   # public key only
```

## Assurance verdicts

| Verdict | Meaning |
| --- | --- |
| `SATISFIED` | Each required Claim has bound, fresh, type-appropriate Evidence. Execution types must be `executed` with exit code 0 |
| `NOT_SATISFIED` | Evidence exists but is wrong, failing, stale, or only self-reported for an execution type |
| `INCONCLUSIVE` | Required Evidence missing or unbound |

Claim results may also say `UNVERIFIED`: a `test_result`, `security_test`, `build_result`, or `lint_result` was self-reported (`evidence add`) instead of produced by `evidence run`. That claim does not yield overall `SATISFIED` (exit 0).

`verify` prints one line per Evidence (`provenance=… status=…`) before the JSON. Narrative types stay acceptable and are labeled `status=self-reported`.

Migration opt-out: `verify --allow-self-reported`, or in `.retornatus/config.toml`:

```toml
[assurance]
allow_self_reported = true
```

If executed Evidence recorded a git commit and HEAD has moved, `verify` prints `WARN … stale snapshot; not a failure`. That warning does not change the verdict. Freshness that uses `subject_state` of the form `commit:<sha>` (`--git-state`) can still mark Evidence stale and fail the claim.

Subject matching is exact after strip, case-fold, and trailing-slash normalization (`/Health/` matches `/health`). A shorter evidence subject is not treated as contained in the claim (`/` does not match `/health`). A longer evidence path may end with the claim's path token (`docs/health.md` matches claim `/health.md`); the reverse does not.

> Agent conclusion ≠ Evidence. A green test suite is evidence of tests — not automatic proof of every Claim unless bound correctly and actually executed by the harness.

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
