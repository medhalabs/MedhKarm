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
                f"Assigned \u201c{task['title']}\u201d to {task['owner']}"
                + (f" ({task['specialty']})" if task.get("specialty", "any") != "any" else ""),
                {
                    "task_id": task["id"],
                    "member": task["owner"],
                    "title": task["title"],
                    "specialty": task.get("specialty", "any"),
                },
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
        await _record_checks(recorder, data)
    elif node == "browser_qa" and data.get("browser", {}).get("needed"):
        await _record_browser(recorder, data)
    elif node == "security" and data.get("security"):
        await _record_security(recorder, data)
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
    elif node == "preview" and data.get("preview", {}).get("kind", "none") != "none":
        preview = data["preview"]
        summary = (
            f"Preview ready: {preview['url']}"
            if preview.get("state") == "READY"
            else f"The preview didn't build: {preview.get('error') or preview.get('state')}"
        )
        await recorder.record(Actor.DEVOPS, EventType.DEPLOY_FINISHED, summary, preview)
    elif node == "finish":
        status = data.get("status", "finished")
        deployment = data.get("deployment")
        if deployment:
            summary = (
                f"Live at {deployment['url']}"
                if deployment.get("state") == "READY"
                else f"Couldn't put it live: {deployment.get('error') or deployment.get('state')}"
            )
            await recorder.record(Actor.DEVOPS, EventType.DEPLOY_FINISHED, summary, deployment)
        delivery = data.get("delivery")
        if delivery:
            if delivery.get("pull_request_url"):
                summary = f"Opened a pull request: {delivery['pull_request_url']}"
            elif delivery.get("repo_url"):
                summary = f"Created the repository and pushed the work: {delivery['repo_url']}"
            else:
                summary = f"Didn't deliver to GitHub: {delivery.get('reason', '')}"
            await recorder.record(Actor.DEVOPS, EventType.CHANGES_DELIVERED, summary, delivery)
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


async def _record_checks(recorder: RunRecorder, data: dict[str, Any]) -> None:
    passed = bool(data.get("verified"))
    checks = data.get("checks", [])
    names = ", ".join(c["name"] for c in checks if c.get("passed")) or "tests"
    old = [c["name"] for c in checks if not c.get("passed") and c.get("already_failing")]
    fix = next(
        (t for t in data.get("tasks", []) if t.get("id") == f"qa{data.get('qa_rounds')}"), None
    )
    if passed:
        summary = f"Checks passed ({names})"
        if old:
            summary += f"; already failing before this work: {', '.join(old)}"
    elif fix and fix.get("status") == "todo":
        summary = f"Checks failed: sent to {fix['owner']} to fix"
    elif str(data.get("verify_output", "")).startswith("No files were changed"):
        summary = "Stopped: no files were changed"
    else:
        summary = "Stopped: the checks still fail"
    await recorder.record(
        Actor.QA,
        EventType.CHECK_FINISHED,
        summary,
        {
            "passed": passed,
            "output": str(data.get("verify_output", ""))[-2000:],
            "checks": checks,
        },
    )
    if fix and fix.get("status") == "todo" and not passed:
        await recorder.record(
            Actor.QA,
            EventType.TASK_ASSIGNED,
            f"Assigned \u201c{fix['title']}\u201d to {fix['owner']}",
            {"task_id": fix["id"], "member": fix["owner"], "title": fix["title"]},
        )


async def _record_security(recorder: RunRecorder, data: dict[str, Any]) -> None:
    report = data["security"]
    blocking, warnings = int(report.get("blocking", 0)), int(report.get("warnings", 0))
    fix = next(
        (t for t in data.get("tasks", []) if t.get("id") == f"sec{report['round'] + 1}"), None
    )
    if not blocking:
        summary = (
            "No security problems found"
            if not warnings
            else (f"No blocking problems; {warnings} warning{'s' if warnings != 1 else ''} for you")
        )
    elif fix:
        problems = f"{blocking} security problem{'s' if blocking != 1 else ''}"
        summary = f"Found {problems}: sent to {fix['owner']} to fix"
    else:
        problems = f"{blocking} security problem{'s' if blocking != 1 else ''}"
        summary = f"Stopped the release: {problems} still there"
    await recorder.record(Actor.SECURITY, EventType.SECURITY_FINISHED, summary, report)
    if fix:
        await recorder.record(
            Actor.SECURITY,
            EventType.TASK_ASSIGNED,
            f"Assigned \u201c{fix['title']}\u201d to {fix['owner']}",
            {"task_id": fix["id"], "member": fix["owner"], "title": fix["title"]},
        )


async def _record_browser(recorder: RunRecorder, data: dict[str, Any]) -> None:
    browser = data["browser"]
    fix = next(
        (t for t in data.get("tasks", []) if t.get("id") == f"ui{browser['round'] + 1}"), None
    )
    tests = ", ".join(browser.get("test_files", [])) or "no test"
    if browser.get("passed"):
        summary = f"Browser test passed ({tests})"
    elif fix:
        summary = f"Browser test failed: sent to {fix['owner']} to fix"
    elif not browser.get("test_files"):
        summary = "Stopped: QA couldn't write a working browser test"
    else:
        summary = "Stopped the release: the browser test still fails"
    await recorder.record(
        Actor.QA,
        EventType.CHECK_FINISHED,
        summary,
        {"passed": bool(browser.get("passed")), "browser": True, **browser},
    )
    if fix:
        await recorder.record(
            Actor.QA,
            EventType.TASK_ASSIGNED,
            f"Assigned \u201c{fix['title']}\u201d to {fix['owner']}",
            {"task_id": fix["id"], "member": fix["owner"], "title": fix["title"]},
        )
