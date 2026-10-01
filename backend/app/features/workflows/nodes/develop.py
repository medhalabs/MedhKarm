"""Developer node: creates the run's sandbox and has the developer engine do the work."""

from typing import Any

from app.features.developer_engine.interfaces import DeveloperEngine
from app.features.developer_engine.schemas import DevTask
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
        recorder = RunRecorder(events, state.get("run_id", "unknown"))
        sandbox = (
            await sandboxes.attach(state["sandbox_id"])
            if state.get("sandbox_id")
            else await sandboxes.create()
        )
        task = DevTask(
            description=f"{state['request']}\n\nPlan from the tech lead:\n{state.get('plan', '')}",
            test_command=state["test_command"],
        )
        await recorder.record(Actor.DEVELOPER, EventType.WORK_STARTED, "Started on the task")
        result = await engine.run_task(task, sandbox, recorder)
        return {"sandbox_id": sandbox.id, "dev_result": result.model_dump()}

    return develop
