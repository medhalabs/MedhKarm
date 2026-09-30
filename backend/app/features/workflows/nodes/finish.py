"""Final node: records the outcome and removes the sandbox."""

from typing import Any

from app.features.sandbox.interfaces import SandboxProvider
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState


def make_finish_node(
    sandboxes: SandboxProvider,
) -> BuildNode:
    async def finish(state: BuildState) -> dict[str, Any]:
        if state.get("sandbox_id"):
            await sandboxes.destroy(state["sandbox_id"])
        if not state.get("verified"):
            return {"status": "failed"}
        return {"status": "released" if state.get("approved") else "rejected"}

    return finish
