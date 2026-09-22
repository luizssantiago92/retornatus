# Credits, Lineage & Prior Art

Ideas are credited by **influence**, not by superficial similarity. Retornatus does not claim novelty for established software-engineering patterns; its design contribution lies in how these ideas are separated, constrained, and composed into its governance model.

This document records **provenance**, not a bibliography of every related tool.

```text
Open-source prior art
        ↓
Spec Guardrails
        ↓
real implementation + dogfooding
        ↓
lessons / limitations / proven guarantees
        ↓
Retornatus-specific research & design
        ↓
Retornatus
```

---

## A. Direct predecessor — Spec Guardrails

**[Spec Guardrails](https://github.com/luizssantiago92/spec-guardrails)** (MIT) is the **direct predecessor** of Retornatus.

Retornatus is a **separate successor architecture** informed by lessons learned while building and dogfooding Spec Guardrails. It is **not** a fork, rename, or line-by-line rewrite of Spec Guardrails.

```text
Spec Guardrails
      ↓
experience
      ↓
failure analysis
      ↓
preserve proven guarantees
      ↓
rethink mechanisms
      ↓
Retornatus
```

### What Spec Guardrails demonstrated in practice

Dogfooding Spec Guardrails showed the practical value of:

| Proven concern | How Spec Guardrails exercised it |
| --- | --- |
| Repo-native governance | Durable project state under `.specs/` |
| Planning before implementation | Spec → tasks → execute → verify phases |
| Gates / brakes | Mechanical STOP checks (exit codes) |
| Tasks and controlled parallelism | Task graphs, waves, loop patterns |
| Evidence before “done” | Verification / proof expectations |
| Persistent project memory | Feature archives and memory index |
| Human checkpoints | Approvals at meaningful boundaries |
| Restart continuity | State that survives chat handoffs |
| Environment / agent integration | Cursor, Claude, Copilot, Codex adapters |

### What Retornatus aims to preserve

Useful **guarantees**, not Spec Guardrails’ npm packaging, skill tree, or command surface:

- governance before opportunistic coding
- non-zero gates as brakes
- attributable proof rather than chat self-report
- memory that outlives a session
- human authority for consequential constraints
- environment awareness without replacing the host

### Why a separate product

The Retornatus PRD treats Spec Guardrails as **archaeology first** (inspect implementation, not only docs), then redesigns mechanisms under **native-first** and **complexity must be earned** ([PRD §66](../prd/PRD.md)).

Retornatus therefore:

- uses a structured Python domain model and `.retornatus/` layout
- separates Demand / Situation / Contract / Action (and Finding / Question / Resolution)
- separates Evidence from Assurance
- prefers host-native isolation and skills over rebuilding them
- does **not** claim 1:1 Spec Guardrails command replacement

### Spec Guardrails’ own lineage (transitive — do not duplicate)

Spec Guardrails itself incorporates and credits prior work in spec-driven development, task graphs, loop engineering, agent skills, and harness engineering. Those **transitive** influences are documented in Spec Guardrails’ own lineage and are **not** repeated here as direct Retornatus influences unless Retornatus independently revisited the original source.

Primary reference:

- [Spec Guardrails — Credits and lineage](https://github.com/luizssantiago92/spec-guardrails/blob/main/docs/guide/credits.md)

Upstream names recorded there (for navigation only — **not** Retornatus direct influences):  
`tlc-spec-driven`, `addyosmani/agent-skills`, `graph-engineering`, `loop-engineering`, Addy Osmani’s Loop Engineering essay, `awesome-harness-engineering`, `loopgate_harness`, `obra/superpowers`, plus cited-not-vendored adjacent tools (e.g. DeepCode, RepoGraph, Graphify, RTK, NVIDIA SkillSpector).

**Audit note:** A search of this repository’s design artifacts (PRD, docs, implementation notes, commit messages) found **no evidence** that Retornatus independently re-studied those upstreams in a way that added influence beyond what arrived through Spec Guardrails. They therefore remain **transitive**.

**Code:** Retornatus does not vendor Spec Guardrails’ Node package, Python gate scripts, or skill trees. Relationship is conceptual / experiential. Spec Guardrails license: **MIT**.

---

## B. Direct Retornatus research

Include only sources with justifiable evidence of study **during Retornatus design**, beyond Spec Guardrails archaeology.

### B.1 Host Environment capability surfaces

| Source | What was studied | What influenced Retornatus | What Retornatus did differently |
| --- | --- | --- | --- |
| [Cursor](https://cursor.com) (rules / skills layout) | Native rules (`.cursor/rules`), skills progressive disclosure | Cursor adapter, hub skill install, Rule projection into `.mdc` | Govern via `.retornatus/`; bridges are projections only |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (`CLAUDE.md` / `.claude`) | Project instruction surfaces | Claude Code adapter + bridge markers | No Claude-specific domain policy in Core |
| [OpenAI Codex](https://github.com/openai/codex) / `AGENTS.md` patterns | Agent instruction files, isolation hints | Codex adapter + `AGENTS.md` bridges; advisory isolation Boundaries | Does not spawn Codex sandboxes; records host execution observations |

**Nature:** environment integration research. **No code vendored** from these products into Retornatus.

### B.2 Implementation libraries (runtime dependencies)

These are engineering dependencies, not governance prior art:

| Package | License (as published) | Role in Retornatus |
| --- | --- | --- |
| [Pydantic](https://github.com/pydantic/pydantic) | MIT | Structured domain models / validation |
| [Typer](https://github.com/fastapi/typer) | MIT | Intention-oriented CLI |
| [tomli-w](https://github.com/hukkin/tomli-w) | MIT | TOML writing for project config |
| Python [sqlite3](https://docs.python.org/3/library/sqlite3.html) + FTS5 | PSF | Derived disposable index |

**No modified copies** of these libraries are vendored in-tree; they are normal package dependencies (`pyproject.toml`).

### B.3 No additional direct conceptual upstreams recorded

As of this audit, **no other external repositories** are classified as direct Retornatus conceptual influences. If future work independently revisits a Spec Guardrails upstream (or a new source) and that study changes Retornatus design, document it here in the same PR with: source, what was studied, what changed, license, and whether any code was adapted.

---

## C. Evaluated alternatives (studied / rejected for V1)

These are **design decisions**, not claims that Retornatus “is based on” the rejected approach. Primary evidence: [PRD §65 Explicit V1 Non-Goals](../prd/PRD.md) and native-first philosophy (§2.2).

| Evaluated direction | Question | Decision | Result in Retornatus V1 |
| --- | --- | --- | --- |
| Graph database / vector store for Memory | Do we need a graph/vector DB? | **No** | Canonical files + relations + derived SQLite/FTS |
| Mandatory Loop Engine | Is a durable Loop engine required? | **No** | `loop next` as **projection** over ready work |
| Proprietary sandbox / worktree orchestrator | Rebuild host isolation? | **No** | Advisory Boundaries → native host isolation |
| Agent Pool / permanent specialist agents | Encode personas in the domain? | **No** | Specialization via Assignment + Context + Skills |
| Automatic Rule graduation | May recurrence create authority? | **No** | Rule Candidate → Human Decision → Rule |
| Event store / distributed scheduler / SaaS control plane | Remote orchestration? | **No** | Local repository-native harness |
| Spec Guardrails command 1:1 clone | Drop-in CLI replacement? | **No** | Behavioral parity where useful; separate UX |

Where Spec Guardrails’ docs cite adjacent graph/harness tools as *referenced, not vendored*, Retornatus treats graph-memory approaches as a **class of alternative** rejected in the PRD — without listing those tools as Retornatus direct influences.

---

## D. Original Retornatus design

“Original” here means **decisions composed inside Retornatus’ architecture**, not invention of generic software-engineering ideas.

Retornatus introduces **within its own architecture** the following separations and compositions.

### Core work spine

```text
Demand → Situation → Contract → Action → Execution (host)
```

Distinctions enforced in the model:

| Separation | Intent |
| --- | --- |
| Demand ≠ Contract | Intent is not yet an obligation |
| Contract ≠ Action | Obligation is not the response |
| Action ≠ Task | Decomposition is optional |
| Task ≠ Execution | Planned work ≠ host run |

### Discovery spine

```text
Finding → Question → Action → Evidence → Assurance → Resolution
```

| Separation | Intent |
| --- | --- |
| Finding ≠ Question | Observation is not yet a problem frame |
| Question ≠ Resolution | Problems are not closed by assertion |
| Evidence ≠ Assurance | Observation ≠ verdict |
| Resolution is established, not claimed | Agent self-report is insufficient when proof is required |

### Adaptation spine

```text
Experience → Learning → Graduation → Rule Candidate → Human Authority → Active Rule
```

| Separation | Intent |
| --- | --- |
| Learning ≠ Skill | Informs vs teaches how |
| Skill ≠ Rule | Procedure vs constraint |
| Rule ≠ Policy | Standing constraint vs effect evaluation |

### Structural choices

| Choice | Retornatus modeling |
| --- | --- |
| Structured domain model | Validated entities (Pydantic) instead of implicit script/doc semantics alone |
| Native-first | Govern; do not duplicate host agent runtime / sandbox / subagents |
| Capability-oriented Environment | Core depends on capabilities; adapters speak environment |
| Context Assembly | Context assembled, not inherited; follows responsibility; sufficient, not comprehensive |
| Derived coordination | Readiness / parallelizable sets as projections — not mandatory canonical Wave/Loop engines |
| On-demand researched Skills | Create/research/activate one Skill when needed; evolve from Learning |
| Complexity discipline | A mechanism must save more complexity than it introduces; complexity earned by concrete failure |

Product contract: [`prd/PRD.md`](../prd/PRD.md). User-facing concepts: [docs/guide/Concepts.md](guide/Concepts.md).

---

## Licensing summary

| Artifact | License | Notes |
| --- | --- | --- |
| Retornatus (this repository) | MIT | [`LICENSE`](../LICENSE) |
| Spec Guardrails (predecessor) | MIT | Conceptual/experiential influence; **no code vendored** |
| Pydantic, Typer, tomli-w | MIT | Dependencies via packaging |
| Host products (Cursor / Claude Code / Codex) | Proprietary / host terms | Adapters write local bridge files only |

**Derived/vendored third-party source trees:** none identified in `src/` at audit time (no NOTICE files, no copied skill packs from Spec Guardrails or its upstreams).

---

## How to update this document

When adding an influence:

1. State whether it is **predecessor**, **direct**, **transitive**, or **evaluated-and-rejected**.
2. Cite evidence (PRD section, design note, or concrete adapter/code change).
3. Record license and whether any code was adapted.
4. Do **not** promote Spec Guardrails upstreams to “direct” without new independent study.

Keep the [README](../README.md) section short; keep detail here.
