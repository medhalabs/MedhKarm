"""Decides what the release gate will do, just before the gate: the founder's own settings
(for the run's project, else the company) turned into approval rules and evaluated against what
this run did. The verdict is saved in the run's state, so it can't change while the release
waits (a settings change made meanwhile must not override the founder's decision), and the
gate and the finish step read it from there."""

from typing import Any

from app.features.approvals.schemas import ApprovalPolicy
from app.features.approvals.service import evaluate
from app.features.workflows.interfaces import RunAutonomies
from app.features.workflows.nodes.approval import approval_facts
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState


def make_autonomy_node(
    policy: ApprovalPolicy | None = None, autonomies: RunAutonomies | None = None
) -> BuildNode:
    """`policy`: the team template's rules, used when the founder set nothing."""
    base = policy or ApprovalPolicy()

    async def autonomy(state: BuildState) -> dict[str, Any]:
        rules, go_live = base, True
        found = (
            await autonomies.for_run(state["run_id"])
            if autonomies and state.get("run_id")
            else None
        )
        if found is not None:
            rules, go_live = found.policy, found.go_live
        verdict = evaluate(rules, approval_facts(state))
        return {"verdict": verdict.model_dump(mode="json"), "go_live": go_live}

    return autonomy
