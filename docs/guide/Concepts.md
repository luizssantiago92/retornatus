# Concepts

Short definitions of the domain objects you will see in CLI output and under `.retornatus/`. Full vocabulary: [Glossary](Glossary.md) · PRD §§9–41.

## Change

A durable unit of governed work. Owns Situation, Contract versions, Actions, Findings, Questions, Evidence.

Id shape: `C-0001`.

## Demand

The statement of intent that opens a Change (`demand_statement`, kind).

## Situation

Enough understanding to activate a Contract. Produced/elicited before formalization; may include repo signals and focused questions.

## Contract

Authoritative WHAT + constraints + DONE. Immutable once active; material change → new version (`change reopen`).

## Action

Bounded work with objective, success conditions, Authority, optional Tasks. Origin may be Contract or Question.

Id: `C-0001/A-001`.

## Task

Optional decomposition inside an Action. Lifecycle: PENDING → ACTIVE → COMPLETED | FAILED (with reopen). **READY / BLOCKED** are derived, not stored as truth.

## Skill

On-demand specialization artifact (`SKILL.md` with RESEARCH + PROCEDURE). Created for a need, gated before activation, exportable to native host skills.

## Evidence

Attributable observation (type, subject, source, producer, optional `subject_state`). Should SUPPORT a Claim for Assurance.

## Claim

A statement that must be established (often derived from Contract DONE). Evidence binds via SUPPORTS.

## Assurance

Evaluation of Claims against Evidence → `SATISFIED` | `NOT_SATISFIED` | `INCONCLUSIVE`.

## Finding / Question / Resolution

Discovery path when execution surfaces a relevant observation. Questions are grounded in Findings; Resolution establishes outcome (with Evidence when verifiable).

## Rule / Learning / Decision

- **Learning** — validated experience (informs)
- **Rule Candidate** — proposed constraint (not yet authoritative)
- **Decision** — Human boundary artifact required to activate a Rule
- **Rule** — active constraint; may be projected into host bridges

## Policy

Evaluation of a governed effect → `ALLOW` | `DENY` | `REQUIRE_HUMAN` (Rules + Authority + Boundaries).

## Authority / Boundaries

Authority categories constrain who may act (DELEGATED, HUMAN, RULED, …). Boundaries describe scope (often advisory isolation projections for the host).

## Status / Runtime / Memory

- **Status** — derived projection (`status`, `loop next`)
- **Runtime** — disposable operational data (safe to clear)
- **Memory** — durable Learnings and engineering continuity (not Evidence, not Status)
