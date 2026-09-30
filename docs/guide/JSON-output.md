# JSON output

`verify`, every `gate` subcommand, and `change overview` accept `--json`. `change overview` also accepts `--format json`, the same mode as the existing `--format text` and `--format pr` switch.

Stdout is one JSON document (`schema_version` 1) and a trailing newline. Rich markup, progress lines, and evidence labels are not written there. Those diagnostics go to stderr. The process exit code is the same as text mode: `0` when `verify` is `SATISFIED` or a gate passes, `1` when it does not, `2` for usage errors.

The schema file is [`schemas/verdict-v1.schema.json`](../../schemas/verdict-v1.schema.json) (JSON Schema draft 2020-12).

## Envelope

| Field | Meaning |
| --- | --- |
| `schema_version` | Always `1` for this document |
| `command` | `verify`, `gate`, or `change overview` |
| `verdict` | Assurance: `SATISFIED`, `NOT_SATISFIED`, or `INCONCLUSIVE`. Gate: `PASS` or `FAIL` (the same fact as `passed`). Overview: the assurance verdict, or `null` when there is no contract |
| `exit_code` | The process exit code for this invocation |
| `claims` | Claim id, subject, statement, status, required evidence types, and Evidence that `SUPPORTS` the claim |
| `warnings` | Warning strings the command already produced |
| `errors` | Gate failure lines (not `WARN` prefixes). Empty for a `verify` verdict; the reason is `rationale` and each claim `status`. Overview uses this when the Change id does not exist |
| `head` | `git` HEAD sha, or `null` outside a work tree |
| `generated_at` | UTC timestamp when the envelope was built |

Gate documents also include `gate`, `passed`, and `findings` (every message text mode prints). `change_id`, `action_id`, and `skill_id` are set from the argument that command takes, and are `null` otherwise.

`verify` adds `rationale`, `evidence_labels`, `unverified_evidence_ids`, and `receipt` (`null` unless `--receipt` wrote a file).

`change overview` adds the dashboard projection: `title`, `lane`, `contract_version`, `contract_active`, `what`, `evidence_lines`, `tasks`, `questions`, `next`, and `parallelizable`.

## Example

```json
{
  "schema_version": 1,
  "command": "verify",
  "exit_code": 0,
  "verdict": "SATISFIED",
  "claims": [
    {
      "id": "C-0001/claim-done-1",
      "subject": "pytest exits 0 for the health command",
      "statement": "pytest exits 0 for the health command",
      "status": "SATISFIED",
      "required_evidence_types": ["test_result"],
      "evidence": [
        {
          "id": "C-0001/E-001",
          "type": "test_result",
          "subject": "pytest exits 0 for the health command",
          "provenance": "executed",
          "exit_code": 0,
          "git_commit": null
        }
      ]
    }
  ],
  "warnings": [],
  "errors": [],
  "head": null,
  "generated_at": "2026-09-30T12:00:00Z",
  "change_id": "C-0001",
  "rationale": "All claims have matching attributable evidence",
  "evidence_labels": [
    "C-0001/E-001 type=test_result provenance=executed exit_code=0 status=executed"
  ],
  "unverified_evidence_ids": [],
  "receipt": null
}
```

```bash
retornatus verify C-0001 --json
retornatus gate contract C-0001 --json
retornatus gate scope C-0001 --base origin/main --json
retornatus change overview C-0001 --format json
```

A missing Change on `change overview --json` still exits `1`. Stderr carries `Change not found: …` and stdout is an envelope with `verdict` null and that sentence in `errors`.
