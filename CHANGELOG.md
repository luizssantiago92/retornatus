# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.9.0] - 2026-10-01

### Added

- `retornatus hook subagent-stop` reminds a Cursor, Claude Code, or Codex subagent when the active Change is not `SATISFIED`. Cursor returns `followup_message` with `loop_limit` 1. Claude Code and Codex return `decision: "block"` and exit 0; `stop_hook_active` lets the subagent finish. Questions, Cursor `aborted` or `error`, no active Change, and a `SATISFIED` Change skip the reminder. `[hooks] subagent_stop` defaults to true. `integrate --hooks` installs it beside Stop, and `doctor` reports it. CI stays the source of truth (PR #69).
- The docs site favicon is a square crop of the mascot head (`docs/assets/favicon.ico` at 16, 32, and 48, and `docs/assets/apple-touch-icon.png` at 180). The landing page and docs hub link both. Open Graph and Twitter stay on the existing square WebP (PR #68).
- `[assurance] required_checks` names pytest, ruff, mypy, the docs HTML check, and `uv lock --check`. `verify` accepts those commands only when they exit 0 on a clean tree at the recorded commit. A later commit that only stores evidence does not stale that check (PR #65).

### Changed

- `ruff format` covers `src`, `tests`, and `scripts`. CI runs `uv run ruff format --check src tests scripts` in the existing lint job. `.git-blame-ignore-revs` names the formatting commit so GitHub blame can skip it (PR #66).
- Changelog sections for 1.0.0 through 1.3.0 now have sourced notes instead of stubs (PR #67).
- The package version is 1.9.0 in `pyproject.toml`, `__version__`, `uv.lock`, and `.retornatus/config.toml`. Docs that name the current release (Cloud agents, Quick start, the guide index, the GitHub Action version example, the README, and the landing highlights) say 1.9.0. The landing What’s new block names the subagent-stop hook. README What's new lists `hook subagent-stop` as shipped in 1.9.0.

### Fixed

- `gate suppressions` scans untracked, non-ignored files when neither `--base` nor `--staged` is set. Gitignored paths stay out. `--base` and `--staged` are unchanged (PR #63).

### Security

- Read-only CI jobs (`test`, `Lowest direct dependencies`, publish `verify`, and publish `package`) set `permissions: contents: read` on the job, so a workflow-level change cannot widen their token. Third-party actions stay pinned to full commit SHAs, checkout does not persist credentials, and Dependabot updates those pins weekly. The publish job still uses the `pypi` environment (PR #64).

## [1.8.0] - 2026-09-30

### Added

- `retornatus hook file-edit` warns when an agent edits a file outside the active Change scope. Claude Code uses `PreToolUse` (`Edit|Write|MultiEdit`, `additionalContext`, and `permissionDecision` deny). Cursor warns on `postToolUse` (`additional_context`) and blocks on `preToolUse` (`permission` deny, `agent_message`); `afterFileEdit` documents no output fields, so it is not installed. Codex uses `PreToolUse` on `apply_patch` (`additionalContext`, and `permissionDecision` deny). The path check is the same match as `gate scope`. `[hooks] scope_mode` is `warn` (default), `block`, or `off`. `block` denies only where the host documents a deny, and otherwise warns. In-scope paths, no active Change, and `.retornatus/` stay silent. Errors fail open. `integrate --hooks` installs the hook beside Stop and session-start, and `integrate --remove-hooks` deletes only those Retornatus entries. `doctor` reports file-edit and `scope_mode`. This repository stays hooks-disabled. CI stays the source of truth. See `docs/guide/Agent-hooks.md`.

### Docs

- README overhaul (PR #61, C-0029): shorter portfolio-friendly README with a 30-second verify demo, one What's new block for releases 1.5 through 1.7, and `hook file-edit` called out beside the other agent hooks.

### Changed

- The package version is 1.8.0 in `pyproject.toml`, `__version__`, `uv.lock`, and `.retornatus/config.toml`. Docs that name the current release (Cloud agents, Quick start, the guide index, the GitHub Action version example, the README, and the landing highlights) say 1.8.0. The landing What’s new block names the scope warning hook. README What's new lists `hook file-edit` as shipped in 1.8.0.

## [1.7.0] - 2026-09-30

### Added

- `retornatus hook session-start` injects the active Change when a Claude Code, Cursor, or Codex session starts. `integrate --hooks` installs it beside the Stop hook and `integrate --remove-hooks` deletes only those Retornatus entries. The text names each active Change id, title, goal, verify status, declared scope, and unproven claim ids with the `evidence run` command that would prove them. Output is capped at 2 KB. No active Change prints nothing. `[hooks] session_context = false` turns the injection off (the default is true). Internal errors fail open. `doctor` reports stop and session-start separately. CI stays the source of truth. See `docs/guide/Agent-hooks.md`.

### Fixed

- `retornatus hook stop` allows the turn to end when the last assistant message is a question to the user. Claude Code and Codex use `last_assistant_message` when it is a string; otherwise, and for Cursor `stop` (which has no such field), the hook reads the last 256 KiB of `transcript_path` as JSONL and ignores malformed lines. The final visible paragraph must end with `?` or `？`, or contain a documented ask phrase, after trailing code fences, inline code, and URLs are ignored. `[hooks] allow_questions` in `.retornatus/config.toml` defaults to true; only boolean false disables it. `doctor` prints the value. Cursor `status` `aborted` or `error`, `stop_hook_active`, Cursor `loop_limit` 1, fail-open, and the block message are unchanged. See `docs/guide/Agent-hooks.md`.

### Changed

- The package version is 1.7.0 in `pyproject.toml`, `__version__`, `uv.lock`, and `.retornatus/config.toml`. Docs that name the current release (Cloud agents, Quick start, the guide index, the GitHub Action version example, the README, and the landing highlights) say 1.7.0. The landing What’s new block names the SessionStart hook.

## [1.6.0] - 2026-09-30

### Added

- `retornatus hook stop` and `retornatus integrate --hooks` install an opt-in Stop hook for Claude Code, Cursor, and Codex. The hook runs the same check as `verify --json` in-process. A `SATISFIED` Change, or no active Change, allows the turn to end. Otherwise the host is asked to continue, with the unproven claim ids and an `evidence run` command. `stop_hook_active` (Claude and Codex) and Cursor `loop_limit` 1 keep that continuation from looping. Internal errors fail open. `integrate --remove-hooks` deletes only the Retornatus entry. `doctor` reports whether each host hook is installed. CI stays the source of truth. See `docs/guide/Agent-hooks.md`.

### Changed

- The package version is 1.6.0 in `pyproject.toml`, `__version__`, `uv.lock`, and `.retornatus/config.toml`. Docs that name the current release (Cloud agents, Quick start, the guide index, the GitHub Action version example, the README, and the landing highlights) say 1.6.0. The landing What’s new block names agent hooks.

## [1.5.0] - 2026-09-30

### Added

- `init --preset worker` extends `python-platform` for background jobs and queues (Celery, RQ, Dramatiq, arq, scheduled jobs). It adds layout globs (`tasks/`, `workers/`, `jobs/`, `schedules/`, `celery_app.py`, `celery.py`, `celeryconfig.py`, `worker.py`, plus the inherited `src/`, `app/`, and `tests/` roots). Task, worker, job, Celery app, beat and schedule, and queue config paths (`**/tasks/**`, `**/tasks.py`, `**/workers/**`, `**/worker.py`, `**/jobs/**`, `**/celery_app.py`, `**/celery.py`, `**/celeryconfig.py`, `**/beat*`, `**/schedules/**`, `**/queues.py`, `**/queues.toml`, `**/queues.y*ml`) trigger the ship surface. The preset sets the ship note subject to `ship rollback and job retry`, so `verify` requires a note that says how the job retries and why running it again is safe. Retornatus has only ship and AI surface kinds, so the preset reuses the ship surface instead of adding a third kind. `celery -A app inspect ping` is an optional check, and eager-task pytest, `rq worker --burst`, and `arq --check` stay comments because a broker or the tool may be absent. `verify` checks that the note exists. It does not judge whether a job is idempotent. See `docs/guide/Presets.md`.
- `init --preset rag` extends `python-platform` with retrieval layout globs (`prompts/`, `evals/`, `tests/eval/`, `mcp/`, `retrieval/`, `rag/`, `ingest*/`, `embeddings/`, `vectorstore*/`, `indexes/`, `*_index/`, `vector-index/`, and model-name config) and a stronger AI surface for those trees. When an AI path changes, `verify` requires `uv run pytest tests/eval -m "not live"` and an `ai fallback` note. It checks that the eval command ran. It does not score retrieval quality. Golden-set, prompt-snapshot, and MCP smoke commands stay comments because those paths may be absent. See `docs/guide/Presets.md`.
- `init --preset django` extends `python-platform` with Django layout globs (`manage.py`, `*/settings*.py`, `*/urls.py`, `apps/**`, `*/migrations/**`, `templates/**`, `static/**`, plus the inherited `src/`, `app/`, and `tests/` roots) and commented suggestions for `python manage.py check --deploy`, `python manage.py makemigrations --check --dry-run`, pytest-django, and `python manage.py test`. Paths under `**/migrations/**` trigger the ship surface and require a `ship rollback` note that describes how to reverse the migration. The migration command stays optional because Django may be absent. See `docs/guide/Presets.md`.
- `init --preset fastapi` extends `python-platform` with FastAPI layout globs (`routers/`, `api/`, `schemas/`, `alembic/`, plus the inherited `src/`, `app/`, and `tests/` roots), commented suggestions for an httpx TestClient pytest run, an OpenAPI JSON export, and optional Alembic commands (`alembic check`, `alembic upgrade head --sql`). Alembic migration paths trigger the ship surface and require a `ship rollback` note that describes the downgrade. The Alembic command stays optional because the tool may be absent. See `docs/guide/Presets.md`.
- `retornatus init --preset` and `init --list-presets`, plus `preset show`. Packaged TOML presets ship in the wheel. `python` sets uv/pytest, ruff, and mypy checks. `python-platform` extends it with path-triggered ship and AI evidence rules (`not required` when those paths are absent). Existing `config.toml` is kept unless `--force-config` is set. See `docs/guide/Presets.md`.
- Composite GitHub Action (`action.yml`) runs `verify` and the diff gates with `--json` and posts or updates one sticky pull-request comment (`<!-- retornatus-verdict -->`). `retornatus ci comment` renders that markdown from the JSON envelopes, including `change overview --format pr`. Fork pull requests with a read-only token skip the comment and still write the job summary. See `docs/guide/GitHub-Action.md`.
- `retornatus verify --json`, every `retornatus gate` subcommand `--json`, and `retornatus change overview --json` (also `--format json`) print a versioned verdict envelope and nothing else on stdout. Diagnostics go to stderr. Exit codes match text mode. The contract is `schemas/verdict-v1.schema.json`. See `docs/guide/JSON-output.md`.

### Changed

- Package metadata uses the PEP 639 license expression `MIT` with `license-files = ["LICENSE"]`. Trove classifiers name a production console tool for developers, OS-independent Python 3.11, 3.12, and 3.13, and software quality assurance and testing. Project URLs point at the website, the guide, the repository, issues, and this changelog. The build backend requires `hatchling>=1.27` so the wheel metadata includes `License-Expression`. Keywords also include `agents` and `verification`. There is no `License ::` classifier.
- README file links use `https://github.com/luizssantiago92/retornatus/blob/main/...` and the mascot image uses `https://raw.githubusercontent.com/luizssantiago92/retornatus/main/...`. In-page `#anchors` stay relative. A test fails when README contains a relative non-anchor link.
- The package version is 1.5.0 in `pyproject.toml`, `__version__`, `uv.lock`, and `.retornatus/config.toml`. Docs that name the current release (Cloud agents, Quick start, the guide index, the GitHub Action version example, and the landing highlights) say 1.5.0.
- README, the docs guide, and the landing page present the six init presets (`python`, `python-platform`, `fastapi`, `django`, `rag`, `worker`), including `init --preset`, `init --list-presets`, `--force-config`, and `preset show`. Ship and AI surfaces are described as path-triggered checks that the command ran. They do not grade quality. See `docs/guide/Presets.md`.
- The docs site hero uses the same static card as the README, `docs/assets/retornatus-mascot-readme.webp`. `docs/assets/retornatus-mascot-neon.webp` is removed. Open Graph, Twitter, and favicon stay on `docs/assets/retornatus-mascot-square.webp`. A subtle glow on the hero container does not run when `prefers-reduced-motion: reduce`.
- The sticky pull-request comment leads with a one-line verdict summary, omits the overview gate list so the JSON gate table is the only gate result, and folds stale-snapshot warnings plus per-evidence labels into a collapsed details block.
- The approved mascot is the chrome-agent artwork (black suit, teal ouroboros, orange comet flame). Background inside the serpent ring is transparent, including the gaps by the head, headphones, and shoulders. The white shirt stays opaque, and every pixel inside the head, hand, and suit silhouette stays opaque, including the specular highlight on the chrome head. Glow edges keep a soft alpha. README and the docs site hero use `docs/assets/retornatus-mascot-readme.webp`. Open Graph, Twitter, and favicon use `docs/assets/retornatus-mascot-square.webp`.

### Fixed

- The packaged hub describes `verify --receipt` as an Ed25519 receipt (public key in `.retornatus/keys/`). `retornatus integrate` copies that hub to `.cursor/skills/retornatus/SKILL.md`. A test fails when the two copies diverge.
- `.retornatus/config.toml` records the installed release. `retornatus doctor` warns when `[retornatus] version` differs from the installed package.
- The README “What you get” link uses the em dash heading anchor. Credits link to the repository `LICENSE` on GitHub, and the product contract link text is `docs/archive/PRD.md`.
- The site Open Graph image is an absolute `https://luizssantiago92.github.io/retornatus/...` URL. The What’s new block names the release and init presets. The README 1.4.0 note pins the current release instead of `retornatus==1.4.1`.
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

## [1.3.0] - 2026-09-26

Already on PyPI. Git tag `v1.3.0` was backfilled on 2026-09-29 and points at `a540efb` (commit date 2026-09-26). The range `v1.2.1..v1.3.0` is pull requests #12 and #13 plus the trees of #14 and #15.

### Added

- Ember replaces Seedcore as the live mascot on the README and the docs site. The README and the landing page document `intake analyze` and `skill need` (#12).
- The site hero floats Ember over teal-gold energy waves. The black plate is keyed to a transparent PNG and cropped to the artwork (#13).
- `verify --receipt` and `receipt verify` write an HMAC-SHA256 receipt (`retornatus-receipt/v1`). The key file is `.retornatus/runtime/receipt.key`, which is gitignored (#15).
- `action budget --max N` and `gate budget` set an Action attempt ceiling (#15).
- Root `AGENTS.md` maps the host loop. CI runs `scripts/build_docs_html.py --check`. `docs/guide/From-spec-guardrails.md` and `docs/guide/Landscape.md` record the Spec Guardrails migration and a comparison with nearby harnesses (#15).

### Changed

- The package version is 1.3.0 in `pyproject.toml` and `__version__` (#15).

### Fixed

- Guide HTML is rebuilt for intake and skills, the README "What you get" anchor is repaired, suggested GitHub topics are documented, and the machine-local path is dropped from project continuity (#14).

### Security

- The HMAC receipt key is created with mode `0600`. `RETORNATUS_RECEIPT_KEY` can supply the key.

## [1.2.1] - 2026-09-23

Already on PyPI. Git tag `v1.2.1` was backfilled on 2026-09-29 and points at `f4d96d3` (commit date 2026-09-23).

### Added

- `intake analyze` reviews a freeform prompt in stages and creates a Skill only after the human answers `CREATE=yes`. `skill need` can run before a Contract or Action exists. Manual `skill create` stays available (#10).

### Changed

- The package version is 1.2.1 in `pyproject.toml`, `__version__`, `uv.lock`, and the README What's new block, so a tag can publish the intake-gated Skill flow (#11).

## [1.2.0] - 2026-09-22

GitHub Release v1.2.0. Annotated tag `v1.2.0` points at `2d38d60`.

### Added

- Vague demands get focused questions with options. `change elicit --answer` and `change elicit --write` record answers, and kickoff facts feed Contract readiness. The hub and the guide frame Understand → Agree → Build → Prove → Learn (tag `2d38d60`; GitHub Release v1.2.0).
- Git blast-radius governance: merge and publish stay owner-only. `.cursor/rules/git-governance.mdc`, `docs/guide/Git-governance.md`, the hub hard rules, and rule candidates R-0001 and R-0002 record it (`ae59584`).
- Seedcore mascot, a landing page, and a GitHub Pages workflow (`d903278`).
- HTML docs: a hub, Quick start, and the rest of the guide rendered for GitHub Pages by `scripts/build_docs_html.py`. The README leads with Website, Docs, and Quick start links (`2c9b23d`, `f80cb03`).

### Changed

- The public site and README lead with benefits, and the README mechanism story is expanded (`1e0fab5`, `c7c6bf5`).
- Seedcore is a clean alpha cutout with a softer hero glow (`b0ffb86`).
- CI pins mypy 1.15.0 so the typecheck job does not drift (`3b373dd`).
- The package version is 1.2.0.

### Fixed

- `stdout.reconfigure` is read with `getattr`, so mypy no longer reports union-attr on `TextIO` (`a307b66`).
- The UTF-8 stdio setup no longer trips ruff E402. Reconfigure lives in a helper so imports stay at the top of the module (`4d038dc`).

## [1.1.1] - 2026-09-22

Annotated tag `v1.1.1` points at `403f3c6`.

### Fixed

- The CLI reconfigures stdout and stderr to UTF-8 with `errors=replace` when `reconfigure` exists, so `change overview` and `doctor` stay readable on a Windows console that defaults to a legacy code page. Overview, doctor, and ops lines use ASCII hyphens instead of em dashes (`f46a2d2`). The package version is 1.1.1 (`403f3c6`).

## [1.1.0] - 2026-09-22

Annotated tag `v1.1.0` points at `f69d822`.

### Added

- `change overview` and `change classify`, including `change create --lane`. `doctor` reports Process and Brakes scores. `lesson from-gate` records a lesson from a failed gate. `ops list`, `ops show`, and `ops run` run operational loops. A consumer CI template lives at `templates/ci/retornatus-pr.yml`. The hub skill states token rules (`f69d822`). Change C-0001 records the same slice; its files were committed in `1e0fab5`.

### Changed

- Install docs prefer PyPI now that 1.0.0 is published (`34a4ba5`).
- The README covers install, pillars, gates, skills, governance, and the CLI surface (`758cc37`).

## [1.0.0] - 2026-09-21

First tagged release. Annotated tag `v1.0.0` points at `78fd66b`. Commits on this tag used 0.x labels in their subjects. Those labels were not separate git tags.

### Added

- `retornatus init`, the console CLI, and a minimal `.retornatus` project tree. Schema-versioned domain models and ID types. File persistence with atomic writes, the change workflow, wake and environment adapters, execution context, assurance, the question loop, a SQLite FTS index, adaptation, and governance policy (`76ea1e5`, `7515eca`, `ec700d6`).
- On-demand Skills: create with a RESEARCH scaffold, link to an Action, evolve, and export to a native Cursor skill (`7dae623`).
- Hub skill, exit-code gates, evidence, finding, and question commands, `loop next`, `project-init`, `integrate`, LICENSE, and a PyPI publish workflow (`1ff9796`).
- Situation elicitation, claim-bound evidence with staleness checks, a human decision before rule activation, governed bypass, and brownfield wake (#1).
- `commit:<sha>` evidence freshness, independent assurance plan and review, and task `depends` and `resources` (#2).
- Path-level evidence freshness, isolation boundaries for worktrees, sandbox, and subagents, and host execution records that do not become an agent runtime (#3).
- `task start`, `task complete`, `task fail`, and `task reopen`, contract reopen that archives the prior version, and `skill need` for trivial work (#4).
- `change activate`, richer `status`, `doctor`, auto-numbered findings and questions, and `question reopen` (#5).
- `policy check` and `gate policy` (ALLOW, DENY, REQUIRE_HUMAN), `run --strict-policy`, native Rule projection into Cursor, Claude, and Codex bridges, and adapter-aware `integrate` (#6).
- Product guide under `docs/guide` (overview, quick start, concepts, gates, governance, CLI, tutorials) and CONTRIBUTING (#7).
- Credits, lineage, and prior-art notes in `docs/credits-and-lineage.md` (#8).
- Quick start and the guide document the TestPyPI install for the published 1.0.0 package. Derived `.retornatus` files are gitignored (`78fd66b`).

### Changed

- The README is a product entry point (#7). CI can publish to TestPyPI or PyPI (`384a10f`).

### Fixed

- The console script works under `uv tool install` (`21a9227`).
- The packaging entrypoint is `entrypoint()`, so it no longer shadows Typer command names. Unused imports and a few types are cleaned up. The duplicate root PRD copy is removed. GitHub Actions runs ruff, mypy, and pytest (#9).
