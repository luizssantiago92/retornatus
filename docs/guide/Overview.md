# Overview

Retornatus is a **repo-native governance harness** for AI-assisted software development.

It keeps agents inside a repeatable contract: understand the demand, activate obligations, execute under authority, and close with attributable proof — all durable under `.retornatus/`, not trapped in chat.

It is **not**:

- an IDE or agent marketplace
- an LLM runtime or multi-tenant orchestrator
- a clone of another kit’s CLI surface

Your coding environment **executes**. Retornatus **governs and records**.

---

## The problem it solves

| Failure mode | What Retornatus does |
| --- | --- |
| Agent jumps to code | Situation elicitation + Contract before build |
| “Done” is a chat claim | Assurance from Claim-bound Evidence |
| Session amnesia | Files + `wake` continuity |
| One-size ceremony | Tasks and Skills only when complexity earns them |
| Silent rule invention | Rule Candidates need a Human Decision |

---

## The core loop

```text
Demand
  → Situation
  → Contract          (WHAT + constraints + DONE)
  → Action            (+ Tasks when needed)
  → Skill?            (research current sources)
  → Execution         (host agent)
  → Evidence
  → Assurance         (SATISFIED | NOT_SATISFIED | INCONCLUSIVE)
  → Learning / Skill evolution
```

If work is blocked by discovery:

```text
Finding → Question → Action → Evidence → Resolution
```

Status commands (`status`, `loop next`) are **projections**. If they disagree with files, the files win.

---

## How much ceremony?

| Work | Typical path |
| --- | --- |
| Trivial fix | Short Contract, skip Skill (`skill need`), light Evidence |
| Normal feature | Full Change loop + gates |
| High-risk / specialized | Skill research gate + optional independent Assurance + Policy |

Complexity must be earned — see [Concepts](Concepts.md) and the PRD philosophy (§2).

---

## How you interact

1. **Chat** — ask the agent to follow the Retornatus hub skill (installed by `integrate`).
2. **CLI** — intentions such as `change create`, `gate contract`, `verify` (source of truth for gates).
3. **Files** — inspect `.retornatus/changes/…` when you need the durable record.

You approve product intent and Human Decisions (Rules). The agent implements. Git push / merge stay yours.

---

## Next steps

- [Quick start](Quick-start.md) — install and first Change
- [How it works](How-it-works.md) — narrative walkthrough
- [Gates](Gates.md) — what actually stops incomplete work
- [Non-goals](Non-goals.md) — what V1 deliberately does not claim
