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
| `init` | Create `.retornatus/` and append ignore rules for the local index, cache, private keys, and `.env` files |
| `init --preset <name>` | Write a packaged config preset. Does not replace an existing `config.toml` unless `--force-config` is set |
| `init --list-presets` | List packaged presets and exit |
| `init --preset <name> --force-config` | Replace an existing `config.toml` with that preset. `--force` alone, with no preset, still writes the minimal config |
| `preset show <name>` / `preset list` | Print one preset's rendered config, or list presets. See [Presets](Presets.md) |
| `integrate` | Hub skill + detected Environment bridges |
| `integrate --hooks` | Also install the agent Stop, subagent-stop, session-start, and file-edit hooks. `--host` selects claude, cursor, or codex. See [Agent hooks](Agent-hooks.md) |
| `integrate --remove-hooks` | Remove the Retornatus Stop hook and leave other hooks in place |
| `project-init` | Brownfield map → `project/project.md` |
| `wake` / `wake --bridges` | Reconstruct state; rebuild index; optional bridges |
| `doctor` | Process vs Brakes scores + governance hygiene. Warns when `[retornatus] version` in config.toml differs from the installed package |
| `status` | Derived Change status |
| `ops list` / `ops show` / `ops run` | Operational hygiene loops |

`init` appends one delimited block to `.gitignore` (`# retornatus-gitignore:begin` through `# retornatus-gitignore:end`) when that begin marker is missing. The block ignores `.retornatus/index/`, `.retornatus/runtime/` (locks, executions, and cache), `*.pem`, `*.key`, `.env`, and `.env.*`. It keeps `!.env.example` and `!.retornatus/keys/*.pub` committable. A second `init` does not duplicate the block and does not remove lines that were already there. If git already tracks a `*.pem` or `*.key` file, `init` prints a warning on stderr. `--preset` still appends that gitignore block. Without `--preset`, the config stays the minimal file.

`--force-config` is what replaces an existing `config.toml` with the selected preset. `--force` without `--preset` still recreates the minimal config. It does not apply a preset over a file that is already there. An unknown preset name exits 2 and prints the names in this install. `preset show <name>` prints the config `init --preset` would write, including the comment block of suggested commands. The packaged names are `python`, `python-platform`, `fastapi`, `django`, `rag`, and `worker`. See [Presets](Presets.md).

## Change workflow

| Command | Purpose |
| --- | --- |
| `change classify` | Ceremony lane QUICK / STANDARD / COMPLEX. `--from-diff <base>` adds file count, lines changed, and scope-gate sensitive paths |
| `change elicit` | Requirements analysis / Situation readiness (`--answer`, `--write`; exit 1 if insufficient) |
| `change create` | Demand → Situation → Contract → optional Action/Tasks |
| `change overview` | Claims ↔ Evidence dashboard. `--format pr` prints a markdown pull-request body. `--json` or `--format json` prints the [verdict envelope](JSON-output.md) |
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
| `skill candidates` | List repetition candidates. An empty list is normal. Does not create a Skill |
| `skill accept <id>` | Approve a pending candidate. Writes a draft `SKILL.md`, or evolves the skill the candidate named |
| `skill reject <id>` | Reject a pending candidate. The same theme waits for new occurrences |
| `skill create` / `list` / `activate` / `evolve` / `export` | Specialization lifecycle (manual create still allowed) |

## Proof and policy

