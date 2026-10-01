"""Second node: gets to know the project before anyone plans or changes it. Clones the
founder's repository when the run has one, maps the code (files, languages, outline, how to
install and test) and installs its dependencies. Safe to repeat after a crash."""

from typing import Any

from app.features.repos.schemas import RepoSource
from app.features.repos.service import RepoService
from app.features.sandbox.interfaces import SandboxProvider
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState

DEFAULT_TEST_COMMAND = "python -m pytest -q"


def make_connect_node(sandboxes: SandboxProvider, repos: RepoService) -> BuildNode:
    async def connect(state: BuildState) -> dict[str, Any]:
        sandbox = await sandboxes.attach(state["sandbox_id"])
        source = RepoSource.model_validate(state["repo"]) if state.get("repo") else None
        checkout = await repos.checkout(sandbox, source)
        brief = checkout.map.brief()
        if not checkout.setup_ok:
            brief += (
                f"\n\nInstalling dependencies ({checkout.map.setup_command}) failed:\n"
                + checkout.setup_output[-800:]
            )
        update: dict[str, Any] = {
            "codebase_map": brief,
            "repo_commit": checkout.commit,
            "setup_ok": checkout.setup_ok,
        }
        if not state.get("test_command"):
            update["test_command"] = checkout.map.test_command or DEFAULT_TEST_COMMAND
        return update

    return connect
