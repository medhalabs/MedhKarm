"""CTO review node: approves the current task or sends it back with specific changes.

Failing tests, and work that replaces the test tool (see guards.py), are sent back without
asking the model (cheaper, and never wrong). Each task
gets at most `max_revisions` rounds of changes; after that the run moves on and QA's final
check decides.
"""

from typing import Any

from app.features.models.interfaces import LLMProvider
from app.features.sandbox.exceptions import SandboxError
from app.features.sandbox.interfaces import Sandbox, SandboxProvider
from app.features.workflows.cto import REVIEW_TOOL, ReviewDecision, parse_review
from app.features.workflows.guards import (
    asks_for_tests,
    hollow_feedback,
    hollow_tests,
    is_test_file,
    missing_tests_feedback,
    shadow_feedback,
    shadowed_test_tools,
)
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState

REVIEW_PROMPT = """You are the CTO reviewing a developer's task. Approve it if it does what
the task asked, with tests, in a small and clear way. Otherwise send it back with specific,
short changes. Don't ask for extras the task didn't ask for. Answer with submit_review."""

MAX_FILE_CHARS = 1500


def make_review_node(
    llm: LLMProvider,
    sandboxes: SandboxProvider,
    instructions: str = REVIEW_PROMPT,
    max_revisions: int = 1,
) -> BuildNode:
    async def review(state: BuildState) -> dict[str, Any]:
        tasks = [dict(t) for t in state.get("tasks", [])]
        if not tasks:  # nothing planned (old checkpoint): nothing to review
            return {"current_task": 1}
        index = min(state.get("current_task", 0), len(tasks) - 1)
        task = tasks[index]

        cto_tokens = 0
        shadows = shadowed_test_tools(task.get("files_changed", []))
        hollow = (
            hollow_tests(await _test_files(await sandboxes.attach(state["sandbox_id"]), task))
            if not shadows and task.get("files_changed")
            else []
        )
        if shadows:
            verdict = ReviewDecision(decision="revise", feedback=shadow_feedback(shadows))
        elif hollow:
            verdict = ReviewDecision(decision="revise", feedback=hollow_feedback(hollow))
        elif not task.get("files_changed"):
            # An existing project's tests pass untouched, so passing tests prove nothing here.
            verdict = ReviewDecision(
                decision="revise",
                feedback="You didn't change any files, so the task isn't done. Make the change "
                "it asks for (write the files), run the tests, then call finish.",
            )
        elif (
            index == len(tasks) - 1  # earlier tasks may leave the tests to a later one
            and asks_for_tests(state["request"])
            and not any(is_test_file(f) for t in tasks for f in t.get("files_changed", []))
        ):
            verdict = ReviewDecision(decision="revise", feedback=missing_tests_feedback())
        elif not task.get("success"):
            verdict = ReviewDecision(
                decision="revise",
                feedback="The tests don't pass yet. Fix them:\n"
                + task.get("test_output", "")[-800:],
            )
        else:
            sandbox = await sandboxes.attach(state["sandbox_id"])
            response = await llm.complete(
                [
                    {"role": "system", "content": instructions.strip()},
                    {"role": "user", "content": await _review_brief(task, sandbox)},
                ],
                [REVIEW_TOOL],
            )
            verdict = parse_review(response)
            cto_tokens = response.usage.total_tokens

        out_of_rounds = task.get("attempts", 0) > max_revisions
        if verdict.decision == "approve" or out_of_rounds:
            task.update(
                status="done" if verdict.decision == "approve" else "done_with_issues", feedback=""
            )
            next_index = index + 1
        else:
            task.update(status="revise", feedback=verdict.feedback)
            next_index = index
        return {
            "tasks": tasks,
            "current_task": next_index,
            "cto_tokens": cto_tokens,
            "cto_tokens_total": state.get("cto_tokens_total", 0) + cto_tokens,
            "own_key": bool(getattr(llm, "own_key", False)) if cto_tokens else False,
            "last_review": {
                "task_id": task["id"],
                "title": task["title"],
                "member": task["owner"],
                "decision": "approve" if task["status"].startswith("done") else "revise",
                "feedback": verdict.feedback,
                "accepted_with_issues": task["status"] == "done_with_issues",
            },
        }

    return review


async def _review_brief(task: dict[str, Any], sandbox: Sandbox) -> str:
    parts = [
        f"Task: {task['title']}\n{task.get('description', '')}",
        f"Developer: {task['owner']}. Their summary: {task.get('summary', '')}",
        "Tests: passed",
        "Changed files:",
    ]
    for path in task.get("files_changed", [])[:6]:
        try:
            content = await sandbox.read_file(path)
        except SandboxError:
            continue
        clipped = content[:MAX_FILE_CHARS] + (
            "\n... (cut)" if len(content) > MAX_FILE_CHARS else ""
        )
        parts.append(f"### {path}\n```\n{clipped}\n```")
    return "\n\n".join(parts)


def after_review(state: BuildState) -> str:
    """Back to the developer for the next (or revised) task, or on to QA when all are done."""
    return "develop" if state.get("current_task", 0) < len(state.get("tasks", [])) else "verify"


async def _test_files(sandbox: Sandbox, task: dict[str, Any]) -> dict[str, str]:
    """The task's changed test files, path -> text (unreadable ones skipped)."""
    files: dict[str, str] = {}
    for path in task.get("files_changed", []):
        if is_test_file(path):
            try:
                files[path] = await sandbox.read_file(path)
            except SandboxError:
                continue
    return files
