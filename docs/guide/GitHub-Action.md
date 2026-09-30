# GitHub Action

The composite action at the repository root runs Retornatus on a pull request and posts **one** sticky comment. Reviewers see the verdict, which claims have evidence, and which gates failed. A red check is not the only signal.

The action does not re-implement Assurance. It runs `verify` and the diff gates with [`--json`](JSON-output.md), then `retornatus ci comment` lays out that JSON. Narrative sections are `change overview --format pr`.

Publish target, after the owner tags it: `uses: luizssantiago92/retornatus@v1`.

## Workflow

Copy [`templates/ci/retornatus-pr.yml`](../../templates/ci/retornatus-pr.yml), or use this job. Checkout must fetch the full history so the diff base is present. Third-party actions stay pinned to commit SHAs.

```yaml
name: Retornatus

on:
  pull_request:

permissions:
  contents: read

jobs:
  retornatus-gates:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          fetch-depth: 0
          persist-credentials: false

      - uses: luizssantiago92/retornatus@v1
        with:
          comment: "true"
          fail-on: not_satisfied
```

`@v1` is the Marketplace major tag. The owner creates that tag and publishes the package. Until the tag exists, pin the action to a full commit SHA. Inside this repository the required check uses `uses: ./` and `version: local` so the pull request runs the branch, not an older PyPI release. The job name stays **Retornatus gates**.

## Permissions

Set these on the job that uses the action. A composite action cannot declare permissions itself.

| Scope | Access | Why |
| --- | --- | --- |
| `contents` | `read` | Checkout and `git diff` |
| `pull-requests` | `write` | Create or update the sticky comment |

The token is the `github-token` input, which defaults to `github.token`. The action passes it as `GH_TOKEN` for `gh`. It is not echoed.

## Inputs

| Input | Default | Meaning |
| --- | --- | --- |
| `version` | `latest` | PyPI release (`1.4.1`), `latest`, or `local` (install the checkout). The installed CLI must provide `retornatus ci comment` |
| `change` | empty | One Change id. Empty detects ids touched under `.retornatus/changes` |
| `base` | empty | Git revision for the diff. Empty uses the pull request base SHA, or `origin/<default branch>` on other events |
| `comment` | `true` | Post or update the sticky comment |
| `fail-on` | `not_satisfied` | Fail the step unless the folded verdict is `SATISFIED`. `never` exits 0 after the comment is written |
| `github-token` | `github.token` | Token for the comment API |

`RETORNATUS_OMISSION` is an environment variable, not an input. `fail` (default) fails the job when a code diff touches no Change. `warn` prints a warning and continues. Code paths are `src/**`, `tests/**`, `scripts/**`, `templates/**`, `pyproject.toml`, and `uv.lock`, the same set as the previous inline workflow.

## Outputs

| Output | Meaning |
| --- | --- |
| `verdict` | `SATISFIED`, `NOT_SATISFIED`, or `INCONCLUSIVE` |
| `json` | Path to a bundle of the verify and gate documents plus that verdict |

`SATISFIED` means every `verify` document is `SATISFIED` and every gate document passed. A gate `FAIL`, a `NOT_SATISFIED` verify, or a code diff with no Change (`RETORNATUS_OMISSION=fail`) folds to `NOT_SATISFIED`. No JSON at all is `INCONCLUSIVE`. The fold reads the `verdict` and `passed` fields. It does not call Assurance again.

## What runs

1. Install Retornatus with uv (`astral-sh/setup-uv` pinned by commit SHA; the uv cache is off so the job does not need `actions: write`).
2. `retornatus gate suppressions --base <base> --json`
3. For each Change: `retornatus verify <C-id> --json` and `retornatus gate scope <C-id> --base <base> --json`
4. `retornatus ci comment` writes markdown to stdout and the bundle to the `json` output path.
5. The same markdown is appended to `$GITHUB_STEP_SUMMARY`.
6. On a pull request, create or update the issue comment whose body contains `<!-- retornatus-verdict -->`.

## Forks

A pull request from a fork gets a read-only `GITHUB_TOKEN` even when the workflow asks for `pull-requests: write`. The action sees `pull_request.head.repo.fork` and skips the API call. If a token is rejected with HTTP 403, it skips the same way. The job summary still contains the markdown. `fail-on: not_satisfied` still fails the step when the verdict is not `SATISFIED`.

Pushes that are not pull requests skip the comment and still write the summary.

## Rendered comment

The hidden marker is how the next run finds the same comment. Overview text comes from `change overview --format pr`. The tables below it are the JSON the action just ran.

```markdown
<!-- retornatus-verdict -->

## Retornatus verdict: `NOT_SATISFIED`

One comment for this pull request. Claim and gate tables are the JSON from `verify` and `gate`. Narrative sections are `change overview --format pr`.

### Verify

- **C-0001** `NOT_SATISFIED` — Unmet claims: C-0001/claim-done-2

## C-0001 — Health check

**Lane:** QUICK
**Contract:** v1 (active)
**WHAT:** GET /health returns 200
**Assurance:** NOT_SATISFIED

### Claims

- **[SATISFIED]** `C-0001/claim-done-1`: pytest exits 0 for the health command (need: test_result; evidence: C-0001/E-001)
- **[NOT_SATISFIED]** `C-0001/claim-done-2`: The guide page contains a copy-paste workflow (need: repository_observation; evidence: (unbound))

### Claim results

| Claim | Status | Evidence |
| --- | --- | --- |
| `C-0001/claim-done-1` pytest exits 0 for the health command | SATISFIED | `C-0001/E-001` |
| `C-0001/claim-done-2` The guide page contains a copy-paste workflow | NOT_SATISFIED | — |

### Gate results

| Gate | Change | Result | Detail |
| --- | --- | --- | --- |
| suppressions | — | PASS | No new suppression markers |
| scope | C-0001 | FAIL | out of scope: scripts/github_action.sh |
```

## Related

- [JSON output](JSON-output.md) — the documents the comment reads
- [Gates](Gates.md) — what `suppressions`, `scope`, and `verify` stop
- [Cloud agents](Cloud-agents.md) — the pull request is the enforcement on a clean machine
