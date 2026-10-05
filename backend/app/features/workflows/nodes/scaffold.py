"""Sets up a new project before anyone plans: decides the stack (the founder's choices, then
the request's words, then our defaults) and, for an app, puts our tested starter and the
modules it needs (sign-in, payments, reminders, admin dashboard) in the workspace and installs
them. Runs on founders' repositories, or a workspace that isn't empty, are left alone.
Safe to repeat after a crash: a workspace this step started filling (it has our AGENTS.md)
is written and installed again; any other non-empty workspace (evals' seeded projects) isn't."""

from typing import Any

from app.features.sandbox.interfaces import SandboxProvider
from app.features.starters.schemas import StackChoice
from app.features.starters.service import StarterService
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState

OUR_MARKERS = {"AGENTS.md", "web/AGENTS.md"}


def make_scaffold_node(sandboxes: SandboxProvider, starters: StarterService | None) -> BuildNode:
    async def scaffold(state: BuildState) -> dict[str, Any]:
        if starters is None or state.get("repo") or "stack_choice" not in state:
            return {}
        choice = StackChoice.model_validate(state["stack_choice"])
        if choice.starter is False and choice.empty:  # starter off, nothing chosen: not our call
            return {}
        stack = starters.resolve(state["request"], choice)
        update: dict[str, Any] = {
            "stack": stack.model_dump(mode="json"),
            "stack_brief": stack.brief(),
        }
        sandbox = await sandboxes.attach(state["sandbox_id"])
        existing = set(await sandbox.list_files())
        if stack.starter is None or (existing and not existing & OUR_MARKERS):
            return update
        result = await starters.scaffold(sandbox, stack)
        if result is None:
            return update
        update["scaffold"] = result.model_dump(mode="json")
        if not state.get("test_command"):
            update["test_command"] = result.test_command
        if not result.setup_ok:
            update["stack_brief"] += (
                f"\n\nInstalling the starter ({result.setup_command}) failed:\n"
                + result.setup_output[-800:]
            )
        return update

    return scaffold
