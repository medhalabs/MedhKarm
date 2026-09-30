"""Developer node: creates the run's sandbox and has the developer engine do the work."""

from typing import Any

from app.features.developer_engine.interfaces import DeveloperEngine
from app.features.developer_engine.schemas import DevTask
from app.features.sandbox.interfaces import SandboxProvider
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState


def make_develop_node(engine: DeveloperEngine, sandboxes: SandboxProvider) -> BuildNode:
    async def develop(state: BuildState) -> dict[str, Any]:
        sandbox = (
            await sandboxes.attach(state["sandbox_id"])
            if state.get("sandbox_id")
            else await sandboxes.create()
        )
        task = DevTask(
            description=f"{state['request']}\n\nPlan from the tech lead:\n{state.get('plan', '')}",
            test_command=state["test_command"],
        )
        result = await engine.run_task(task, sandbox)
        return {"sandbox_id": sandbox.id, "dev_result": result.model_dump()}

    return develop
