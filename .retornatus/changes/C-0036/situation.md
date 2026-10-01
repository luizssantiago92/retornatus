<!-- retornatus-meta
{
  "change_id": "C-0036",
  "schema_version": 1
}
-->

# Situation

## Demand

Site visitors must see a square favicon of the mascot head on every docs page. In scope: a tightly cropped multi-size favicon.ico and a 180px apple-touch-icon.png derived only from the existing docs/assets mascot, icon link tags in the HTML builder and the two committed HTML pages, and an Unreleased changelog note. Out of scope: new mascot artwork, Open Graph or Twitter image changes, Python package behavior, merging, and publishing.

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

- Demand stated: Site visitors must see a square favicon of the mascot head on every docs page. In scope: a tightly cropped multi-size favicon.ico and a 180px apple-touch-icon.png derived only from the existing docs/assets mascot, icon link tags in the HTML builder and the two committed HTML pages, and an Unreleased changelog note. Out of scope: new mascot artwork, Open Graph or Twitter image changes, Python package behavior, merging, and publishing.
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
- Proposed WHAT: Derive a square head-and-face crop from docs/assets/retornatus-mascot-square.webp as favicon.ico at 16, 32, and 48 pixels and apple-touch-icon.png at 180 pixels, wire rel=icon and apple-touch-icon through scripts/build_docs_html.py plus docs/index.html and docs/guide/index.html, and record an Unreleased changelog entry. Keep the existing square WebP for Open Graph and Twitter.
- DONE criterion: uv run pytest -q exits 0
- DONE criterion: uv run python scripts/build_docs_html.py --check exits 0 as a build
- DONE criterion: uv lock --check exits 0 as a build
- DONE criterion: CHANGELOG.md is documented and contains an Unreleased favicon entry
- DONE criterion: docs/index.html links a square favicon.ico and an apple-touch-icon

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

The docs site currently points rel=icon at the full-body square WebP, which is too large and too detailed to read at 16–32 px. The source art is a raster WebP, so a traced SVG is not a clean vector. Deliver favicon.ico (16/32/48) and apple-touch-icon.png (180) cropped to the mascot head, link both from the HTML builder and the two committed pages, and note it under Unreleased. Open Graph and Twitter stay on the existing square WebP. Constraint: no new large images, no duplicate mascot copies, no unused icon files, and no Python package behavior changes.
