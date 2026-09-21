# Gap Analysis — Functional Parity & Hardening (v0.5.0)

Post-implementation status. Source of truth remains `prd/PRD.md`.

## Before (gaps closed in this pass)

1. Situation elicitation — no Demand→inspect→ambiguities loop
2. Task auto-chaining from declaration order; no cycle/readiness projection
3. Assurance matched any evidence type for any DONE (no Claim binding)
4. Staleness unused; Resolution accepted bare summary
5. Rule activation only checked `authority=HUMAN` on the Rule object
6. `--force` skipped gates without reason/record
7. Context loaded all active Rules; thin brownfield map
8. Happy-path tests only

## After (implemented)

| Area | Mechanism | Tests |
| --- | --- | --- |
| Situation | `change/situation.py` + `change elicit` | dogfood + create soft-guard |
| Task sync | `readiness.py` + non-chaining workflow | adversarial |
| Claim↔Evidence | SUPPORTS claim id + subject/type | adversarial + construction |
| Staleness | `evidence_is_fresh` | adversarial |
| Assurance | `build_claims_from_contract` proportional types | gates + dogfood |
| Resolution | Evidence required for verifiable Q | adversarial |
| Human authority | `Decision` + `activate_rule(decision_id)` | e2e + adversarial |
| Bypass | `BypassRecord` + force+reason | adversarial + skills |
| Context | applicability filter + contract subset | adversarial |
| Brownfield | richer `project-init` + wake summary | construction_path |
| Dogfood | Host boundary health endpoint | `test_construction_dogfood.py` |

## Remaining gaps

- No real multi-agent Host integration tests (by design — Environment-provided)
- Workspace isolation remains Environment-native only
- Evidence subject_state is explicit string matching, not git commit hashing
- Situation elicitation is heuristic/process, not an LLM RequirementsEngine
- Spec Guardrails behavioral parity is partial — see README capability matrix
