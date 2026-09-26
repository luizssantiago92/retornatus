# FAQ

## Is Retornatus an agent framework?

No. It is a **governance harness**. The host runs the model; Retornatus structures obligations, proof, and memory.

## Do I need a cloud account?

No. V1 is local and repository-native. No mandatory SaaS runtime or remote database.

## Must every Change use Skills and Tasks?

No. Ceremony scales with complexity. For freeform chat prompts, prefer `intake analyze` (propose Skill → human CREATE=yes) or explicit `skill create`. Use `skill need` as a signal only. Agents should **not** invent Skills without confirmation.

## Why did `verify` fail when tests passed?

Assurance needs Evidence **bound to Claims** (`--claim`). Unbound `test_result` artifacts do not automatically satisfy DONE Claims.

## Can I delete the SQLite database?

Yes. Run `retornatus wake` to rebuild. Do **not** delete canonical JSON/Markdown under `.retornatus/changes/` unless you intend to discard history.

## How is this different from Spec Guardrails?

**Spec Guardrails** is the **direct predecessor**. Retornatus is a **separate successor architecture** informed by building and dogfooding Spec Guardrails — not a fork or rename.

Spec Guardrails proved repo-native gates, memory, evidence, and human checkpoints in practice (npm / `.specs/` / skill-driven phases). Retornatus preserves those *guarantees* while rethinking *mechanisms*: structured Demand→Situation→Contract→Action, Evidence ≠ Assurance, Finding→Question→Resolution, native-first Python harness under `.retornatus/`.

Command 1:1 parity with Spec Guardrails is **not** a goal. Migration map: [From Spec Guardrails](From-spec-guardrails.md). Provenance: [Credits & lineage](../credits-and-lineage.md). Adjacent products: [Landscape](Landscape.md).

## What does native-first mean for sandboxes?

Isolation Boundaries are advisory projections toward host worktrees/sandboxes. Retornatus does not enforce OS-level sandboxes in V1.

## How do Rules reach Cursor / Claude / Codex?

On `rule activate` and `integrate` / bridge refresh, active Rules are upserted into host bridge files. Canonical Rules stay in `.retornatus/`.

## Who can activate a Rule?

Only a recorded Human Decision of kind `APPROVE_RULE_ACTIVATION` for that Rule id (with matching confirmation token).

## Where is the product contract?

[`prd/PRD.md`](../../prd/PRD.md). Guides in this folder explain; the PRD decides.
