# Quick start

Get Retornatus running in a project in about ten minutes.

## 1. Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended)
- An AI coding agent (Cursor, Claude Code, Codex, …)

```bash
python --version
uv --version
```

## 2. Install the CLI

**From TestPyPI (available now — `retornatus==1.0.0`):**

```bash
uv tool install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  retornatus
retornatus --version   # 1.0.x
```

`--extra-index-url` is required so dependencies still resolve from production PyPI.

**From PyPI (after a `v*` release tag publishes):**

```bash
uv tool install retornatus
```

One-shot without a global install: `uvx retornatus --help`.

**From Git or a local clone:**

```bash
uv tool install --force git+https://github.com/luizssantiago92/retornatus.git
# or
uv tool install --force /path/to/retornatus
```

## 3. Initialize the project

In the **application** repository (not necessarily this harness repo):

```bash
cd /path/to/your-app
retornatus init
retornatus integrate
retornatus doctor
```

You should see:

- `.retornatus/config.toml`
- Hub skill (e.g. `.cursor/skills/retornatus/SKILL.md` on Cursor)
- `doctor` reporting initialized state

Optional for brownfield repos:

```bash
retornatus project-init
retornatus wake --bridges
```

## 4. Create your first Change

**Via agent (recommended):** open chat and ask it to follow the Retornatus hub skill, for example:

> Create a Retornatus Change for GET /health returning 200. Contract and gates before code.

**Via CLI:**

```bash
retornatus change elicit \
  --demand "Expose a liveness check for ops" \
  --what "GET /health returns 200 with status ok" \
  --done "Automated test covers /health"

retornatus change create \
  --title "Add health endpoint" \
  --demand "Expose a liveness check for ops" \
  --what "GET /health returns 200 with status ok" \
  --done "Automated test covers /health" \
  --objective "Implement and verify health endpoint"

retornatus gate contract C-0001
```

If Situation is incomplete, use `--draft-contract` on create, then `retornatus change activate C-0001` when ready.

## 5. Execute and prove

```bash
retornatus loop next C-0001
retornatus run C-0001/A-001
# implement in the host…
retornatus evidence add -c C-0001 -t test_result -s "/health" \
  --source pytest --state passing --claim C-0001/claim-done-1
retornatus gate evidence C-0001
retornatus verify C-0001
```

Non-zero gate exit = **STOP**. Do not treat a chat summary as success.

## 6. Preserve the return

```bash
retornatus change learn \
  --title "Health checks need Claim-bound test_result Evidence" \
  --body "Dogfood: verify failed until --claim was set."
retornatus status
```

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `Not initialized` | `retornatus init` |
| Hub skill missing | `retornatus integrate` |
| Index empty after crash | `retornatus wake` (rebuilds from files) |
| Contract gate fails | Active Contract with WHAT + DONE |
| Verify inconclusive | Evidence must SUPPORT the Claim id |

More: [FAQ](FAQ.md) · [Gates](Gates.md) · [Tutorial: first Change](tutorials/01-first-change.md)
