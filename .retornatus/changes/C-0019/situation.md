<!-- retornatus-meta
{
  "change_id": "C-0019",
  "schema_version": 1
}
-->

# Situation

## Demand

Readers of the README, the docs guide, and the public site must see the five init presets that are already on main: python, python-platform, fastapi, django, and rag. The CLI user must find init --preset, init --list-presets, --force-config, and preset show in the CLI reference. The site hero must use the same static card image as the README, docs/assets/retornatus-mascot-readme.webp. Out of scope: changing preset behavior, a version bump, merge, and publish. Ship and AI rules must be described as checks that evidence ran, not as quality grades.

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

- Demand stated: Readers of the README, the docs guide, and the public site must see the five init presets that are already on main: python, python-platform, fastapi, django, and rag. The CLI user must find init --preset, init --list-presets, --force-config, and preset show in the CLI reference. The site hero must use the same static card image as the README, docs/assets/retornatus-mascot-readme.webp. Out of scope: changing preset behavior, a version bump, merge, and publish. Ship and AI rules must be described as checks that evidence ran, not as quality grades.
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
- Proposed WHAT: Present the five init presets in README.md, the docs guide index, CLI reference, Overview, and the docs site, swap the site hero to docs/assets/retornatus-mascot-readme.webp, remove the unused neon asset, and record the updates in CHANGELOG Unreleased.
- DONE criterion: README.md contains a Presets section naming python, python-platform, fastapi, django, and rag, the command retornatus init --preset fastapi, and a link to docs/guide/Presets.md
- DONE criterion: docs/guide/index.html links presets.html and docs/guide/CLI.md documents init --preset, init --list-presets, --force-config, and preset show
- DONE criterion: docs/guide/Overview.md mentions init presets
- DONE criterion: docs/index.html hero src is assets/retornatus-mascot-readme.webp and the page contains a presets section
- DONE criterion: docs/assets/retornatus-mascot-neon.webp does not exist
- DONE criterion: CHANGELOG.md Unreleased records the README, docs, site, and mascot asset updates
- DONE criterion: uv run python scripts/build_docs_html.py --check exits 0
- DONE criterion: uv run pytest -q exits 0
- DONE criterion: uv run ruff check src tests scripts exits 0
- DONE criterion: uv run mypy exits 0
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

The five presets already ship in src/retornatus/bootstrap/presets and docs/guide/Presets.md. The README, Overview, the hand-written docs hub, and the landing page do not present them. The site hero still points at the badly cut neon WebP. Favicon and Open Graph stay on the square asset.
