# Retornatus

[![PyPI version](https://img.shields.io/pypi/v/retornatus.svg)](https://pypi.org/project/retornatus/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/luizssantiago92/retornatus/actions/workflows/ci.yml/badge.svg)](https://github.com/luizssantiago92/retornatus/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Repo-native governance harness for AI-assisted software development.**

More than a checklist — a **governance harness** (Contracts, gates, on-demand Skills, Evidence, Assurance, and Memory) that lives inside your repository.

Agents are fast — and optimistic. They ship code, summarize what they *think* they did, and move on. Retornatus installs a **repeatable contract** into your repo: express a Demand, understand the Situation, activate a Contract, specialize with a researched Skill when needed, execute under Authority and Boundaries, and close with attributable Evidence — all durable under `.retornatus/`, not trapped in chat scrollback.

You keep control: the agent proposes and implements; **gates** stop “done” without proof; Human Decisions authorize Rules; Learning and Skill evolution improve the next return.

> **Govern the work. Bound the agent. Verify the outcome.**

| Without Retornatus | With Retornatus |
| --- | --- |
| Jumps to code and says “done” | Active Contract + DONE criteria first |
| “Done” is a chat claim | Assurance verdict from Claim-bound Evidence |
| Each chat starts from zero | `.retornatus/` survives sessions and handoffs |
| Stale skill packs for every stack | **One specialization Skill**, researched *now* for this Change |
| Same ceremony for a typo and a payment flow | Tasks / Skills only when complexity earns them; `loop next` projects the next unit |
| Silent policy / rule invention | Policy check + Human Decision before authoritative Rules |
| Failures vanish when the tab closes | Finding → Question → Action leaves a trail |

PyPI: [`retornatus`](https://pypi.org/project/retornatus/) **1.0.x** · primary run via [`uv`](https://docs.astral.sh/uv/) (`uv tool install` / `uvx`)

**Docs:** [Overview](docs/guide/Overview.md) · [Quick start](docs/guide/Quick-start.md) · [Full guide index](docs/guide/README.md) · [PRD](prd/PRD.md)

[What it is](#what-it-is) · [Install](#1-install) · [Verify](#2-verify-readiness) · [First Change](#3-run-your-first-change) · [Checklist](#getting-started-checklist) · [Pillars](#four-pillars) · [How it works](#how-it-works) · [Gates](#gates-and-guarantees) · [Skills](#on-demand-specialization-skills) · [Governance](#human-decisions-rules--policy) · [Commands](#commands-cheat-sheet) · [Docs](#documentation) · [Credits](#credits-lineage--prior-art)

---

## What it is

A **governance layer** for AI coding agents — not an IDE, not an autonomous agent platform, and not a remote control plane.

After install in a project, work moves through governed intentions:

```text
Demand → Situation → Contract → Action (+ Tasks when needed)
       → Skill? (research current sources) → Execution (host agent)
       → Evidence → Assurance → Learning / Skill evolution
```

If discovery blocks progress:

```text
Finding → Question → Action → Evidence → Resolution
```

Retornatus is **repository-native**:

- no mandatory SaaS runtime
- no remote database required for V1
- durable truth = files under `.retornatus/`
- SQLite/FTS5 is a **derived** index (safe to delete; `wake` rebuilds)

Philosophy: **native first** — prefer Cursor / Claude Code / Codex capabilities; implement only what the host does not already guarantee.

You do not need to already know “harness engineering.” The hub skill teaches the loop; **gates** enforce the stops. Failure modes and mechanisms: [four pillars](#four-pillars).

---

## 1. Install

Install the CLI once, then bind it to each **project** you want to govern.

| Requirement | What you get |
| --- | --- |
| **Python 3.11+** | **Required** — harness runtime |
| **[uv](https://docs.astral.sh/uv/)** | **Recommended** — `uv tool`, `uvx`, reproducible installs |
| **AI coding agent** (Cursor, Claude Code, Codex, …) | Executes work; Retornatus governs and records |

### A. Install the CLI

**From PyPI (recommended):**

```bash
uv tool install retornatus
retornatus --version   # 1.0.x
```

One-shot without a global install:

```bash
uvx retornatus --help
```

**From TestPyPI (CI / pre-release dry-run):**

```bash
uv tool install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  retornatus
```

`--extra-index-url` keeps dependencies resolving from production PyPI.

**From Git or a local clone:**

```bash
uv tool install --force git+https://github.com/luizssantiago92/retornatus.git
uv tool install --force /path/to/retornatus
```

Re-run `uv tool install --force …` after upgrades. Project state under `.retornatus/` is preserved.

### B. Bind a project (once per repo)

```bash
cd /path/to/your-app
retornatus init
retornatus integrate   # hub skill + host bridges
retornatus doctor
```

| Command | What it does |
| --- | --- |
| **`init`** | Creates `.retornatus/` (config, changes, governance, adaptation, index, runtime) |
| **`integrate`** | Installs the Retornatus **hub skill** + Environment bridge projections |
| **`doctor` / `wake`** | Audits continuity, hub/bridge presence, capabilities, and index health |

Day to day you work in **agent chat**; the agent calls the CLI when a phase needs structure or a gate.

**Go deeper:** [Quick start](docs/guide/Quick-start.md) · [Environments](docs/guide/Environments.md)

### Working in this source repository (contributors / dogfood)

```bash
uv sync
uv run retornatus --help
uv run pytest -q
uv run retornatus integrate
uv run retornatus wake --bridges
```

---

## 2. Verify readiness

Re-run `doctor` after upgrades or machine changes. You are ready when:

- `retornatus --version` prints `1.0.x` (or newer)
- `.retornatus/` exists with `config.toml`
- Hub skill is visible (for example `.cursor/skills/retornatus/SKILL.md` after `integrate`)
- Your AI coding agent can open the project

```bash
retornatus doctor
retornatus wake
# optional native bridges + hub refresh:
retornatus wake --bridges
retornatus integrate
```

Deleting `.retornatus/index/retornatus.db` must **not** destroy semantic history — run `wake` again to rebuild.

For multi-environment notes, see [Environment adapters](#environment-adapters-native-first).

---

## 3. Run your first Change

Open your AI coding agent in the project and ask for a concrete governed goal, for example:

> Create a Retornatus Change for a health endpoint: GET /health returns 200. Follow the Retornatus hub skill — Contract and gates before code.

Ask it to follow the installed **Retornatus hub skill**. Chat phrases are guidance; **shell commands are the source of truth** for gates.

| Step | You do | Agent / CLI does |
| --- | --- | --- |
| 1 | Approve Demand / Situation | `change elicit` · `change create` (or `--draft-contract` then `change activate`) |
| 2 | Confirm Contract WHAT + DONE | `gate contract <C-id>` must exit **0** |
| 3 | Optional: specialize | `skill create` → research → `gate skill-research` → `skill activate` |
| 4 | Build one unit at a time | `loop next` · `run <A-id>` · implement in the host |
| 5 | Demand attributable proof | `evidence add --claim …` · `gate evidence` · `verify` |
| 6 | Preserve experience | `change learn` · `skill evolve` |

If the agent jumps straight to code: *Stop. Finish Situation + Contract and pass `gate contract` first.*

Or drive the CLI yourself:

```bash
retornatus change elicit \
  --demand "Expose a liveness check for ops"

retornatus change create \
  --title "Add health endpoint" \
  --demand "Expose a liveness check" \
  --what "GET /health returns 200 with status ok" \
  --done "Automated test covers /health" \
  --objective "Implement and verify health endpoint"

retornatus gate contract C-0001
retornatus loop next C-0001
retornatus run C-0001/A-001
# …implement in the host, then:
retornatus evidence add C-0001 --claim "GET /health returns 200" --type test_result --summary "pytest passed"
retornatus gate evidence C-0001
retornatus verify C-0001
```

**Go deeper:** [Quick start](docs/guide/Quick-start.md) · [How it works](docs/guide/How-it-works.md) · [CLI](docs/guide/CLI.md)

---

## Getting started checklist

- [ ] Python 3.11+ available (`python --version`)
- [ ] Installed CLI (`uv tool install retornatus`) and `retornatus --version` works
- [ ] Ran `retornatus init` + `retornatus integrate` in the **application** repo
- [ ] `retornatus doctor` exits 0 / reports initialized
- [ ] Opened the project in your AI coding agent and confirmed the hub skill is visible
- [ ] Created a Change and passed `retornatus gate contract <C-id>` before implementation
- [ ] Know where docs live: [Quick start](docs/guide/Quick-start.md) · [Full guide](docs/guide/README.md)

Stuck? See [FAQ](docs/guide/FAQ.md) and [Non-goals](docs/guide/Non-goals.md).

---

## Four pillars

| Problem | Pillar | One-line win |
| --- | --- | --- |
| Built the wrong thing / skipped obligations | **Contract** | Active WHAT + constraints + DONE before build |
| Declared “done” without proof | **Gates & Assurance** | Exit codes + Claim-bound Evidence → verdict |
| Every chat starts from zero | **Memory / Learning** | `.retornatus/` + FTS index outlive the session |
| Wrong expertise / stale playbooks | **On-demand Skills** | Research *now*; one Skill per need; evolve later |

### 1. Contract — stop building the wrong obligation

**Without it:** “Add login” becomes three different products in three chats — and you discover the mismatch halfway through a PR.

**With Contracts:** Demand and Situation are written first. The active Contract is the authoritative obligation (WHAT, constraints, DONE). Material change requires a **new Contract version** (`change reopen`) — not silent mutation. Optional `change elicit` surfaces readiness before create/activate.

| Without Contract | With Contract |
| --- | --- |
| Assumptions stay implicit in chat | Situation + Contract make obligations explicit |
| “Done” means “agent said so” | DONE criteria are Claims that Evidence must bind |
| Mid-build goal drift | Versioned Contract; reopen for material change |

**Go deeper:** [Concepts](docs/guide/Concepts.md) · [How it works](docs/guide/How-it-works.md)

---

### 2. Gates & Assurance — “done” has to be provable

Scripts and CLI commands return **non-zero = STOP**; fix the artifact, re-run.

| Moment | What gates protect |
| --- | --- |
| **Before build** | Active Contract with WHAT + DONE (`gate contract`) |
| **Before specialized execution** | Skill RESEARCH has sources (`gate skill-research`) |
| **Before claiming progress** | Evidence artifacts exist (`gate evidence`) |
| **Before “Change done”** | Assurance `SATISFIED` over Contract DONE Claims (`verify` / `gate assurance`) |
| **Before risky effects** | Policy ALLOW vs DENY / REQUIRE_HUMAN (`gate policy`) |

**Process vs brakes:** the hub skill teaches the method; gates enforce it with exit codes.

> Agent conclusion ≠ Evidence. A green test suite is evidence of tests — not automatic proof of every Claim unless bound correctly.

**Go deeper:** [Gates](docs/guide/Gates.md) · [Governance](docs/guide/Governance.md)

---

### 3. Memory — the repo remembers so you do not have to

**Without memory:** Every new session starts cold. You re-paste context and hope the model does not contradict last week’s architecture chat.

**With `.retornatus/`:** Changes, Contracts, Evidence, Findings, Questions, Learnings, Skills, and Rules are files. `wake` rebuilds the derived SQLite/FTS5 index. `search` finds prior work. `project-init` maps brownfield context into `project/project.md`.

| Without `.retornatus/` | With `.retornatus/` |
| --- | --- |
| Chat is the source of truth | Git / files are the source of truth |
| Handoff = long message | Handoff = `wake` + Change folder |
| Same mistake twice | Learning + Skill evolution + Rule Candidates |
| “What did we decide?” | `search`, `inspect`, Decisions under governance |

**Go deeper:** [Memory](docs/guide/Memory.md) · [Architecture](docs/guide/Architecture.md)

---

### 4. On-demand Skills — specialize without rotting packs

Retornatus does **not** ship a giant library of preloaded skills that go stale.

When a Change needs specialization: create **one** Skill for that need, research **current** sources into RESEARCH + PROCEDURE, pass `gate skill-research`, activate, optionally `export` to the host, and later `evolve` from validated Learning. `skill need` can skip ceremony for trivial Actions.

**Go deeper:** [Skills](docs/guide/Skills.md) · section below

---

## How it works

High-level lifecycle — with **gates** at the boundaries that matter:

```text
wake / doctor
      ↓
change elicit? → change create (Demand → Situation → Contract → Action)
      ↓
gate contract  (must exit 0)
      ↓
skill need? → skill create → research → gate skill-research → activate → export?
      ↓
run <A-id>  (ExecutionContext: rules, learnings, skills, boundaries)
      ↓
loop next / task lifecycle  (one ready unit at a time)
      ↓
evidence add --claim … → gate evidence → verify / assurance
      ↓
finding/question if blocked → resolve
      ↓
change learn · skill evolve · rule propose (+ Human Decision)
```

Status (`retornatus status`, `loop next`) is a **projection**. If it disagrees with files, **the files win**.

### Capability map — what is available when

| Capability | Required? | What happens | Human? |
| --- | --- | --- | --- |
| **init / integrate** | Once per project | Scaffold + hub + bridges | — |
| **project-init** | Brownfield | Continuity map in `project.md` | — |
| **change elicit** | Optional | Situation readiness check | As needed |
| **change create / activate** | Yes (full path) | Demand → Contract (+ optional draft) | Approve intent |
| **Tasks** | When work needs a job list | Explicit Task graph + `task start|complete|…` | — |
| **Skill** | When specialization earned | Research → activate → export / evolve | Bypass needs reason |
| **Execution** | Yes | Host agent; `run` assembles context; `execution record` observes | — |
| **Evidence / verify** | Yes for “done” | Claim-bound Evidence → Assurance verdict | Independent `assurance review` optional |
| **Finding / Question** | When blocked | Discovery loop with durable trail | — |
| **Learning** | After validated experience | Informs future Context | — |
| **Rule / Policy / Decision** | When governance tightens | Candidates → Human Decision → Rule; Policy ALLOW/DENY/REQUIRE_HUMAN | **Decision** |

> More risk and novelty → more Contract rigor, Skill research, Evidence, and Policy — complexity must be earned (PRD §71).

**Go deeper:** [How it works](docs/guide/How-it-works.md) · [Concepts](docs/guide/Concepts.md)

---

## Gates and guarantees

Exit code **0** = pass; **non-zero** = STOP.

| Command | Stops when |
| --- | --- |
| `gate contract <C-id>` | No active Contract, empty WHAT, or no DONE criteria |
| `gate skill-research <S-id>` | RESEARCH lacks sources / PROCEDURE blank |
| `gate evidence <C-id>` | No Evidence artifacts for the Change |
| `gate assurance <C-id>` | Assurance is not `SATISFIED` |
| `gate policy <A-id>` | Policy is `DENY` or `REQUIRE_HUMAN` |
| `verify <C-id>` | Assurance over Contract DONE Claims fails |

### Assurance verdicts

| Verdict | Meaning |
| --- | --- |
| `SATISFIED` | Each required Claim has bound, fresh, type-appropriate Evidence |
| `NOT_SATISFIED` | Evidence exists but wrong claim/subject/type or stale |
| `INCONCLUSIVE` | Required Evidence missing or unbound |

### Product-level guarantees

| Guarantee | Mechanism |
| --- | --- |
| Contract before build | `gate contract` + Situation sufficiency |
| Research before specialized execution | `gate skill-research` |
| Evidence before done | Claim-bound Evidence + `verify` |
| Continuity after crash / handoff | Canonical files + `wake` |
| No silent Rule authority | Human Decision required |
| Policy visibility | `gate policy` / `run --strict-policy` |

**Go deeper:** [Gates](docs/guide/Gates.md)

---

## What is enforced — and what is not

Gates enforce **structure and attributable proof in `.retornatus/`** — not product taste, not semantic test quality, not a full AST review of application code.

| Enforced | Not enforced |
| --- | --- |
| Contract shape and active version | Whether the WHAT is the “right” product idea |
| Claim-bound Evidence presence for Assurance | Whether tests are clever or sufficient |
| Skill RESEARCH sources before activate | Correctness of every researched fact forever |
| Policy DENY / REQUIRE_HUMAN visibility | Full OS sandboxing (host-native) |
| Continuity of canonical files | Multi-tenant SaaS orchestration |

> A green gate means the required **process and evidence** exist — it is not proof that the product is perfect.

Honest V1 bounds: [Non-goals](docs/guide/Non-goals.md).

---

## On-demand specialization Skills

```text
skill need? → create → research (web/docs) → fill RESEARCH + PROCEDURE
           → gate skill-research → activate → export? → evolve from Learning
```

```bash
retornatus skill need --action C-0001/A-001
retornatus skill create --need "Stripe webhook signatures (current API)" --action C-0001/A-001
# agent fills .retornatus/adaptation/skills/S-0001/SKILL.md
retornatus gate skill-research S-0001
retornatus skill activate S-0001
retornatus skill export S-0001
retornatus skill evolve S-0001 --note "Added timestamp tolerance"
```

| Location | Role |
| --- | --- |
| `.retornatus/adaptation/skills/S-xxxx/SKILL.md` | Canonical Skill |
| Host skill tree (e.g. `.cursor/skills/…`) | Native projection via `export` / hub |

Governed bypass (records reason): `skill activate S-0001 --force --reason "…"`.

**Go deeper:** [Skills](docs/guide/Skills.md)

---

## Human Decisions, Rules & Policy

| Intent | Command |
| --- | --- |
| Record a Human Decision | `decision record` |
| Propose a Rule Candidate | `rule propose` |
| Activate a Rule (requires Decision) | `rule activate --decision <D-id>` |
| Evaluate Policy | `policy check --action <A-id>` / `--effect "…"` |
| Stop on DENY / REQUIRE_HUMAN | `gate policy <A-id>` · `run --strict-policy` |

Learning **informs**; Rules **constrain**. Recurrence alone never auto-promotes an authoritative Rule.

**Go deeper:** [Governance](docs/guide/Governance.md)

---

## Finding → Question loop

When implementation discovers unknowns, do not bury them in chat:

```bash
retornatus finding add C-0001 --summary "Auth cookie SameSite unclear for mobile WebView"
retornatus question open C-0001 --finding F-0001 --text "Which SameSite policy do we ship?"
retornatus question resolve C-0001/Q-0001 --resolution "SameSite=Lax; document tradeoff"
# or reopen if the answer was wrong:
retornatus question reopen C-0001/Q-0001
```

`loop next` projects the next ready Question, Task, or Action.

---

## Environment adapters (native-first)

`integrate` and `wake --bridges` detect the host and write **projections** only. Canonical truth stays in `.retornatus/`.

| Host | Surface |
| --- | --- |
| Cursor | `.cursor/skills/retornatus/` + `.cursor/rules/retornatus.mdc` |
| Claude Code | `CLAUDE.md` bridge markers |
| Codex | `AGENTS.md` bridge markers |
| Generic | `.retornatus/` alone |

Active Rules are projected into those bridges when present. Prefer host worktrees / sandboxes / subagents — Retornatus records Boundaries and Execution observations; it does not reimplement the IDE.

**Go deeper:** [Environments](docs/guide/Environments.md)

---

## Brownfield projects

```bash
retornatus init
retornatus project-init
retornatus integrate
retornatus wake --bridges
retornatus doctor
```

`project-init` writes a lightweight continuity map (identity, stack signals, important directories, tests) under `.retornatus/project/project.md` so the next session does not start cold.

---

## Commands cheat sheet

Run from the governed project root (or pass `--path`).

### Continuity

| Command | What it does |
| --- | --- |
| `init` | Create `.retornatus/` |
| `integrate` | Hub skill + Environment bridges |
| `project-init` | Brownfield continuity map |
| `wake` / `wake --bridges` | Reconstruct state; rebuild index; optional bridges |
| `doctor` | Continuity + governance hygiene |
| `status` | Derived Change status |
| `inspect <id>` | Print artifact JSON |
| `search <query>` | FTS5 over the derived index |

### Change & tasks

| Command | What it does |
| --- | --- |
| `change elicit` | Situation readiness (exit 1 if insufficient) |
| `change create` | Demand → Situation → Contract → optional Action/Tasks |
| `change activate` | Activate a draft Contract |
| `change reopen` | Material Contract version (archive prior) |
| `change learn` | Record Learning |
| `task start\|complete\|fail\|reopen` | Durable Task lifecycle |
| `loop next` / `loop next --all-ready` | Next ready Question / Task / Action |

### Skills

| Command | What it does |
| --- | --- |
| `skill need` | Complexity-sensitive specialization check |
| `skill create` / `list` | Create / list Skills |
| `skill activate` / `evolve` / `export` | Lifecycle + native projection |

### Proof, policy, execution

| Command | What it does |
| --- | --- |
| `evidence add --claim` | Claim-bound Evidence (`--git-state` optional) |
| `gate contract\|evidence\|skill-research\|assurance\|policy` | STOP gates |
| `verify` | Assurance over Contract DONE |
| `assurance plan` / `assurance review` | Independent review path |
| `policy check` | ALLOW / DENY / REQUIRE_HUMAN |
| `run` / `run --assurance` / `run --strict-policy` | Assemble ExecutionContext |
| `execution record` / `list` | Host execution observations |

### Problems & governance

| Command | What it does |
| --- | --- |
| `finding add` | Record observation |
| `question open\|resolve\|reopen` | Question lifecycle |
| `decision record` | Human Decision |
| `rule propose` / `rule activate` | Rule Candidate → Rule |

IDs are stable strings such as `C-0001`, `C-0001/A-001`, `S-0001`, `R-0001`, `D-0001`.

Full surface: `retornatus --help` · [CLI guide](docs/guide/CLI.md).

---

## Explore the repository

| Path | What you find |
| --- | --- |
| [`src/retornatus/`](src/retornatus/) | Package — CLI, domain, application, infrastructure |
| [`docs/guide/`](docs/guide/) | Product guide — start at [Quick start](docs/guide/Quick-start.md) |
| [`docs/credits-and-lineage.md`](docs/credits-and-lineage.md) | Provenance and prior art |
| [`prd/PRD.md`](prd/PRD.md) | Product requirements (V1) |
| [`tests/`](tests/) | Unit, adversarial, and construction dogfood |
| [`.specs/`](.specs/) | Internal parity / gap notes for maintainers |

After install in a consumer project, day-to-day artifacts live under **`.retornatus/`** (`changes/`, `governance/`, `adaptation/`, `index/`, `runtime/`, `project/`).

---

## Documentation

| Area | Guides |
| --- | --- |
| **Start** | [Overview](docs/guide/Overview.md) · [Quick start](docs/guide/Quick-start.md) · [FAQ](docs/guide/FAQ.md) |
| **Core** | [How it works](docs/guide/How-it-works.md) · [Concepts](docs/guide/Concepts.md) · [Memory](docs/guide/Memory.md) · [Skills](docs/guide/Skills.md) |
| **Enforcement** | [Gates](docs/guide/Gates.md) · [Governance](docs/guide/Governance.md) · [Non-goals](docs/guide/Non-goals.md) |
| **Platform** | [Architecture](docs/guide/Architecture.md) · [Environments](docs/guide/Environments.md) · [CLI](docs/guide/CLI.md) · [Glossary](docs/guide/Glossary.md) |
| **Provenance** | [Credits & lineage](docs/credits-and-lineage.md) · [PRD](prd/PRD.md) |

Full index: [docs/guide/README.md](docs/guide/README.md).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Preserve **native-first** and **complexity must be earned** (PRD §71).

```bash
uv sync
uv run pytest -q
```

---

## Credits, Lineage & Prior Art

Retornatus grew directly from the experience of building and dogfooding **[Spec Guardrails](https://github.com/luizssantiago92/spec-guardrails)**. It is a **separate successor architecture** — not a fork or rename — that preserves proven governance guarantees while rethinking mechanisms (structured Contracts, Evidence ≠ Assurance, native-first Environment adapters, on-demand Skills, …).

| Category | What belongs here |
| --- | --- |
| **Direct predecessor** | Spec Guardrails (MIT) — practical proof of repo-native gates, memory, evidence, human checkpoints |
| **Direct Retornatus research** | Host capability surfaces (Cursor / Claude Code / Codex adapters); runtime libraries (Pydantic, Typer, …) |
| **Transitive prior art** | Spec Guardrails’ own upstreams — documented **there**, not re-listed as Retornatus direct influences |
| **Original composition** | Demand→Situation→Contract→Action; Finding→Question→Resolution; Learning/Skill/Rule/Policy separations |

Full provenance: **[docs/credits-and-lineage.md](docs/credits-and-lineage.md)** · Spec Guardrails lineage: [credits.md](https://github.com/luizssantiago92/spec-guardrails/blob/main/docs/guide/credits.md).

> Ideas are credited by influence, not by superficial similarity.

---

## License

MIT — see [LICENSE](LICENSE).

[↑ Back to top](#retornatus)
