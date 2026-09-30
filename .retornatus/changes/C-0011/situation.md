<!-- retornatus-meta
{
  "change_id": "C-0011",
  "schema_version": 1
}
-->

# Situation

## Demand

Replace the public Retornatus mascot with the approved chrome-agent artwork. Scope is optimized WebP files under docs/assets, the README image, the docs website hero plus a CSS glow, Open Graph and favicon references, and an Unreleased changelog note. Out of scope is a package version bump, merging the pull request, and publishing to PyPI.

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

- Demand stated: Replace the public Retornatus mascot with the approved chrome-agent artwork. Scope is optimized WebP files under docs/assets, the README image, the docs website hero plus a CSS glow, Open Graph and favicon references, and an Unreleased changelog note. Out of scope is a package version bump, merging the pull request, and publishing to PyPI.
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
- Proposed WHAT: Ship three optimized transparent WebP mascots under docs/assets, point the README at the sharp image, point the site hero at the neon image with a 3.6s CSS teal and orange glow that stops under prefers-reduced-motion, and point OG and favicon images at the square crop.
- DONE criterion: pytest confirms README.md contains the sharp mascot file docs/assets/retornatus-mascot.webp
- DONE criterion: pytest confirms docs/index.html contains the neon hero assets/retornatus-mascot-neon.webp
- DONE criterion: pytest confirms docs/index.html og:image and favicon point at assets/retornatus-mascot-square.webp
- DONE criterion: pytest confirms docs/site.css contains prefers-reduced-motion: reduce and animation-duration 3.6s
- DONE criterion: pytest confirms scripts/build_docs_html.py references assets/retornatus-mascot-square.webp
- DONE criterion: pytest confirms CHANGELOG.md contains an Unreleased note for the approved mascot
- DONE criterion: The docs HTML build via scripts/build_docs_html.py --check exits 0
- DONE criterion: uv run pytest -q exits 0

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

The approved artwork is a chrome AI agent in a black suit adjusting sunglasses, with a teal ouroboros and an orange comet flame. Three source PNGs exist: a sharp 1280x720 plate for the README, a neon 1280x720 plate for the site hero, and an 830x830 crop for social and favicon use. The plates have a white background that must become transparency so the dark site atmosphere shows through. The current public file is docs/assets/retornatus-mascot.webp, referenced by README.md, docs/index.html, docs/guide/index.html, and scripts/build_docs_html.py. Change id C-0011 is the next free id: C-0009 is on main and C-0010 belongs to the in-flight JSON-output pull request.
