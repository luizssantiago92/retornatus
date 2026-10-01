<!-- retornatus-meta
{
  "change_id": "C-0029",
  "schema_version": 1
}
-->

# Situation

## Demand

Rewrite README.md so it is shorter, current through 1.7.0 plus the unreleased file-edit scope warning, and portfolio-friendly. Docs only. No product behavior changes.

## Project context

# Project

Retornatus continuity map for `retornatus`.

## Identity

- Path: repository root (clone path varies by machine)
- README signal: # Retornatus

## Language / stack

- `pyproject.toml`

## Important directories

- `src`
- `tests`
- `docs`
- `.github`
- `.cursor`
- `docs/archive`

## Tests

- tests/
- pytest (pyproject)

## CI

- `ci.yml`
- `publish.yml`

## Architecture clues

- src packages: retornatus

## Environment capabilities

- Detected: `cursor`
- native_rules: True
- native_skills: True
- native_sandbox: False

## Existing Retornatus state

- changes: 1
- rules: 0
- skills: 0

## Conventions

_Agents: update this file when durable project conventions are discovered._

## Stack notes

_Fill during Wake / first Change. Prefer facts from the repo over assumptions._

## Kickoff sources

- `docs/archive/PRD.md`

## Repo signals (inferred)

- stack manifests: `pyproject.toml`
- tests: tests/, pytest (pyproject)
- ci: `ci.yml`, `codeql.yml`, `pages.yml`, `publish.yml`
- architecture: AGENTS.md; src packages: retornatus
- code path present: `src`
- Retornatus already initialized

## Known facts

- Demand stated: Rewrite README.md so it is shorter, current through 1.7.0 plus the unreleased file-edit scope warning, and portfolio-friendly. Docs only. No product behavior changes.
- Repo: stack manifests: `pyproject.toml`
- Repo: tests: tests/, pytest (pyproject)
- Repo: ci: `ci.yml`, `codeql.yml`, `pages.yml`, `publish.yml`
- Repo: architecture: AGENTS.md; src packages: retornatus
- Repo: code path present: `src`
- Repo: Retornatus already initialized
- Kickoff `docs/archive/PRD.md` present (1494 chars loaded)
- From `docs/archive/PRD.md`: Govern the work. Bound the agent. Verify the outcome.**
- From `docs/archive/PRD.md`: coordination;
- Path: repository root (clone path varies by machine)
- README signal: # Retornatus
- `pyproject.toml`
- `src`
- `tests`
- `docs`
- `.github`
- `.cursor`
- `docs/archive`
- tests/
- pytest (pyproject)
- `ci.yml`
- `publish.yml`
- src packages: retornatus
- Detected: `cursor`
- native_rules: True
- native_skills: True
- native_sandbox: False
- Situation narrative provided by agent/human
- Proposed WHAT: README.md is about 150-200 lines, leads with a 30-second verify demo, highlights agent hooks including file-edit, summarizes 1.5-1.7 in one What's new block, and points long receipts, presets, freshness, and credits detail at existing docs.
- DONE criterion: The file /README.md contains between 150 and 200 lines, a console demo of verify then evidence run then SATISFIED, one What's new block for releases 1.5 through 1.7 plus hook file-edit, an agent hooks comparison row, a Quick start section, and a PyPI cloud install
- DONE criterion: uv run pytest -q exits 0
- DONE criterion: uv run ruff check src tests scripts exits 0
- DONE criterion: uv run mypy exits 0
- DONE criterion: uv run python scripts/build_docs_html.py --check exits 0
- DONE criterion: uv lock --check exits 0

## Constraints

- Prefer pytest for automated verification (inferred from repo)
- Prefer pytest for automated verification (inferred from repo)

## Assumptions

- (none)

## Ambiguities

- (none)

## Missing decisions

- (none)

## Contract readiness

- Sufficient: **yes**
- Rationale: Demand, WHAT, and DONE are sufficiently clear; repo/kickoff signals incorporated; no material requirements ambiguity detected

## Agent narrative

Requirements are sufficient. Keep the mascot, tagline, badges, and comparison table. Replace per-version What's new sections with one block for 1.5-1.7 plus the unreleased hook file-edit scope warning, linking to the GitHub CHANGELOG. Add an agent-hooks row and mention hook file-edit with scope_mode warn/block/off. Add a 30-second console demo from real CLI output. Target 150-200 lines by moving receipt, freshness, preset, and credits detail to existing docs. Merge install, verify readiness, and the checklist into Quick start. Move maintainer release steps to a Contributing section. Cloud agents install from PyPI. Plain wording above the fold.
