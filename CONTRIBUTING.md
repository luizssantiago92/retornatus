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
- Update `docs/guide/` when user-visible behavior changes, then run `uv run python scripts/build_docs_html.py` so Pages HTML stays in sync.
- When adding external influence, update [`docs/credits-and-lineage.md`](docs/credits-and-lineage.md) in the same PR — credit by real influence; do not promote Spec Guardrails transitive upstreams to “direct” without independent study.
- Do not claim Spec Guardrails full replacement in marketing copy.
- Add or extend tests for gates, Policy, and persistence invariants.

## GitHub discoverability (owner)

Homepage should stay `https://luizssantiago92.github.io/retornatus/`.

Suggested repository topics (set in the GitHub UI or with `gh repo edit --add-topic …`):

`python` · `ai` · `governance` · `developer-tools` · `cursor` · `cli` · `uv` · `llm` · `agents` · `software-engineering` · `harness`

## Where to look

| Area | Path |
| --- | --- |
| Product contract | `prd/PRD.md` |
| User docs | `docs/guide/` |
| CLI | `src/retornatus/cli/` |
| Tests | `tests/` |

## License

By contributing, you agree that your contributions are licensed under the MIT License.
