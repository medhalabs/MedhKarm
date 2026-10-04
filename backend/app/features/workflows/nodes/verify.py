"""QA node: checks the work itself. The developer's own report is never trusted as proof.
A run that changed no files fails: on an existing project the old tests pass untouched. So
does a run whose request asks for tests when no test file was added or changed.

Failed checks go back to a developer as one more task (once): the failing output is the task.
If they still fail after that, the release stops without asking the founder."""

from typing import Any

from app.features.sandbox.exceptions import SandboxError
from app.features.sandbox.interfaces import Sandbox, SandboxProvider
from app.features.workflows.guards import (
    asks_for_tests,
    hollow_feedback,
    hollow_tests,
    is_test_file,
)
from app.features.workflows.interfaces import WorkChecker
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState

FIX_TITLE = "Make QA's checks pass"
NO_TESTS = "The request asks for tests, but no test file was added or changed."


def make_verify_node(
    sandboxes: SandboxProvider,
    checker: WorkChecker,
    developer_names: list[str] | None = None,
    max_fix_rounds: int = 1,
) -> BuildNode:
    owner = (developer_names or ["Developer"])[0]

    async def verify(state: BuildState) -> dict[str, Any]:
        changed = state.get("dev_result", {}).get("files_changed", [])
        if not changed:  # nothing to fix: the developers didn't get anywhere
            return {
                "verified": False,
                "verify_output": "No files were changed: nothing to release.",
            }
        update: dict[str, Any]
        sandbox = await sandboxes.attach(state["sandbox_id"])
        hollow = hollow_tests(await _read_tests(sandbox, changed))
        if asks_for_tests(state["request"]) and not any(is_test_file(f) for f in changed):
            update = {"verified": False, "verify_output": NO_TESTS, "checks": []}
        elif hollow:  # tests that check nothing make "tests pass" meaningless
            update = {"verified": False, "verify_output": hollow_feedback(hollow), "checks": []}
        else:
            result = await checker.check(state, sandbox)
            update = {
                "verified": result.passed,
                "verify_output": result.output,
                "checks": [c.model_dump(mode="json") for c in result.checks],
            }
        rounds = state.get("qa_rounds", 0)
        if not update["verified"] and rounds < max_fix_rounds:
            tasks = [dict(t) for t in state.get("tasks", [])]
            tasks.append(_fix_task(update, state.get("test_command", ""), owner, rounds + 1))
            update |= {"tasks": tasks, "current_task": len(tasks) - 1, "qa_rounds": rounds + 1}
        return update

    return verify


def after_verify(state: BuildState) -> str:
    """Back to a developer for a fix task, on to the browser test, or stop."""
    if state.get("current_task", 0) < len(state.get("tasks", [])):
        return "develop"
    return "browser_qa" if state.get("verified") else "finish"


def _fix_task(update: dict[str, Any], test_command: str, owner: str, round_: int) -> dict[str, Any]:
    failing = [c for c in update.get("checks", []) if _blocks(c)]
    commands = [c["command"] for c in failing] or [test_command]
    return {
        "id": f"qa{round_}",
        "title": FIX_TITLE,
        "description": (
            "QA re-ran the checks on your work and they fail:\n\n"
            + update["verify_output"][-2500:]
            + "\n\nFix the code so they pass. Run them yourself with: "
            + " ; ".join(f"`{c}`" for c in commands if c)
            + ". Never delete, skip or weaken tests or checks, or change their configuration, "
            "to make them pass."
        ),
        "owner": owner,
        "status": "todo",
        "attempts": 0,
        "feedback": "",
        "summary": "",
        "files_changed": [],
        "success": False,
    }


def _blocks(check: dict[str, Any]) -> bool:
    return not (check.get("passed") or check.get("skipped") or check.get("already_failing"))


async def _read_tests(sandbox: Sandbox, changed: list[str]) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in changed:
        if is_test_file(path):
            try:
                files[path] = await sandbox.read_file(path)
            except SandboxError:
                continue
    return files
