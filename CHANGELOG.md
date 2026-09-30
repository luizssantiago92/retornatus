# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `init --preset rag` extends `python-platform` with retrieval layout globs (`prompts/`, `evals/`, `tests/eval/`, `mcp/`, `retrieval/`, `rag/`, `ingest*/`, `embeddings/`, `vectorstore*/`, `indexes/`, `*_index/`, `vector-index/`, and model-name config) and a stronger AI surface for those trees. When an AI path changes, `verify` requires `uv run pytest tests/eval -m "not live"` and an `ai fallback` note. It checks that the eval command ran. It does not score retrieval quality. Golden-set, prompt-snapshot, and MCP smoke commands stay comments because those paths may be absent. See `docs/guide/Presets.md`.
- `init --preset django` extends `python-platform` with Django layout globs (`manage.py`, `*/settings*.py`, `*/urls.py`, `apps/**`, `*/migrations/**`, `templates/**`, `static/**`, plus the inherited `src/`, `app/`, and `tests/` roots) and commented suggestions for `python manage.py check --deploy`, `python manage.py makemigrations --check --dry-run`, pytest-django, and `python manage.py test`. Paths under `**/migrations/**` trigger the ship surface and require a `ship rollback` note that describes how to reverse the migration. The migration command stays optional because Django may be absent. See `docs/guide/Presets.md`.
- `init --preset fastapi` extends `python-platform` with FastAPI layout globs (`routers/`, `api/`, `schemas/`, `alembic/`, plus the inherited `src/`, `app/`, and `tests/` roots), commented suggestions for an httpx TestClient pytest run, an OpenAPI JSON export, and optional Alembic commands (`alembic check`, `alembic upgrade head --sql`). Alembic migration paths trigger the ship surface and require a `ship rollback` note that describes the downgrade. The Alembic command stays optional because the tool may be absent. See `docs/guide/Presets.md`.
- `retornatus init --preset` and `init --list-presets`, plus `preset show`. Packaged TOML presets ship in the wheel. `python` sets uv/pytest, ruff, and mypy checks. `python-platform` extends it with path-triggered ship and AI evidence rules (`not required` when those paths are absent). Existing `config.toml` is kept unless `--force-config` is set. See `docs/guide/Presets.md`.
- Composite GitHub Action (`action.yml`) runs `verify` and the diff gates with `--json` and posts or updates one sticky pull-request comment (`<!-- retornatus-verdict -->`). `retornatus ci comment` renders that markdown from the JSON envelopes, including `change overview --format pr`. Fork pull requests with a read-only token skip the comment and still write the job summary. See `docs/guide/GitHub-Action.md`.
- `retornatus verify --json`, every `retornatus gate` subcommand `--json`, and `retornatus change overview --json` (also `--format json`) print a versioned verdict envelope and nothing else on stdout. Diagnostics go to stderr. Exit codes match text mode. The contract is `schemas/verdict-v1.schema.json`. See `docs/guide/JSON-output.md`.

### Changed

- README, the docs guide, and the landing page present the five init presets (`python`, `python-platform`, `fastapi`, `django`, `rag`), including `init --preset`, `init --list-presets`, `--force-config`, and `preset show`. Ship and AI surfaces are described as path-triggered checks that the command ran. They do not grade quality. See `docs/guide/Presets.md`.
- The docs site hero uses the same static card as the README, `docs/assets/retornatus-mascot-readme.webp`. `docs/assets/retornatus-mascot-neon.webp` is removed. Open Graph, Twitter, and favicon stay on `docs/assets/retornatus-mascot-square.webp`. A subtle glow on the hero container does not run when `prefers-reduced-motion: reduce`.
- The sticky pull-request comment leads with a one-line verdict summary, omits the overview gate list so the JSON gate table is the only gate result, and folds stale-snapshot warnings plus per-evidence labels into a collapsed details block.
- The approved mascot is the chrome-agent artwork (black suit, teal ouroboros, orange comet flame). Background inside the serpent ring is transparent, including the gaps by the head, headphones, and shoulders. The white shirt stays opaque, and every pixel inside the head, hand, and suit silhouette stays opaque, including the specular highlight on the chrome head. Glow edges keep a soft alpha. README and the docs site hero use `docs/assets/retornatus-mascot-readme.webp`. Open Graph, Twitter, and favicon use `docs/assets/retornatus-mascot-square.webp`.

### Fixed

- The README mascot looks the same on GitHub dark and light themes. It is a static frame of the site hero: the neon artwork with the resting teal/orange glow on the site background, in a rounded 960×528 card shown at 320 px. The artwork was re-cut from the white-background original. The white patch between the index finger and the visor is gone, and the ring and flame edges no longer carry a pale white/pink fringe.
- Skill Markdown saved with Windows CRLF line endings still loads. `gate skill-research --json` prints the verdict envelope instead of failing before any stdout.
- Tutorial 01 and How it works section 7 use the DONE criterion `docs/health.md documents GET /health`, so evidence subject `docs/health.md` matches claim subject `/health.md` and `verify` returns SATISFIED. A regression test runs the Tutorial 01 and Quick start command sequences.

### Security

- `retornatus init` appends a delimited `.gitignore` block for `.retornatus/index/`, `.retornatus/runtime/`, `*.pem`, `*.key`, `.env`, and `.env.*`, and keeps `!.env.example` plus `.retornatus/keys/*.pub` committable. A second run does not duplicate the block or remove existing lines.
- `retornatus init` and `retornatus receipt keygen` warn when git tracks a `*.pem` or `*.key` file. The signing private key is still written only outside the repository.

## [1.4.1] - 2026-09-30

### Fixed

- Runtime dependency floors now match imports that 1.4.0 already used. `typer>=0.27.2` covers `typer.exceptions` (absent before 0.27.2). `pydantic>=2.1` covers `StringConstraints` (absent in 2.0). `cryptography>=42` and `tomli-w>=1.0` stay, because a lowest-direct resolution on Python 3.11 still passes the suite. A `pip` install into an environment that already had Typer 0.12–0.27.1 no longer produces `ModuleNotFoundError: No module named 'typer.exceptions'`.
- CI job `Lowest direct dependencies` installs with `uv sync --resolution lowest-direct --group dev` on ubuntu-latest and Python 3.11, then runs pytest.
- A CLI smoke test imports `retornatus.cli.main` and checks that `retornatus --version` prints `__version__`.

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
- Dependabot bumped pinned GitHub Actions: setup-uv 10.2.0 (#30), configure-pages 6 (#32), upload-pages-artifact 5.0.0 (#33), and upload-artifact 7.0.1 (#34).
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
