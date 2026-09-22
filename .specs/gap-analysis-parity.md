# Gap Analysis — Functional Parity & Hardening (v1.0.0)

## Closed in v1.0.0 (V1 acceptance)

| Item | Mechanism | Test |
| --- | --- | --- |
| Policy CLI + gate | `policy check` / `gate policy` / `run --strict-policy` | `test_governance_native_v1` |
| Native Rule projection | Active Rules upserted into Cursor/Claude/Codex bridges | same |
| Adapter-aware integrate | Detected Environment owns bridges | same |
| V1 continuity acceptance | wake → change → policy → bridges → index rebuild | same |

## Closed in v0.9.0

| Item | Mechanism | Test |
| --- | --- | --- |
| Draft Contract activation | `change activate` after Situation sufficiency | `test_activate_status_doctor` |
| Rich status projection | `status` / `project_change_status` | same |
| Doctor hygiene | draft contracts, skill research, inactive rules | same |
| Question reopen CLI | `question reopen` clears Resolution | same |
| Finding/Question auto-number | omit `--number` → next free id | same |

## Closed in v0.8.0

| Item | Mechanism | Test |
| --- | --- | --- |
| Task lifecycle CLI | `task start/complete/fail/reopen` | `test_task_contract_security` |
| Contract reopen | archive `contracts/vN.json` + Situation note + new version | same |
| Skill need (complexity) | `skill need` / `assess_skill_need` | same |
| Security review dogfood | security_test + independent review_result | same |

## Still remaining (honest — out of V1 harness scope)

- Live multi-provider LLM integration tests (Environment owns agents)
- Enforced sandbox/worktree orchestration (advisory only by design)
- Claiming Spec Guardrails is fully replaced across all workflows
