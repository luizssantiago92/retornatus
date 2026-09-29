# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.4.0] - 2026-09-29

Work landed after PyPI **1.3.0**, including stacked pull requests #17, #18, #19, #28, #29, and the release-hardening follow-up.

### Security

- GitHub Actions in `.github/workflows` and the consumer PR template are pinned to full commit SHAs. Workflows grant `contents: read` at the top level and add write permissions only on the job that needs them. Checkout does not persist credentials. The publish workflow does not restore the uv cache.
- The Ed25519 private key file is created with mode `0600` (POSIX) instead of being written and then chmod'd.
- `SECURITY.md` asks for private reports via GitHub Security Advisories. CodeQL analyzes Python on pull requests and on `main`.

### Added

- Guide for cloud and remote agents: install the CLI on the clean VM, run `hooks install` on every fresh clone, leave receipts unsigned there, and treat the GitHub pull-request workflow (`verify`, `gate suppressions`, `gate scope`) as the enforcement.
- Owner-declared `[assurance] required_checks`. `verify` accepts execution evidence only when the argv matches a check, the exit code is 0, the recorded commit is HEAD, and the worktree is clean. `verify --run-checks` and `checks run` execute those commands (#17, #19).
- Ed25519 receipts. The private key stays off the git tree; `receipt verify` uses the committed public key (#18).
- `gate suppressions` and `gate scope` against the real diff, plus optional git hooks (#19).
- Publish workflow: tests, ruff, mypy, and the docs check run before a build; distribution contents are rejected when test fixtures, `tests/`, `scripts/`, or assets ship; the tag must match the package version and sit on `main`; a new release needs a matching changelog section; versions already on PyPI are skipped; publish uses PyPI Trusted Publishing (no API token). TestPyPI is an optional, non-blocking manual path.
- CI matrix for Python 3.11, 3.12, and 3.13 on Ubuntu, Windows, and macOS, with coverage. Weekly Dependabot updates for uv and GitHub Actions.
- DONE-criteria lint on `gate contract` (placeholders, duplicates, vague wording; warning when a criterion has no observable outcome).
- GitHub Copilot adapter (`.github/copilot-instructions.md`). Claude and Codex bridge blocks refresh when their text changes.
- CI job `Retornatus gates` runs this repository's own gates: doctor, wake, gate-scan, `verify`, `gate suppressions`, and `gate scope` (#36).
- `change classify --from-diff` combines changed-file count, lines changed, and scope-gate sensitive globs with the existing text heuristics.
- `change overview --format pr` prints a markdown pull-request body (claims, executed vs self-reported evidence, exit codes, commit, stale/unverified, required checks, gates).
- Stricter consumer PR workflow template: pinned install, blocking `verify` for Changes the PR touches, `gate suppressions --base` and `gate scope --base`, and a configurable failure when code changes but no Change was touched.

### Changed

- Ruff is 0.16.9 (#31). `(str, Enum)` types are `enum.StrEnum` (Python 3.11+). JSON, receipts, and evidence still store the enum value. The rule-activation error still prints `DecisionKind.<NAME>`, which is what `str()` used to produce.
- Dependabot bumped pinned GitHub Actions: `astral-sh/setup-uv` 10.2.0 (#30), `actions/configure-pages` 6 (#32), `actions/upload-pages-artifact` 5.0.0 (#33), and `actions/upload-artifact` 7.0.1 (#34).
- `gate suppressions` ignores markers inside Markdown fenced code blocks and inline code spans (`.md`, `.markdown`, `.mdx`, `.mdc`) (#36).
- C-0001 DONE criteria were rewritten. C-0003 and C-0004 task resources were backfilled (#36).
- Test-only modules `host_boundary.py` and `brownfield_fixture.py` live under `tests/support/` and are not installed.
- Docs HTML is generated in the GitHub Pages workflow. Markdown stays in git; generated HTML does not.
- Product requirements moved from `prd/PRD.md` to `docs/archive/PRD.md`.
- Ruff and mypy configuration live in `pyproject.toml`. Authors is Luiz Santiago.
- The public mascot is the single image the README and the site reference, under `docs/assets/`.

### Fixed

- README no longer says PyPI is waiting on a `v1.3.0` tag. 1.3.0 is already published.
- `retornatus init` writes the installed Retornatus version into `config.toml` instead of hard-coded `0.8.0` (#36).
- `project.md` references `docs/archive/PRD.md`. The docs credits link points at the Pages site and the source markdown file (#36).
- The `Retornatus gates` job and `templates/ci/retornatus-pr.yml` pin `astral-sh/setup-uv` to the same commit the other jobs use (`c18668ad3cf93ea998bef934396af7bb5c839dc7`, v10.2.0).

## [1.3.0]

Already on PyPI. Git tag `v1.3.0` was backfilled on 2026-09-29 and points at `a540efb`.

## [1.2.1]

Already on PyPI. Git tag `v1.2.1` was backfilled on 2026-09-29 and points at `f4d96d3`.
