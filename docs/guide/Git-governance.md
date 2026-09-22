# Git governance

Structural gates enforce artifact quality under `.retornatus/`. **Git tiers** enforce what leaves the machine.

Retornatus adopts the same blast-radius idea as Spec Guardrails’ Human-in-the-loop / git-handoff — adapted to Contracts and this repo’s ownership model.

> Approving a Change or Contract authorizes **local** work — not share, merge, or publish.

## Tiers

| Tier | What the agent may do | What needs the human |
| --- | --- | --- |
| **0 — Local** | Implement, test, commit locally (code + `.retornatus/` memory) | — |
| **1 — Share** | Nothing automatic | Explicit ask: `git push`, open/update PR |
| **2 — External** | **Never** (owner-only in this project) | Merge, deploy, force-push, production data, **PyPI publish**, **release tags that publish** |

### Owner hard rule

In this repository (and by default for Retornatus-governed work here):

- **Merge** and **publish** stay with the human owner.
- Agents prepare work, local commits, and (when asked) PRs — then stop.
- Do not create/push `v*` tags that trigger Publish workflows; do not run `uv publish` / workflow_dispatch publish for the owner.

## What to commit (Tier 0)

**Usually yes**

- Application / package source and tests
- Docs that describe shipped behavior
- Canonical `.retornatus/` artifacts for the Change (contracts, evidence, learnings, skills, decisions)

**Usually no**

- Secrets (`.env`, tokens, credentials)
- Derived `.retornatus/index/` and `.retornatus/runtime/` (see root `.gitignore`)
- Accidental IDE noise

## Commit messages

- English, concise, focused on **why**
- Prefer Conventional Commits style when natural (`feat:`, `fix:`, `docs:`, `test:`)
- Do not bypass hooks (`--no-verify`) unless the owner explicitly requests it

## Handoff checklist

Before ending a session or asking for review:

1. `git status` is understood (clean or intentional leftovers)
2. Local commits exist for finished units (Tier 0)
3. No Tier 1/2 actions unless the owner asked
4. One concrete next human step (review PR / merge / tag to publish)

## Cursor bridge

Project rule: [`.cursor/rules/git-governance.mdc`](../../.cursor/rules/git-governance.mdc) (`alwaysApply: true`).

## Related

- [Governance](Governance.md) — Rules, Policy, Human Decisions
- [Non-goals](Non-goals.md) — what V1 does not claim
- Spec Guardrails: [Human-in-the-loop](https://github.com/luizssantiago92/spec-guardrails#human-in-the-loop-and-git-governance) (predecessor)
