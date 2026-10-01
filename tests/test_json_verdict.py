"""--json verdict envelope for verify, gates, and change overview."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from typer.testing import CliRunner

from retornatus.application.assurance.evaluate import infer_claim_subject
from retornatus.application.assurance.evidence import EvidenceService
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app

runner = CliRunner()

_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "verdict-v1.schema.json"
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
Draft202012Validator.check_schema(_SCHEMA)
_VALIDATOR = Draft202012Validator(
    _SCHEMA,
    format_checker=Draft202012Validator.FORMAT_CHECKER,
)

_DONE = "pytest exits 0 for the health command"


def _lines(text: str) -> list[str]:
    return text.splitlines()


def _load(stdout: str) -> dict[str, object]:
    """Parse stdout as one JSON document with nothing after it."""
    stripped = stdout.strip()
    assert stripped.startswith("{"), repr(stdout)
    assert stripped.endswith("}"), repr(stdout)
    decoder = json.JSONDecoder()
    document, offset = decoder.raw_decode(stdout)
    assert stdout[offset:].strip() == ""
    assert isinstance(document, dict)
    return document


def _assert_schema(document: dict[str, object]) -> None:
    errors = list(_VALIDATOR.iter_errors(document))
    assert not errors, errors[0].message


def _create(tmp_path: Path, *, draft: bool = False, task: bool = False, done: str = _DONE) -> None:
    initialize_project(tmp_path)
    args = [
        "change",
        "create",
        "--path",
        str(tmp_path),
        "--title",
        "Health",
        "--demand",
        "Operators need a health command with a clear exit code",
        "--what",
        "The health command exits 0",
        "--done",
        done,
        "--situation",
        "Operators run one health command and read its exit code.",
    ]
    if draft:
        args.append("--draft-contract")
    if task:
        args.extend(["--task", "Implement the health command", "--resource", "0:README"])
    created = runner.invoke(app, args)
    assert created.exit_code == 0, created.stdout + created.stderr


def _satisfy(tmp_path: Path, done: str = _DONE) -> None:
    EvidenceService(tmp_path).run(
        change_id="C-0001",
        evidence_type="test_result",
        subject=infer_claim_subject(done),
        command=[sys.executable, "-c", "print('ok')"],
        supports_claim_id="C-0001/claim-done-1",
    )


def _git(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "json@retornatus.local"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "JSON Test"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    (root / "README").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "README"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "base"],
        cwd=root,
        check=True,
        capture_output=True,
    )


def _pair(args: list[str]) -> tuple[object, dict[str, object]]:
    plain = runner.invoke(app, args)
    rendered = runner.invoke(app, [*args, "--json"])
    assert rendered.exit_code == plain.exit_code
    document = _load(rendered.stdout)
    _assert_schema(document)
    assert document["exit_code"] == rendered.exit_code
    return plain, document


def test_schema_file_is_draft_2020_12() -> None:
    assert _SCHEMA["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert _SCHEMA["properties"]["schema_version"]["const"] == 1


def test_verify_json_satisfied_keeps_exit_code(tmp_path: Path) -> None:
    _create(tmp_path)
    _satisfy(tmp_path)
    EvidenceService(tmp_path).add(
        change_id="C-0001",
        evidence_type="repository_observation",
        subject="unrelated note",
        source="note",
        producer="agent",
    )
    plain, document = _pair(["verify", "C-0001", "--path", str(tmp_path)])
    rendered = runner.invoke(app, ["verify", "C-0001", "--path", str(tmp_path), "--json"])
    assert plain.exit_code == 0
    assert document["command"] == "verify"
    assert document["verdict"] == "SATISFIED"
    assert document["change_id"] == "C-0001"
    assert document["errors"] == []
    assert document["receipt"] is None
    claims = document["claims"]
    assert isinstance(claims, list) and len(claims) == 1
    claim = claims[0]
    assert isinstance(claim, dict)
    assert claim["status"] == "SATISFIED"
    evidence = claim["evidence"]
    assert isinstance(evidence, list) and evidence[0]["provenance"] == "executed"
    assert evidence[0]["exit_code"] == 0
    assert '"command"' not in plain.stdout
    assert '"evidence_ids"' not in rendered.stdout
    assert _lines(rendered.stderr) == _lines(plain.stdout.split("{", 1)[0])


def test_verify_json_not_satisfied_keeps_exit_code(tmp_path: Path) -> None:
    _create(tmp_path)
    plain, document = _pair(["verify", "C-0001", "--path", str(tmp_path)])
    assert plain.exit_code == 1
    assert document["verdict"] == "INCONCLUSIVE"
    assert document["exit_code"] == 1
    assert document["claims"][0]["status"] == "INCONCLUSIVE"
    assert document["claims"][0]["evidence"] == []


def test_verify_json_run_checks_notes_go_to_stderr(tmp_path: Path) -> None:
    _create(tmp_path)
    exe = Path(sys.executable).as_posix()
    config = tmp_path / ".retornatus" / "config.toml"
    config.write_text(
        config.read_text(encoding="utf-8")
        + "\n[assurance]\n"
        + f'required_checks = [{{name = "unit", run = ["{exe}", "-c", "print(1)"]}}]\n',
        encoding="utf-8",
    )
    rendered = runner.invoke(
        app,
        ["verify", "C-0001", "--path", str(tmp_path), "--run-checks", "--json"],
    )
    document = _load(rendered.stdout)
    _assert_schema(document)
    assert "Recorded " in rendered.stderr
    assert "Recorded " not in rendered.stdout
    assert document["command"] == "verify"


def test_gate_contract_pass_fail_and_warning(tmp_path: Path) -> None:
    _create(tmp_path)
    plain, document = _pair(["gate", "contract", "C-0001", "--path", str(tmp_path)])
    rendered = runner.invoke(app, ["gate", "contract", "C-0001", "--path", str(tmp_path), "--json"])
    assert plain.exit_code == 0
    assert document["gate"] == "contract"
    assert document["passed"] is True
    assert document["verdict"] == "PASS"
    assert document["findings"] == _lines(plain.stdout)
    assert _lines(rendered.stderr) == _lines(plain.stdout)

    failing = tmp_path / "draft"
    _create(failing, draft=True)
    failed_plain, failed = _pair(["gate", "contract", "C-0001", "--path", str(failing)])
    assert failed_plain.exit_code == 1
    assert failed["verdict"] == "FAIL"
    assert failed["passed"] is False
    assert failed["errors"]

    warned = tmp_path / "warn"
    _create(warned, done="Deliver the weekly digest")
    _plain, warning_doc = _pair(["gate", "contract", "C-0001", "--path", str(warned)])
    assert warning_doc["passed"] is True
    assert warning_doc["errors"] == []
    assert any(str(item).startswith("WARN") for item in warning_doc["warnings"])


def test_gate_evidence_pass_and_fail(tmp_path: Path) -> None:
    _create(tmp_path)
    failed_plain, failed = _pair(["gate", "evidence", "C-0001", "--path", str(tmp_path)])
    assert failed_plain.exit_code == 1
    assert failed["gate"] == "evidence"
    assert failed["verdict"] == "FAIL"

    EvidenceService(tmp_path).add(
        change_id="C-0001",
        evidence_type="repository_observation",
        subject="health command",
        source="note",
        producer="agent",
    )
    plain, document = _pair(["gate", "evidence", "C-0001", "--path", str(tmp_path)])
    assert plain.exit_code == 0
    assert document["passed"] is True
    assert document["verdict"] == "PASS"


def test_gate_assurance_pass_and_fail(tmp_path: Path) -> None:
    _create(tmp_path)
    failed_plain, failed = _pair(["gate", "assurance", "C-0001", "--path", str(tmp_path)])
    assert failed_plain.exit_code == 1
    assert failed["gate"] == "assurance"
    assert failed["verdict"] == "FAIL"

    _satisfy(tmp_path)
    plain, document = _pair(["gate", "assurance", "C-0001", "--path", str(tmp_path)])
    assert plain.exit_code == 0
    assert document["passed"] is True
    assert document["findings"]


def test_gate_skill_research_pass_and_fail(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    created = runner.invoke(
        app,
        ["skill", "create", "--need", "JSON consumers", "--path", str(tmp_path)],
    )
    assert created.exit_code == 0, created.stdout
    skill_dir = next((tmp_path / ".retornatus" / "adaptation" / "skills").glob("S-*"))
    skill_id = skill_dir.name
    failed_plain, failed = _pair(["gate", "skill-research", skill_id, "--path", str(tmp_path)])
    assert failed_plain.exit_code == 1
    assert failed["gate"] == "skill-research"
    assert failed["skill_id"] == skill_id
    assert failed["change_id"] is None
    assert failed["verdict"] == "FAIL"

    skill_md = skill_dir / "SKILL.md"
    # Canonical skill files are LF. Path.write_text translates ``\n`` to
    # os.linesep unless newline is set, which rewrites the file as CRLF
    # on Windows.
    body = skill_md.read_text(encoding="utf-8")
    needle = "1.\n2.\n3.\n"
    assert needle in body
    body = body.replace(
        needle,
        "1. Read the schema.\n2. Call the command.\n3. Parse stdout.\n",
        1,
    )
    body += "\nSource: https://json-schema.org/draft/2020-12/schema\n"
    skill_md.write_text(body, encoding="utf-8", newline="\n")
    plain, document = _pair(["gate", "skill-research", skill_id, "--path", str(tmp_path)])
    assert plain.exit_code == 0
    assert document["passed"] is True


def test_gate_skill_research_json_accepts_crlf_skill(tmp_path: Path) -> None:
    """A Windows editor may save SKILL.md with CRLF. The gate still emits JSON."""
    initialize_project(tmp_path)
    created = runner.invoke(
        app,
        ["skill", "create", "--need", "JSON consumers", "--path", str(tmp_path)],
    )
    assert created.exit_code == 0, created.stdout
    skill_dir = next((tmp_path / ".retornatus" / "adaptation" / "skills").glob("S-*"))
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_bytes(skill_md.read_bytes().replace(b"\n", b"\r\n"))
    plain, document = _pair(["gate", "skill-research", skill_dir.name, "--path", str(tmp_path)])
    assert plain.exit_code == 1
    assert document["verdict"] == "FAIL"
    assert document["skill_id"] == skill_dir.name
    assert any("PROCEDURE" in str(item) for item in document["findings"])


def test_gate_policy_pass_and_fail(tmp_path: Path) -> None:
    _create(tmp_path)
    plain, document = _pair(["gate", "policy", "C-0001/A-001", "--path", str(tmp_path)])
    assert plain.exit_code == 0
    assert document["gate"] == "policy"
    assert document["action_id"] == "C-0001/A-001"
    assert document["passed"] is True

    failed_plain, failed = _pair(["gate", "policy", "C-0001/A-999", "--path", str(tmp_path)])
    assert failed_plain.exit_code == 1
    assert failed["verdict"] == "FAIL"
    assert failed["passed"] is False
    assert any("not found" in str(item).lower() for item in failed["findings"])


def test_gate_budget_pass_and_fail(tmp_path: Path) -> None:
    _create(tmp_path, task=True)
    plain, document = _pair(["gate", "budget", "C-0001/A-001", "--path", str(tmp_path)])
    assert plain.exit_code == 0
    assert document["gate"] == "budget"
    assert document["passed"] is True

    limited = runner.invoke(
        app,
        ["action", "budget", "C-0001/A-001", "--max", "1", "--path", str(tmp_path)],
    )
    assert limited.exit_code == 0, limited.stdout
    failed_task = runner.invoke(app, ["task", "fail", "C-0001/T-001", "--path", str(tmp_path)])
    assert failed_task.exit_code == 0, failed_task.stdout
    failed_plain, failed = _pair(["gate", "budget", "C-0001/A-001", "--path", str(tmp_path)])
    assert failed_plain.exit_code == 1
    assert failed["verdict"] == "FAIL"
    assert failed["errors"]


def test_gate_suppressions_pass_and_fail(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    plain, document = _pair(["gate", "suppressions", "--path", str(tmp_path)])
    assert plain.exit_code == 0
    assert document["gate"] == "suppressions"
    assert document["passed"] is True
    assert document["change_id"] is None

    source = tmp_path / "app.py"
    source.write_text("def ok() -> None:\n    return None\n", encoding="utf-8")
    subprocess.run(["git", "add", "app.py"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "app"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    marker = "no" + "qa"
    source.write_text(f"def ok() -> None:  # {marker}\n    return None\n", encoding="utf-8")
    failed_plain, failed = _pair(["gate", "suppressions", "--path", str(tmp_path)])
    assert failed_plain.exit_code == 1
    assert failed["verdict"] == "FAIL"
    assert failed["findings"]
    rendered = runner.invoke(app, ["gate", "suppressions", "--path", str(tmp_path), "--json"])
    assert _lines(rendered.stderr) == _lines(failed_plain.stdout)
    assert rendered.stdout.strip().startswith("{")


def test_gate_scope_pass_and_fail(tmp_path: Path) -> None:
    _git(tmp_path)
    _create(tmp_path, task=True)
    # init writes .gitignore. Commit it so the clean scope check is not an
    # untracked file outside the task resources.
    subprocess.run(
        ["git", "add", "--", ".gitignore"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "gitignore"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    plain, document = _pair(["gate", "scope", "C-0001", "--path", str(tmp_path)])
    assert plain.exit_code == 0
    assert document["gate"] == "scope"
    assert document["passed"] is True

    (tmp_path / "sneak.py").write_text("x = 1\n", encoding="utf-8")
    failed_plain, failed = _pair(["gate", "scope", "C-0001", "--path", str(tmp_path)])
    assert failed_plain.exit_code == 1
    assert failed["verdict"] == "FAIL"
    assert any("sneak.py" in str(item) for item in failed["findings"])


def test_overview_json_pass_and_missing(tmp_path: Path) -> None:
    _create(tmp_path)
    _satisfy(tmp_path)
    plain = runner.invoke(app, ["change", "overview", "C-0001", "--path", str(tmp_path)])
    rendered = runner.invoke(app, ["change", "overview", "C-0001", "--path", str(tmp_path), "--json"])
    formatted = runner.invoke(
        app,
        ["change", "overview", "C-0001", "--path", str(tmp_path), "--format", "json"],
    )
    assert plain.exit_code == 0
    assert rendered.exit_code == 0
    assert formatted.exit_code == 0
    assert rendered.stderr.strip() == ""
    document = _load(rendered.stdout)
    via_format = _load(formatted.stdout)
    _assert_schema(document)
    _assert_schema(via_format)
    assert document["command"] == "change overview"
    assert document["verdict"] == "SATISFIED"
    assert document["title"] == "Health"
    assert document["exit_code"] == 0
    assert document["claims"][0]["status"] == "SATISFIED"
    assert via_format["command"] == document["command"]
    assert via_format["verdict"] == document["verdict"]
    assert "#" in plain.stdout

    contract = tmp_path / ".retornatus" / "changes" / "C-0001" / "contract.json"
    contract.unlink()
    bare = runner.invoke(app, ["change", "overview", "C-0001", "--path", str(tmp_path), "--json"])
    bare_doc = _load(bare.stdout)
    _assert_schema(bare_doc)
    assert bare.exit_code == 0
    assert bare_doc["verdict"] is None
    assert bare_doc["claims"] == []

    missing_plain = runner.invoke(app, ["change", "overview", "C-0099", "--path", str(tmp_path)])
    missing = runner.invoke(app, ["change", "overview", "C-0099", "--path", str(tmp_path), "--json"])
    assert missing_plain.exit_code == 1
    assert missing.exit_code == 1
    assert "Change not found: C-0099" in missing_plain.stdout
    assert "Change not found: C-0099" in missing.stderr
    missing_doc = _load(missing.stdout)
    _assert_schema(missing_doc)
    assert missing_doc["verdict"] is None
    assert missing_doc["exit_code"] == 1
    assert missing_doc["errors"] == ["Change not found: C-0099"]


def test_verify_json_warning_is_diagnostic(tmp_path: Path) -> None:
    _create(tmp_path)
    EvidenceService(tmp_path).add(
        change_id="C-0001",
        evidence_type="test_result",
        subject=infer_claim_subject(_DONE),
        source="noted by hand",
        producer="agent",
        supports_claim_id="C-0001/claim-done-1",
    )
    plain, document = _pair(["verify", "C-0001", "--allow-self-reported", "--path", str(tmp_path)])
    rendered = runner.invoke(
        app,
        [
            "verify",
            "C-0001",
            "--allow-self-reported",
            "--path",
            str(tmp_path),
            "--json",
        ],
    )
    assert plain.exit_code == 0
    assert document["verdict"] == "SATISFIED"
    assert document["warnings"]
    assert "WARN " in rendered.stderr
    assert "WARN " not in rendered.stdout


def test_overview_json_rejects_pr_combination(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    result = runner.invoke(
        app,
        [
            "change",
            "overview",
            "C-0001",
            "--path",
            str(tmp_path),
            "--format",
            "pr",
            "--json",
        ],
    )
    assert result.exit_code == 2
    assert "cannot be combined" in (result.stderr + result.stdout)


def test_documented_example_matches_schema() -> None:
    page = Path(__file__).resolve().parents[1] / "docs" / "guide" / "JSON-output.md"
    text = page.read_text(encoding="utf-8")
    start = text.index("```json")
    body = text[start + len("```json") :]
    example = body[: body.index("```")].strip()
    document = json.loads(example)
    _assert_schema(document)
    assert document["schema_version"] == 1
    assert document["command"] == "verify"
