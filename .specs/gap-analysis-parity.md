# Gap Analysis — Functional Parity & Hardening (v0.8.0)

## Closed in v0.8.0

| Item | Mechanism | Test |
| --- | --- | --- |
| Task lifecycle CLI | `task start/complete/fail/reopen` | `test_task_contract_security` |
| Contract reopen | archive `contracts/vN.json` + Situation note + new version | same |
| Skill need (complexity) | `skill need` / `assess_skill_need` | same |
| Security review dogfood | security_test + independent review_result | same |

## Still remaining (honest)

- Live multi-provider LLM integration tests (Environment owns agents)
- Enforced sandbox/worktree orchestration (advisory only by design)
- Claiming Spec Guardrails is fully replaced across all workflows
