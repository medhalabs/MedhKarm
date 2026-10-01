"""Developer node: the assigned developer works on the current task in the run's sandbox."""

from typing import Any

from app.features.developer_engine.interfaces import DeveloperEngine
from app.features.developer_engine.schemas import DevResult, DevTask
from app.features.events.interfaces import EventStore
from app.features.events.schemas import Actor, EventType
from app.features.events.service import RunRecorder
from app.features.sandbox.interfaces import SandboxProvider
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState


def make_develop_node(
    engine: DeveloperEngine, sandboxes: SandboxProvider, events: EventStore | None = None
) -> BuildNode:
    async def develop(state: BuildState) -> dict[str, Any]:
        sandbox = (
            await sandboxes.attach(state["sandbox_id"])
            if state.get("sandbox_id")
            else await sandboxes.create()
        )
        tasks = [dict(t) for t in state.get("tasks", [])] or [_whole_request(state)]
        index = min(state.get("current_task", 0), len(tasks) - 1)
        task = tasks[index]
        recorder = RunRecorder(events, state.get("run_id", "unknown")).with_context(
            member=task["owner"], task_id=task["id"]
        )

        await recorder.record(
            Actor.DEVELOPER,
            EventType.WORK_STARTED,
            f"{task['owner']} started: {task['title']}"
            + (" (changes from review)" if task.get("feedback") else ""),
        )
        result = await engine.run_task(
            DevTask(
                description=_brief(state, task, index, len(tasks)),
                test_command=state["test_command"],
            ),
            sandbox,
            recorder,
        )

        task.update(
            status="review",
            attempts=task.get("attempts", 0) + 1,
            summary=result.summary,
            success=result.success,
            test_output=result.test_output[-1500:],
            files_changed=sorted(set(task.get("files_changed", [])) | set(result.files_changed)),
        )
        return {
            "sandbox_id": sandbox.id,
            "tasks": tasks,
            "dev_result": _total(state.get("dev_result", {}), result),
        }

    return develop


def _brief(state: BuildState, task: dict[str, Any], index: int, count: int) -> str:
    brief = (
        f"{state['request']}\n\nThe CTO's plan:\n{state.get('plan', '')}\n\n"
        f"Your task ({index + 1} of {count}): {task['title']}\n{task.get('description', '')}\n"
        "Earlier tasks may already be done in this workspace; build on them."
    )
    if task.get("feedback"):
        brief += (
            "\n\nThe CTO reviewed your last attempt and asked for these changes:\n"
            + task["feedback"]
        )
    return brief


def _total(previous: dict[str, Any], result: DevResult) -> dict[str, Any]:
    """All developer work in this run, totalled, in DevResult's shape (latest task's outcome)."""
    return {
        "success": result.success,
        "summary": result.summary,
        "files_changed": sorted(set(previous.get("files_changed", [])) | set(result.files_changed)),
        "test_output": result.test_output,
        "steps": previous.get("steps", 0) + result.steps,
        "total_tokens": previous.get("total_tokens", 0) + result.total_tokens,
    }


def _whole_request(state: BuildState) -> dict[str, Any]:
    return {
        "id": "t1",
        "title": "Build the request",
        "description": state["request"],
        "owner": "Developer",
        "status": "todo",
        "attempts": 0,
        "feedback": "",
        "files_changed": [],
    }
