# Architecture

Retornatus is a Python package with clear layers. Domain policy does not live in Environment adapters.

```text
CLI (intentions)
  → Application (Change, gates, Assurance, Skills, Policy, Question loop)
  → Domain (Pydantic models, IDs, relations)
  → Infrastructure (files, SQLite index, adapters, hub skill)
  → Bootstrap (init, wake, doctor, project-init)
```

## Invariants

1. **Files persist truth** under `.retornatus/`
2. **Models validate truth** (schema versioning, optimistic concurrency)
3. **SQLite indexes and finds** — never sole authority
4. **Status is a projection**
5. **Native first** — adapters project; hosts execute

## Package map

| Path | Responsibility |
| --- | --- |
| `src/retornatus/cli/` | Typer entrypoints |
| `src/retornatus/domain/` | Models, enums, relations |
| `src/retornatus/application/` | Workflows and gates |
| `src/retornatus/infrastructure/` | Persistence, index, Environment |
| `src/retornatus/bootstrap/` | init / wake / doctor |

## Filesystem (consumer project)

```text
.retornatus/
  config.toml
  changes/C-xxxx/
    change.json
    situation.md
    contract.json
    contracts/vN.json      # archives
    actions/
    findings/
    questions/
    evidence/
  governance/              # rules, bypasses, …
  adaptation/              # learnings, skills
  project/                 # project.md, decisions
  index/                   # disposable SQLite
  runtime/                 # disposable host observations
```

Exact layout: PRD §52.

## Adapters

```text
detect Environment → CapabilityModel → ensure_bridge_files
```

Adapters must not invent domain Policy. They translate capabilities and write bridge projections (including active Rules). See [Environments](Environments.md).

## Design test (before new abstractions)

From PRD §71:

```text
Concrete failure?
  → Existing Retornatus mechanism?
  → Environment native solution?
  → Simpler established pattern?
  → Only then: new mechanism
```
