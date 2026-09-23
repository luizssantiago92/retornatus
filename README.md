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

PyPI: [`retornatus`](https://pypi.org/project/retornatus/) **1.2.x**

[What it is](#what-it-is) · [Install](#1-install) · [Verify](#2-verify-readiness) · [First change](#3-run-your-first-change) · [Checklist](#getting-started-checklist) · [How it works](#how-it-works) · [What you get](#what-you-get--and-why-it-helps) · [Commands](#commands-cheat-sheet) · [Docs](#documentation) · [Credits](#credits)

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
| 1 | Describe what you want | **Requirements analysis** (`change elicit`) — if questions remain, answer them in chat; size the work (`change classify`) |
| 2 | Agree how you’ll know it’s done | Create/activate the finish line → check it (`gate contract`) |
| 3 | Let it build | Work the next ready step (`loop next` / `run`); split into jobs only when useful |
| 4 | Demand proof | Attach proof to the goals → done check (`verify`) |

If the agent jumps straight to code: *Stop. Finish Situation (requirements) + Contract (and pass `gate contract`) before the build sprint.*

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

A focused software-construction cycle — durable files under `.retornatus/`, gates as brakes:

```text
Understand  →  Agree     →  Build              →  Prove           →  Learn
Situation      Contract     Action (+ Tasks)      Evidence            Learning
(requirements) (WHAT+DONE)  (agent writes code)   + verify            (+ Rules?)
```

| Step | In plain words | Command / artifact |
| --- | --- | --- |
| **Understand** | Before coding, clarify what “login” / “fix X” actually means | `change elicit` → Situation |
| **Agree** | Write the finish line you both accept | Contract → `gate contract` |
| **Build** | Implement under that agreement | Action / Tasks → `loop next` / `run` |
| **Prove** | “Done” needs evidence, not a chat summary | Evidence → `verify` |
| **Learn** | Keep what mattered for the next Change | Learning / optional Rules |

When the ask is fuzzy, `change elicit` exits `1` and lists **focused questions** (with options). The agent should ask them in chat; you answer; record with `--answer TOPIC=…`. Clear asks can skip straight to a Contract.

Optional: `change classify` picks QUICK / STANDARD / COMPLEX so ceremony matches risk. Skills load only when needed.

**Status / overview** are projections. If they disagree with files, **the files win**.

---

## What you get — and why it helps

### Requirements analysis (Situation)

**Without it:** “Add login” becomes three different products in three chats.

**With Situation:** The harness surfaces material questions (actors, scope, out of scope, how you’ll know it worked), reads kickoff files when present, and refuses to pretend the Contract is ready until those answers exist.

### Memory — the repo remembers

Changes, Contracts, Evidence, and Learnings live under `.retornatus/` in git. `wake` rebuilds continuity. Chat is a window; **git is the source of truth**.

### Proof before “done”

A Contract states WHAT and DONE. Evidence binds to those claims. `verify` returns SATISFIED / NOT_SATISFIED / INCONCLUSIVE. Gates return non-zero = **STOP**.

### Ceremony matches risk

QUICK for a typo; STANDARD for a normal feature; COMPLEX when security, payments, or high novelty need more depth.

### Hub + Skills

The hub skill is the map every turn. At most one specialization Skill while executing — research current sources when needed, not a mega-pack every message.

**Go deeper:** [How it works](https://luizssantiago92.github.io/retornatus/guide/how-it-works.html) · [Gates](https://luizssantiago92.github.io/retornatus/guide/gates.html) · [Memory](https://luizssantiago92.github.io/retornatus/guide/memory.html) · [Skills](https://luizssantiago92.github.io/retornatus/guide/skills.html)

---

## Commands cheat sheet

| Intent | Command |
| --- | --- |
| Continuity | `wake`, `doctor`, `status`, `project-init`, `integrate` |
| Requirements / lane | `change elicit` (`--answer`, `--write`), `change classify`, `change create`, `change activate` |
| Dashboard | `change overview` |
| Next work | `loop next` · `task start\|complete\|fail\|reopen` |
| Skills | `skill need`, `skill create`, `skill activate`, `skill export` |
| Proof | `evidence add --claim …`, `gate *`, `verify` |
| Learning | `change learn`, `lesson from-gate` |
| Human boundary | `decision record`, `rule propose\|activate` |

Full map: [CLI](https://luizssantiago92.github.io/retornatus/guide/cli.html) · hub skill after `integrate`.

---

## What’s new (1.2.1)

- **Prompt intake** — `intake analyze` stages a freeform request against `.retornatus/`, proposes Skill only with human `CREATE=yes`  
- **Two Skill worlds** — analyzed intake (controlled) or manual `skill create`  
- **Early skill need** — `skill need --prompt` without requiring an Action  

## What’s new (1.2.0)

- **Situation as requirements analysis** — focused questions with options, `--answer` / `--write`, kickoff discovery  
- Focused software cycle in hub/README: Understand → Agree → Build → Prove → Learn  

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

## Credits

Ideas are credited by **influence**, not by superficial similarity. Retornatus does not claim novelty for established software-engineering patterns; its contribution is how those guarantees are separated, constrained, and composed.

### Direct predecessor — Spec Guardrails

**[Spec Guardrails](https://github.com/luizssantiago92/spec-guardrails)** (MIT) is the **direct predecessor** of Retornatus.

Retornatus is a **separate successor architecture** informed by building and dogfooding Spec Guardrails. It is **not** a fork, rename, or line-by-line rewrite.

| Proven concern (from Spec Guardrails dogfooding) | How Retornatus carries the guarantee |
| --- | --- |
| Repo-native governance | Durable state under `.retornatus/` |
| Planning before opportunistic coding | Situation (requirements analysis) → Contract before the build sprint |
| Gates / brakes | Mechanical STOP checks (non-zero exit) |
| Evidence before “done” | Claim-bound Evidence → Assurance / `verify` |
| Persistent memory | Changes, Learnings, Rules in git; `wake` continuity |
| Human checkpoints | Human Decisions for consequential Rules |
| Environment awareness | Hub skill + host adapters — agent still executes |

**Original work in Retornatus:** Python domain model and CLI, `.retornatus/` layout, Demand / Situation / Contract / Action (plus Finding / Question / Resolution), Evidence separated from Assurance, complexity lanes (QUICK / STANDARD / COMPLEX), on-demand specialization Skills with research gates, doctor Process vs Brakes, overview / ops / lessons loops, and the public docs site.

**Transitive lineage:** Spec Guardrails itself credits upstream open-source work (spec-driven phases, task graphs, loop engineering, harness vocabulary, and related tools). Those influences arrive **through** Spec Guardrails unless Retornatus independently revisited them — see the full provenance write-up.

**Full credits & lineage:** [credits on the website](https://luizssantiago92.github.io/retornatus/credits.html) · [credits-and-lineage.md](docs/credits-and-lineage.md) · Spec Guardrails’ own [credits](https://github.com/luizssantiago92/spec-guardrails/blob/main/docs/guide/credits.md)

---

## License

MIT — see [LICENSE](LICENSE).
