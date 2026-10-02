# Retornatus

<p align="center">
  <a href="https://luizssantiago92.github.io/retornatus/"><img src="https://raw.githubusercontent.com/luizssantiago92/retornatus/main/docs/assets/retornatus-mascot-readme.webp" alt="Retornatus mascot: a chrome AI agent in a black suit adjusting sunglasses, with a teal ouroboros serpent and an orange comet flame" width="420" height="231" /></a>
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
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/luizssantiago92/retornatus/blob/main/LICENSE)

Agents are fast — and optimistic. They ship code, summarize what they think they did, and move on. Retornatus keeps the finish line, the proof, and the notes in **`.retornatus/` inside git**, so the next session does not start from zero. Your coding agent still **writes the code**.

| Without Retornatus | With Retornatus |
| --- | --- |
| Jumps to code and says “done” | Written finish line first; “done” needs evidence |
| Each chat starts from zero | `.retornatus/` survives sessions and handoffs |
| Same ceremony for a typo and a payment flow | Depth matches the risk |
| The whole manual pasted every turn | One short map each turn; extra guidance only when the task needs it |
| Agent invents a procedure from a vague prompt | You confirm before a new procedure is saved |
| The agent stops when it feels finished | Optional hooks carry the open goal into the session, the edit, and the end of the turn |
| Lessons vanish when the tab closes | Notes (and optional rules you accept) stay in the repo |

