"""QA node: checks the work itself. The developer's own report is never trusted as proof."""

from typing import Any

from app.features.sandbox.interfaces import SandboxProvider
from app.features.workflows.interfaces import WorkChecker
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState


def make_verify_node(sandboxes: SandboxProvider, checker: WorkChecker) -> BuildNode:
    async def verify(state: BuildState) -> dict[str, Any]:
        sandbox = await sandboxes.attach(state["sandbox_id"])
        result = await checker.check(state, sandbox)
        return {"verified": result.passed, "verify_output": result.output}

    return verify
