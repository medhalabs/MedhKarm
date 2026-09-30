"""QA node: re-runs the tests itself. The developer's own report is never trusted as proof."""

from typing import Any

from app.features.sandbox.interfaces import SandboxProvider
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState


def make_verify_node(
    sandboxes: SandboxProvider,
) -> BuildNode:
    async def verify(state: BuildState) -> dict[str, Any]:
        sandbox = await sandboxes.attach(state["sandbox_id"])
        result = await sandbox.run(state["test_command"])
        return {"verified": result.ok, "verify_output": result.output[-4000:]}

    return verify
