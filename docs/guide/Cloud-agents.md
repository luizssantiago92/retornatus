# Cloud agents

Cursor cloud agents, Codex, Claude Code on a remote VM, and CI sandboxes start from a clean machine and a git clone.

| Missing on that machine | Why | What to run |
| --- | --- | --- |
| `retornatus` CLI | The package is installed on the machine. It is not a file in the tree | `uv tool install …` (below) |
| Git hooks | Git does not version the hooks directory (`git rev-parse --git-path hooks`, including `core.hooksPath`) | `retornatus hooks install` on every fresh clone |

Canonical files under `.retornatus/` (Changes, Contracts, Evidence, the public receipt key) come with the clone. `.retornatus/index/` and `.retornatus/runtime/` do not. `retornatus wake` rebuilds the index. `retornatus init` appends ignore rules for that index and cache, plus `*.pem`, `*.key`, and `.env` files, when the delimited block is missing. `.retornatus/keys/*.pub` stays tracked.

## Session setup

Install the CLI on the agent machine. Release 1.6.0 includes `gate scope`, `gate suppressions`, blocking `verify`, `hooks install`, `hooks status`, `evidence run`, `checks run`, the Ed25519 `receipt` commands, and the opt-in agent Stop hook (`retornatus hook stop`):

```bash
uv tool install "retornatus==1.6.0"
```

The pull-request check is the [GitHub Action](GitHub-Action.md). Copy [`templates/ci/retornatus-pr.yml`](../../templates/ci/retornatus-pr.yml). It uses `luizssantiago92/retornatus@v1` (the tag the owner publishes) and does not pin the old inline `uv tool install` steps.

To install this git tree instead of the PyPI pin (for example while developing the harness), use the same command as [Quick start](Quick-start.md):

```bash
uv tool install --force git+https://github.com/luizssantiago92/retornatus.git
export PATH="$HOME/.local/bin:$PATH"
retornatus hooks install
retornatus hooks status
retornatus doctor
```

`hooks status` reports `pre-commit` and `commit-msg` as `installed`, `absent`, or `foreign`. `doctor` exits 0 when the project is ready, and 1 when it is not.

Hooks call `python -m retornatus` with the interpreter that performed the install. `uvx retornatus` runs one command and does not leave that interpreter for the next commit.

Inside this harness repository, CI installs from the checkout instead (`uv sync --group dev` in [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)):

```bash
uv sync --group dev
uv run retornatus hooks install
uv run retornatus doctor
```

On a repo that already contains `.retornatus/`, `retornatus init` reports that it is initialized. `retornatus wake` rebuilds continuity from the committed files. `retornatus integrate` refreshes the hub skill and host bridges on that machine.

Keep `hooks install`, `hooks status`, and `doctor` after either install. The published pin is the line in the workflow file.

## Install script and agent instructions

Put the CLI on the image, and run `hooks install` for every fresh clone.

**Cursor cloud agents.** `.cursor/environment.json` field `install` runs after checkout. With an environment build, `install` is not rerun when a new pod boots from that build. Per-pod commands belong in `start`. Hooks live in the clone, so they belong in `start` (or in the agent prompt) even when the CLI is already on the image:

```json
{
  "install": "uv tool install --force git+https://github.com/luizssantiago92/retornatus.git",
  "start": "export PATH=\"$HOME/.local/bin:$PATH\" && retornatus hooks install && retornatus hooks status && retornatus doctor"
}
```

A machine without `uv` can install it first (same command as the [README](../../README.md)):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**`AGENTS.md`, `CLAUDE.md`, or a Cursor rule.** When there is no install script, the agent instructions carry the same steps:

```markdown
## Fresh machine

Install the CLI (`uv tool install --force git+https://github.com/luizssantiago92/retornatus.git`) and export `PATH="$HOME/.local/bin:$PATH"`.
Run `retornatus hooks install`, then `retornatus hooks status` (expect `installed`).
Run `retornatus doctor` before the first Change.
Leave receipts unsigned. Do not set `RETORNATUS_SIGNING_KEY`.
`verify` and the diff gates on the GitHub pull request are the enforcement.
```

## Proof on the agent

Record a command Retornatus itself ran. `evidence run` disables the shell; the command follows `--`. Working directory is the project root. `--timeout` defaults to 120 seconds.

```bash
retornatus evidence run -c C-0001 -t test_result -s "/health" \
  --claim C-0001/claim-done-1 -- python -m pytest -q
