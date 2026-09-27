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
| `doctor` | Process vs Brakes scores + governance hygiene |
| `status` | Derived Change status |
| `ops list` / `ops show` / `ops run` | Operational hygiene loops |

## Change workflow

| Command | Purpose |
| --- | --- |
| `change classify` | Ceremony lane QUICK / STANDARD / COMPLEX. `--from-diff <base>` adds file count, lines changed, and scope-gate sensitive paths |
| `change elicit` | Requirements analysis / Situation readiness (`--answer`, `--write`; exit 1 if insufficient) |
| `change create` | Demand → Situation → Contract → optional Action/Tasks |
| `change overview` | Claims ↔ Evidence dashboard. `--format pr` prints a markdown pull-request body (executed vs self-reported, exit code, commit, stale/unverified, required checks, gates) |
| `change activate` | Activate draft Contract |
| `change reopen` | Material Contract version (archive prior) |
| `change learn` | Record Learning |
| `change create --task/--depends/--resource` | Explicit Task graph |
| `change create --lane` | Pin ceremony lane |

## Tasks and loop

| Command | Purpose |
| --- | --- |
| `task start` / `complete` / `fail` / `reopen` | Durable Task lifecycle |
| `loop next` / `loop next --all-ready` | Ready work projection |

## Intake

| Command | Purpose |
| --- | --- |
| `intake analyze --prompt` | Stage-based prompt analysis; propose Skill with human questions |
| `intake analyze --answer TOPIC=…` | Record human answers (SPECIALIZATION / NEED / CREATE) |
| `intake analyze --create-skill` | Create DRAFT Skill only when `create_authorized=true` |

## Skills

| Command | Purpose |
| --- | --- |
| `skill need --prompt` / `--action` | Assess specialization need (Action optional) |
| `skill create` / `list` / `activate` / `evolve` / `export` | Specialization lifecycle (manual create still allowed) |

## Proof and policy

| Command | Purpose |
| --- | --- |
| `evidence add --claim` | Self-reported Evidence (`provenance=self_reported`). Fine for narrative types |
| `evidence run [options] -- <command…>` | Run a command (no shell, cwd = project root) and record `provenance=executed` |
| `checks run -c <C-id>` | Execute `[assurance] required_checks` and record Evidence |
| `gate contract` / `evidence` / `skill-research` / `assurance` / `policy` / `budget` | STOP gates |
| `gate suppressions` | STOP when added lines contain suppression or skip markers (`--staged`, `--base`) |
| `gate scope <C-id>` | STOP when the diff leaves Task resources or hits denied/sensitive paths (`--base`, `--staged`) |
| `policy check --effect` / `--action` | ALLOW / DENY / REQUIRE_HUMAN. Optional `--effect-type`, `--resource`, `--command` |
| `hooks install` / `remove` / `status` | pre-commit (suppressions + scope) and commit-msg (reads `$1`) |
| `verify` / `verify --receipt` | Assurance over Contract DONE (+ optional Ed25519 receipt) |
| `verify --run-checks` | Run required checks, record Evidence, then verify |
| `verify --allow-self-reported` | Migration opt-out: accept self-reported test/build/lint evidence. Does not bypass required checks |
| `receipt keygen` / `receipt keygen --print` | Write the public key into `.retornatus/keys/`. Private key goes to the user config dir, or stdout for a CI secret |
| `receipt sign --change <C-id>` | Sign the current Assurance result |
| `receipt verify <path>` | Check a receipt with the committed public key |
| `action budget <A-id> --max N` | Set Action attempt ceiling (`--clear` removes it) |
| `assurance plan` / `assurance review` | Independent review path |
| `run` / `run --assurance` / `run --strict-policy` | Assemble ExecutionContext |
| `lesson from-gate` | Learning from gate failure (+ optional Rule Candidate) |

## Exit codes

| Code | When |
| --- | --- |
| `0` | Success. Gate passed. `verify` is `SATISFIED`. Receipt signature ok |
| `1` | Gate STOP. `verify` is not `SATISFIED`. Signature failed. Known id or file missing |
| `2` | Usage: invalid id, path outside `.retornatus`, empty or unusable search text, malformed signing key, invalid receipt JSON |

`gate` and `verify` keep those meanings for real checks. A bad id is usage (`2`), not a traceback. Search treats your text as literal tokens (hyphens and quotes are not FTS operators).

## Receipts

Ed25519. Public key: `.retornatus/keys/<key-id>.pub` (committed). Private key: `RETORNATUS_SIGNING_KEY` or the user config directory — never inside the project, and never copied from the environment onto disk.

An agent that can read the private key can still sign. Keep the key out of the agent's environment. In CI, put the PEM in a GitHub Actions secret and run `retornatus verify <C-id> --receipt` with `RETORNATUS_SIGNING_KEY` set. Clones verify with only the public key.

Legacy HMAC receipts verify only where the old local key exists. The result is `legacy_hmac`, `portable: false`, plus a deprecation warning.

## Problems

| Command | Purpose |
| --- | --- |
| `finding add` | Record observation (auto-number) |
| `question open` / `resolve` / `reopen` | Question lifecycle |

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
