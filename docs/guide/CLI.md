# CLI reference

Intention-oriented commands. Run from the governed project (or pass `--path`).

```bash
retornatus --help
retornatus gate --help
retornatus skill --help
```

## Continuity

| Command | Purpose |
| --- | --- |
| `init` | Create `.retornatus/` |
| `integrate` | Hub skill + detected Environment bridges |
| `project-init` | Brownfield map → `project/project.md` |
| `wake` / `wake --bridges` | Reconstruct state; rebuild index; optional bridges |
| `doctor` | Continuity + governance hygiene |
| `status` | Derived Change status |

## Change workflow

| Command | Purpose |
| --- | --- |
| `change elicit` | Situation readiness (exit 1 if insufficient) |
| `change create` | Demand → Situation → Contract → optional Action/Tasks |
| `change activate` | Activate draft Contract |
| `change reopen` | Material Contract version (archive prior) |
| `change learn` | Record Learning |
| `change create --task/--depends/--resource` | Explicit Task graph |

## Tasks and loop

| Command | Purpose |
| --- | --- |
| `task start\|complete\|fail\|reopen` | Durable Task lifecycle |
| `loop next` / `loop next --all-ready` | Ready work projection |

## Skills

| Command | Purpose |
| --- | --- |
| `skill create/list/need/activate/evolve/export` | Specialization lifecycle |

## Proof and policy

| Command | Purpose |
| --- | --- |
| `evidence add --claim` | Claim-bound Evidence (`--git-state` optional) |
| `gate contract\|evidence\|skill-research\|assurance\|policy` | STOP gates |
| `policy check --effect\|--action` | ALLOW / DENY / REQUIRE_HUMAN |
| `verify` | Assurance over Contract DONE |
| `assurance plan` / `assurance review` | Independent review path |
| `run` / `run --assurance` / `run --strict-policy` | Assemble ExecutionContext |

## Problems

| Command | Purpose |
| --- | --- |
| `finding add` | Record observation (auto-number) |
| `question open\|resolve\|reopen` | Question lifecycle |

## Human boundary

| Command | Purpose |
| --- | --- |
| `decision record` | Human Decision |
| `rule propose` / `rule activate --decision` | Rule Candidate → Rule |

## Inspection

| Command | Purpose |
| --- | --- |
| `inspect <id>` | Print artifact JSON |
| `search <query>` | FTS5 over index |
| `execution record` / `execution list` | Host execution observations |

IDs are stable strings such as `C-0001`, `C-0001/A-001`, `S-0001`, `R-0001`, `D-0001`.
