<!-- retornatus-meta
{
  "change_id": "C-0031",
  "schema_version": 1
}
-->

# Situation

## Demand

The CLI command gate suppressions must also scan untracked non-ignored files, treating each as added lines, while --base and a clean CI checkout stay unchanged. Gitignored files stay out of scope.

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

- Demand stated: The CLI command gate suppressions must also scan untracked non-ignored files, treating each as added lines, while --base and a clean CI checkout stay unchanged. Gitignored files stay out of scope.
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
- Proposed WHAT: When neither --base nor --staged is set, gate suppressions scans every untracked non-ignored file from git ls-files --others --exclude-standard as wholly added lines. --staged stays the index. --base stays base...HEAD. Gitignored paths are not scanned. docs/guide/Gates.md and the CHANGELOG Unreleased Fixed entry describe the selection.
- DONE criterion: pytest reports an untracked non-ignored file that contains a suppression marker
- DONE criterion: pytest does not report a gitignored file that contains a suppression marker
- DONE criterion: pytest shows --base and --staged still ignore untracked files
- DONE criterion: docs/guide/Gates.md states that the default scan includes untracked non-ignored files
- DONE criterion: CHANGELOG.md Unreleased contains a Fixed entry for the suppressions scan of untracked files
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

gate suppressions reads added diff lines only. changed_paths already includes untracked non-ignored files when no base or staged flag is set, but added_lines does not, so a new file that was never git-added can hide a suppression locally. CI uses --base on a clean checkout and must keep that range.
