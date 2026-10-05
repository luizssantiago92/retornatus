<!-- retornatus-meta
{
  "change_id": "C-0041",
  "schema_version": 1
}
-->

# Situation

## Demand

Dependabot pull requests that only bump a dependency manifest fail the omission gate because a bot cannot write a Change. The GitHub Action must exempt a listed bot author when every changed file is an allowed manifest, and must still fail when any other file changes. The author must come from the pull request event, not from the title or body. Out of scope: a version bump, a release, and merging pull requests.

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

- Demand stated: Dependabot pull requests that only bump a dependency manifest fail the omission gate because a bot cannot write a Change. The GitHub Action must exempt a listed bot author when every changed file is an allowed manifest, and must still fail when any other file changes. The author must come from the pull request event, not from the title or body. Out of scope: a version bump, a release, and merging pull requests.
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
- Proposed WHAT: Exempt configured dependency-bot pull requests from the omission gate when every changed file matches the manifest allow-list, pass with a visible warning, and keep every other omission failure unchanged.
- DONE criterion: uv run pytest -q exits 0 and covers bot exemption, a source file, a human author, a disabled config, custom authors, and glob edges
- DONE criterion: uv run ruff check src tests scripts exits 0
- DONE criterion: uv run mypy exits 0
- DONE criterion: uv run python scripts/build_docs_html.py --check exits 0 as a build
- DONE criterion: uv lock --check exits 0 as a build

## Constraints

- Prefer pytest for automated verification (inferred from repo)
- The pull request author is read from github.event.pull_request.user.login or the --pr-author flag. Title, body, and commit messages are not a source of the author.
- No package version bump and no release tag.

## Assumptions

- (none)

## Ambiguities

- (none)

## Missing decisions

- (none)

## Contract readiness

- Sufficient: **yes**
- Rationale: Demand, WHAT, and DONE are sufficiently clear; the author source is constrained to the trusted event login or --pr-author.

## Agent narrative

The omission check in the GitHub Action treats pyproject.toml and uv.lock as code. A Dependabot pull request changes those files and touches no Change, so the check fails. Bots cannot commit a Change. The exemption belongs in Retornatus, configured beside the other governance tables, and the Action must pass the trusted event login.
