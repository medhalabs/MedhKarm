from typing import Any, TypedDict


class BuildState(TypedDict, total=False):
    """Everything a build run knows. Saved in a checkpoint after every node: keep it JSON-like."""

    run_id: str  # the run's id, so nodes can record activity against it
    request: str  # what the founder asked for
    test_command: str  # shell command that decides "done"
    plan: str  # the CTO's plan, as text for people
    tasks: list[dict[str, Any]]  # the CTO's tasks: id, title, description, owner, status, ...
    current_task: int  # index of the task being worked on or reviewed
    last_review: dict[str, Any]  # the CTO's latest review verdict
    cto_tokens: int  # tokens the CTO's last model call used (recorded as model.used)
    cto_tokens_total: int  # all the CTO's tokens in this run (for approval rules)
    sandbox_id: str  # lets any worker re-attach to the same sandbox
    dev_result: dict[str, Any]  # all developer work so far, totalled (DevResult-shaped)
    verified: bool  # our own re-run of the tests passed
    verify_output: str
    approved: bool  # the founder's decision at the release gate
    feedback: str  # the founder's note at the gate, if any
    approval: dict[str, Any]  # the approval rules' verdict at the gate (Verdict-shaped)
    status: str  # "released" | "rejected" | "failed"