| Command | Purpose |
| --- | --- |
| `evidence add --claim` | Self-reported Evidence (`provenance=self_reported`). Fine for narrative types |
| `evidence run [options] -- <command…>` | Run a command (no shell, cwd = project root) and record `provenance=executed` |
| `checks run -c <C-id>` | Execute `[assurance] required_checks` and record Evidence |
| `gate contract` / `evidence` / `skill-research` / `assurance` / `policy` / `budget` | STOP gates. `--json` prints the [verdict envelope](JSON-output.md) |
| `gate suppressions` | STOP when added lines contain suppression or skip markers. The default scan includes untracked non-ignored files; `--staged` and `--base` do not (`--json`) |
| `gate scope <C-id>` | STOP when the diff leaves Task resources or hits denied/sensitive paths (`--base`, `--staged`, `--json`) |
| `policy check --effect` / `--action` | ALLOW / DENY / REQUIRE_HUMAN. Optional `--effect-type`, `--resource`, `--command` |
| `hooks install` / `remove` / `status` | pre-commit (suppressions + scope) and commit-msg (reads `$1`) |
| `hook stop --host HOST` | Agent turn-end hook (`HOST` is claude, cursor, or codex). Reads host JSON on stdin. See [Agent hooks](Agent-hooks.md) |
| `hook subagent-stop --host HOST` | Subagent-stop hook. Same reminder as `hook stop`. See [Agent hooks](Agent-hooks.md) |
| `hook session-start --host HOST` | Agent session-start hook. Injects the active Change. See [Agent hooks](Agent-hooks.md) |
| `hook file-edit --host HOST` | Agent file-edit hook. Warns when the path leaves the active Change scope. See [Agent hooks](Agent-hooks.md) |
| `verify` / `verify --receipt` / `verify --json` | Assurance over Contract DONE. `--json` prints the [verdict envelope](JSON-output.md) |
| `ci comment` | Sticky pull-request markdown from `verify --json` and `gate --json`, plus `change overview --format pr` when `--path` is set. See [GitHub Action](GitHub-Action.md) |
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

`gate` and `verify` keep those meanings for real checks, including when `--json` is set. A bad id is usage (`2`), not a traceback. Search treats your text as literal tokens (hyphens and quotes are not FTS operators).

## JSON output

`verify --json`, every `gate` subcommand `--json`, and `change overview --json` (or `--format json`) write one versioned document to stdout. Labels, warnings, gate findings, and other diagnostics go to stderr. The shape, a worked example, and the schema file are in [JSON output](JSON-output.md).

## Receipts

`verify --receipt` and `receipt sign` write an Ed25519 receipt under `.retornatus/assurance/receipts/`. The signature covers the verify verdict. `receipt verify` checks it with the committed public key.

Someone who held the private key signed that result. The receipt does not prove the agent was sandboxed, and it is not a receipt network.

| Material | Where | Committed? |
| --- | --- | --- |
| Public key | `.retornatus/keys/<key-id>.pub` | Yes. `<key-id>` is the SHA-256 fingerprint of the raw public key |
| Private key | User config directory, or `RETORNATUS_SIGNING_KEY` (PEM, base64, or even-length hex) | No. Never inside the repo, and never copied there from the environment |

`receipt keygen` writes the public key into the repo and the private key under the user config dir (`$XDG_CONFIG_HOME/retornatus` or `%APPDATA%\retornatus`). `--print` sends the private key to stdout for a CI secret and does not write a key file. `retornatus init` and `receipt keygen` warn on stderr if git already tracks a `*.pem` or `*.key` file. Untrack that file. The ignore rules from `init` keep a later `git add` from picking up a new one, and they do not ignore `.retornatus/keys/*.pub`.

An agent that can read the private key can still sign. Keep `RETORNATUS_SIGNING_KEY` and the config-dir key out of the agent's environment. Cloud and remote agents leave receipts unsigned. Verification needs only the committed public key, so a fresh clone can check a receipt without the secret. Setup for a clean VM: [Cloud agents](Cloud-agents.md).

Store the private key as a GitHub Actions secret and sign in CI, where the agent that edits the repo does not see it:

```yaml
- name: Sign verify receipt
  env:
    RETORNATUS_SIGNING_KEY: ${{ secrets.RETORNATUS_SIGNING_KEY }}
  run: retornatus verify C-0001 --receipt
```

Anyone who clones the repo can run `retornatus receipt verify path/to/receipt.json`.

Legacy HMAC receipts verify only where the old local key exists. The result is `legacy_hmac`, `portable: false`, plus a deprecation warning. That key is not written into the repo.

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