Package **1.9.0** is on [PyPI](https://pypi.org/project/retornatus/).

[What it is](#what-it-is) · [30 seconds](#see-it-in-30-seconds) · [What’s new](#whats-new) · [Quick start](#quick-start) · [Presets](#presets) · [How it works](#how-it-works) · [What you get](#what-you-get--and-why-it-helps) · [Hooks](#agent-hooks) · [Docs](#documentation)

## See it in 30 seconds

A Change for `GET /health` already has a self-reported test note. That note does not count. Record the command, then verify again. Trimmed from a real run:

```console
$ retornatus verify C-0001
C-0001/E-001 type=test_result provenance=self_reported status=UNVERIFIED
{
  "verdict": "NOT_SATISFIED",
  "rationale": "Unverified claims (self-reported execution evidence does not satisfy): C-0001/claim-done-1. Re-record with `evidence run` or pass --allow-self-reported."
}

$ retornatus evidence run -c C-0001 -t test_result -s "/health" \
    --claim C-0001/claim-done-1 -- python3 -c 'print("ok")'
Recorded C-0001/E-002
provenance=executed exit_code=0 timed_out=false
git_commit=28be3be8c93e098080c9692e32a18c263b525f0e dirty=False

$ retornatus verify C-0001
C-0001/E-002 type=test_result provenance=executed exit_code=0 status=executed
{
  "verdict": "SATISFIED",
  "rationale": "All claims have matching attributable evidence"
}
```

## What it is

A **governance harness** — not an IDE, not a model, and not an agent store. The host agent still writes code. Retornatus keeps the agreement, the proof, and the memory under **`.retornatus/`**.

**Demand** → **Situation** → **Contract** → **Action** → **Evidence** → **Assurance** → **Learning**

You approve the product intent. The agent implements. Push, merge, and publish stay on your terms ([git governance](https://luizssantiago92.github.io/retornatus/guide/git-governance.html)).

## What’s new

One block for the **current release** **1.9.0**. From **1.5** through **1.9**:

- **Presets (1.5)** — `retornatus init --preset` for `python`, `python-platform`, `fastapi`, `django`, `rag`, and `worker`
- **Pull requests (1.5)** — the [GitHub Action](https://luizssantiago92.github.io/retornatus/guide/github-action.html) comments the verdict on the PR
- **Agent hooks** — `hook stop` (1.6; 1.7 lets a real question end the turn), `hook session-start` (1.7), `hook file-edit` (1.8.0 scope warning; `[hooks] scope_mode` is `warn`, `block`, or `off`), and `hook subagent-stop` (shipped in 1.9.0). It reminds a Cursor, Claude Code, or Codex subagent when the active Change is not SATISFIED. `[hooks] subagent_stop` defaults to true.

Full notes: [CHANGELOG.md](https://github.com/luizssantiago92/retornatus/blob/main/CHANGELOG.md).

## Quick start

Python 3.11+. Install [uv](https://docs.astral.sh/uv/) if you do not have it, then run this in **your application repository** (the project the agent should change):

```bash
uv tool install retornatus
cd /path/to/your-app
retornatus init && retornatus integrate && retornatus doctor
```

| Command | What it does |
| --- | --- |
| **`uv tool install retornatus`** | Puts `retornatus` on your PATH |
| **`init`** | Creates `.retornatus/`. Optional `--preset` — see [Presets](#presets) |
| **`integrate`** | Installs the hub skill so the agent knows the loop |
| **`doctor`** | Readiness: healthy workflow versus hard stops |

One-shot without a global install: `uvx retornatus --help`. You are ready when `.retornatus/` exists, the hub skill is visible to the agent, and `doctor` is not stopping on “not initialized.” For a repo that already has history: `retornatus project-init` and `retornatus wake --bridges`.

Ask the agent for a written Change before code: *Create a Retornatus Change for GET /health returning 200. Contract and gates before code.*

**Go deeper:** [Quick start](https://luizssantiago92.github.io/retornatus/guide/quick-start.html) · [Environments](https://luizssantiago92.github.io/retornatus/guide/environments.html) · [FAQ](https://luizssantiago92.github.io/retornatus/guide/faq.html)

## Presets

`init` without `--preset` writes a minimal config. `retornatus init --list-presets` lists packaged configs. An existing `config.toml` stays unless you pass `--force-config`.

`python` (pytest, ruff, and mypy), `python-platform` (deploy files or model behavior), `fastapi`, `django`, `rag`, and `worker` (background jobs).

```bash
retornatus init --preset fastapi
```

These checks record that a command ran and exited 0. They do not review a Terraform plan or score retrieval quality. Full page: [Presets](https://github.com/luizssantiago92/retornatus/blob/main/docs/guide/Presets.md).

## How it works

| Step | In plain words | Command |
| --- | --- | --- |
| **Understand** | Clarify the ask before coding | `change elicit` |
| **Agree** | Write the finish line | `gate contract` |
| **Build** | Implement under that agreement | `loop next` / `run` |
| **Prove** | “Done” needs evidence | `evidence run` → `verify` |
| **Learn** | Keep what mattered | `change learn` |

A fuzzy ask makes `change elicit` exit `1` and list questions. A prompt that might need a new procedure goes through `intake analyze`; nothing is saved until you answer `CREATE=yes`. [How it works](https://luizssantiago92.github.io/retornatus/guide/how-it-works.html).

## What you get — and why it helps

**Requirements.** Without a written situation, “add login” becomes three products in three chats. [How it works](https://luizssantiago92.github.io/retornatus/guide/how-it-works.html).

**Memory.** Changes, proof, and lessons live in git. `wake` rebuilds continuity. [Memory](https://luizssantiago92.github.io/retornatus/guide/memory.html).

**Proof.** `verify` returns `SATISFIED`, `NOT_SATISFIED`, or `INCONCLUSIVE`. Test, build, and lint results count only when Retornatus ran the command. Required checks, freshness, and `gate suppressions` / `gate scope`: [Gates](https://luizssantiago92.github.io/retornatus/guide/gates.html).

**Depth.** A typo stays small. Payments, security, or a new design get a deeper pass.

**One map, then one extra guide.** The hub skill is the short map every turn. A specialization Skill is an optional playbook for one kind of work — at most one, and only after you confirm it. [Skills](https://luizssantiago92.github.io/retornatus/guide/skills.html).

## Agent hooks

`retornatus integrate --hooks` installs four opt-in hooks for Claude Code, Cursor, and Codex. `hook session-start` injects the active Change. `hook file-edit` warns when an edit leaves that Change’s scope (`[hooks] scope_mode` is `warn` by default, or `block`, or `off`). `hook stop` asks the agent to keep going when the Change is not `SATISFIED`, and lets a real question to you end the turn. `hook subagent-stop` sends that same reminder when a subagent finishes (`[hooks] subagent_stop` defaults to true). They fail open. The pull-request check stays the source of truth. Guide: [Agent hooks](https://luizssantiago92.github.io/retornatus/guide/agent-hooks.html).

## Commands

Continuity: `wake`, `doctor`, `status`, `init --preset`, `integrate`. Finish line: `change elicit`, `change create`, `gate contract`. Proof: `evidence run --claim … -- <command>`, `verify`. Agent hooks: `integrate --hooks`, `hook file-edit`, `hook session-start`, `hook stop`, `hook subagent-stop`. Diff gates: `gate suppressions`, `gate scope`, `hooks install`. Full map: [CLI](https://luizssantiago92.github.io/retornatus/guide/cli.html).

## Verify receipts

`verify --receipt` writes an Ed25519 receipt for the verdict. The private key stays outside the repo; a clone checks the receipt with the committed public key. Keys, the CI signing step, and the threat model: [CLI — Receipts](https://luizssantiago92.github.io/retornatus/guide/cli.html).

## Cloud and remote agents

A cloud agent starts from a clean machine. Install from PyPI. Git does not version hooks, so every fresh clone runs `hooks install`. Leave receipts unsigned.

```bash
pip install retornatus
# or
uv tool install retornatus
export PATH="$HOME/.local/bin:$PATH"
retornatus hooks install
retornatus hooks status
retornatus doctor
```

[`templates/ci/retornatus-pr.yml`](https://github.com/luizssantiago92/retornatus/blob/main/templates/ci/retornatus-pr.yml) runs the [GitHub Action](https://github.com/luizssantiago92/retornatus/blob/main/docs/guide/GitHub-Action.md) (`uses: luizssantiago92/retornatus@v1`) and comments the verdict on the PR. Notes: [Cloud agents](https://luizssantiago92.github.io/retornatus/guide/cloud-agents.html).

## Documentation

[Website](https://luizssantiago92.github.io/retornatus/) · [Quick start](https://luizssantiago92.github.io/retornatus/guide/quick-start.html) · [Docs hub](https://luizssantiago92.github.io/retornatus/guide/) · [From Spec Guardrails](https://luizssantiago92.github.io/retornatus/guide/from-spec-guardrails.html) · [PRD](https://github.com/luizssantiago92/retornatus/blob/main/docs/archive/PRD.md).

Sources: [`docs/guide/`](https://github.com/luizssantiago92/retornatus/blob/main/docs/guide/README.md). Pages builds the HTML. Local preview: `python scripts/build_docs_html.py` (output is gitignored).

## Credits

Ideas are credited by influence. **[Spec Guardrails](https://github.com/luizssantiago92/spec-guardrails)** (MIT) is the direct predecessor: a separate successor, not a fork. Retornatus keeps the written plan, the gates, the proof, and the memory in a Python CLI under `.retornatus/`.

Provenance: [credits](https://luizssantiago92.github.io/retornatus/credits.html) · [credits-and-lineage.md](https://github.com/luizssantiago92/retornatus/blob/main/docs/credits-and-lineage.md).

## Contributing / Maintainers

Issues and pull requests: [CONTRIBUTING.md](https://github.com/luizssantiago92/retornatus/blob/main/CONTRIBUTING.md). Maintainer release steps: [CONTRIBUTING — Releases](https://github.com/luizssantiago92/retornatus/blob/main/CONTRIBUTING.md#releases).

## License

MIT — see [LICENSE](https://github.com/luizssantiago92/retornatus/blob/main/LICENSE).
