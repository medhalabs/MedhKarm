from typing import Any, TypedDict


class BuildState(TypedDict, total=False):
    """Everything a build run knows. Saved in a checkpoint after every node: keep it JSON-like."""

    run_id: str  # the run's id, so nodes can record activity against it
    request: str  # what the founder asked for
    test_command: str  # shell command that decides "done"
    plan: str  # the planner's short plan
    sandbox_id: str  # lets any worker re-attach to the same sandbox
    dev_result: dict[str, Any]  # DevResult as a dict
    verified: bool  # our own re-run of the tests passed
    verify_output: str
    approved: bool  # the founder's decision at the release gate
    feedback: str  # the founder's note at the gate, if any
    status: str  # "released" | "rejected" | "failed"
