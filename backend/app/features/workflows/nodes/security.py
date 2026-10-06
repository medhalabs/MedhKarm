"""Security engineer (Vikram): scans what the run changed, after QA passed and before the
release gate. Blocking findings go back to a developer as one more task (once); if they're
still there after that, the release stops without asking the founder. Warnings go on to the
gate, where the founder sees them."""

from typing import Any

from app.features.sandbox.interfaces import SandboxProvider
from app.features.security.schemas import SecurityReport
from app.features.security.service import SecurityReview
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState

FIX_TITLE = "Fix the security findings"


def make_security_node(
    sandboxes: SandboxProvider,
    review: SecurityReview | None,
    developer_names: list[str] | None = None,
    max_fix_rounds: int = 1,
) -> BuildNode:
    owner = (developer_names or ["Developer"])[0]

    async def security(state: BuildState) -> dict[str, Any]:
        if review is None:  # no security engineer on this team
            return {"security_passed": True}
        sandbox = await sandboxes.attach(state["sandbox_id"])
        changed = list(state.get("dev_result", {}).get("files_changed", []))
        report = await review.review(sandbox, changed)
        rounds = state.get("security_rounds", 0)
        update: dict[str, Any] = {
            "security": {
                **report.model_dump(mode="json"),
                "blocking": len(report.blocking),
                "warnings": len(report.warnings),
                "round": rounds,
            },
            "security_passed": not report.blocking,
        }
        if report.blocking and rounds < max_fix_rounds:
            tasks = [dict(t) for t in state.get("tasks", [])]
            tasks.append(_fix_task(report, owner, rounds + 1))
            update |= {
                "tasks": tasks,
                "current_task": len(tasks) - 1,
                "security_rounds": rounds + 1,
            }
        return update

    return security


def after_security(state: BuildState) -> str:
    """Back to a developer for a fix task, on to the founder's gate, or stop."""
    if state.get("current_task", 0) < len(state.get("tasks", [])):
        return "develop"
    return "changelog" if state.get("security_passed", True) else "finish"


def _fix_task(report: SecurityReport, owner: str, round_: int) -> dict[str, Any]:
    return {
        "id": f"sec{round_}",
        "title": FIX_TITLE,
        "description": report.brief(),
        "owner": owner,
        "status": "todo",
        "attempts": 0,
        "feedback": "",
        "summary": "",
        "files_changed": [],
        "success": False,
    }
