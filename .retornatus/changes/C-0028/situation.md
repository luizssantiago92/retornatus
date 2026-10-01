<!-- retornatus-meta
{
  "change_id": "C-0028",
  "schema_version": 1
}
-->

# Situation

## Demand

Add an early warning when an agent edits a file outside the active Change declared scope.

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

- Demand stated: Add an early warning when an agent edits a file outside the active Change declared scope.
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
- Proposed WHAT: Add retornatus hook file-edit for Claude Code, Cursor, and Codex. Compare the edited path with gate scope matching. Warn by default. Honor scope_mode warn, block, or off. Install and remove it with integrate --hooks. Document the host mechanisms.
- DONE criterion: tests/test_file_edit_hook.py exits 0
- DONE criterion: src/retornatus/cli/hook.py contains hook file-edit for claude, cursor, and codex
- DONE criterion: The file /guide/Agent-hooks.md contains file-edit, scope_mode, additionalContext, and additional_context
- DONE criterion: The file /CLI.md contains hook file-edit
- DONE criterion: The file /CHANGELOG.md contains an Unreleased file-edit entry
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

Phase 2b warns when a file edit leaves the active Change scope. Host docs checked 2026-10-01. Claude Code PreToolUse matches Edit, Write, and MultiEdit, reads tool_input.file_path, returns hookSpecificOutput.additionalContext to warn, and permissionDecision deny to block (https://code.claude.com/docs/en/hooks). The current reference lists Write and Edit with file_path; MultiEdit stays in the matcher so an older client that still sends that name with file_path is covered. Cursor afterFileEdit carries file_path and matches Write, but the reference documents no output fields, so that event is not installed (https://cursor.com/docs/hooks). beforeReadFile can deny a read with user_message shown to the user, which is not an edit warning to the agent, so it is not installed. Cursor preToolUse can deny Write with agent_message, and postToolUse injects additional_context. Codex PreToolUse matches apply_patch, Edit, or Write. The payload tool_name stays apply_patch and the patch body is tool_input.command. Paths come from the documented apply_patch headers (https://github.com/openai/codex/blob/main/codex-rs/prompts/templates/apply_patch_tool_instructions.md). Codex returns additionalContext to warn and permissionDecision deny to block (https://developers.openai.com/codex/hooks). Default mode is warn and never blocks. scope_mode block denies only where the host documents a deny, and otherwise warns. In-scope edits, no active Change, and .retornatus/ are silent. Errors fail open. This repository stays hooks-disabled. CI remains the source of truth.
