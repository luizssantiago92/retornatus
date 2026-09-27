# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Work landed after PyPI **1.3.0**, including stacked pull requests #17, #18, #19, and the release-hardening follow-up. The package version stays 1.3.0 until a maintainer cuts the next release (move these notes under a new `## [x.y.z]` heading).

### Added

- Owner-declared `[assurance] required_checks`. `verify` accepts execution evidence only when the argv matches a check, the exit code is 0, the recorded commit is HEAD, and the worktree is clean. `verify --run-checks` and `checks run` execute those commands (#17, #19).
- Ed25519 receipts. The private key stays off the git tree; `receipt verify` uses the committed public key (#18).
- `gate suppressions` and `gate scope` against the real diff, plus optional git hooks (#19).
- Publish workflow: tests, ruff, mypy, and the docs check run before a build; distribution contents are rejected when test fixtures, `tests/`, `scripts/`, or assets ship; the tag must match the package version and sit on `main`; a new release needs a matching changelog section; versions already on PyPI are skipped; publish uses PyPI Trusted Publishing (no API token). TestPyPI is an optional, non-blocking manual path.
- CI matrix for Python 3.11, 3.12, and 3.13 on Ubuntu, Windows, and macOS, with coverage. Weekly Dependabot updates for uv and GitHub Actions.
- DONE-criteria lint on `gate contract` (placeholders, duplicates, vague wording; warning when a criterion has no observable outcome).
- GitHub Copilot adapter (`.github/copilot-instructions.md`). Claude and Codex bridge blocks refresh when their text changes.
- `change classify --from-diff` combines changed-file count, lines changed, and scope-gate sensitive globs with the existing text heuristics.
- `change overview --format pr` prints a markdown pull-request body (claims, executed vs self-reported evidence, exit codes, commit, stale/unverified, required checks, gates).
- Stricter consumer PR workflow template: pinned install, blocking `verify` for Changes the PR touches, `gate suppressions --base` and `gate scope --base`, and a configurable failure when code changes but no Change was touched.

### Changed

- Test-only modules `host_boundary.py` and `brownfield_fixture.py` live under `tests/support/` and are not installed.
- Docs HTML is generated in the GitHub Pages workflow. Markdown stays in git; generated HTML does not.
- Product requirements moved from `prd/PRD.md` to `docs/archive/PRD.md`.
- Ruff and mypy configuration live in `pyproject.toml`. Authors is Luiz Santiago.
- The public mascot is the single image the README and the site reference, under `docs/assets/`.

### Fixed

- README no longer says PyPI is waiting on a `v1.3.0` tag. 1.3.0 is already published.

## [1.3.0]

Already on PyPI. No git tag `v1.3.0` was pushed for that publish. See the version bump commit `a540efb`.

## [1.2.1]

Already on PyPI. No git tag `v1.2.1` was pushed for that publish. See the version bump commit `f4d96d3`.
