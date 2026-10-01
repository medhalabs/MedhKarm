"""QA node: checks the work itself. The developer's own report is never trusted as proof.
A run that changed no files fails: on an existing project the old tests pass untouched. So
does a run whose request asks for tests when no test file was added or changed."""

from typing import Any

from app.features.sandbox.interfaces import SandboxProvider
from app.features.workflows.guards import asks_for_tests, is_test_file
from app.features.workflows.interfaces import WorkChecker
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState


def make_verify_node(sandboxes: SandboxProvider, checker: WorkChecker) -> BuildNode:
    async def verify(state: BuildState) -> dict[str, Any]:
        if not state.get("dev_result", {}).get("files_changed"):
            return {
                "verified": False,
                "verify_output": "No files were changed: nothing to release.",
            }
        changed = state.get("dev_result", {}).get("files_changed", [])
        if asks_for_tests(state["request"]) and not any(is_test_file(f) for f in changed):
            return {
                "verified": False,
                "verify_output": "The request asks for tests, but no test file was added "
                "or changed.",
            }
        sandbox = await sandboxes.attach(state["sandbox_id"])
        result = await checker.check(state, sandbox)
        return {"verified": result.passed, "verify_output": result.output}

    return verify
