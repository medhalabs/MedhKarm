"""Final node: hands released work to GitHub (a pull request on the founder's repository, or
a new private repository for a new project), records the outcome and removes the sandbox."""

from typing import Any

from app.features.repos.schemas import RepoSource
from app.features.repos.service import RepoService
from app.features.sandbox.interfaces import SandboxProvider
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState


def make_finish_node(sandboxes: SandboxProvider, repos: RepoService | None = None) -> BuildNode:
    async def finish(state: BuildState) -> dict[str, Any]:
        if not state.get("verified"):
            status = "failed"
        else:
            status = "released" if state.get("approved") else "rejected"
        update: dict[str, Any] = {"status": status}
        if status == "released" and state.get("repo") and repos and state.get("sandbox_id"):
            # Before the sandbox goes: if delivery fails, a retry still has the work.
            delivery = await repos.deliver(
                await sandboxes.attach(state["sandbox_id"]),
                RepoSource.model_validate(state["repo"]),
                state.get("run_id", "run"),
                state["request"],
                state.get("dev_result", {}).get("summary", ""),
            )
            update["delivery"] = delivery.model_dump(mode="json")
        elif status == "released" and state.get("new_repo") is not None and repos:
            new_repo = state.get("new_repo") or {}
            delivery = await repos.publish(
                await sandboxes.attach(state["sandbox_id"]),
                state.get("run_id", "run"),
                state["request"],
                new_repo.get("name"),
            )
            update["delivery"] = delivery.model_dump(mode="json")
        if state.get("sandbox_id"):
            await sandboxes.destroy(state["sandbox_id"])
        return update

    return finish
