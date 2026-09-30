# Gates

Gates are mechanical brakes. **Non-zero exit = STOP.**

They do not replace judgment; they prevent pretending success when structure or proof is missing.

`--json` on `verify` and on every `gate` subcommand prints the same pass or fail as text mode, as a versioned document on stdout. See [JSON output](JSON-output.md).

## Gate catalog

| Command | Stops when |
| --- | --- |
| `retornatus gate contract <C-id>` | No active Contract, empty WHAT, or no DONE criteria |
| `retornatus gate skill-research <S-id>` | RESEARCH lacks sources / PROCEDURE blank |
| `retornatus gate evidence <C-id>` | No Evidence artifacts for the Change |
| `retornatus gate assurance <C-id>` | Assurance is not `SATISFIED` |
| `retornatus gate policy <A-id>` | Policy is `DENY` or `REQUIRE_HUMAN` |
| `retornatus gate budget <A-id>` | Action `attempt_count` reached `max_attempts` |
| `retornatus gate suppressions` | Added diff lines introduce a suppression or skip marker |
| `retornatus gate scope <C-id>` | The diff leaves Task resources, hits a denied path, or touches a sensitive path without a satisfied review/security claim |
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

If executed Evidence recorded a git commit and HEAD has moved, `verify` prints `WARN … stale snapshot; not a failure`. That warning does not change the verdict, unless required checks are configured (below). Freshness that uses `subject_state` of the form `commit:<sha>` (`--git-state`) can still mark Evidence stale and fail the claim.

Uncommitted or untracked edits to a claim subject path are visible to `verify`. Execution-type claims fail (the evidence is stale). Narrative claims warn. Override with:

```toml
[assurance]
uncommitted_changes = "fail"  # or "warn"
```

## Required checks

The agent chooses the command for `evidence run`, so `evidence run -- true` would otherwise be a passing test. The owner names the commands that count:

```toml
[assurance]
required_checks = [
  { name = "tests", run = ["pytest", "-q"] },
  { name = "lint", run = ["ruff", "check", "src"], types = ["lint_result"] },
]
```

`types` (alias `claim_types`) is optional. Empty means the argv may satisfy any execution type (`test_result`, `security_test`, `build_result`, `lint_result`). For those claims, `verify` then requires:

- provenance `executed` and exit code 0
- `command` exactly equal to one applicable check’s `run`
- recorded `git_commit` equal to current HEAD
- a clean worktree at execution time, and no uncommitted source changes now

Evidence files Retornatus just wrote under `.retornatus/changes/` do not, by themselves, count as a dirty tree. Any other uncommitted path does. `allow_self_reported` does not bypass a configured check.

```bash
retornatus checks run -c C-0001
retornatus verify C-0001 --run-checks
```

Both execute the declared argv through the same capture path as `evidence run` and record the Evidence.

## Suppression gate

```bash
retornatus gate suppressions
retornatus gate suppressions --staged
retornatus gate suppressions --base main
```

Added lines (`+`, not file headers) are scanned for markers such as `noqa`, `type: ignore`, `pragma: no cover`, `pytest.mark.skip`, `pytest.mark.xfail`, `unittest.skip`, `eslint-disable`, `@ts-ignore`, `@ts-expect-error`, `.only(`, `it.skip`, `describe.skip`, `pylint: disable`, and `--no-verify`.

Markdown (`.md`, `.markdown`, `.mdx`, `.mdc`) skips a match that sits inside a fenced code block or an inline code span. Naming `` `--no-verify` `` in a sentence is documentation of the marker, not a suppression added to executable code. The same marker outside a code span still fails the gate. `allow_paths` and `allow_patterns` still apply to every file.

```toml
[governance.suppressions]
extra_patterns = ["\\bHACK\\b"]
allow_patterns = ["type:\\s*ignore\\[override\\]"]
allow_paths = ["vendor/**"]
```

`allow_patterns` skip a whole added line. `allow_paths` skip a file. With no flag, the scan is `git diff HEAD` (staged and unstaged). `--staged` is the index. `--base` is `base...HEAD`.

## Scope gate

```bash
retornatus gate scope C-0001 --base main
retornatus gate scope C-0001            # staged + unstaged + untracked
retornatus gate scope C-0001 --staged
```

Changed paths must sit in the union of the change’s `Task.resources` and `.retornatus/**`. A resource is an exact path, a directory prefix when it ends with `/`, or a glob when it contains `*`, `?`, or `[`.

These globs always fail (override with `[governance.scope] denied_globs`):

`**/.env`, `**/.env.*`, `**/secrets/**`, `**/*.pem`, `**/*.key`

Sensitive paths (infra, auth, migrations, CI workflows — override with `sensitive_globs`) fail unless the change has a **satisfied** `review_result` or `security_test` claim backed by evidence of that type.

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
