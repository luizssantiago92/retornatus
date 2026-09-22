"""Project active Rules into native Environment bridge surfaces (PRD M10/M11)."""

from __future__ import annotations

from pathlib import Path

from retornatus.domain.models import Rule
from retornatus.infrastructure.persistence.repository import FileRepository

RULES_BEGIN = "<!-- retornatus-active-rules:begin -->"
RULES_END = "<!-- retornatus-active-rules:end -->"


def list_active_rules(root: Path) -> list[Rule]:
    """Return active Rules from canonical storage (empty if uninitialized)."""
    try:
        return [r for r in FileRepository(root).list_rules() if r.active]
    except Exception:  # noqa: BLE001 — projection must not break adapters
        return []


def format_active_rules_markdown(rules: list[Rule]) -> str:
    """Human-readable projection of active Rules for bridge files."""
    active = [r for r in rules if r.active]
    if not active:
        return "_No active Retornatus Rules._"
    lines = ["Active Retornatus Rules (canonical truth: `.retornatus/`):", ""]
    for rule in sorted(active, key=lambda r: r.id):
        lines.append(
            f"- **{rule.id}**: {rule.statement} "
            f"_(applicability: {rule.applicability})_"
        )
    return "\n".join(lines)


def upsert_rules_section(text: str, rules_body: str) -> str:
    """Insert or replace the marked active-Rules section in bridge text."""
    block = f"{RULES_BEGIN}\n{rules_body.rstrip()}\n{RULES_END}"
    if RULES_BEGIN in text and RULES_END in text:
        start = text.index(RULES_BEGIN)
        end = text.index(RULES_END) + len(RULES_END)
        return text[:start] + block + text[end:]
    base = text.rstrip()
    if base:
        return base + "\n\n" + block + "\n"
    return block + "\n"


def project_active_rules_into(path: Path, root: Path) -> Path:
    """
    Upsert active Rules into an existing or new markdown/mdc bridge file.

    Creates parent directories. Does not delete host content outside the markers.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    body = format_active_rules_markdown(list_active_rules(root))
    path.write_text(upsert_rules_section(existing, body), encoding="utf-8")
    return path


def refresh_detected_bridges(root: Path) -> list[Path]:
    """Re-project bridges for the detected Environment (Rules + markers)."""
    from retornatus.infrastructure.environment.adapters import detect_environment

    adapter, _ = detect_environment(root)
    return adapter.ensure_bridge_files(root)
