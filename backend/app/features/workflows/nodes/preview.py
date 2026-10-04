"""DevOps (Neel): before the founder's release gate, put the work online as a preview they can
try. Apps that can't run online (libraries, scripts) are skipped. A failed preview doesn't
stop the run: the founder sees why at the gate."""

from typing import Any

from app.features.deploys.service import DeployService
from app.features.sandbox.interfaces import SandboxProvider
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState


def deploy_name(state: BuildState) -> str:
    """The same name for every run of a project, so it keeps one URL."""
    new_repo = state.get("new_repo") or {}
    repo = state.get("repo") or {}
    if new_repo.get("name"):
        return str(new_repo["name"])
    if repo.get("url"):
        return str(repo["url"]).rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
    return f"medhkarm-{state.get('run_id', 'app')}"


def make_preview_node(sandboxes: SandboxProvider, deploys: DeployService | None) -> BuildNode:
    async def preview(state: BuildState) -> dict[str, Any]:
        if deploys is None:
            return {}
        sandbox = await sandboxes.attach(state["sandbox_id"])
        deployment = await deploys.deploy(sandbox, deploy_name(state), production=False)
        return {"preview": deployment.model_dump(mode="json")}

    return preview
