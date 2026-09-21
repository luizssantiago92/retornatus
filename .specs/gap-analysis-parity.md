# Gap Analysis — Functional Parity & Hardening (v0.6.0)

## Closed in v0.5.0

Situation elicit, task readiness, Claim↔Evidence, Resolution proof, Human Decision,
governed bypass, context relevance, adversarial tests, health dogfood.

## Closed in v0.6.0 (this pass)

| # | Item | Mechanism | Test |
| --- | --- | --- | --- |
| 1 | Brownfield dogfood | `seed_brownfield_service` + full governed path | `test_brownfield_gap_closure` |
| 2 | Commit staleness | `commit:<sha>` + `derive_current_subject_states` | same (stale after new commit) |
| 3 | Independent Assurance | `assurance plan/review` + `review_result` Claims | same |
| 4 | Task CLI resources/deps | `--task` / `--depends` / `--resource` | same + readiness |
| 5 | Situation repo signals | `collect_repo_signals` (stack/tests/CI/health) | same |

## Still remaining (honest)

- Live LLM/Host integration (Environment-provided; not harness unit scope)
- Workspace isolation orchestration (native Environment)
- Spec Guardrails full behavioral replacement across all workflows
- Automatic file-level git path freshness (only HEAD commit comparison today)
