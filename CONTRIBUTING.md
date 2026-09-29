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
- Update `docs/guide/` when user-visible behavior changes. GitHub Pages runs `scripts/build_docs_html.py` on deploy. Do not commit the generated HTML. Preview locally with `uv run python scripts/build_docs_html.py` if you want to read it.
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
| Product contract | `docs/archive/PRD.md` |
| User docs | `docs/guide/` |
| CLI | `src/retornatus/cli/` |
| Tests | `tests/` |

## Releases

Publishing is the owner's job. Do not upload from a laptop, do not create `v*` tags that publish, and do not run the Publish workflow for someone else.

PyPI **1.2.1** and **1.3.0** are already published. Git tags for those versions were backfilled on 2026-09-29: `v1.2.1` points at `f4d96d3`, and `v1.3.0` points at `a540efb`. The workflow that publishes *new* versions is `.github/workflows/publish.yml` (Trusted Publishing, no API token):

1. In a PR, bump `version` in `pyproject.toml` and move `## [Unreleased]` notes in `CHANGELOG.md` under `## [x.y.z]`. This repository does not bump the version inside the publish workflow.
2. Merge to `main`.
3. One-time, on [pypi.org](https://pypi.org/manage/project/retornatus/settings/publishing/): add a trusted publisher for owner `luizssantiago92`, repository `retornatus`, workflow `publish.yml`, environment `pypi`. On GitHub, create an environment named `pypi` (optionally require a reviewer). You can then delete the old API token secrets (`UV_PUBLISH_TOKEN`, `TEST_PYPI_TOKEN`).
4. Tag a commit that is on `main` as `v<pyproject version>` (the tag name must match the `version` in `pyproject.toml`). Pushing the tag runs tests, ruff, mypy, the docs check, a wheel/sdist contents check, and the changelog check. If that version is already on PyPI, publish is skipped.
5. Optional TestPyPI: Actions → Publish to PyPI → Run workflow, from `main`, target `test`. That job is non-blocking. It expects a GitHub environment named `testpypi` and a TestPyPI trusted publisher. Skip it if you do not want a staging upload.

## License

By contributing, you agree that your contributions are licensed under the MIT License.
