# Retornatus

<p align="center">
  <img src=".assets/retornatus-mascot.png" alt="Retornatus Seedcore mascot" width="280" />
</p>

<p align="center">
  <strong>Keep AI coding agents honest — with goals, memory, and proof.</strong><br />
  <em>Govern the work. Bound the agent. Verify the outcome.</em>
</p>

<p align="center">
  <a href="https://luizssantiago92.github.io/retornatus/"><strong>Website →</strong></a>
  ·
  <a href="https://luizssantiago92.github.io/retornatus/guide/">Docs</a>
  ·
  <a href="https://luizssantiago92.github.io/retornatus/guide/quick-start.html">Quick start</a>
  ·
  <a href="https://pypi.org/project/retornatus/">PyPI</a>
</p>

[![Website](https://img.shields.io/badge/website-live-14b8a6?style=flat)](https://luizssantiago92.github.io/retornatus/)
[![PyPI version](https://img.shields.io/pypi/v/retornatus.svg)](https://pypi.org/project/retornatus/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/luizssantiago92/retornatus/actions/workflows/ci.yml/badge.svg)](https://github.com/luizssantiago92/retornatus/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Repo-native governance harness** for AI coding agents (Cursor, Claude Code, Codex, and similar).

Agents are fast — and optimistic. They ship code, summarize what they *think* they did, and move on. Retornatus installs a **repeatable contract** into your repo: agree on the finish line in writing, execute under that agreement, and close only when **evidence** supports the goal. Intent, progress, and lessons live under **`.retornatus/` in git**, not in a chat scrollback.

Your coding agent still **writes the code**. Retornatus **governs the loop and keeps the record**.

| Without Retornatus | With Retornatus |
| --- | --- |
| Jumps to code and says “done” | Written finish line first; “done” needs evidence |
| Each chat starts from zero | `.retornatus/` survives sessions and handoffs |
| Same ceremony for a typo and a payment flow | Complexity lanes match depth to risk |
| Whole playbook pasted every turn | Hub + at most one specialization skill per turn |
| Lessons vanish when the tab closes | Learnings (and optional Rules) stay in the repo |

PyPI: [`retornatus`](https://pypi.org/project/retornatus/) **1.1.x**

[What it is](#what-it-is) · [Install](#1-install) · [Verify](#2-verify-readiness) · [First change](#3-run-your-first-change) · [Checklist](#getting-started-checklist) · [How it works](#how-it-works) · [Mechanisms](#core-mechanisms--why-each-exists) · [Commands](#commands-cheat-sheet) · [Docs](#documentation)

---

## What it is

A **governance layer** for AI-assisted software work — not an IDE, not an LLM runtime, and not an agent marketplace.

After install, work moves through a durable loop you can inspect in files:

**Demand** → **Situation** → **Contract** (WHAT + DONE) → **Action** (+ **Tasks** when needed) → **Evidence** → **Assurance** → **Learning**

You approve product intent and consequential Rules. The agent implements. Push, merge, and publish stay on your terms ([git governance](https://luizssantiago92.github.io/retornatus/guide/git-governance.html)).

---

## 1. Install

You need **Python 3.11+**. We recommend [`uv`](https://docs.astral.sh/uv/) (installs Python CLIs quickly). If you do not have `uv` yet:

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then run these in **your application repository** (the project the agent should change — not necessarily this harness repo):

```bash
# Install the Retornatus CLI once on your machine
uv tool install retornatus

cd /path/to/your-app

# Create .retornatus/ (config + durable memory layout)
retornatus init

# Install the hub skill into your agent environment (e.g. .cursor/skills/)
retornatus integrate

# Readiness check — Process vs Brakes scores
retornatus doctor
```

| Command | What it does |
| --- | --- |
| **`uv tool install retornatus`** | Puts the `retornatus` CLI on your PATH via uv |
| **`init`** | Creates `.retornatus/config.toml` and the canonical folders for Changes, Evidence, Learnings |
| **`integrate`** | Projects the **hub skill** so your AI agent knows the Retornatus loop |
| **`doctor`** | Audits readiness — **Process** (healthy workflow) vs **Brakes** (hard STOPs / gates) |

One-shot without a global install: `uvx retornatus --help`. Package page: [PyPI](https://pypi.org/project/retornatus/).

Day to day you work in **agent chat**; the agent (following the hub skill) calls the CLI when a gate or record is needed.

**Go deeper:** [Quick start](https://luizssantiago92.github.io/retornatus/guide/quick-start.html) · [Environments](https://luizssantiago92.github.io/retornatus/guide/environments.html)

---

## 2. Verify readiness

Re-run `doctor` after upgrades or machine changes. You are ready when:

- `.retornatus/` exists and `init` has been run in this project  
- The hub skill is visible to your agent (after `integrate`)  
- `doctor` is not hard-stopping on “not initialized”  
- Your AI coding agent can open the project and follow the hub skill  

For brownfield repos, also consider `retornatus project-init` and `retornatus wake --bridges` so existing context is captured before the first Change.

---

## 3. Run your first change

Open your AI coding agent in the project and ask for a concrete goal, for example:

> Create a Retornatus Change for GET /health returning 200. Contract and gates before code.

Ask it to follow the installed **Retornatus hub skill**. Prefer chat for product intent; use the CLI when you want mechanical gates yourself.

| Step | You do | Agent / CLI does |
| --- | --- | --- |
| 1 | Describe the demand | Optional `change classify` / `change elicit` for Situation |
| 2 | Agree the finish line | `change create` (+ activate Contract) → `gate contract` |
| 3 | Let it build under the Contract | `loop next` / `run` + Tasks when useful |
| 4 | Demand proof | `evidence add --claim …` → `gate evidence` → `verify` |

If the agent jumps straight to code: *Stop. Finish Situation + Contract (and pass `gate contract`) before the build sprint.*

**Go deeper:** [Quick start](https://luizssantiago92.github.io/retornatus/guide/quick-start.html) · [Tutorials](https://luizssantiago92.github.io/retornatus/guide/tutorials/) · [How it works](https://luizssantiago92.github.io/retornatus/guide/how-it-works.html)

---

## Getting started checklist

- [ ] Python 3.11+ available (`python --version`)
- [ ] Ran `uv tool install retornatus` (or use `uvx`)
- [ ] In **your app** repo: `retornatus init` → `integrate` → `doctor`
- [ ] Opened the project in your AI coding agent and confirmed the hub skill is visible
- [ ] Asked for a written Change / Contract before implementation
- [ ] Know where docs live: [Website](https://luizssantiago92.github.io/retornatus/) · [Docs hub](https://luizssantiago92.github.io/retornatus/guide/)

Stuck? [Quick start](https://luizssantiago92.github.io/retornatus/guide/quick-start.html) · [FAQ](https://luizssantiago92.github.io/retornatus/guide/faq.html)

---

## How it works

High-level lifecycle — durable files under `.retornatus/`, with gates as brakes:

```text
classify? (QUICK / STANDARD / COMPLEX)
      ↓
elicit Situation? (when the ask is fuzzy)
      ↓
Contract (WHAT + constraints + DONE) → activate → gate contract
      ↓
Action (+ Tasks when decomposition helps)
      ↓
Skill? (research + activate only when skill need says so)
      ↓
Execute in the host agent (run / loop next)
      ↓
Evidence bound to Claims → gate evidence → verify (Assurance)
      ↓
Learning (and optional Rule Candidates → Human Decision)
```

**Status / overview** are projections. If they disagree with files, **the files win**.

---

## Core mechanisms — why each exists

### 1. Memory — the repo remembers so you do not have to

**Without memory:** Every new session starts cold. You re-paste context, re-explain decisions, and hope the model does not contradict last week’s architecture chat.

**With `.retornatus/`:** Changes, Contracts, Evidence, Questions, and Learnings are files you can diff and review. `wake` rebuilds continuity (and an optional search index) from those files. Chat is a window; **git is the source of truth**.

| Without `.retornatus/` | With `.retornatus/` |
| --- | --- |
| Chat is the source of truth | Git is the source of truth |
| Handoff = long message | Handoff = `wake` + open the Change |
| Same mistake twice | Learnings (and Rules after Human Decision) constrain the next run |
| “What did we decide?” | Inspect the Change folder / `change overview` |

The index under `.retornatus/index/` is **disposable** — delete and `retornatus wake` to rebuild. Canonical truth stays in the markdown/JSON artifacts.

**Go deeper:** [Memory](https://luizssantiago92.github.io/retornatus/guide/memory.html)

---

### 2. Contract, Evidence, Assurance — “done” has to be checkable

**Without it:** “Done” is a confident paragraph in chat. Nobody can re-check it next week.

**With Retornatus:**

- A **Contract** states WHAT must be true and what DONE means (claims you can test)  
- **Evidence** is attributable proof **bound to those claims** (`evidence add --claim …`)  
- **Assurance** / `verify` asks whether evidence actually supports the claims — SATISFIED, NOT_SATISFIED, or INCONCLUSIVE  
- **Gates** return non-zero = **STOP** until the artifact is fixed  

| Moment | What you gain |
| --- | --- |
| Before the build sprint | Shared finish line (`gate contract`) |
| During / after implementation | Proof tied to claims, not vibes |
| Before calling the Change done | `verify` / Assurance verdict you can trust across agents |

> Gates turn “trust the agent” into “the agent has to prove it.”

**Go deeper:** [Gates](https://luizssantiago92.github.io/retornatus/guide/gates.html) · [Concepts](https://luizssantiago92.github.io/retornatus/guide/concepts.html)

---

### 3. Complexity lanes — ceremony matches risk

Not every change deserves the same ritual. `change classify` (and optional `--lane`) steers **QUICK / STANDARD / COMPLEX**:

| Lane | Typical work | Ceremony |
| --- | --- | --- |
| **QUICK** | Typo, docs, tiny localized fix | Short Contract; often skip Skill; light Evidence |
| **STANDARD** | Normal feature | Full Change loop + gates; Skill optional |
| **COMPLEX** | Security, payment, migration, high novelty | Fuller Situation; Skill research more often; stricter proof |

**Without lanes:** A one-line copy tweak and a payment integration get the same bureaucratic weight (or the same chaos).

**With lanes:** Depth is **earned**. You still get a finish line and proof — you do not paste the entire playbook for a typo.

**Go deeper:** [Overview — how much ceremony?](https://luizssantiago92.github.io/retornatus/guide/overview.html) · CLI `change classify`

---

### 4. Actions, Tasks, and the loop — progress you can steer

An **Action** is a bounded unit of work under the Contract. **Tasks** appear when decomposition helps (explicit dependencies and resources — declaration order is **not** an automatic dependency chain).

| Mechanism | Advantage |
| --- | --- |
| **`loop next`** | Shows the next ready unit of work (projection from durable state) |
| **`task start / complete / …`** | Lifecycle you can audit; failures are first-class |
| **`change overview` / `status`** | One-screen view of claims, evidence, tasks, and what’s next |

**Without Tasks:** Big Changes stay as one vague blob — hard to parallelize or resume.  
**With Tasks (when needed):** Clear ownership of slices; the loop can advance what is actually ready.

**Go deeper:** [How it works](https://luizssantiago92.github.io/retornatus/guide/how-it-works.html) · [CLI](https://luizssantiago92.github.io/retornatus/guide/cli.html)

---

### 5. Hub skill and specialization Skills — focus without a mega-pack

**Hub skill** (installed by `integrate`): the map every turn — Demand→Assurance, gates, git tiers. Load **at most one** specialization Skill while executing.

**Specialization Skills** (`skill need` → research → `skill activate`): on-demand depth for *this* problem (current sources in RESEARCH), not a stale mega-pack pasted every time.

| Without this split | With hub + Skills |
| --- | --- |
| Entire methodology dumped into context | Hub stays small; specialize only when needed |
| Skills never refreshed | Research gate expects real sources (or a governed bypass) |
| Typo fix loads security playbooks | `skill need` can skip ceremony for trivial Actions |

**Go deeper:** [Skills](https://luizssantiago92.github.io/retornatus/guide/skills.html)

---

### 6. Doctor, lessons, ops — keep the harness honest

| Tool | Advantage |
| --- | --- |
| **`doctor`** | Separates “process needs care” from hard brakes |
| **`lesson from-gate`** | A failed gate can become lasting guidance (optional Rule Candidate) |
| **`ops list / run`** | Light hygiene loops on demand — not the construction path |

**Go deeper:** [FAQ](https://luizssantiago92.github.io/retornatus/guide/faq.html) · [Governance](https://luizssantiago92.github.io/retornatus/guide/governance.html)

---

## Commands cheat sheet

| Intent | Command |
| --- | --- |
| Continuity | `wake`, `doctor`, `status`, `project-init`, `integrate` |
| Lane / Situation | `change classify`, `change elicit`, `change create`, `change activate` |
| Dashboard | `change overview` |
| Next work | `loop next` · `task start\|complete\|fail\|reopen` |
| Skills | `skill need`, `skill create`, `skill activate`, `skill export` |
| Proof | `evidence add --claim …`, `gate *`, `verify` |
| Learning | `change learn`, `lesson from-gate` |
| Human boundary | `decision record`, `rule propose\|activate` |

Full map: [CLI](https://luizssantiago92.github.io/retornatus/guide/cli.html) · hub skill after `integrate`.

---

## What’s new (1.1.x)

- **Change overview** — claims, evidence, tasks, and next work in one view  
- **Doctor scores** — process health vs hard brakes  
- **Lessons from gates** — failed checks can guide the next return  
- **Ops loops** — optional hygiene scans  
- **Public site** — product landing + full HTML docs on GitHub Pages  

---

## Documentation

| Want… | Go here |
| --- | --- |
| Product story (non-jargon) | [Website](https://luizssantiago92.github.io/retornatus/) |
| First ten minutes | [Quick start](https://luizssantiago92.github.io/retornatus/guide/quick-start.html) |
| Full technical guide | [Docs hub](https://luizssantiago92.github.io/retornatus/guide/) |
| Concepts | [Overview](https://luizssantiago92.github.io/retornatus/guide/overview.html) · [Concepts](https://luizssantiago92.github.io/retornatus/guide/concepts.html) |
| Product requirements | [PRD](prd/PRD.md) |
| Credits & lineage | [Credits](https://luizssantiago92.github.io/retornatus/credits.html) |

Markdown sources for editors: [`docs/guide/`](docs/guide/README.md). After editing them, run `python scripts/build_docs_html.py` so the site stays in sync.

---

## License

MIT — see [LICENSE](LICENSE).
