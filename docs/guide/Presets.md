# Presets

`retornatus init` can write a starting `.retornatus/config.toml` from a **preset**. Presets are TOML files inside the installed package (`retornatus/bootstrap/presets/`). They are not hard-coded command branches, and they are not the Spec Guardrails `.specs/design.md` workflow.

Without `--preset`, `init` behaves as it does today: a minimal config, the directory tree, and the idempotent `.gitignore` block (local index, runtime cache, private keys, and env files). Public keys under `.retornatus/keys/*.pub` stay committable.

An existing `config.toml` is left in place unless you pass `--force-config`. `--force` alone still recreates the **minimal** config when no preset is selected. It does not apply a preset over a file that is already there.

## Commands

```bash
retornatus init --list-presets
retornatus preset show python
retornatus preset show python-platform
retornatus preset show fastapi
retornatus preset show django
retornatus init --preset python
retornatus init --preset python-platform
retornatus init --preset fastapi
retornatus init --preset django
retornatus init --preset python-platform --force-config
```

An unknown name exits with code 2 and lists the presets that ship in this install.

`preset show` prints the config `init --preset` would write, including the comment block of suggested commands.

## python

For a Python 3.11+ repository whose proof is tests and static checks.

| Check | Command | Evidence type |
| --- | --- | --- |
| pytest | `uv run pytest -q` | `test_result` |
| ruff | `uv run ruff check src app tests` | `lint_result` |
| mypy | `uv run mypy` | `lint_result` |

`[governance.scope] code_globs` is `src/**`, `app/**`, and `tests/**`. Those globs describe the roots the ruff command names. They do not change `gate scope`. If `app/` or `src/` is not a directory in your tree, edit the ruff argv or the command fails.

`[assurance] required_checks` means `verify` accepts execution evidence only when the argv matches one of these commands, the exit code is 0, the recorded commit is HEAD, and the worktree is clean. See [Gates](Gates.md).

## python-platform

For people who ship **Python backend + DevOps + AI** from one repository: services, Compose or Terraform or Helm or GitHub Actions, and LLM, RAG, agents, MCP, or an offline eval suite.

Use `python` when pytest, ruff, and mypy are the whole bar. Use `python-platform` when deploy files or model behavior are normal work. It **extends** `python`, so the three checks and the code globs above are included.

This preset does not turn Retornatus into a live observability product. It adds two path-triggered rules to `verify`.

### When a rule runs

