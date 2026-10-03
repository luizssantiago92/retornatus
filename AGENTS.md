# Retornatus — agent map

Short map for coding agents. **Durable truth:** `.retornatus/` and the hub skill — not this file alone.

## What this repo is

Repo-native **governance harness** for AI-assisted software work. You write the code; Retornatus governs the loop (Situation → Contract → Action → Evidence → Assurance).

## Before coding

1. `retornatus wake` (brownfield: `project-init`, `wake --bridges`)
2. Requirements: `retornatus change elicit --demand "…" --what "…" --done "…"`  
   - Exit `1` → ask Focused questions in chat; record `--answer TOPIC=…` until exit `0`
3. `retornatus change create …` / `change activate <C-id>`
4. `retornatus gate contract <C-id>` must exit `0`

## Build / prove

- Next work: `retornatus loop next <C-id>` · `task start|complete|fail|reopen`
- Context: `retornatus run <A-id>` (optional `--strict-policy`)
- Skills: `intake analyze` (human `CREATE=yes`) or `skill need --prompt` / `skill create`. A pending skill candidate is a suggestion: ask once with the reason from `skill candidates`, and never run `skill accept` unless the user explicitly says so.
- Proof: `evidence run … --claim <id> -- <command>` for test/build/lint results (`evidence add` is self-reported and does not satisfy those types) → `retornatus verify <C-id>`  
  - Optional Ed25519 receipt: `verify <C-id> --receipt` (public key in `.retornatus/keys/`; private key outside the repo and outside the agent environment)
- Attempt budget (optional): `action budget <A-id> --max N` · `gate budget <A-id>`

## Verification stack (this repository)

From repo root, after code changes:

```bash
uv run ruff check src tests scripts
uv run mypy
uv run python scripts/build_docs_html.py --check
uv run pytest -q
```

## Deeper sources

| Topic | Where |
| --- | --- |
| Hub procedure | `.cursor/skills/retornatus/SKILL.md` (after `integrate`) |
| Product PRD | `docs/archive/PRD.md` |
| User docs | `docs/guide/` → site HTML via `scripts/build_docs_html.py` |
| SG migration | `docs/guide/From-spec-guardrails.md` |
| Landscape | `docs/guide/Landscape.md` |
| Git tiers | `docs/guide/Git-governance.md` |
| Cloud / remote agents | `docs/guide/Cloud-agents.md` |

Do **not** claim DONE without Assurance `SATISFIED`. Do **not** invent Skills without human confirmation.
