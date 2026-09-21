# Retornatus

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uvx%20%2F%20uv%20tool-recommended-de5fe9.svg)](https://docs.astral.sh/uv/)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![version](https://img.shields.io/badge/version-0.6.0-informational.svg)](pyproject.toml)

**Repo-native governance harness for AI-assisted software development.**

More than a checklist — a **governance harness** (contracts, gates, on-demand skills, evidence, and memory) that lives inside your repository.

Agents are fast — and optimistic. They ship code, summarize what they *think* they did, and move on. Retornatus installs a **repeatable contract** into your repo: express a Demand, understand the Situation, activate a Contract, specialize with a researched Skill, execute under Authority and Boundaries, and close with attributable Evidence — all durable under `.retornatus/`, not trapped in chat scrollback.

You keep control: the agent proposes and implements; **gates** stop “done” without proof; Learning and Skill evolution improve the next return.

> **Govern the work. Bound the agent. Verify the outcome.**

| Without Retornatus | With Retornatus |
| --- | --- |
| Jumps to code and says “done” | Active Contract + DONE criteria first |
| “Done” is a chat claim | Assurance verdict from attributable Evidence |
| Each chat starts from zero | `.retornatus/` survives sessions and handoffs |
| Stale skill packs for every stack | **One specialization Skill**, researched *now* for this Change |
| Same ceremony for a typo and a payment flow | Tasks only when needed; `loop next` projects the next unit |
| Failures vanish when the tab closes | Finding → Question → Action leaves a trail |

**Python** · **0.6.x** · primary run via [`uv`](https://docs.astral.sh/uv/) (`uvx` / `uv tool install`)

**Docs:** [Product PRD](prd/PRD.md) · this README

[What it is](#what-it-is) · [Install](#1-install) · [Verify](#2-verify-readiness) · [First Change](#3-run-your-first-change) · [Checklist](#getting-started-checklist) · [Pillars](#four-pillars) · [How it works](#how-it-works) · [Gates](#gates-and-guarantees) · [Skills](#on-demand-specialization-skills) · [Commands](#commands-cheat-sheet) · [Docs](#documentation) · [Credits](#credits)

---

## What it is

A **governance layer** for AI coding agents — not an IDE, not an autonomous agent platform, and not a remote control plane.

After install in a project, work moves through governed intentions:

**Demand** → **Situation** → **Contract** → **Action** (+ Tasks when needed) → **Skill** (specialize) → **Execution** (native agent) → **Evidence** → **Assurance** → **Learning** / **Skill evolution** → return informed

Retornatus is **repository-native**:

- no mandatory SaaS runtime
- no remote database required for V1
- durable truth = files under `.retornatus/`
- SQLite/FTS5 is a **derived** index (safe to delete; `wake` rebuilds)

Philosophy: **native first** — prefer Cursor / Claude Code / Codex capabilities; implement only what the host does not already guarantee.

You do not need to already know “harness engineering.” The hub skill teaches the loop; **gates** enforce the stops. Failure modes and mechanisms: [four pillars](#four-pillars).

---

## 1. Install

Two commands — run both once in your **project** root (the app you are building):

```bash
# From a clone of this repository (until PyPI is live):
uv tool install --force /path/to/retornatus

cd /path/to/your-app
retornatus init
retornatus integrate   # hub skill + Cursor bridges
retornatus doctor
```

| Command | What it does |
| --- | --- |
| **`init`** | Creates `.retornatus/` (config, changes, governance, adaptation, index, runtime) |
| **`integrate`** | Installs the Retornatus **hub skill** under `.cursor/skills/retornatus/` + bridge rules |
| **`doctor` / `wake`** | Audits continuity, environment capabilities, and index health |

| Requirement | What you get |
| --- | --- |
| **Python 3.11+** | **Required** — harness runtime |
| **[uv](https://docs.astral.sh/uv/)** | **Recommended** — `uv tool`, `uvx`, reproducible installs |
| **AI coding agent** (Cursor, Claude Code, Codex, …) | Executes work; Retornatus governs and records |

### Install options

**Persistent tool (recommended):**

```bash
uv tool install --force /path/to/retornatus
retornatus --version   # 0.6.x
```

**Windows (PowerShell) — ensure `uv` is on PATH:**

```powershell
$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
uv tool install --force "C:\path\to\retornatus"
```

**One-shot without a global tool:**

```bash
uvx --from /path/to/retornatus retornatus --help
```

**From Git (once you prefer remote install):**

```bash
uv tool install --force git+https://github.com/luizssantiago92/retornatus.git
```

**PyPI (when published):**

```bash
uvx retornatus --help
uv tool install retornatus
```

Re-run `uv tool install --force …` after pulling harness upgrades. Project state under `.retornatus/` is preserved.

### Working in this source repository (contributors / dogfood)

```bash
uv sync
uv run retornatus --help
uv run pytest -q
uv run retornatus integrate
uv run retornatus wake --bridges
```

Day to day you work in **agent chat**; the agent calls the CLI when a phase needs structure or a gate.

---

## 2. Verify readiness

Re-run `doctor` / `wake` after upgrades or machine changes. You are ready when:

- `retornatus --version` prints `0.6.x` (or newer)
- `.retornatus/` exists with `config.toml`
- Hub skill is visible (for example `.cursor/skills/retornatus/SKILL.md` after `integrate`)
- Your AI coding agent can open the project

```bash
retornatus doctor
retornatus wake
# optional native bridges + hub:
retornatus wake --bridges
retornatus integrate
```

Deleting `.retornatus/index/retornatus.db` must **not** destroy semantic history — run `wake` again to rebuild.

For multi-environment notes, see [Environment adapters](#environment-adapters-native-first).

---

## 3. Run your first Change

Open your AI coding agent in the project and ask for a concrete governed goal, for example:

> Create a Retornatus Change for a health endpoint: GET /health returns 200. Follow the Retornatus hub skill — Contract and gates before code.

Ask it to follow the installed **Retornatus hub skill**. Chat phrases are guidance; shell commands are the source of truth.

| Step | You do | Agent / CLI does |
| --- | --- | --- |
| 1 | Approve Demand / Contract intent | `change create` → Situation, active Contract, Action |
| 2 | Gate the Contract | `gate contract C-xxxx` (exit 0 required) |
| 3 | Specialize if needed | `skill create --need "…"` → research web → fill RESEARCH → `gate skill-research` → `activate` |
| 4 | Build one unit at a time | `loop next` · `run A-xxxx` · implement in the host |
| 5 | Demand proof | `evidence add` · `gate evidence` · `verify` / `gate assurance` |
| 6 | Preserve the return | `change learn` · `skill evolve` |

Example shell path:

```bash
retornatus init
retornatus integrate
retornatus project-init

retornatus change elicit \
  --demand "Expose a liveness check for ops" \
  --what "GET /health returns 200 with status ok" \
  --done "Automated test covers /health" \
  --done "Endpoint documented"

retornatus change create \
  --title "Add health endpoint" \
  --demand "Expose a liveness check for ops" \
  --what "GET /health returns 200 with status ok" \
  --done "Automated test covers /health" \
  --done "Endpoint documented" \
  --objective "Implement and verify health endpoint"

retornatus gate contract C-0001
retornatus skill create --need "Framework health-check patterns (current docs)" --action C-0001/A-001
# agent researches, fills SKILL.md, then:
retornatus gate skill-research S-0001
retornatus skill activate S-0001
retornatus skill export S-0001

retornatus loop next C-0001
retornatus run C-0001/A-001

retornatus evidence add -c C-0001 -t test_result -s "/health" --source pytest --state passing \
  --claim C-0001/claim-done-1
retornatus evidence add -c C-0001 -t repository_observation -s "docs/health.md" --source filesystem \
  --claim C-0001/claim-done-2
retornatus gate evidence C-0001
retornatus verify C-0001
```

If the agent jumps straight to code: *Stop. Activate a Contract and pass `gate contract` first.*

---

## Capability status (honest)

| Status | Meaning |
| --- | --- |
| **Implemented** | Exercised by unit, adversarial, and/or construction dogfood tests |
| **Environment-provided** | Host (Cursor / Claude Code / Codex) owns the capability; Retornatus does not duplicate it |
| **Projected/integrated** | Bridge/hub skill teaches or surfaces the capability |
| **Experimental** | Present but lightly proven |
| **Not yet supported** | Known gap |

| Capability | Status | Notes |
| --- | --- | --- |
| Situation elicitation | Implemented | `change elicit` + repo signals (stack/tests/CI) before Contract |
| Task readiness / deps / cycles | Implemented | Derived READY/BLOCKED; CLI `--task` / `--depends` / `--resource` |
| Claim↔Evidence binding | Implemented | `--claim` + SUPPORTS relation; subject/type checks |
| Evidence staleness | Implemented | `commit:<sha>` via `--git-state`; stale after new HEAD |
| Assurance (proportional) | Implemented | Types inferred from DONE; `human_decision` not universal |
| Independent Assurance | Implemented | `assurance plan` + `assurance review` + `run --assurance` |
| Question Resolution proof | Implemented | Verifiable Questions need Evidence |
| Human Decision → Rule | Implemented | `decision record` + `rule activate --decision` |
| Governed bypass | Implemented | `--force --reason` records Bypass + Decision |
| Brownfield `project-init` / wake | Implemented | Stack, tests, CI, dirs, Retornatus state |
| Context relevance | Implemented | Applicability-filtered Rules/Learnings |
| Brownfield construction dogfood | Implemented | Fixture service + health Change + git freshness |
| Host Execution runtime | Environment-provided | Retornatus assembles context; host implements |
| Workspace isolation / worktrees | Environment-provided | Native first |
| Spec Guardrails fully replaced | Not yet supported | Dogfood proves governed path; not full replacement claim |

---

## Getting started checklist

- [ ] Python 3.11+ available (`python --version`)
- [ ] `uv` installed and on `PATH`
- [ ] Installed Retornatus (`uv tool install --force …`)
- [ ] Ran `retornatus init` in the target project
- [ ] Ran `retornatus integrate` and confirmed the hub skill is visible
- [ ] `doctor` / `wake` succeeds
- [ ] Created a first Change and passed `gate contract`
- [ ] Know where the product contract lives: [prd/PRD.md](prd/PRD.md)

---

## Four pillars

| Problem | Pillar | One-line win |
| --- | --- | --- |
| Built the wrong thing | **Contract** | WHAT + constraints + DONE before execution |
| Called it done without proof | **Gates + Assurance** | Exit codes + verdict from Evidence, not self-report |
| Every chat starts from zero | **Memory / Learning** | `.retornatus/` + FTS index outlive the session |
| Stale playbooks for every stack | **On-demand Skills** | One researched specialization Skill per need |

### 1. Contract — stop “done” from meaning “I typed a lot”

**Without it:** acceptance criteria live in a chat bubble and evaporate.

**With it:** an active Contract is the authoritative obligation. Material change requires a new version — not silent mutation.

### 2. Gates + Assurance — “done” has to be provable

Mechanical gates return **non-zero = STOP**:

| Gate | Stops when |
| --- | --- |
| `gate contract` | No active Contract / empty WHAT or DONE |
| `gate skill-research` | Skill has no research URLs / blank PROCEDURE |
| `gate evidence` | No Evidence artifacts for the Change |
| `gate assurance` / `verify` | Assurance is not `SATISFIED` |

Assurance verdicts:

| Verdict | Meaning |
| --- | --- |
| `SATISFIED` | Each Claim has bound, fresh, type-appropriate Evidence |
| `NOT_SATISFIED` | Evidence present but wrong claim/subject/type or stale |
| `INCONCLUSIVE` | Required Evidence unavailable / unbound |

> Agent conclusion ≠ Evidence. A green suite is evidence, not proof of overall correctness.
> Evidence must SUPPORT a specific Claim — “some test_result exists” is not enough.

### 3. Memory — return informed

Learnings are Markdown with structured metadata. Rules may be **proposed** from experience (Graduation → Rule Candidate) but **never** become authoritative without a durable **Human Decision** (`decision record` → `rule activate --decision`).

> Learning informs; Rules constrain. Recurrence never creates authority automatically.
> Setting `authority=HUMAN` on a Rule object is not sufficient — activation requires a Decision artifact.

### 4. On-demand Skills — specialize without stale packs

Retornatus does **not** ship a giant library of preloaded skills that rot.

When a Change needs specialization:

1. `skill create --need "…"` creates **one** Skill tied to the Action
2. The agent **researches current sources** (web / official docs) and fills RESEARCH + PROCEDURE
3. `gate skill-research` blocks activation until sources exist
4. Governed bypass only: `skill activate --force --reason "…"` (records Bypass + Decision)
5. Subagents consume the same Skill snapshot (`skill export` → native Cursor skill)
6. `skill evolve` updates the Skill from validated Learning

> Specialization comes from Assignment + Context + Skills — not permanent Agent personas.

---

## How it works

```text
                    RETORNATUS
                         │
     ┌───────────────────┼───────────────────┐
     ▼                   ▼                   ▼
 Continuity          Governance          Environment
  (Memory)         Rule · Policy         Wake · Caps
                   Authority · Bounds    Adapters · Hub
                         │
                         ▼
                      CHANGE
         Demand · Situation · Contract
              Action · Task?
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           Skill     Execution   Assurance
        (research)  (native)   Evidence → Verdict
              │
         Finding → Question → Action → Resolution
              │
              ▼
          Adaptation
     Learning · Skill evolution · Rule Candidate → Human → Rule
```

| Layer | Responsibility |
| --- | --- |
| **CLI** | Intention-oriented commands (`init`, `wake`, `change`, `gate`, `skill`, …) |
| **Hub skill** | Teaches the construction loop inside the agent tree |
| **Application** | Change workflow, gates, Assurance, Question loop, Adaptation, `loop next` |
| **Domain** | Pydantic models, IDs, relations, schema versioning |
| **Infrastructure** | Atomic persistence, optimistic concurrency, SQLite FTS5, env adapters |

Invariant: **files persist truth; models validate truth; SQLite indexes and finds truth.**

Status is a **projection** (`status`, `loop next`) — not a second source of truth.

---

## Gates and guarantees

| Guarantee | How Retornatus enforces it |
| --- | --- |
| Contract before “build” | `gate contract` + Situation sufficiency |
| Research before specialized execution | `gate skill-research` + blocked `skill activate` |
| Evidence before “done” | Claim-bound `evidence add` + `gate evidence` + `verify` |
| Continuity after crash | Canonical files + `wake` index rebuild |
| No silent Rule authority | Rule Candidates require Human Decision |
| No ungovered gate skip | Bypass requires reason + authority + durable record |

### Process vs brakes (honest)

| | **Process** (hub skill + CLI) | **Brakes** (gates) |
| --- | --- | --- |
| **Workflow** | Same Change → Skill → Evidence loop | Same loop |
| **Who checks** | Agent follows the hub skill | CLI exit codes |
| **When incomplete** | Agent *should* stop | Agent **cannot** pretend success — non-zero = STOP |
| **Best for** | Learning the method | Teams that want proof between approvals |

> Gates turn “trust the agent” into “the agent has to prove it.”

---

## On-demand specialization Skills

```bash
retornatus skill create --need "Stripe webhook signatures (current API)" --action C-0001/A-001
retornatus inspect S-0001
# agent fills RESEARCH with URLs + PROCEDURE
retornatus gate skill-research S-0001
retornatus skill activate S-0001
retornatus skill export S-0001          # → .cursor/skills/<name>/SKILL.md
retornatus skill evolve S-0001 --note "Added timestamp tolerance"
```

Canonical storage: `.retornatus/adaptation/skills/S-xxxx/SKILL.md`  
Native projection: `.cursor/skills/…` (and similar bridges for other hosts)

---

## Environment adapters (native first)

```bash
retornatus wake --bridges
retornatus integrate
```

| Environment | Native preference |
| --- | --- |
| Cursor | Hub + rules under `.cursor/` |
| Claude Code | `CLAUDE.md` / `.claude` bridge markers |
| Codex | `AGENTS.md` / `.codex` bridge markers |
| Generic | `.retornatus/` alone is enough |

Adapters write **projections** only. Canonical truth stays in `.retornatus/`.

---

## What is enforced — and what is not

| Enforced / owned by Retornatus | Not Retornatus’s job (host / human) |
| --- | --- |
| Structure of Changes, Contracts, Skills, Evidence | Writing application code |
| Schema validation & atomic persistence | Replacing the IDE agent runtime |
| Gate exit codes & Assurance verdicts | Rebuilding sandboxes the host already has |
| Skill research scaffold + activation gate | Surfing the web for the agent (host tools do that) |
| Index rebuild after crash | Multi-tenant SaaS control plane |

Honest scope: V1 is a **local harness** for governed software construction. It does not claim to be a remote orchestration platform.

---

## Commands cheat sheet

Run from the project you want to govern (or pass `--path`).

| Command | What it does |
| --- | --- |
| `init` | Create `.retornatus/` |
| `integrate` | Install hub skill + Cursor bridges |
| `project-init` | Brownfield continuity map → `project/project.md` |
| `wake` / `wake --bridges` | Reconstruct state, rebuild index, optional bridges |
| `doctor` | Diagnostics |
| `status` | Derived Change status |
| `change elicit` | Assess Situation readiness (exit 1 if insufficient) |
| `change create` / `change learn` | Demand→Situation→Contract→Action · record Learning |
| `change create --task/--depends/--resource` | Explicit Task deps and resource conflicts |
| `skill create/list/activate/evolve/export` | On-demand specialization Skills |
| `gate contract\|evidence\|skill-research\|assurance` | Mechanical STOP gates |
| `evidence add --claim` / `--git-state` | Claim-bound Evidence; optional `commit:<HEAD>` |
| `finding add` · `question open\|resolve` | Problem loop (resolve needs Evidence when verifiable) |
| `loop next` / `loop next --all-ready` | Ready work projection (never returns BLOCKED) |
| `run <action-id>` / `run --assurance` | Assemble ExecutionContext (optional independent Assurance) |
| `assurance plan` / `assurance review` | Independent review projection + review_result Evidence |
| `verify <change-id>` | Assurance over Contract DONE Claims (git freshness) |
| `decision record` · `rule propose\|activate` | HUMAN boundary for Rule activation |
| `inspect <id>` · `search <query>` | Read artifacts · FTS5 search |

```bash
retornatus --help
retornatus gate --help
retornatus skill --help
```

---

## Explore the repository

| Path | What you find |
| --- | --- |
| [`src/retornatus/cli/`](src/retornatus/cli/) | Intention-oriented CLI |
| [`src/retornatus/domain/`](src/retornatus/domain/) | Pydantic models, IDs, relations |
| [`src/retornatus/application/`](src/retornatus/application/) | Change, gates, Assurance, Skills, Question loop, `loop next` |
| [`src/retornatus/infrastructure/`](src/retornatus/infrastructure/) | Persistence, SQLite index, adapters, hub skill |
| [`src/retornatus/bootstrap/`](src/retornatus/bootstrap/) | `init`, `wake`, `project-init` |
| [`prd/PRD.md`](prd/PRD.md) | Product requirements (canonical V1) |
| [`tests/`](tests/) | Unit + adversarial + construction dogfood |
| [`.github/workflows/publish.yml`](.github/workflows/publish.yml) | PyPI / TestPyPI publish |

After install in a consumer project, day-to-day artifacts live under **`.retornatus/`** (`changes/`, `governance/`, `adaptation/`, `index/`, `runtime/`).

---

## Documentation

| Area | Where |
| --- | --- |
| **Start** | This README · [prd/PRD.md](prd/PRD.md) |
| **Philosophy & invariants** | PRD §§2, 72 |
| **Filesystem layout** | PRD §52 |
| **CLI intentions** | PRD §62 · [Commands](#commands-cheat-sheet) |
| **Skills / Adaptation** | PRD §§39–41 · [On-demand Skills](#on-demand-specialization-skills) |
| **Milestones M0–M12** | PRD §68 |

Deeper narrative guides can grow under `docs/` as the product hardens — the PRD remains the source of truth.

---

## Contributing

Improvements that preserve **native-first** and **complexity must be earned** are welcome.

```bash
uv sync
uv run pytest -q
```

Prefer small milestones over speculative engines. Architecture changes should cite a concrete failure mode (PRD §71).

---

## Credits

*Credits and upstream attributions will be added here.*

Related prior work in this ecosystem: [spec-guardrails](https://github.com/luizssantiago92/spec-guardrails) (governed spec-driven development for AI coding agents). Retornatus is a **separate harness** focused on Change/Contract/Skill/Evidence continuity — not a fork of Spec Guardrails.

**Replacement readiness:** brownfield dogfood proves Retornatus can govern Demand→Situation (with repo signals)→Contract→Action (explicit Task deps/resources)→Host execution→Claim-bound Evidence with `commit:<sha>` freshness→independent review Evidence→Assurance→wake continuity. That is **not** a claim that Spec Guardrails is fully replaced for every workflow.

---

## License

MIT — see [LICENSE](LICENSE).

[↑ Back to top](#retornatus)