retornatus verify C-0001
```

`evidence add` is self-reported. For `test_result`, `security_test`, `build_result`, and `lint_result`, `verify` does not treat it as satisfying.

When `[assurance] required_checks` is set, an execution claim counts only when the argv matches a declared check, the exit code is 0, the recorded commit is HEAD, and the source worktree is clean. Run those commands with:

```bash
retornatus checks run -c C-0001
retornatus verify C-0001 --run-checks
```

Diff gates, including the ones the pull-request workflow runs:

```bash
retornatus gate contract C-0001
retornatus gate suppressions --base main
retornatus gate scope C-0001 --base main
```

After `hooks install`, pre-commit runs `gate suppressions --staged` and `hooks scope`. commit-msg runs `hooks commit-msg --message-file "$1"`. Details: [Git governance](Git-governance.md), [Gates](Gates.md).

## Agent Stop hooks

Git hooks are not in the clone. Agent Stop hooks are. `retornatus integrate --hooks` writes `.cursor/hooks.json`, `.claude/settings.json`, and `.codex/hooks.json`. Those files are project config. Commit them in the application repository when you want the guardrail. This harness repository does not enable them on itself.

Cursor cloud agents run command hooks from `.cursor/hooks.json` at the repo root, including `stop`, once the VM is writable. They do not run hooks during an early read-only turn. `sessionStart` does not run in the cloud, and `~/.cursor/hooks.json` is not on the VM. The Stop hook calls `retornatus hook stop`, so the CLI still has to be on `PATH` in `start` (the same install as the git hooks above).

The hook is a guardrail. A crash fails open, Cursor's `loop_limit` caps follow-ups, and Claude and Codex will not block twice in a row. **CI remains the source of truth.** Full page: [Agent hooks](Agent-hooks.md).

## Receipts

Receipts are optional. Leave them unsigned on the agent VM.

The private signing key stays off that machine:

- Do not set `RETORNATUS_SIGNING_KEY` or `RETORNATUS_SIGNING_KEY_PATH`.
- Do not run `receipt keygen`, `receipt keygen --print`, `receipt sign --change <C-id>`, or `verify <C-id> --receipt`.

An agent that can read the private key can produce a valid signature. The committed public key is `.retornatus/keys/<key-id>.pub`. Checking a receipt uses only that key:

```bash
retornatus receipt verify path/to/receipt.json
```

When you do want a signature, sign in CI or on the owner's machine, with the secret kept out of the agent environment. The [README](../../README.md#verify-receipts) shows the step: a GitHub Actions secret `RETORNATUS_SIGNING_KEY`, then `retornatus verify <C-id> --receipt`.

## GitHub CI is the enforcement

A session can skip `hooks install`, and a commit can pass `--no-verify`. The check that runs for every pull request is GitHub Actions. It is the same check whether the agent was a laptop, a Cursor cloud agent, Codex, Claude Code, or a CI sandbox.

Copy [`templates/ci/retornatus-pr.yml`](../../templates/ci/retornatus-pr.yml) to `.github/workflows/retornatus.yml`. On `pull_request`, and on pushes to `main` or `master`, the job checks out the repository with full history and runs the [GitHub Action](GitHub-Action.md):

1. Installs Retornatus (`version` defaults to the latest PyPI release that includes `retornatus ci comment`).
2. Runs `retornatus gate suppressions --base <base> --json`.
3. For each Change touched under `.retornatus/changes/`, runs `retornatus verify <C-id> --json` and `retornatus gate scope <C-id> --base <base> --json`.
4. Renders one markdown comment with `retornatus ci comment` (overview plus claim and gate tables) and writes it to the job summary.
5. On a same-repository pull request, creates or updates the comment whose body contains `<!-- retornatus-verdict -->`.

`RETORNATUS_OMISSION` defaults to `fail`: a code diff that touches no Change fails the job. Set it to `warn` to print a warning and continue. Fork pull requests skip the comment because the token is read-only. The workflow does not push, merge, deploy, or sign receipts.

This repository's [CI workflow](../../.github/workflows/ci.yml) keeps the required check named **Retornatus gates**. That job still runs `doctor`, `wake`, and `gate-scan` from the checkout, then calls the action with `version: local` so the pull request exercises the branch, not an older PyPI release. The template above is the Retornatus gate for an application repository.

## Related

- [Environments](Environments.md) — host detection and bridges
- [Git governance](Git-governance.md) — hooks and git tiers
- [Gates](Gates.md) — STOP checks and Assurance
- [GitHub Action](GitHub-Action.md) — sticky pull-request comment
- [CLI](CLI.md) — command reference
