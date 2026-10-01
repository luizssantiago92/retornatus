"""Path-triggered ship and AI rules on verify."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import tomli_w
from jsonschema import Draft202012Validator
from typer.testing import CliRunner

from retornatus.application.assurance.evidence import EvidenceService
from retornatus.application.assurance.surfaces import (
    evaluate_surface_rules,
    load_surface_settings,
)
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app
from retornatus.domain.enums import EvidenceProvenance
from retornatus.domain.models import Evidence
from retornatus.domain.relations import Relation, RelationType

runner = CliRunner()
_SCHEMA = json.loads(
    (Path(__file__).resolve().parents[1] / "schemas" / "verdict-v1.schema.json").read_text(encoding="utf-8")
)
_VALIDATOR = Draft202012Validator(
    _SCHEMA,
    format_checker=Draft202012Validator.FORMAT_CHECKER,
)
_DONE = "docs/surface.md documents the rollback field"
_CLAIM = "C-0001/claim-done-1"


def _combined(result: object) -> str:
    stdout = getattr(result, "stdout", "") or ""
    stderr = getattr(result, "stderr", "") or ""
    output = getattr(result, "output", "") or ""
    return f"{stdout}\n{stderr}\n{output}"


def _git(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "surface@retornatus.local"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Surface Test"],
        cwd=root,
        check=True,
        capture_output=True,
    )


def _project(tmp_path: Path) -> None:
    initialize_project(tmp_path, preset="python-platform")


def _change(tmp_path: Path, *resources: str) -> None:
    args = [
        "change",
        "create",
        "--path",
        str(tmp_path),
        "--title",
        "Surfaces",
        "--demand",
        "Operators must see ship and AI rules fail closed when scoped paths match and stay not required otherwise.",
        "--what",
        "verify enforces path-triggered surface evidence",
        "--done",
        _DONE,
        "--situation",
        "Infra and AI paths are Task resources or uncommitted files.",
        "--task",
        "Touch the scoped paths",
    ]
    for resource in resources:
        args.extend(["--resource", f"0:{resource}"])
    created = runner.invoke(app, args)
    assert created.exit_code == 0, _combined(created)


def _satisfy_claim(tmp_path: Path) -> None:
    EvidenceService(tmp_path).add(
        change_id="C-0001",
        evidence_type="repository_observation",
        subject="/surface.md",
        source="The surface field is described.",
        producer="test",
        supports_claim_id=_CLAIM,
    )


def _verify(tmp_path: Path) -> tuple[object, dict[str, object]]:
    result = runner.invoke(
        app,
        ["verify", "C-0001", "--path", str(tmp_path), "--json"],
    )
    document = json.loads(result.stdout)
    errors = list(_VALIDATOR.iter_errors(document))
    assert not errors, errors[0].message
    return result, document


def _surface(document: dict[str, object], name: str) -> dict[str, object]:
    surfaces = document["surfaces"]
    assert isinstance(surfaces, list)
    found = [item for item in surfaces if isinstance(item, dict) and item.get("name") == name]
    assert len(found) == 1
    assert isinstance(found[0], dict)
    return found[0]


def _write(tmp_path: Path, mutate: Callable[[dict[str, Any]], None]) -> None:
    path = tmp_path / ".retornatus" / "config.toml"
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(tomli_w.dumps(data), encoding="utf-8")


def test_minimal_verify_omits_surfaces(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    _change(tmp_path, "src/app.py")
    _result, document = _verify(tmp_path)
    assert "surfaces" not in document


def test_rules_are_not_required_without_matching_paths(tmp_path: Path) -> None:
    _project(tmp_path)
    _change(tmp_path, "src/app.py")
    _satisfy_claim(tmp_path)
    result, document = _verify(tmp_path)

    assert result.exit_code == 0, _combined(result)
    assert document["verdict"] == "SATISFIED"
    assert _surface(document, "ship")["status"] == "not required"
    assert _surface(document, "ai")["status"] == "not required"
    assert _surface(document, "ship")["matched_paths"] == []


def test_ship_fails_without_evidence_and_passes_with_it(tmp_path: Path) -> None:
    _project(tmp_path)
    _change(tmp_path, "deploy/Dockerfile")
    _satisfy_claim(tmp_path)
    failed, failed_doc = _verify(tmp_path)

    assert failed.exit_code == 1
    assert failed_doc["verdict"] == "NOT_SATISFIED"
    ship = _surface(failed_doc, "ship")
    assert ship["status"] == "unsatisfied"
    assert ship["matched_paths"] == ["deploy/Dockerfile"]
    missing = " ".join(ship["missing"]) if isinstance(ship["missing"], list) else ""
    assert "docker build ." in missing
    assert "ship rollback" in missing
    assert _surface(failed_doc, "ai")["status"] == "not required"

    command = [sys.executable, "-c", "raise SystemExit(0)"]
    _write(
        tmp_path,
        lambda data: data["surfaces"]["ship"].__setitem__(
            "checks",
            [{"name": "docker", "globs": ["**/Dockerfile"], "run": command}],
        ),
    )
    EvidenceService(tmp_path).run(
        change_id="C-0001",
        evidence_type="build_result",
        subject="deploy/Dockerfile",
        command=command,
    )
    still, still_doc = _verify(tmp_path)
    assert still.exit_code == 1
    assert "rollback note" in " ".join(_surface(still_doc, "ship")["missing"])

    EvidenceService(tmp_path).add(
        change_id="C-0001",
        evidence_type="repository_observation",
        subject="ship rollback",
        source="Redeploy the previous image tag.",
        producer="owner",
    )
    passed, passed_doc = _verify(tmp_path)
    assert passed.exit_code == 0, _combined(passed)
    assert passed_doc["verdict"] == "SATISFIED"
    assert _surface(passed_doc, "ship")["status"] == "satisfied"
    assert _surface(passed_doc, "ship")["missing"] == []


def test_ai_fails_without_evidence_and_passes_with_it(tmp_path: Path) -> None:
    _project(tmp_path)
    _change(tmp_path, "prompts/system.md")
    _satisfy_claim(tmp_path)
    failed, failed_doc = _verify(tmp_path)

    assert failed.exit_code == 1
    ai = _surface(failed_doc, "ai")
    assert ai["status"] == "unsatisfied"
    missing = " ".join(ai["missing"]) if isinstance(ai["missing"], list) else ""
    assert "uv run pytest tests/eval -m not live" in missing
    assert "ai fallback" in missing
    assert _surface(failed_doc, "ship")["status"] == "not required"

    command = [sys.executable, "-c", "raise SystemExit(0)"]
    _write(tmp_path, lambda data: data["surfaces"]["ai"].__setitem__("run", command))
    EvidenceService(tmp_path).run(
        change_id="C-0001",
        evidence_type="test_result",
        subject="prompts/system.md",
        command=command,
    )
    EvidenceService(tmp_path).add(
        change_id="C-0001",
        evidence_type="review_result",
        subject="ai fallback",
        source="Serve the last cached answer and skip tool calls.",
        producer="owner",
    )
    passed, passed_doc = _verify(tmp_path)
    assert passed.exit_code == 0, _combined(passed)
    assert _surface(passed_doc, "ai")["status"] == "satisfied"


def test_untracked_infra_path_triggers_ship_without_a_resource(tmp_path: Path) -> None:
    _git(tmp_path)
    _project(tmp_path)
    _change(tmp_path, "README.md")
    (tmp_path / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    _satisfy_claim(tmp_path)
    _result, document = _verify(tmp_path)

    ship = _surface(document, "ship")
    assert ship["status"] == "unsatisfied"
    assert "docker-compose.yml" in ship["matched_paths"]
    missing = " ".join(ship["missing"]) if isinstance(ship["missing"], list) else ""
    assert "docker compose config --quiet" in missing


def test_glob_override_and_placeholder_note(tmp_path: Path) -> None:
    _project(tmp_path)
    settings = load_surface_settings(tmp_path)
    assert settings is not None
    paths = [
        "Dockerfile",
        "services/Dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        "docker-compose.prod.yml",
        "infra/main.tf",
        "terraform/main.tf",
        "charts/app/Chart.yaml",
        "helm/app/values.yaml",
        ".github/workflows/ci.yml",
        "prompts/system.md",
        "mcp/server.py",
        "evals/golden.json",
        "tests/eval/test_smoke.py",
        "app/llm_client.py",
        "app/rag_index.py",
        "app/embedder.py",
        "src/app.py",
    ]
    rules = evaluate_surface_rules(paths=paths, evidence=[], settings=settings)
    ship = next(item for item in rules if item["name"] == "ship")
    ai = next(item for item in rules if item["name"] == "ai")
    assert ship["status"] == "unsatisfied"
    assert "src/app.py" not in ship["matched_paths"]
    assert "prompts/system.md" not in ship["matched_paths"]
    for path in (
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        "docker-compose.prod.yml",
        "infra/main.tf",
        "terraform/main.tf",
        "charts/app/Chart.yaml",
        "helm/app/values.yaml",
        ".github/workflows/ci.yml",
    ):
        assert path in ship["matched_paths"]
    for path in (
        "prompts/system.md",
        "mcp/server.py",
        "evals/golden.json",
        "tests/eval/test_smoke.py",
        "app/llm_client.py",
        "app/rag_index.py",
        "app/embedder.py",
    ):
        assert path in ai["matched_paths"]
    assert "src/app.py" not in ai["matched_paths"]

    _write(
        tmp_path,
        lambda data: data["surfaces"]["ship"].__setitem__("globs", ["kept/**"]),
    )
    narrowed = load_surface_settings(tmp_path)
    assert narrowed is not None
    narrowed_rules = evaluate_surface_rules(
        paths=["Dockerfile", "kept/notes.txt"],
        evidence=[],
        settings=narrowed,
    )
    narrowed_ship = next(item for item in narrowed_rules if item["name"] == "ship")
    assert narrowed_ship["matched_paths"] == ["kept/notes.txt"]
    assert any("no ship check covers kept/notes.txt" in item for item in narrowed_ship["missing"])

    note = Evidence(
        id="C-0001/E-0001",
        type="repository_observation",
        subject="ship rollback",
        source="tbd",
        producer="test",
        provenance=EvidenceProvenance.SELF_REPORTED,
    )
    fake = Evidence(
        id="C-0001/E-0002",
        type="build_result",
        subject="Dockerfile",
        source="noted",
        producer="test",
        provenance=EvidenceProvenance.SELF_REPORTED,
        command=["docker", "build", "."],
        exit_code=0,
        relations=[Relation(type=RelationType.SUPPORTS, target_id=_CLAIM)],
    )
    placeholder = evaluate_surface_rules(
        paths=["Dockerfile"],
        evidence=[note, fake],
        settings=settings,
    )
    missed = next(item for item in placeholder if item["name"] == "ship")
    blob = " ".join(missed["missing"])
    assert "executed check docker" in blob
    assert "rollback note" in blob


def test_fastapi_migration_paths_trigger_ship_surface(tmp_path: Path) -> None:
    initialize_project(tmp_path, preset="fastapi")
    _change(
        tmp_path,
        "alembic/versions/0001_init.py",
        "src/myapp/alembic/versions/0002_column.py",
    )
    _satisfy_claim(tmp_path)
    failed, failed_doc = _verify(tmp_path)

    assert failed.exit_code == 1
    ship = _surface(failed_doc, "ship")
    assert ship["status"] == "unsatisfied"
    assert ship["matched_paths"] == [
        "alembic/versions/0001_init.py",
        "src/myapp/alembic/versions/0002_column.py",
    ]
    assert ship["required_checks"] == []
    missing = " ".join(ship["missing"]) if isinstance(ship["missing"], list) else ""
    assert "ship rollback" in missing
    assert "alembic check" not in missing
    assert "no ship check covers" not in missing
    assert _surface(failed_doc, "ai")["status"] == "not required"

    EvidenceService(tmp_path).add(
        change_id="C-0001",
        evidence_type="repository_observation",
        subject="ship rollback",
        source="Run alembic downgrade -1 back to the previous revision.",
        producer="owner",
    )
    passed, passed_doc = _verify(tmp_path)
    assert passed.exit_code == 0, _combined(passed)
    assert passed_doc["verdict"] == "SATISFIED"
    assert _surface(passed_doc, "ship")["status"] == "satisfied"
    assert _surface(passed_doc, "ship")["missing"] == []


def test_django_migration_paths_trigger_ship_surface(tmp_path: Path) -> None:
    initialize_project(tmp_path, preset="django")
    _change(
        tmp_path,
        "polls/migrations/0001_initial.py",
        "apps/blog/migrations/0002_title.py",
    )
    _satisfy_claim(tmp_path)
    failed, failed_doc = _verify(tmp_path)

    assert failed.exit_code == 1
    ship = _surface(failed_doc, "ship")
    assert ship["status"] == "unsatisfied"
    assert ship["matched_paths"] == [
        "polls/migrations/0001_initial.py",
        "apps/blog/migrations/0002_title.py",
    ]
    assert ship["required_checks"] == []
    missing = " ".join(ship["missing"]) if isinstance(ship["missing"], list) else ""
    assert "ship rollback" in missing
    assert "makemigrations" not in missing
    assert "no ship check covers" not in missing
    assert _surface(failed_doc, "ai")["status"] == "not required"

    EvidenceService(tmp_path).add(
        change_id="C-0001",
        evidence_type="repository_observation",
        subject="ship rollback",
        source="Reverse polls with python manage.py migrate polls zero.",
        producer="owner",
    )
    passed, passed_doc = _verify(tmp_path)
    assert passed.exit_code == 0, _combined(passed)
    assert passed_doc["verdict"] == "SATISFIED"
    assert _surface(passed_doc, "ship")["status"] == "satisfied"
    assert _surface(passed_doc, "ship")["missing"] == []


def test_fastapi_keeps_platform_docker_check(tmp_path: Path) -> None:
    initialize_project(tmp_path, preset="fastapi")
    settings = load_surface_settings(tmp_path)
    assert settings is not None
    rules = evaluate_surface_rules(
        paths=["deploy/Dockerfile"],
        evidence=[],
        settings=settings,
    )
    ship = next(item for item in rules if item["name"] == "ship")
    assert ship["matched_paths"] == ["deploy/Dockerfile"]
    assert "docker build ." in " ".join(ship["missing"])


_RAG_AI_PATHS = (
    "prompts/system.txt",
    "evals/golden.jsonl",
    "tests/eval/test_retrieval.py",
    "mcp/server.py",
    "retrieval/search.py",
    "rag/pipeline.py",
    "src/rag/chain.py",
    "ingest/load.py",
    "ingestion/chunk.py",
    "embeddings/store.py",
    "vectorstore/client.py",
    "vectorstores/qdrant.py",
    "indexes/chunks.bin",
    "faiss_index/data.bin",
    "vector-index/meta.json",
    "config/models.yaml",
    "service/models.toml",
)


def test_rag_ai_paths_trigger_ai_surface(tmp_path: Path) -> None:
    initialize_project(tmp_path, preset="rag")
    _change(tmp_path, *_RAG_AI_PATHS)
    _satisfy_claim(tmp_path)
    failed, failed_doc = _verify(tmp_path)

    assert failed.exit_code == 1
    ai = _surface(failed_doc, "ai")
    assert ai["status"] == "unsatisfied"
    assert ai["matched_paths"] == list(_RAG_AI_PATHS)
    missing = " ".join(ai["missing"]) if isinstance(ai["missing"], list) else ""
    assert "uv run pytest tests/eval -m not live" in missing
    assert "ai fallback" in missing
    assert _surface(failed_doc, "ship")["status"] == "not required"

    command = [sys.executable, "-c", "raise SystemExit(0)"]
    _write(tmp_path, lambda data: data["surfaces"]["ai"].__setitem__("run", command))
    EvidenceService(tmp_path).run(
        change_id="C-0001",
        evidence_type="test_result",
        subject="tests/eval",
        command=command,
    )
    EvidenceService(tmp_path).add(
        change_id="C-0001",
        evidence_type="repository_observation",
        subject="ai fallback",
        source="Return a cached FAQ when the model times out.",
        producer="owner",
    )
    passed, passed_doc = _verify(tmp_path)
    assert passed.exit_code == 0, _combined(passed)
    assert passed_doc["verdict"] == "SATISFIED"
    assert _surface(passed_doc, "ai")["status"] == "satisfied"
    assert _surface(passed_doc, "ai")["missing"] == []


def test_rag_non_ai_paths_are_not_required(tmp_path: Path) -> None:
    initialize_project(tmp_path, preset="rag")
    _change(
        tmp_path,
        "src/app.py",
        "tests/test_api.py",
        "docs/index/page.md",
        "src/domain/models.py",
        "README.md",
    )
    _satisfy_claim(tmp_path)
    result, document = _verify(tmp_path)

    assert result.exit_code == 0, _combined(result)
    assert document["verdict"] == "SATISFIED"
    assert _surface(document, "ai")["status"] == "not required"
    assert _surface(document, "ai")["matched_paths"] == []
    assert _surface(document, "ship")["status"] == "not required"


_WORKER_SHIP_PATHS = (
    "tasks/email.py",
    "app/tasks.py",
    "src/myapp/workers/billing.py",
    "app/worker.py",
    "jobs/nightly.py",
    "celery_app.py",
    "src/myapp/celery.py",
    "celeryconfig.py",
    "app/beat_schedule.py",
    "schedules/cron.yaml",
    "config/queues.yaml",
)


def test_worker_task_paths_require_retry_note(tmp_path: Path) -> None:
    initialize_project(tmp_path, preset="worker")
    _change(tmp_path, *_WORKER_SHIP_PATHS)
    _satisfy_claim(tmp_path)
    failed, failed_doc = _verify(tmp_path)

    assert failed.exit_code == 1
    ship = _surface(failed_doc, "ship")
    assert ship["status"] == "unsatisfied"
    assert ship["matched_paths"] == list(_WORKER_SHIP_PATHS)
    assert ship["required_checks"] == []
    missing = " ".join(ship["missing"]) if isinstance(ship["missing"], list) else ""
    assert "ship rollback and job retry" in missing
    assert "inspect ping" not in missing
    assert "no ship check covers" not in missing
    assert _surface(failed_doc, "ai")["status"] == "not required"

    EvidenceService(tmp_path).add(
        change_id="C-0001",
        evidence_type="repository_observation",
        subject="ship rollback",
        source="Redeploy the previous image tag.",
        producer="owner",
    )
    still, still_doc = _verify(tmp_path)
    assert still.exit_code == 1
    assert _surface(still_doc, "ship")["status"] == "unsatisfied"

    EvidenceService(tmp_path).add(
        change_id="C-0001",
        evidence_type="repository_observation",
        subject="ship rollback and job retry",
        source=(
            "Redeploy the previous image tag. send_invoice retries three times with "
            "backoff and checks the invoice id first, so a re-run does not send twice."
        ),
        producer="owner",
    )
    passed, passed_doc = _verify(tmp_path)
    assert passed.exit_code == 0, _combined(passed)
    assert passed_doc["verdict"] == "SATISFIED"
    assert _surface(passed_doc, "ship")["status"] == "satisfied"
    assert _surface(passed_doc, "ship")["missing"] == []


def test_worker_non_task_paths_are_not_required(tmp_path: Path) -> None:
    initialize_project(tmp_path, preset="worker")
    _change(
        tmp_path,
        "src/myapp/api.py",
        "tests/test_tasks.py",
        "docs/jobs.md",
        "README.md",
    )
    _satisfy_claim(tmp_path)
    result, document = _verify(tmp_path)

    assert result.exit_code == 0, _combined(result)
    assert document["verdict"] == "SATISFIED"
    assert _surface(document, "ship")["status"] == "not required"
    assert _surface(document, "ship")["matched_paths"] == []
    assert _surface(document, "ai")["status"] == "not required"


def test_worker_keeps_platform_docker_check(tmp_path: Path) -> None:
    initialize_project(tmp_path, preset="worker")
    settings = load_surface_settings(tmp_path)
    assert settings is not None
    assert settings.ship_note_subject == "ship rollback and job retry"
    rules = evaluate_surface_rules(
        paths=["deploy/Dockerfile"],
        evidence=[],
        settings=settings,
    )
    ship = next(item for item in rules if item["name"] == "ship")
    assert ship["matched_paths"] == ["deploy/Dockerfile"]
    blob = " ".join(ship["missing"])
    assert "docker build ." in blob
    assert "ship rollback and job retry" in blob
