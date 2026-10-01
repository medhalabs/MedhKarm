"""Turns workflow steps into activity-log events. One place decides what each step means
to the founder, so the office, the feed and the standup all describe it the same way."""

from typing import Any

from app.features.events.schemas import Actor, EventType
from app.features.events.service import RunRecorder


async def record_step(recorder: RunRecorder, node: str, data: dict[str, Any]) -> None:
    if node == "plan":
        await recorder.record(
            Actor.CTO, EventType.PLAN_CREATED, "Wrote the plan", {"plan": data.get("plan", "")}
        )
    elif node == "develop":
        dev = data.get("dev_result", {})
        files = dev.get("files_changed", [])
        await recorder.record(
            Actor.DEVELOPER,
            EventType.WORK_FINISHED,
            dev.get("summary") or "Finished working",
            {
                "success": dev.get("success"),
                "files_changed": files,
                "steps": dev.get("steps"),
                "total_tokens": dev.get("total_tokens"),
            },
        )
    elif node == "verify":
        passed = bool(data.get("verified"))
        await recorder.record(
            Actor.QA,
            EventType.CHECK_FINISHED,
            "Checks passed" if passed else "Checks failed: sent back",
            {"passed": passed, "output": str(data.get("verify_output", ""))[-2000:]},
        )
    elif node == "finish":
        status = data.get("status", "finished")
        summaries = {
            "released": "Released",
            "rejected": "Stopped: release not approved",
            "failed": "Stopped: checks did not pass",
        }
        await recorder.record(
            Actor.SYSTEM, EventType.RUN_FINISHED, summaries.get(status, status), {"status": status}
        )
