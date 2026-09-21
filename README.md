# Retornatus

Repo-native governance harness for AI-assisted software development.

> **Govern the work. Bound the agent. Verify the outcome.**

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended)

## Quick start

```bash
uv sync
uv run retornatus --help
uv run retornatus init
uv run retornatus wake
```

Or via `uvx` from a local path:

```bash
uvx --from . retornatus init
uvx --from . retornatus wake
```

## CLI intentions

| Command | Purpose |
|---------|---------|
| `init` | Create `.retornatus/` |
| `wake` | Reconstruct continuity + rebuild index |
| `status` | Derived Change status |
| `change create` | Demand → Situation → Contract → Action |
| `run` | Assemble ExecutionContext |
| `verify` | Assurance over Contract DONE |
| `inspect` | Show artifact by id |
| `search` | FTS5 search |
| `doctor` | Diagnostics |

## Product requirements

See [`prd/PRD.md`](./prd/PRD.md) (mirror of the canonical PRD in the repo root).

## Status

V1 milestones **M0–M12** implemented in this repository:

- M0 Foundation · M1 Domain Core · M2 Persistence
- M3 Change Workflow · M4 Wake/Environment · M5 Execution Context
- M6 Assurance · M7 Finding/Question · M8 Memory/Index
- M9 Adaptation · M10 Governance · M11 Adapters · M12 Dogfood E2E
