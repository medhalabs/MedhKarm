"""First node: creates the run's sandbox, so its id is saved in a checkpoint before any work.
A retry, or another worker taking over, then re-attaches to it instead of leaking a new one."""

from typing import Any

from app.features.sandbox.interfaces import SandboxProvider
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState


def make_prepare_node(sandboxes: SandboxProvider) -> BuildNode:
    async def prepare(state: BuildState) -> dict[str, Any]:
        if state.get("sandbox_id"):  # given a prepared sandbox (evals)
            return {}
        return {"sandbox_id": (await sandboxes.create()).id}

    return prepare
