# Gap Analysis — Functional Parity & Hardening (v0.7.0)

## Closed through v0.6.0

Situation, task readiness, Claim↔Evidence, Resolution, Human Decision, bypass,
brownfield dogfood, commit HEAD freshness, independent assurance, task CLI,
repo-signal Situation.

## Closed in v0.7.0

| Item | Mechanism | Test |
| --- | --- | --- |
| Path-level Evidence freshness | `git log -1 -- path` for file subjects | `test_path_isolation_host` |
| Workspace isolation projection | advisory Boundaries + wake caps | same |
| Host Execution observation | `HostExecutionRecord` + `execution record` CLI | same |
| Parity matrix doc | `.specs/parity-matrix.md` | documentation |

## Still remaining (honest)

- Live multi-provider LLM integration tests (Environment owns agents)
- Enforced sandbox/worktree orchestration (intentionally native-only; advisory here)
- Claiming Spec Guardrails is fully replaced across all workflows
