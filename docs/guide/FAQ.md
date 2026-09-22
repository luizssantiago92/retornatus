# FAQ

## Is Retornatus an agent framework?

No. It is a **governance harness**. The host runs the model; Retornatus structures obligations, proof, and memory.

## Do I need a cloud account?

No. V1 is local and repository-native. No mandatory SaaS runtime or remote database.

## Must every Change use Skills and Tasks?

No. Ceremony scales with complexity. Use `skill need` and only add Tasks when decomposition helps.

## Why did `verify` fail when tests passed?

Assurance needs Evidence **bound to Claims** (`--claim`). Unbound `test_result` artifacts do not automatically satisfy DONE Claims.

## Can I delete the SQLite database?

Yes. Run `retornatus wake` to rebuild. Do **not** delete canonical JSON/Markdown under `.retornatus/changes/` unless you intend to discard history.

## How is this different from Spec Guardrails?

Related prior work in the same ecosystem, **separate product**. Spec Guardrails emphasizes spec-driven phases and npm packaging; Retornatus emphasizes Change/Contract/Skill/Evidence continuity as a Python harness. Behavioral overlap exists; command 1:1 parity is **not** a goal. See [Non-goals](Non-goals.md).

## What does native-first mean for sandboxes?

Isolation Boundaries are advisory projections toward host worktrees/sandboxes. Retornatus does not enforce OS-level sandboxes in V1.

## How do Rules reach Cursor / Claude / Codex?

On `rule activate` and `integrate` / bridge refresh, active Rules are upserted into host bridge files. Canonical Rules stay in `.retornatus/`.

## Who can activate a Rule?

Only a recorded Human Decision of kind `APPROVE_RULE_ACTIVATION` for that Rule id (with matching confirmation token).

## Where is the product contract?

[`prd/PRD.md`](../../prd/PRD.md). Guides in this folder explain; the PRD decides.
