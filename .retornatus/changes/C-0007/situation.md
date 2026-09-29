<!-- retornatus-meta
{
  "change_id": "C-0007",
  "schema_version": 1
}
-->

# Situation

## Demand

Maintainers must record the merged 1.4.0 follow-ups in CHANGELOG.md. Scope is the existing 1.4.0 section, the leftover setup-uv pin in CI and the consumer template, and Change C-0007 task resources. Out of scope is merging, tagging v1.4.0, and publishing to PyPI. The heading ## [1.4.0] - 2026-09-29 must stay unchanged and Unreleased must stay empty.

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

- Demand stated: Maintainers must record the merged 1.4.0 follow-ups in CHANGELOG.md. Scope is the existing 1.4.0 section, the leftover setup-uv pin in CI and the consumer template, and Change C-0007 task resources. Out of scope is merging, tagging v1.4.0, and publishing to PyPI. The heading ## [1.4.0] - 2026-09-29 must stay unchanged and Unreleased must stay empty.
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
- Proposed WHAT: Correct the 1.4.0 changelog so Ruff reads 0.16.9, Dependabot action bumps are listed, and pull request 36 behavior sits under the matching subsections, and switch leftover astral-sh/setup-uv pins from v7.6.0 to commit c18668ad3cf93ea998bef934396af7bb5c839dc7.
- DONE criterion: CHANGELOG.md contains the text Ruff is 0.16.9 and the heading ## [1.4.0] - 2026-09-29
- DONE criterion: CHANGELOG.md contains setup-uv 10.2.0, configure-pages 6, upload-pages-artifact 5.0.0, and upload-artifact 7.0.1
- DONE criterion: CHANGELOG.md contains fenced code blocks, inline code spans, config.toml, and Retornatus gates
- DONE criterion: A permission check shows .github/workflows/ci.yml and templates/ci/retornatus-pr.yml pin setup-uv to SHA c18668ad3cf93ea998bef934396af7bb5c839dc7 and no workflow file contains SHA 37802adc94f370d6bfd71619e3f0bf239e1f3b78
- DONE criterion: scripts/publish_preflight.py exits 0 for tag v1.4.0 and prints version 1.4.0 with skip false
- DONE criterion: retornatus doctor and retornatus ops run gate-scan exit 0
- DONE criterion: retornatus gate suppressions exits 0 against origin/main

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

PRs 30 through 36 are already on main. Version 1.4.0 is declared everywhere and v1.4.0 is not tagged. The 1.4.0 changelog still says Ruff 0.16.8 and omits the Dependabot action bumps and the governance hygiene from PR 36. The Retornatus gates job and the consumer template still pin setup-uv v7.6.0 while the other jobs use v10.2.0. Owner will tag the merge commit of this PR as v1.4.0. Do not merge, tag, or publish.
