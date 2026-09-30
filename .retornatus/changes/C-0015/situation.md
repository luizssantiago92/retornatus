<!-- retornatus-meta
{
  "change_id": "C-0015",
  "schema_version": 1
}
-->

# Situation

## Demand

GitHub readers must see the README mascot the same way on dark and light themes. The image must be a static frame of the docs site hero, with resting glow, a dark background, and rounded corners. Out of scope: retornatus-mascot-neon.webp, retornatus-mascot-square.webp, docs/index.html, and site.css.

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

- Demand stated: GitHub readers must see the README mascot the same way on dark and light themes. The image must be a static frame of the docs site hero, with resting glow, a dark background, and rounded corners. Out of scope: retornatus-mascot-neon.webp, retornatus-mascot-square.webp, docs/index.html, and site.css.
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
- Proposed WHAT: Replace the README image with docs/assets/retornatus-mascot-readme.webp, centered and linked to the site at width 420 and height 231, delete docs/assets/retornatus-mascot.webp, and record the swap in the CHANGELOG Unreleased section.
- DONE criterion: pytest exits 0
- DONE criterion: ruff check of src tests and scripts exits 0
- DONE criterion: mypy exits 0
- DONE criterion: The HTML documentation check exits 0
- DONE criterion: uv lock check exits 0
- DONE criterion: pytest confirms README.md contains a centered link to docs/assets/retornatus-mascot-readme.webp with width 420 and height 231
- DONE criterion: pytest confirms docs/assets/retornatus-mascot.webp is absent from README.md, CHANGELOG.md, docs, scripts, tests, pyproject, and HTML
- DONE criterion: pytest confirms CHANGELOG.md Unreleased names docs/assets/retornatus-mascot-readme.webp and records a Fixed README mascot note

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

C-0013 is the highest Change on origin/main. C-0014 is reserved by the unmerged branch cursor/init-config-presets-bc2b, so this Change is C-0015. The README still points at docs/assets/retornatus-mascot.webp, which is a sharp plate that does not match the docs-site hero and does not look the same on GitHub dark and light. The replacement is a 960x528 static frame of that hero (neon artwork re-cut without the white patch and fringe, resting glow, dark background, rounded corners) stored as docs/assets/retornatus-mascot-readme.webp. Net asset bytes must go down. No extra image copies.
