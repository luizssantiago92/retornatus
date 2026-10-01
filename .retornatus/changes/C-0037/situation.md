<!-- retornatus-meta
{
  "change_id": "C-0037",
  "schema_version": 1
}
-->

# Situation

## Demand

Add a subagent-stop hook that reuses the Stop hook decision. Cursor subagentStop returns followup_message and sets loop_limit to 1. Claude Code SubagentStop and Codex SubagentStop return decision block with the reason and honor stop_hook_active. Skip questions, Cursor aborted or error, no active Change, and a SATISFIED Change. [hooks] subagent_stop defaults to true. doctor reports the toggle and the installed hook. Document the host payloads checked on 2026-10-01.

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

- Demand stated: Add a subagent-stop hook that reuses the Stop hook decision. Cursor subagentStop returns followup_message and sets loop_limit to 1. Claude Code SubagentStop and Codex SubagentStop return decision block with the reason and honor stop_hook_active. Skip questions, Cursor aborted or error, no active Change, and a SATISFIED Change. [hooks] subagent_stop defaults to true. doctor reports the toggle and the installed hook. Document the host payloads checked on 2026-10-01.
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
- Proposed WHAT: Add retornatus hook subagent-stop for Claude Code, Cursor, and Codex by reusing the Stop hook decision, install it with integrate --hooks, honor [hooks] subagent_stop, report it from doctor, and document the host payloads.
- DONE criterion: uv run pytest -q exits 0
- DONE criterion: uv run python scripts/build_docs_html.py --check exits 0 as a build
- DONE criterion: uv lock --check exits 0 as a build
- DONE criterion: The file /guide/Agent-hooks.md is documented and contains subagentStop, followup_message, and subagent_stop
- DONE criterion: The file /CLI.md is documented and contains hook subagent-stop
- DONE criterion: The file /CHANGELOG.md is documented and contains an Unreleased subagent-stop entry
- DONE criterion: The file /README.md is documented and contains hook subagent-stop

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

Cursor subagentStop, Claude Code SubagentStop, and Codex SubagentStop are documented events. The existing Stop hook already decides whether an active Change is SATISFIED, skips questions and interrupts, and fails open. The subagent hook must call that same decision. Codex is in scope because its hooks reference documents SubagentStop with decision block and stop_hook_active. Out of scope: SubagentStart, MCP, enabling hooks in this repository, merging, and publishing.
