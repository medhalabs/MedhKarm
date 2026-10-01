"""Release gate. The team's approval rules decide what happens here: pause for the founder
(the default), or approve or stop on their own, saying which rule decided and why.

`interrupt()` saves the run in its checkpoint and stops. The run resumes — possibly in a
different worker process, hours later — when it is invoked again with `Command(resume=...)`.
"""

from typing import Any

from langgraph.types import interrupt

from app.features.approvals.schemas import Action, ApprovalPolicy
from app.features.approvals.service import evaluate
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState


def approval_facts(state: BuildState) -> dict[str, Any]:
    """What approval rules can look at. Keep in sync with WORKFLOW_FACTS["build_app"]."""
    dev = state.get("dev_result", {})
    tasks = state.get("tasks", [])
    files = list(dev.get("files_changed", []))
    return {
        "files_changed": files,
        "files_count": len(files),
        "tokens": int(dev.get("total_tokens", 0)) + int(state.get("cto_tokens_total", 0)),
        "tasks_count": len(tasks),
        "tasks_with_issues": sum(t.get("status") == "done_with_issues" for t in tasks),
        "tests_passed": bool(state.get("verified")),
    }


def make_approval_node(policy: ApprovalPolicy | None = None) -> BuildNode:
    rules = policy or ApprovalPolicy()

    async def approval(state: BuildState) -> dict[str, Any]:
        facts = approval_facts(state)
        verdict = evaluate(rules, facts)
        if verdict.action != Action.ASK:
            return {
                "approved": verdict.action == Action.APPROVE,
                "feedback": " ".join(verdict.reasons),
                "approval": {**verdict.model_dump(mode="json"), "decided_by": "rules"},
            }

        dev = state.get("dev_result", {})
        decision = interrupt(
            {
                "gate": "release",
                "question": "Approve this build for release?",
                "reasons": verdict.reasons,  # why the founder is asked
                "rules": verdict.rule_ids,  # empty = every release is asked by default
                "summary": dev.get("summary", ""),
                "files_changed": dev.get("files_changed", []),
                "tokens": facts["tokens"],
                "tests": state.get("verify_output", ""),
            }
        )
        if isinstance(decision, dict):
            approved = bool(decision.get("approved"))
            feedback = str(decision.get("feedback", ""))
        else:
            approved, feedback = bool(decision), ""
        return {
            "approved": approved,
            "feedback": feedback,
            "approval": {**verdict.model_dump(mode="json"), "decided_by": "founder"},
        }

    return approval
