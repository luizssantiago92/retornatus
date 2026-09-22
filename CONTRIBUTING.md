# Contributing

Thanks for helping improve Retornatus.

## Principles

1. **Native first** — prefer Environment capabilities; do not rebuild host sandboxes or agent runtimes without a concrete failure.
2. **Complexity must be earned** — cite a real failure mode before new abstractions (PRD §71).
3. **Files are truth** — SQLite/status are derived; do not invent a second canonical store.
4. **Docs in English** for code, tests, commits, and `docs/` · product conversation may be Portuguese, but artifacts stay English.

## Setup

```bash
uv sync
uv run pytest -q
uv run retornatus --help
```

## Pull requests

- Keep changes scoped; prefer small milestones.
- Update `docs/guide/` when user-visible behavior changes.
- Do not claim Spec Guardrails full replacement in marketing copy.
- Add or extend tests for gates, Policy, and persistence invariants.

## Where to look

| Area | Path |
| --- | --- |
| Product contract | `prd/PRD.md` |
| User docs | `docs/guide/` |
| CLI | `src/retornatus/cli/` |
| Tests | `tests/` |

## License

By contributing, you agree that your contributions are licensed under the MIT License.
