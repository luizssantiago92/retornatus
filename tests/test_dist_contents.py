"""Distribution contents checker."""

from __future__ import annotations

import importlib.util
import io
import tarfile
import zipfile
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "check_dist_contents",
    Path(__file__).resolve().parents[1] / "scripts" / "check_dist_contents.py",
)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
check_dist = _MODULE.check_dist
offending_members = _MODULE.offending_members


def test_offending_members_flags_fixtures_and_leaks() -> None:
    names = [
        "retornatus/application/execution/context.py",
        "retornatus/application/execution/host_boundary.py",
        "retornatus/application/execution/brownfield_fixture.py",
        "tests/test_cli.py",
        "scripts/build_docs_html.py",
        ".assets/retornatus-mascot.png",
        "docs/assets/mascot.webp",
    ]
    bad = offending_members(names)
    assert "retornatus/application/execution/context.py" not in bad
    assert any(name.endswith("host_boundary.py") for name in bad)
    assert any(name.endswith("brownfield_fixture.py") for name in bad)
    assert any(name.startswith("tests/") for name in bad)
    assert any(name.startswith("scripts/") for name in bad)
    assert any(".assets/" in name for name in bad)
    assert any(name.endswith("mascot.webp") for name in bad)


def test_check_dist_reads_a_wheel(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    wheel = dist / "retornatus-1.3.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("retornatus/__init__.py", "")
        archive.writestr("retornatus/application/execution/host_boundary.py", "x = 1\n")

    payload = b"print('ok')\n"
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as archive:
        info = tarfile.TarInfo("retornatus-1.3.0/src/retornatus/__init__.py")
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    (dist / "retornatus-1.3.0.tar.gz").write_bytes(buf.getvalue())

    problems = check_dist(dist)
    assert any("host_boundary.py" in problem for problem in problems)
    assert not any(problem.endswith("__init__.py") for problem in problems)
