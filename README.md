# Retornatus

<p align="center">
  <img src="docs/assets/retornatus-mascot.webp" alt="Ember — Retornatus mascot" width="280" />
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
| Whole playbook pasted every turn | Hub + at most one specialization Skill per turn |
| Agent invents a Skill from a vague prompt | `intake analyze` proposes; you confirm `CREATE=yes` |
| Lessons vanish when the tab closes | Learnings (and optional Rules) stay in the repo |

Package **1.4.1** is on [PyPI](https://pypi.org/project/retornatus/). Maintainer release steps: [CONTRIBUTING](CONTRIBUTING.md#releases).

[What it is](#what-it-is) · [Install](#1-install) · [Verify](#2-verify-readiness) · [First change](#3-run-your-first-change) · [Checklist](#getting-started-checklist) · [How it works](#how-it-works) · [What you get](#what-you-get-and-why-it-helps) · [Commands](#commands-cheat-sheet) · [Cloud agents](#cloud-and-remote-agents) · [Docs](#documentation) · [Credits](#credits)

---

## What it is

A **governance harness** for AI-assisted software work — not an IDE, not an LLM runtime, and not an agent marketplace. The host agent still writes code; Retornatus structures obligations, proof, and memory under **`.retornatus/`**.

After install, work moves through a durable loop you can inspect in files:

**Demand** → **Situation** (requirements) → **Contract** (WHAT + DONE) → **Action** (+ **Tasks** when needed) → **Evidence** → **Assurance** → **Learning**

Along that loop the harness also:

- Sizes ceremony to risk (**QUICK** / **STANDARD** / **COMPLEX**)
- Surfaces **focused questions** when the ask is fuzzy (`change elicit`)
- Scores readiness (**Process** vs **Brakes**) via `doctor`
- Stages freeform chat into Skill proposals only with **human confirmation** (`intake analyze`)
- Loads at most **one** specialization Skill when needed (`skill need` / `skill create`)

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

**Go deeper:** [Quick start](https://luizssantiago92.github.io/retornatus/guide/quick-start.html) · [Environments](https://luizssantiago92.github.io/retornatus/guide/environments.html) · [Cloud agents](https://luizssantiago92.github.io/retornatus/guide/cloud-agents.html)

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
| 1 | Describe what you want | Optional **intake** staging (`intake analyze`) and/or **requirements analysis** (`change elicit`) — answer focused questions in chat; size the work (`change classify`) |
| 2 | Agree how you’ll know it’s done | Create/activate the finish line → check it (`gate contract`) |
| 3 | Let it build | Work the next ready step (`loop next` / `run`); specialize only if needed (`skill need` → human confirm → `skill create`) |
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

Optional: `change classify` picks QUICK / STANDARD / COMPLEX so ceremony matches risk.

For a freeform chat prompt that might need specialization, prefer **`intake analyze`**: it stages the ask against `.retornatus/`, proposes a Skill only when you answer `CREATE=yes`, and never auto-creates from chat alone. Early signal without creating: `skill need --prompt "…"`.

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

Test, security-test, build, and lint results only count when Retornatus ran the command (`evidence run … -- <command>`). The record stores argv, exit code, timing, a SHA-256 of combined stdout/stderr, and the git HEAD (when the directory is a repository). `evidence add` is self-reported: for those types `verify` marks the evidence **UNVERIFIED** and does not exit 0. Narrative notes (`review_result`, `repository_observation`) can still be recorded with `evidence add` and are labeled self-reported. While migrating, `verify --allow-self-reported` or `[assurance] allow_self_reported = true` in `.retornatus/config.toml` restores the old acceptance. A recorded commit that no longer matches HEAD is a warning, not a failure — unless the owner named the commands that count.

**Required checks.** Put the real commands in `[assurance] required_checks` (`name` + `run` argv, optional `types`). `verify` then accepts execution evidence only when the argv matches one of those checks exactly, the exit code is 0, the recorded commit is the current HEAD, and the worktree has no uncommitted source changes. `evidence run -- true` does not pass. `verify --run-checks` and `checks run` execute the declared commands through the same capture path. `allow_self_reported` does not bypass a configured check.

**Freshness.** Uncommitted or untracked edits to a claim subject path make that evidence stale. Execution types fail by default; narrative types warn. Set `[assurance] uncommitted_changes` to `"fail"` or `"warn"` to override.

**Diff gates and hooks.** `gate suppressions` stops newly added skip and ignore markers. `gate scope` compares the git diff with the change’s Task resources (denied paths always fail; sensitive paths need a satisfied `review_result` or `security_test` claim). `hooks install` wires both into pre-commit, and a commit-msg hook that reads the message from `$1`.

### Ceremony matches risk

QUICK for a typo; STANDARD for a normal feature; COMPLEX when security, payments, or high novelty need more depth.

### Hub + Skills (human-controlled)

The hub skill is the map every turn. At most one specialization Skill while executing — research current sources when needed, not a mega-pack every message.

Two Skill worlds:

| Path | When | Control |
| --- | --- | --- |
| **Analyzed intake** | Freeform prompt may need specialization | `intake analyze` → human answers → `--create-skill` only with `CREATE=yes` |
| **Manual** | You explicitly ask for a Skill | `skill create --need "…"` |

`skill need --prompt` can flag need early (no Action required). Agents must not invent Skills from a vague prompt without your confirmation.

**Go deeper:** [How it works](https://luizssantiago92.github.io/retornatus/guide/how-it-works.html) · [Gates](https://luizssantiago92.github.io/retornatus/guide/gates.html) · [Memory](https://luizssantiago92.github.io/retornatus/guide/memory.html) · [Skills](https://luizssantiago92.github.io/retornatus/guide/skills.html)

---

## Commands cheat sheet

| Intent | Command |
| --- | --- |
| Continuity | `wake`, `doctor`, `status`, `project-init`, `integrate` |
| Requirements / lane | `change elicit` (`--answer`, `--write`), `change classify`, `change create`, `change activate` |
| Prompt intake | `intake analyze` (`--answer`, `--create-skill` with human `CREATE=yes`) |
| Dashboard | `change overview` |
| Next work | `loop next` · `task start` / `complete` / `fail` / `reopen` |
| Skills | `skill need` (`--prompt` / `--action`), `skill create`, `skill activate`, `skill export` |
| Proof | `evidence run --claim … -- <command>` (tests/build/lint), `evidence add --claim …` (notes), `checks run`, `gate *` (including `suppressions` and `scope`), `verify` / `verify --run-checks` / `verify --allow-self-reported` / `verify --receipt`, `receipt keygen` / `sign` / `verify` |
| Hooks | `hooks install` / `remove` / `status` (pre-commit + commit-msg) |
| Attempt budget | `action budget --max N` · `gate budget` |
| Learning | `change learn`, `lesson from-gate` |
| Human boundary | `decision record`, `rule propose` / `activate` · `policy check` |

Full map: [CLI](https://luizssantiago92.github.io/retornatus/guide/cli.html) · hub skill after `integrate`.

---

## Verify receipts

`verify --receipt` and `receipt sign` write an **Ed25519** receipt under `.retornatus/assurance/receipts/`. The signature covers the verify verdict. `receipt verify` checks it.

**What a receipt proves.** Someone who held the private key signed that result. It does not prove the agent was sandboxed, and it is not a receipt network.

**Where the keys live.**

| Material | Where | Committed? |
| --- | --- | --- |
| Public key | `.retornatus/keys/<key-id>.pub` | Yes. `<key-id>` is the SHA-256 fingerprint of the raw public key |
| Private key | User config directory, or `RETORNATUS_SIGNING_KEY` (PEM, base64, or even-length hex) | **No.** Never inside the repo, and never copied there from the environment |

`receipt keygen` writes the public key into the repo and the private key under the user config dir (`$XDG_CONFIG_HOME/retornatus` or `%APPDATA%\retornatus`). `receipt keygen --print` prints the private key instead, for a CI secret. `retornatus init` and `receipt keygen` warn on stderr if git already tracks a `*.pem` or `*.key` file.

**Threat model.** An agent that can read the private key can produce a valid signature. Keep `RETORNATUS_SIGNING_KEY` and the config-dir key **out of the agent's environment**. Verification needs only the committed public key, so a fresh clone can check a receipt without the secret.

**CI.** Store the private key as a GitHub Actions secret and sign in CI, where the agent that edits the repo does not see it:

```yaml
- name: Sign verify receipt
  env:
    RETORNATUS_SIGNING_KEY: ${{ secrets.RETORNATUS_SIGNING_KEY }}
  run: retornatus verify C-0001 --receipt
```

Anyone who clones the repo (the public key is already in `.retornatus/keys/`) can run `retornatus receipt verify path/to/receipt.json`.

**Legacy HMAC.** Older `HMAC-SHA256` receipts still verify only on a machine that has the old local key. `receipt verify` reports them as `legacy_hmac` with `portable: false` and prints a deprecation warning. That key is not written into the repo.

CLI mistakes print `error: …` instead of a traceback. An invalid id such as `verify ../../../tmp` exits `2`. Search text with quotes or hyphens is matched as literal words (it does not crash). Gates and `verify` still use `0` for pass / SATISFIED and `1` for STOP / not SATISFIED.

---

## What’s new (1.4.0)

- **Required checks** — when `[assurance] required_checks` is set, `verify` accepts execution evidence only for those commands (`verify --run-checks`, `checks run`)
- **Cloud and remote agents** — install the CLI on the clean VM, run `hooks install` on every fresh clone, and leave receipts unsigned
- **PR gates** — the consumer workflow pins `retornatus==1.4.1` and runs blocking `verify`, `gate suppressions`, and `gate scope`
- **Trusted Publishing** — tag `v*` on `main` publishes after tests, a distribution contents check, and a matching changelog section
- **Supply chain** — GitHub Actions are pinned to commit SHAs; `SECURITY.md` and CodeQL cover private reports and Python analysis

## What’s new (1.3.0)

- **Verify receipts** — Ed25519 signature checked with the committed public key; private key stays outside the repo (`verify --receipt`, `receipt verify`). Legacy HMAC receipts are `legacy_hmac` and not portable  
- **Action attempt budget** — `action budget --max N` + `gate budget` stop runaway retries  
- **AGENTS.md** map for host agents + CI check that docs HTML stays in sync with markdown  
- **From Spec Guardrails** migration page + **Landscape** comparison with adjacent harnesses  

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

## Cloud and remote agents

A cloud or remote agent (Cursor cloud agent, Codex, Claude Code on a VM, a CI sandbox) starts clean. Install the CLI on that machine. Git does not version hooks, so every fresh clone runs `retornatus hooks install`. Leave receipts unsigned: the private signing key stays off the agent VM. The enforcement is the GitHub pull-request workflow (`verify`, `gate suppressions --base`, `gate scope --base`), wherever the agent ran.

```bash
uv tool install --force git+https://github.com/luizssantiago92/retornatus.git
export PATH="$HOME/.local/bin:$PATH"
retornatus hooks install
retornatus hooks status
retornatus doctor
```

[`templates/ci/retornatus-pr.yml`](templates/ci/retornatus-pr.yml) pins `uv tool install "retornatus==1.4.1"`. That release includes `hooks install` and the diff gates. Full notes: [Cloud agents](docs/guide/Cloud-agents.md).

---

## Documentation

| Want… | Go here |
| --- | --- |
| Product story (non-jargon) | [Website](https://luizssantiago92.github.io/retornatus/) |
| First ten minutes | [Quick start](https://luizssantiago92.github.io/retornatus/guide/quick-start.html) |
| Cloud / remote agents | [Cloud agents](https://luizssantiago92.github.io/retornatus/guide/cloud-agents.html) |
| Full technical guide | [Docs hub](https://luizssantiago92.github.io/retornatus/guide/) |
| Concepts | [Overview](https://luizssantiago92.github.io/retornatus/guide/overview.html) · [Concepts](https://luizssantiago92.github.io/retornatus/guide/concepts.html) |
| Coming from Spec Guardrails | [From Spec Guardrails](https://luizssantiago92.github.io/retornatus/guide/from-spec-guardrails.html) |
| Adjacent harnesses | [Landscape](https://luizssantiago92.github.io/retornatus/guide/landscape.html) |
| Product requirements | [PRD](docs/archive/PRD.md) |
| Credits & lineage | [Credits](https://luizssantiago92.github.io/retornatus/credits.html) |

Markdown sources for editors: [`docs/guide/`](docs/guide/README.md). GitHub Pages generates the HTML from those files. To preview locally, run `python scripts/build_docs_html.py` (the output is gitignored).

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

**Original work in Retornatus:** Python domain model and CLI, `.retornatus/` layout, Demand / Situation / Contract / Action (plus Finding / Question / Resolution), Evidence separated from Assurance, complexity lanes (QUICK / STANDARD / COMPLEX), on-demand specialization Skills with research gates, human-controlled prompt intake (`intake analyze`), doctor Process vs Brakes, overview / ops / lessons loops, and the public docs site.

**Transitive lineage:** Spec Guardrails itself credits upstream open-source work (spec-driven phases, task graphs, loop engineering, harness vocabulary, and related tools). Those influences arrive **through** Spec Guardrails unless Retornatus independently revisited them — see the full provenance write-up.

**Full credits & lineage:** [credits on the website](https://luizssantiago92.github.io/retornatus/credits.html) · [credits-and-lineage.md](docs/credits-and-lineage.md) · Spec Guardrails’ own [credits](https://github.com/luizssantiago92/spec-guardrails/blob/main/docs/guide/credits.md)

---

## License

MIT — see [LICENSE](LICENSE).
