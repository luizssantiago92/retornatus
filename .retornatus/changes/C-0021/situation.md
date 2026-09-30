<!-- retornatus-meta
{
  "change_id": "C-0021",
  "schema_version": 1
}
-->

# Situation

## Demand

Readers and agents must see an Ed25519 receipt in the packaged hub skill and in the repo hub copy. The CLI doctor must warn when config.toml version differs from the installed release. The README anchor, credits license link, product contract link text, site og:image, and README whats-new pin must be corrected. Out of scope: PyPI metadata, CI workflows, and ruff format.

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

- Demand stated: Readers and agents must see an Ed25519 receipt in the packaged hub skill and in the repo hub copy. The CLI doctor must warn when config.toml version differs from the installed release. The README anchor, credits license link, product contract link text, site og:image, and README whats-new pin must be corrected. Out of scope: PyPI metadata, CI workflows, and ruff format.
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
- Proposed WHAT: Correct the packaged hub receipt wording, sync the repo hub copy, warn on config version drift, and fix the README anchor, credits links, landing og:image, and version-pinned whats-new line.
- DONE criterion: pytest confirms hub copies match and name an Ed25519 receipt
- DONE criterion: pytest confirms doctor warns when config version differs
- DONE criterion: pytest confirms config.toml version equals the installed release
- DONE criterion: pytest confirms the README em dash heading anchor
- DONE criterion: pytest confirms the credits license target and PRD link text
- DONE criterion: pytest confirms the landing og image and 1.4 preset news
- DONE criterion: pytest confirms README news does not pin a package version
- DONE criterion: uv run ruff check src tests scripts exits 0
- DONE criterion: uv run mypy exits 0
- DONE criterion: uv run pytest -q exits 0
- DONE criterion: HTML docs check exits 0
- DONE criterion: uv lock --check exits 0
- DONE criterion: CHANGELOG Unreleased contains hub and site hygiene notes

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

Audit I4, M-a, and M-h on 1.4.1: the packaged hub still says portable HMAC receipt, the repo hub copy has drifted, config.toml is 0.8.0 and doctor does not warn, the README anchor drops the em dash, credits.html points at guide/license.html and still labels the PRD as prd/PRD.md, og:image is relative, the site news block omits the 1.4 line, and README 1.4.0 pins retornatus==1.4.1.
