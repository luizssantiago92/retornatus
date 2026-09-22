# Non-goals (V1)

Retornatus V1 is intentionally bounded. These are **not bugs** — they are product choices.

## Out of scope

| Non-goal | Rationale |
| --- | --- |
| Multi-provider live LLM integration tests as default CI | Environment owns execution; harness tests structure and gates |
| Enforced OS sandbox / worktree orchestration | Prefer native host isolation; Boundaries stay advisory |
| Drop-in 1:1 Spec Guardrails command replacement | Behavioral parity ≠ clone; avoids coupling to another product’s surface |
| Remote multi-tenant control plane | Local repository-native harness |
| Permanent agent personas / identity model | Specialization via Assignment + Context + Skills |
| Automatic authoritative Rules from recurrence | Human Decision required |

PRD §65 lists explicit V1 non-goals in full.

## What “done” means for V1

A developer can wake a repo, open a Change, activate a Contract, execute under the host, record Claim-bound Evidence, reach Assurance `SATISFIED`, preserve Learning, and recover via `wake` after interruption — without chat as canonical state.

See PRD §§69–70.

## Reopening a non-goal

Only when a **concrete failure mode** appears that existing mechanisms and the Environment cannot solve (PRD §71). Prefer gates that *prove* host behavior over rebuilding host capabilities inside Retornatus.
