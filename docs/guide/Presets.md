# Presets

`retornatus init` can write a starting `.retornatus/config.toml` from a **preset**. Presets are TOML files inside the installed package (`retornatus/bootstrap/presets/`). They are not hard-coded command branches, and they are not the Spec Guardrails `.specs/design.md` workflow.

Without `--preset`, `init` behaves as it does today: a minimal config, the directory tree, and the idempotent `.gitignore` block (local index, runtime cache, private keys, and env files). Public keys under `.retornatus/keys/*.pub` stay committable.

An existing `config.toml` is left in place unless you pass `--force-config`. `--force` alone still recreates the **minimal** config when no preset is selected. It does not apply a preset over a file that is already there.

## Commands

```bash
retornatus init --list-presets
retornatus preset show python
retornatus preset show python-platform
retornatus init --preset python
retornatus init --preset python-platform
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

## Limitations

| Limitation | What it means |
| --- | --- |
| Structural checks only | `docker compose config`, `terraform validate`, `helm template`, and `actionlint` parse or render. They are not `terraform plan` review, a cluster dry-run, or a security audit |
| Not AppSec | Secrets, threat models, and authz review stay on `gate scope` sensitive paths and on `review_result` / `security_test` claims |
| Eval quality is yours | `verify` checks that the configured command was executed and that a fallback note exists. It does not score the golden set |
| No live traces | Production LLM telemetry is out of scope. The record is git plus Evidence |
| Framework-agnostic | FastAPI, Django, and workers are all just Python here. There is no framework preset |
| Notes are declarations | The rollback and fallback subjects must be non-empty and specific. Retornatus does not judge whether the plan would work |

## What did not come over from Spec Guardrails

Spec Guardrails stored Ship Surface and AI Surface as sections in `design.md` and gated them with `validate_ship_surface.py`. Retornatus keeps the path lists and the honest limits, and turns them into executed Evidence plus a note. There is no `design.md` checklist to satisfy.
