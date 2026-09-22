# Spec Guardrails behavioral parity matrix (v1.0)

Retornatus answers useful Spec Guardrails capabilities without cloning its architecture.

| Capability | How Retornatus handles it | Status | Evidence |
| --- | --- | --- | --- |
| requirements analysis | Situation elicit + repo signals | RETORNATUS | `change/situation.py`, brownfield tests |
| complexity-sensitive workflow | Tasks conditional; elicit skips ceremony | RETORNATUS | situation sufficiency |
| technical investigation/design | Finding → Question → Action | RETORNATUS | question loop |
| task decomposition | Embedded Tasks + TaskSpec | RETORNATUS | workflow |
| task dependencies/readiness | derived sync, cycles blocked | RETORNATUS | readiness + adversarial |
| parallelizable work | `loop next --all-ready` | RETORNATUS | readiness |
| workspace isolation when required | advisory Boundaries → native worktree/sandbox | COMPOSITION | `execution/isolation.py` |
| execution context | assemble_execution_context (+ policy) | RETORNATUS | context.py |
| context boundaries | Boundaries + applicability | RETORNATUS | context + policy |
| skills | on-demand specialization | RETORNATUS | skills.py |
| quality checks | gates (incl. policy) | RETORNATUS | gates.py |
| evidence | Claim-bound Evidence + path/HEAD freshness | RETORNATUS | evidence + subject_state |
| traceability | relations SUPPORTS/GROUNDED_IN | RETORNATUS | domain relations |
| independent verification | assurance plan/review + fresh context | RETORNATUS | independent.py |
| security/QA review when required | review_result / security_test Claims | RETORNATUS | evaluate infer types |
| brownfield context | project-init + wake + repo signals | RETORNATUS | project_init / wake |
| memory | Learnings + disposable SQLite | RETORNATUS | adaptation + index |
| restart/handoff | wake rebuild | RETORNATUS | wake tests |
| human approval | Decision → Rule activate | RETORNATUS | adaptation service |
| policy evaluation | ALLOW / DENY / REQUIRE_HUMAN | RETORNATUS | policy.py + CLI |
| native rule realization | project active Rules into host bridges | COMPOSITION | rule_projection.py |
| git/environment constraints | commit/path freshness + env caps | COMPOSITION | subject_state + adapters |
| diagnostics | doctor hygiene + wake diagnostics | RETORNATUS | doctor.py + wake |
| status projection | rich derived Change status | RETORNATUS | status.py |
| draft contract activation | `change activate` after elicitation | RETORNATUS | workflow.activate_contract |
| question reopen | clear Resolution when condition returns | RETORNATUS | QuestionLoop.reopen_question |
| host execution observation | HostExecutionRecord (not runtime) | RETORNATUS | host_record.py |
| Cursor / Claude Code / Codex adapters | detect + bridge + rule projection | RETORNATUS | adapters.py |
| LLM agent runtime | Environment-native | NATIVE ENVIRONMENT | — |
| remote orchestration | not in V1 | NOT REQUIRED | — |

## Remaining honest gaps

- No live multi-provider LLM integration test (Environment owns execution)
- Isolation is advisory projection, not enforced sandbox orchestration
- Spec Guardrails command 1:1 parity is intentionally NOT a goal
