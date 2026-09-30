<!-- retornatus-meta
{
  "change_id": "C-0013",
  "schema_version": 1
}
-->

# Situation

## Demand

Reviewers on a pull request must see one sticky comment that states the Retornatus CLI verdict, which claims have evidence, and which gates passed or failed. The comment is rendered from verify and gate JSON. Out of scope: a package version bump, a release tag, and merging the pull request.

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

- Demand stated: Reviewers on a pull request must see one sticky comment that states the Retornatus CLI verdict, which claims have evidence, and which gates passed or failed. The comment is rendered from verify and gate JSON. Out of scope: a package version bump, a release tag, and merging the pull request.
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
- Proposed WHAT: Add a composite GitHub Action that runs verify and the diff gates with --json and posts one sticky pull-request comment rendered by retornatus ci comment.
- DONE criterion: pytest exits 0 for the CI comment tests
- DONE criterion: ruff check of src tests and scripts exits 0
- DONE criterion: mypy on the retornatus package exits 0
- DONE criterion: The HTML documentation check exits 0
- DONE criterion: uv lock check exits 0
- DONE criterion: CHANGELOG Unreleased section records the GitHub Action
- DONE criterion: CLI reference contains a GitHub Action guide link
- DONE criterion: Independent review of the pull request workflow is recorded

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

The sticky comment is a projection of verify and gate JSON. Those commands keep the verdict. The composite action lives at the repository root so it can be published. A fork pull request with a read-only token skips the comment and still writes the job summary.
