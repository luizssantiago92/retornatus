# Retornatus

Repo-native governance harness for AI-assisted software development.

> **Govern the work. Bound the agent. Verify the outcome.**

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended)

## Quick start

```bash
# From a clone of this repository
uv sync
uv run retornatus --help
uv run retornatus init
```

Or via `uvx` once published / from a local path:

```bash
uvx --from . retornatus init
```

`init` creates a minimal `.retornatus/` tree in the current project.

## Product requirements

See [`PRD.md - Retornatus V1.md`](./PRD.md%20-%20Retornatus%20V1.md) and the mirror under [`prd/`](./prd/).

## Status

Milestone **M0 — Foundation** delivered: Python package, CLI bootstrap, tests, and `retornatus init`.
