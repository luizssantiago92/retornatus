<!-- retornatus-meta
{
  "change_id": "C-0018",
  "schema_version": 1
}
-->

# Situation

## Demand

CLI users must initialize a RAG, LLM, or MCP repository with retornatus init --preset rag. The preset extends python-platform, adds scope and AI globs for prompts, evals, tests/eval, mcp, retrieval, rag, ingest, embeddings, vectorstore, sensible index directories, and model-name config, requires the inherited offline eval command plus an ai fallback note when those paths change, and comments suggested commands for a golden-set retrieval script, prompt snapshot tests, and an MCP server smoke test. Out of scope: a version bump, merging, and publishing. verify checks that the eval command ran; it does not score eval quality.

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

- Demand stated: CLI users must initialize a RAG, LLM, or MCP repository with retornatus init --preset rag. The preset extends python-platform, adds scope and AI globs for prompts, evals, tests/eval, mcp, retrieval, rag, ingest, embeddings, vectorstore, sensible index directories, and model-name config, requires the inherited offline eval command plus an ai fallback note when those paths change, and comments suggested commands for a golden-set retrieval script, prompt snapshot tests, and an MCP server smoke test. Out of scope: a version bump, merging, and publishing. verify checks that the eval command ran; it does not score eval quality.
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
- Proposed WHAT: The rag preset extends python-platform, renders a valid config, is listed by init --list-presets, and makes AI paths trigger the AI surface while non-AI paths stay not required.
- DONE criterion: pytest exits 0
- DONE criterion: ruff check of src tests and scripts exits 0
- DONE criterion: mypy exits 0
- DONE criterion: The HTML documentation check exits 0
- DONE criterion: uv lock check exits 0
- DONE criterion: pytest confirms rag extends python-platform and python
- DONE criterion: init --list-presets prints rag
- DONE criterion: pytest confirms AI paths trigger the AI surface
- DONE criterion: pytest confirms non-AI paths stay not required
- DONE criterion: CHANGELOG Unreleased records the rag preset

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

Index directories use indexes/, *_index/, and vector-index/ rather than a bare *index*/ glob, so docs/index/ does not trigger the AI surface. Model-name config is config files whose names contain model, not src/**/models.py. Spec Guardrails appendix D requires an offline eval command and a fallback note; this preset keeps that pair and does not score the golden set.