`verify` looks at Task `resources` (the Change's scoped paths) and at git worktree changes (staged, unstaged, and untracked). A committed file counts when a Task lists it. If nothing in that set matches the globs, the rule's status is `not required` and it does not affect the verdict.

`verify --json` includes a `surfaces` array only when `[surfaces]` is in config. Each item has `name` (`ship` or `ai`), `status` (`not required`, `satisfied`, or `unsatisfied`), `matched_paths`, `required_checks`, and `missing`.

### Ship surface

Triggered by:

| Glob | Suggested command |
| --- | --- |
| `**/Dockerfile` | `docker build .` |
| `**/docker-compose*.y*ml` | `docker compose config --quiet` |
| `**/*.tf`, `**/terraform/**` | `terraform validate` |
| `**/charts/**`, `**/helm/**` | `helm template .` |
| `**/.github/workflows/**` | `actionlint` |

Those commands are **comments** in the generated config. `verify` uses them as the packaged defaults until you write `[[surfaces.ship.checks]]`. A checks table you write **replaces the whole default list**, so copy every check you still want.

Each matching check needs executed evidence: `evidence run`, exit code 0, argv equal to that check. One narrative note covers the Change, not one note per tool. Record it with subject `ship rollback` (override with `note_subject`):

```bash
retornatus evidence add -c C-0001 -t repository_observation \
  -s "ship rollback" --source "Redeploy the previous image tag" --producer owner
```

Placeholder text (`tbd`, `todo`, `n/a`, `(fill in)`) does not count. A self-reported command does not count as the infra check.

### AI surface

Triggered by `**/prompts/**`, `**/mcp/**`, `**/evals/**`, `**/tests/eval/**`, `**/*llm*`, `**/*rag*`, and `**/*embed*`.

The default eval command is written in config and is what `verify` requires:

```bash
uv run pytest tests/eval -m "not live"
```

Change `surfaces.ai.run` when the suite lives somewhere else. The same Change also needs a narrative note with subject `ai fallback` describing how the feature degrades when the model is down or wrong. Placeholder text does not count.

### Override the globs

```toml
[surfaces.ship]
globs = ["deploy/**", "**/*.tf"]

[surfaces.ai]
globs = ["prompts/**", "evals/**"]
```

Narrowing `globs` drops paths that no longer match. A path that matches `globs` but no check is `unsatisfied` until you configure a command for it.

## fastapi

For a FastAPI service. It **extends** `python-platform`, so the pytest, ruff, and mypy checks, the `src/**`, `app/**`, and `tests/**` code globs, and the ship and AI surfaces above are included. `src/**` already covers `src/<package>/`.

Extra `[governance.scope] code_globs`:

| Glob | Layout it names |
| --- | --- |
| `routers/**` | Routers at the repository root |
| `api/**` | An `api/` package at the repository root |
| `schemas/**` | Pydantic schemas at the repository root |
| `alembic/**` | Alembic migrations at the repository root |

Those globs describe roots. They do not change `gate scope`. Nested routers under `app/` or `src/` are already covered by the inherited globs.

### Suggested evidence

These commands are **comments** in the generated config. They are not `[assurance] required_checks`. httpx, the application import path, and Alembic may be absent, so `verify` does not demand them.

| Suggestion | Command | Why it stays a comment |
| --- | --- | --- |
| httpx | `uv run pytest -q` | Same argv as the inherited pytest check. Write the tests with `fastapi.testclient.TestClient` or `httpx` `ASGITransport`. httpx may be absent |
| OpenAPI | `uv run python -c "import json; from app.main import app; print(json.dumps(app.openapi()))"` | Example export. The module path is yours (`app.main` here). Write `openapi.json` and diff it in review |
| Alembic SQL | `uv run alembic upgrade head --sql` | Optional alternative to `alembic check`. Prints SQL and does not apply it. Alembic may be absent |

### Alembic migrations are a ship surface

`alembic/**` and `**/alembic/**` are added to the ship globs. A Task resource or a worktree path under Alembic makes the ship rule run. `verify` then requires one narrative note with subject `ship rollback` (the subject inherited from `python-platform`). For a migration, that note has to describe the downgrade, for example `alembic downgrade -1` or restoring the previous revision. Placeholder text does not count.

The packaged Alembic check is optional:

```toml
[[surfaces.ship.checks]]
name = "alembic"
optional = true
globs = ["alembic/**", "**/alembic/**"]
run = ["uv", "run", "alembic", "check"]
```

`optional = true` covers those paths so `verify` does not report `no ship check covers`. It does **not** require `alembic check` to have been executed. `alembic check` needs a database, and Alembic may not be installed. The command stays in the comment block next to `alembic upgrade head --sql`.

Docker, Compose, Terraform, Helm, and workflow paths still require their executed checks. A `[[surfaces.ship.checks]]` table you write still replaces the whole packaged list, including this optional Alembic check, so copy every check you still want.

## django

For a Django project. It **extends** `python-platform`, so the pytest, ruff, and mypy checks, the `src/**`, `app/**`, and `tests/**` code globs, and the ship and AI surfaces above are included. `src/**` already covers `src/<package>/`.

Extra `[governance.scope] code_globs`:

| Glob | Layout it names |
| --- | --- |
| `manage.py` | The Django entry script at the repository root |
| `*/settings*.py` | Settings modules one directory down (`config/settings.py`, `myproject/settings_local.py`) |
| `*/urls.py` | URLConf modules one directory down (`myproject/urls.py`) |
| `apps/**` | An `apps/` package |
| `*/migrations/**` | Migrations one directory down (`polls/migrations/`) |
| `templates/**` | Project templates |
| `static/**` | Project static files |

Those globs describe roots. They do not change `gate scope`. Nested modules under `app/` or `src/` are already covered by the inherited globs. `*/migrations/**` is only a scope glob. The ship surface uses the wider `**/migrations/**`.

### Suggested evidence

These commands are **comments** in the generated config. They are not `[assurance] required_checks`. Django, pytest-django, and a project-specific settings module may be absent, so `verify` does not demand them.

| Suggestion | Command | Why it stays a comment |
| --- | --- | --- |
| `check --deploy` | `python manage.py check --deploy` | Deployment system checks. Django may be absent |
| pytest-django | `uv run pytest -q` | Same argv as the inherited pytest check. Install pytest-django and set `DJANGO_SETTINGS_MODULE` (or pass `--ds`). The plugin may be absent |
| `manage.py test` | `python manage.py test` | Django's test runner when pytest-django is not the suite. Django may be absent |

`python manage.py makemigrations --check --dry-run` is also commented. It is the optional ship check below, not a second required check. It reports models that lack a migration and does not write files.

### Migrations are a ship surface

`**/migrations/**` is added to the ship globs. A Task resource or a worktree path inside a migrations directory makes the ship rule run. `verify` then requires one narrative note with subject `ship rollback` (the subject inherited from `python-platform`). For a migration, that note has to describe how to reverse it, for example `python manage.py migrate polls 0001_initial` back to the previous applied migration, or restoring that revision. Placeholder text does not count.

Spec Guardrails appendix B calls the same idea a migrate reverse plan, recorded next to the previous image. Retornatus keeps that plan as the rollback note. It does not run `migrate`.

The packaged migration check is optional:

```toml
[[surfaces.ship.checks]]
name = "migrations"
optional = true
globs = ["**/migrations/**"]
run = ["python", "manage.py", "makemigrations", "--check", "--dry-run"]
```

`optional = true` covers those paths so `verify` does not report `no ship check covers`. It does **not** require `makemigrations --check --dry-run` to have been executed. The command needs Django, and Django may not be installed. The command stays in the comment block next to `check --deploy` and the test-runner suggestions.

Docker, Compose, Terraform, Helm, and workflow paths still require their executed checks. A `[[surfaces.ship.checks]]` table you write still replaces the whole packaged list, including this optional migration check, so copy every check you still want.

## Limitations

| Limitation | What it means |
| --- | --- |
| Structural checks only | `docker compose config`, `terraform validate`, `helm template`, and `actionlint` parse or render. They are not `terraform plan` review, a cluster dry-run, or a security audit |
| Not AppSec | Secrets, threat models, and authz review stay on `gate scope` sensitive paths and on `review_result` / `security_test` claims |
| Eval quality is yours | `verify` checks that the configured command was executed and that a fallback note exists. It does not score the golden set |
| No live traces | Production LLM telemetry is out of scope. The record is git plus Evidence |
| Framework presets | `fastapi` extends `python-platform` for API layouts and Alembic. `django` extends it for Django layouts and migrations. Workers stay on `python` or `python-platform` |
| Notes are declarations | The rollback and fallback subjects must be non-empty and specific. Retornatus does not judge whether the plan would work |

## What did not come over from Spec Guardrails

Spec Guardrails stored Ship Surface and AI Surface as sections in `design.md` and gated them with `validate_ship_surface.py`. Retornatus keeps the path lists and the honest limits, and turns them into executed Evidence plus a note. There is no `design.md` checklist to satisfy.
