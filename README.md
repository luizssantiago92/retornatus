# Retornatus

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-informational.svg)](pyproject.toml)

**Repo-native governance for AI-assisted software development.**

Retornatus is a local harness that keeps AI coding agents accountable inside your repository: Contracts before code, gates that stop false “done”, Evidence bound to Claims, and Learning that survives the next chat.

It is not an IDE plugin marketplace, not an agent runtime, and not a remote control plane. Your host (Cursor, Claude Code, Codex, …) executes; Retornatus governs and records.

> Govern the work. Bound the agent. Verify the outcome.

## Why it exists

AI agents are fast and optimistic. Without structure they:

- jump to implementation before the goal is clear
- declare success from a chat summary
- forget project context when the session ends
- apply the same ceremony to a typo and a payment flow

Retornatus installs durable structure under `.retornatus/` so Demand → Situation → Contract → Action → Evidence → Assurance → Learning is **repository truth**, not scrollback.

## Highlights

- **Contract-first Changes** — WHAT, constraints, and DONE before execution
- **Mechanical gates** — non-zero exit codes stop incomplete work (`contract`, `evidence`, `assurance`, `skill-research`, `policy`)
- **Claim-bound Evidence** — Assurance verdicts from attributable proof, not self-report
- **On-demand Skills** — one researched specialization per need; no rotting skill packs
- **Native-first** — prefer host rules, skills, worktrees, and sandboxes; project only what is missing
- **Continuity** — `wake` rebuilds index and status from files after crash or handoff

## Quick start

**Requirements:** Python 3.11+ · [uv](https://docs.astral.sh/uv/) recommended · an AI coding agent

```bash
# Install the CLI from PyPI
uv tool install retornatus
retornatus --version   # 1.0.x

cd /path/to/your-app
retornatus init
retornatus integrate   # hub skill + host bridges
retornatus doctor
```

Then ask your agent, with the Retornatus hub skill in context:

> Create a Change for GET /health → 200. Follow Retornatus: Contract and gates before code.

Or drive the CLI yourself:

```bash
retornatus change create \
  --title "Add health endpoint" \
  --demand "Expose a liveness check" \
  --what "GET /health returns 200 with status ok" \
  --done "Automated test covers /health" \
  --objective "Implement and verify health endpoint"

retornatus gate contract C-0001
retornatus loop next C-0001
retornatus run C-0001/A-001
# …implement in the host, then record Evidence and verify…
retornatus verify C-0001
```

## Documentation

| Start here | |
| --- | --- |
| [Overview](docs/guide/Overview.md) | What Retornatus is, and how much ceremony you need |
| [Quick start](docs/guide/Quick-start.md) | First ten minutes in a real project |
| [How it works](docs/guide/How-it-works.md) | End-to-end Change story |
| [Guide index](docs/guide/README.md) | Concepts, gates, skills, governance, CLI, FAQ |

Canonical product requirements: [`prd/PRD.md`](prd/PRD.md).

## Core loop

```text
Demand → Situation → Contract → Action (+ Tasks when needed)
       → Skill? → Execution (host) → Evidence → Assurance
       → Finding/Question if blocked → Learning / Skill evolution
```

Status (`retornatus status`, `loop next`) is a **projection**. Canonical truth lives in files under `.retornatus/`.

## What Retornatus owns vs what it does not

| Owns | Does not own |
| --- | --- |
| Change / Contract / Evidence structure | Writing your application code |
| Gates and Assurance verdicts | Running the LLM or IDE agent |
| `.retornatus/` persistence + index rebuild | Enforced OS sandboxes (host-native) |
| Hub skill + Environment bridges | Multi-tenant SaaS orchestration |

Honest non-goals: [docs/guide/Non-goals.md](docs/guide/Non-goals.md).

## Install options

**From PyPI (recommended):**

```bash
uv tool install retornatus
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

**From Git:**

```bash
uv tool install --force git+https://github.com/luizssantiago92/retornatus.git
```

**From a local clone:**

```bash
uv tool install --force /path/to/retornatus
uvx --from /path/to/retornatus retornatus --help
```

**Contributors / dogfood in this repo:**

```bash
uv sync
uv run retornatus --help
uv run pytest -q
```

Re-run `uv tool install --force …` after upgrades. Project state under `.retornatus/` is preserved.

## Environments

`integrate` and `wake --bridges` detect the host and write projections only:

| Host | Surface |
| --- | --- |
| Cursor | `.cursor/skills/retornatus/` + `.cursor/rules/retornatus.mdc` |
| Claude Code | `CLAUDE.md` bridge markers |
| Codex | `AGENTS.md` bridge markers |
| Generic | `.retornatus/` alone |

Active Rules are projected into those bridges when present. Canonical Rules stay in `.retornatus/`.

## Project layout (this repository)

| Path | Role |
| --- | --- |
| [`src/retornatus/`](src/retornatus/) | Package — CLI, domain, application, infrastructure |
| [`docs/guide/`](docs/guide/) | Product documentation |
| [`docs/credits-and-lineage.md`](docs/credits-and-lineage.md) | Provenance and prior art |
| [`prd/PRD.md`](prd/PRD.md) | Product requirements (V1) |
| [`tests/`](tests/) | Unit, adversarial, and construction dogfood |
| [`.specs/`](.specs/) | Internal parity / gap notes for maintainers |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Preserve **native-first** and **complexity must be earned** (PRD §71).

```bash
uv sync
uv run pytest -q
```

## Credits, Lineage & Prior Art

Retornatus grew directly from the experience of building and dogfooding **[Spec Guardrails](https://github.com/luizssantiago92/spec-guardrails)**. It is a **separate successor architecture** — not a fork or rename — that preserves proven governance guarantees while rethinking mechanisms (structured Contracts, Evidence ≠ Assurance, native-first Environment adapters, …).

| Category | What belongs here |
| --- | --- |
| **Direct predecessor** | Spec Guardrails (MIT) — practical proof of repo-native gates, memory, evidence, human checkpoints |
| **Direct Retornatus research** | Host capability surfaces (Cursor / Claude Code / Codex adapters); runtime libraries (Pydantic, Typer, …) |
| **Transitive prior art** | Spec Guardrails’ own upstreams (`tlc-spec-driven`, loop/graph harness essays, …) — documented **there**, not re-listed as Retornatus direct influences |
| **Original composition** | Demand→Situation→Contract→Action; Finding→Question→Resolution; Learning/Skill/Rule/Policy separations |

Full provenance, evaluated alternatives, and licensing notes: **[docs/credits-and-lineage.md](docs/credits-and-lineage.md)** · Spec Guardrails lineage: [credits.md](https://github.com/luizssantiago92/spec-guardrails/blob/main/docs/guide/credits.md).

> Ideas are credited by influence, not by superficial similarity.

## License

MIT — see [LICENSE](LICENSE).
