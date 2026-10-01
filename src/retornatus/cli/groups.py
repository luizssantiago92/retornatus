"""Typer apps. Command modules register themselves on import."""

from __future__ import annotations

import typer

from retornatus.cli.common import configure_stdio
from retornatus.cli.errors import GuardedTyperGroup

configure_stdio()

app = typer.Typer(
    name="retornatus",
    help=(
        "Repo-native governance harness for AI-assisted software development.\n\n"
        "Govern the work. Bound the agent. Verify the outcome."
    ),
    no_args_is_help=True,
    add_completion=False,
    cls=GuardedTyperGroup,
)

change_app = typer.Typer(help="Create and inspect Changes.")
skill_app = typer.Typer(help="Specialization Skills — create, evolve, export.")
gate_app = typer.Typer(help="Mechanical gates (non-zero exit = STOP).")
evidence_app = typer.Typer(help="Attributable Evidence.")
finding_app = typer.Typer(help="Findings.")
question_app = typer.Typer(help="Questions grounded in Findings.")
loop_app = typer.Typer(help="Next ready unit of work (projection).")
decision_app = typer.Typer(help="Human Decisions (HUMAN authority boundary).")
rule_app = typer.Typer(help="Rule candidates and activation.")
policy_app = typer.Typer(help="Policy evaluation (ALLOW / DENY / REQUIRE_HUMAN).")
assurance_app = typer.Typer(help="Assurance evaluation and independent review.")
execution_app = typer.Typer(help="Host Execution observations (not an agent runtime).")
task_app = typer.Typer(help="Task lifecycle within an Action.")
lesson_app = typer.Typer(help="Lessons from gate failures (Learning + optional Rule Candidate).")
ops_app = typer.Typer(help="Operational hygiene loops (not Change construction).")
intake_app = typer.Typer(help="Analyze freeform prompts; propose Skills only with human confirmation.")
action_app = typer.Typer(help="Action utilities (budget / attempt ceiling).")
checks_app = typer.Typer(help="Run owner-declared required checks and record Evidence.")
ci_app = typer.Typer(help="CI helpers. Render a pull-request comment from verify and gate JSON.")
hooks_app = typer.Typer(help="Git hooks: suppression scan, scope gate, commit message path.")
hook_app = typer.Typer(
    help=(
        "Agent hooks. stop guards the turn. "
        "session-start injects the active Change. "
        "file-edit warns when an edit leaves the active Change scope."
    )
)
preset_app = typer.Typer(help="Inspect packaged config presets.")
receipt_app = typer.Typer(
    help=(
        "Ed25519 verify receipts. The private key stays outside the repository; "
        "verification uses the committed public key."
    )
)

app.add_typer(change_app, name="change")
app.add_typer(skill_app, name="skill")
app.add_typer(gate_app, name="gate")
app.add_typer(evidence_app, name="evidence")
app.add_typer(finding_app, name="finding")
app.add_typer(question_app, name="question")
app.add_typer(loop_app, name="loop")
app.add_typer(decision_app, name="decision")
app.add_typer(rule_app, name="rule")
app.add_typer(policy_app, name="policy")
app.add_typer(assurance_app, name="assurance")
app.add_typer(execution_app, name="execution")
app.add_typer(task_app, name="task")
app.add_typer(lesson_app, name="lesson")
app.add_typer(ops_app, name="ops")
app.add_typer(intake_app, name="intake")
app.add_typer(action_app, name="action")
app.add_typer(checks_app, name="checks")
app.add_typer(ci_app, name="ci")
app.add_typer(hooks_app, name="hooks")
app.add_typer(hook_app, name="hook")
app.add_typer(preset_app, name="preset")
app.add_typer(receipt_app, name="receipt")
