"""Turns workflow steps into activity-log events. One place decides what each step means
to the founder, so the office, the feed and the standup all describe it the same way."""

from typing import Any

from app.features.events.schemas import Actor, EventType
from app.features.events.service import RunRecorder


async def record_step(recorder: RunRecorder, node: str, data: dict[str, Any]) -> None:
    if node in ("plan", "review") and data.get("cto_tokens"):
        await recorder.record(
            Actor.CTO,
            EventType.MODEL_USED,
            "Thought about the plan" if node == "plan" else "Reviewed the work",
            tokens=int(data["cto_tokens"]),
        )
    if node == "connect" and data.get("codebase_map"):
        first_line = str(data["codebase_map"]).splitlines()[0]
        await recorder.record(
            Actor.CTO,
            EventType.CODEBASE_MAPPED,
            ("Read the project before planning: " + first_line)
            + ("" if data.get("setup_ok", True) else " Installing its dependencies failed."),
            {
                "map": str(data["codebase_map"])[:6000],
                "commit": data.get("repo_commit", ""),
                "test_command": data.get("test_command", ""),
                "setup_ok": data.get("setup_ok", True),
            },
        )
    if node == "plan":
        tasks = data.get("tasks", [])
        team = sorted({t["owner"] for t in tasks})
        await recorder.record(
            Actor.CTO,
            EventType.PLAN_CREATED,
            f"Split the work into {len(tasks)} task{'s' if len(tasks) != 1 else ''} "
            f"for {', '.join(team) or 'the team'}",
            {"plan": data.get("plan", ""), "tasks": [_task_brief(t) for t in tasks]},
        )
        for task in tasks:
            await recorder.record(
                Actor.CTO,
                EventType.TASK_ASSIGNED,
                f"Assigned \u201c{task['title']}\u201d to {task['owner']}",
                {"task_id": task["id"], "member": task["owner"], "title": task["title"]},
            )
    elif node == "develop":
        task = next((t for t in data.get("tasks", []) if t.get("status") == "review"), None)
        if task:
            await recorder.record(
                Actor.DEVELOPER,
                EventType.WORK_FINISHED,
                f"{task['owner']}: {task.get('summary') or 'finished ' + task['title']}",
                {
                    "task_id": task["id"],
                    "member": task["owner"],
                    "success": task.get("success"),
                    "files_changed": task.get("files_changed", []),
                    "attempt": task.get("attempts"),
                },
            )
    elif node == "review":
        review = data.get("last_review")
        if review:
            if review["decision"] == "approve":
                title = review["title"]
                summary = f"Approved \u201c{title}\u201d"
                if review.get("accepted_with_issues"):
                    summary = f"Moved on from \u201c{title}\u201d after the last round of changes"
            else:
                feedback = review["feedback"][:160]
                summary = (
                    f"Sent \u201c{review['title']}\u201d back to {review['member']}: {feedback}"
                )
            await recorder.record(Actor.CTO, EventType.REVIEW_FINISHED, summary, review)
    elif node == "verify":
        passed = bool(data.get("verified"))
        await recorder.record(
            Actor.QA,
            EventType.CHECK_FINISHED,
            "Checks passed" if passed else "Checks failed: sent back",
            {"passed": passed, "output": str(data.get("verify_output", ""))[-2000:]},
        )
    elif node == "approval":
        approval = data.get("approval", {})
        if approval.get("decided_by") == "rules":  # founders' decisions are recorded on resume
            approved = bool(data.get("approved"))
            await recorder.record(
                Actor.SYSTEM,
                EventType.APPROVAL_DECIDED,
                ("Approved the release by your rules: " if approved else "Stopped by your rules: ")
                + " ".join(approval.get("reasons", [])),
                {"approved": approved, "rules": approval.get("rule_ids", []), "by": "rules"},
            )
    elif node == "finish":
        status = data.get("status", "finished")
        delivery = data.get("delivery")
        if delivery:
            await recorder.record(
                Actor.DEVOPS,
                EventType.CHANGES_DELIVERED,
                f"Opened a pull request: {delivery['pull_request_url']}"
                if delivery.get("pull_request_url")
                else f"Didn't open a pull request: {delivery.get('reason', '')}",
                delivery,
            )
        summaries = {
            "released": "Released",
            "rejected": "Stopped: release not approved",
            "failed": "Stopped: checks did not pass",
        }
        await recorder.record(
            Actor.SYSTEM, EventType.RUN_FINISHED, summaries.get(status, status), {"status": status}
        )


def _task_brief(task: dict[str, Any]) -> dict[str, Any]:
    return {"id": task["id"], "title": task["title"], "owner": task["owner"]}
