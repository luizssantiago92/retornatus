# Retornatus

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-recommended-de5fe9.svg)](https://docs.astral.sh/uv/)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Repo-native governance harness for AI-assisted software development.**

Retornatus turns engineering intent into structured, governed, evidence-backed work — without replacing your coding agent, IDE, sandbox, or worktree. The host environment supplies **capability**; Retornatus supplies **governance, continuity, and assurance**.

Agents are fast — and optimistic. They ship code, summarize what they *think* they did, and move on. Retornatus installs a **repeatable contract** into your repository: express a Demand, understand the Situation, activate a Contract, bound Actions with Authority and Rules, and close outcomes with attributable Evidence — all durable under `.retornatus/`, not trapped in chat scrollback.

The name means **return with memory**: each iteration should start from evidence and learning, not from amnesia.

> **Govern the work. Bound the agent. Verify the outcome.**

| Without Retornatus | With Retornatus |
| --- | --- |
| “Done” is a chat claim | “Done” is Contract DONE + Assurance verdict |
| Every session rediscovers context | `.retornatus/` preserves Changes, Evidence, Learning |
| Rules live in sticky notes (or nowhere) | Rules, Authority, and Boundaries are first-class |
| Failures vanish when the tab closes | Findings → Questions → Actions leave a trail |
| Environment quirks get reinvented | Native-first adapters (Cursor, Claude Code, Codex) |

Distribution: **Python** · primary run via [`uvx`](https://docs.astral.sh/uv/) · persistent install via `uv tool install`

**Product spec:** [prd/PRD.md](prd/PRD.md)

[What it is](#what-it-is) · [Install](#1-install) · [Verify](#2-verify-readiness) · [First change](#3-run-your-first-change) · [Checklist](#getting-started-checklist) · [How it works](#how-it-works) · [Commands](#commands-cheat-sheet) · [Docs](#documentation) · [Credits](#credits)

---

## What it is

A **governance layer** for AI coding agents — not an IDE, not an autonomous agent platform, and not a remote control plane.

Retornatus is **repository-native**:

- no mandatory SaaS runtime
- no remote database required for V1
- durable truth lives as files in `.retornatus/`
- SQLite is a **derived** search index (safe to delete and rebuild)

Core cycle:

**Demand** → **Situation** → **Contract** → **Action** (+ Tasks when needed) → **Execution** (in your native environment) → **Evidence** → **Assurance** → **Resolution** → **Learning** → return better informed

Philosophy in one line: **native first** — prefer Cursor / Claude Code / Codex capabilities; implement only what the host does not already guarantee.

---

## 1. Install

### Requirements

| Requirement | Role |
| --- | --- |
| **Python 3.11+** | Required — harness runtime |
| **[uv](https://docs.astral.sh/uv/)** | Recommended — install, `uvx`, tool management |

### Persistent install (recommended)

From a clone of this repository:

```bash
uv tool install --force /path/to/retornatus
retornatus --version
```

On Windows (PowerShell), ensure uv’s bin dir is on `PATH`:

```powershell
$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
uv tool install --force "C:\path\to\retornatus"
retornatus --version
```

After pulling updates, re-run `uv tool install --force …` so the tool binary matches the tree.

### One-shot / no install

```bash
uvx --from /path/to/retornatus retornatus --help
```

### Working inside this source repository

```bash
uv sync
uv run retornatus --help
uv run pytest -q
```

> PyPI publication is planned; today install from a local path or git checkout.

---

## 2. Verify readiness

You are ready when:

- `retornatus --version` prints `0.2.x` (or newer)
- `retornatus doctor` (or `wake`) can see or create `.retornatus/`
- Your AI coding environment can open the project that owns `.retornatus/`

```bash
retornatus doctor
# or
retornatus wake
```

`wake` reconstructs continuity from durable files, detects the environment, and rebuilds the SQLite/FTS5 index when needed.

Deleting `.retornatus/index/retornatus.db` must **not** destroy semantic history — run `wake` again to rebuild.

---

## 3. Run your first Change

In any software project root:

```bash
retornatus init
retornatus wake

retornatus change create \
  --title "Add health endpoint" \
  --demand "Expose a liveness check for ops" \
  --what "GET /health returns 200 with status ok" \
  --done "Automated test covers /health" \
  --done "Endpoint documented" \
  --objective "Implement and verify health endpoint"
```

Then:

| Step | You / agent | Retornatus |
| --- | --- | --- |
| 1 | Approve the written Demand & Contract intent | Persists Change, Situation, active Contract, Action |
| 2 | Implement in Cursor / Claude / Codex | `run <action-id>` assembles ExecutionContext (rules, learnings, authority) |
| 3 | Attach attributable Evidence | JSON under `.retornatus/changes/C-xxxx/evidence/` |
| 4 | Demand proof | `verify C-xxxx` → Assurance `SATISFIED` / `NOT_SATISFIED` / `INCONCLUSIVE` |
| 5 | Preserve experience | `change learn` records Learning for future wake/search |

Inspect artifacts:

```bash
retornatus status
retornatus inspect C-0001
retornatus inspect C-0001/A-001
retornatus search health
```

If the agent jumps straight to code: *Stop. Activate a Contract and success conditions before treating the work as governed.*

---

## Getting started checklist

- [ ] Python 3.11+ available (`python --version`)
- [ ] `uv` installed and on `PATH`
- [ ] Installed Retornatus (`uv tool install` or `uv sync` in this repo)
- [ ] Ran `retornatus init` in a target project
- [ ] Ran `retornatus wake` successfully
- [ ] Created a first Change with `change create`
- [ ] Know where the product contract lives: [prd/PRD.md](prd/PRD.md)

---

## Three pillars

| Problem | Pillar | One-line win |
| --- | --- | --- |
| Built the wrong thing | **Contract** | WHAT + constraints + DONE before execution |
| Called it done without proof | **Assurance** | Verdict from attributable Evidence, not agent self-report |
| Every chat starts from zero | **Memory / Learning** | `.retornatus/` + searchable index outlive the session |

### 1. Contract — stop “done” from meaning “I typed a lot”

**Without it:** acceptance criteria live in a chat bubble and evaporate.

**With it:** an active Contract is the authoritative obligation. Material change requires a new version — not silent mutation.

### 2. Assurance — “done” has to be observable

Evidence is attributable (tests, scans, human decisions, runtime observation). Assurance evaluates claims and returns:

| Verdict | Meaning |
| --- | --- |
| `SATISFIED` | Required evidence types present for claims |
| `NOT_SATISFIED` | Evidence present but claims unmet |
| `INCONCLUSIVE` | Required capability/evidence unavailable |

> Agent conclusion ≠ Evidence. A green suite is evidence, not proof of overall correctness.

### 3. Memory — return informed

Learnings are Markdown with structured metadata. Rules may be **proposed** from experience (Graduation → Rule Candidate) but **never** become authoritative without human validation.

> Learning informs; Rules constrain. Recurrence never creates authority automatically.

---

## How it works

```text
                    RETORNATUS
                         │
     ┌───────────────────┼───────────────────┐
     ▼                   ▼                   ▼
 Continuity          Governance          Environment
  (Memory)         Rule · Policy         Wake · Caps
                   Authority · Bounds    Adapters
                         │
                         ▼
                      CHANGE
         Demand · Situation · Contract
              Action · Task?
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
          Execution              Assurance
       (native agent)         Evidence → Verdict
              │
         Finding → Question → Action → Resolution
              │
              ▼
          Adaptation
     Learning · Skill · Rule Candidate → Human → Rule
```

| Layer | Responsibility |
| --- | --- |
| **CLI** | Intention-oriented commands (`init`, `wake`, `change`, `verify`, …) |
| **Application** | Change workflow, Assurance, Policy, Question loop, Adaptation |
| **Domain** | Pydantic models, IDs, relations, schema versioning |
| **Infrastructure** | Atomic file persistence, optimistic concurrency, SQLite FTS5, env adapters |

Invariant: **files persist truth; models validate truth; SQLite indexes and finds truth.**

---

## Environment adapters (native first)

Retornatus detects Cursor, Claude Code, Codex, or falls back to generic.

```bash
retornatus wake --bridges
```

When useful, adapters write **bridge projections** only (for example Cursor rules, `CLAUDE.md`, `AGENTS.md`). Canonical truth stays in `.retornatus/`.

| Environment | Native preference |
| --- | --- |
| Cursor | Rules / skills surfaces |
| Claude Code | `CLAUDE.md` / `.claude` |
| Codex | `AGENTS.md` / `.codex` |
| Generic | No bridge files required |

---

## What is enforced — and what is not

| Enforced / owned by Retornatus | Not Retornatus’s job (host / human) |
| --- | --- |
| Structure of Changes, Contracts, Evidence | Writing application code |
| Schema validation & atomic persistence | Replacing the IDE agent |
| Assurance verdicts from evidence types | Rebuilding sandboxes the host already has |
| Policy ALLOW / DENY / REQUIRE_HUMAN (basic) | Distributed locking / multi-tenant SaaS |
| Index rebuild after crash | Publishing to PyPI (pending) |

Honest scope: V1 is a **local harness**. It governs work and preserves continuity; it does not claim to be a full remote orchestration platform.

---

## Commands cheat sheet

Run from the project you want to govern (or pass `--path`).

| Command | What it does |
| --- | --- |
| `retornatus init` | Create `.retornatus/` tree + `config.toml` |
| `retornatus wake` | Reconstruct state, detect environment, rebuild index |
| `retornatus wake --bridges` | Also write native bridge files when detected |
| `retornatus doctor` | Diagnostics / readiness |
| `retornatus status` | Derived Change status projection |
| `retornatus change create …` | Demand → Situation → Contract → Action |
| `retornatus change learn …` | Record a Learning |
| `retornatus skill create --need "…"` | Create one specialization Skill (agent researches & fills) |
| `retornatus skill list` / `activate` / `evolve` / `export` | Skill lifecycle + native Cursor export |
| `retornatus run <action-id>` | Assemble ExecutionContext (does not run the agent) |
| `retornatus verify <change-id>` | Assurance over Contract DONE criteria |
| `retornatus inspect <id>` | Print Change / Action / Finding / Question / Evidence / Rule / Learning |
| `retornatus search <query>` | FTS5 search over the derived index |

```bash
retornatus --help
retornatus change create --help
```

---

## Explore the repository

| Path | What you find |
| --- | --- |
| [`src/retornatus/cli/`](src/retornatus/cli/) | Intention-oriented CLI |
| [`src/retornatus/domain/`](src/retornatus/domain/) | Pydantic domain models, IDs, relations |
| [`src/retornatus/application/`](src/retornatus/application/) | Change, Assurance, Policy, Question, Adaptation, Execution context |
| [`src/retornatus/infrastructure/`](src/retornatus/infrastructure/) | Persistence, SQLite index, environment adapters |
| [`src/retornatus/bootstrap/`](src/retornatus/bootstrap/) | `init` and `wake` |
| [`prd/PRD.md`](prd/PRD.md) | Product requirements (canonical V1) |
| [`tests/`](tests/) | Unit + dogfood E2E (M0–M12) |

Day-to-day governed state in a consumer project lives under **`.retornatus/`** (`changes/`, `governance/`, `adaptation/`, `index/`, `runtime/`).

---

## Documentation

| Area | Where |
| --- | --- |
| **Product definition** | [prd/PRD.md](prd/PRD.md) |
| **Philosophy & invariants** | PRD §§2, 72 |
| **Filesystem layout** | PRD §52 |
| **CLI intentions** | PRD §62 · this README |
| **Milestones M0–M12** | PRD §68 |

Deeper narrative guides (tutorials, FAQ) can grow under `docs/` as the product hardens — the PRD is the source of truth today.

---

## Contributing

Improvements that preserve **native-first** and **complexity must be earned** are welcome.

```bash
uv sync
uv run pytest -q
```

Prefer small milestones over speculative engines. Architecture changes should cite a concrete failure mode (see PRD §71).

---

## Credits

*Credits and upstream attributions will be added here.*

If you contributed ideas, patterns, or references used to shape Retornatus, send them for inclusion in this section.

Related prior work in this ecosystem: [spec-guardrails](https://github.com/luizssantiago92/spec-guardrails) (governed spec-driven development for AI coding agents).

---

## License

MIT — see [LICENSE](LICENSE) (to be added alongside this repository’s packaging metadata).

[↑ Back to top](#retornatus)
