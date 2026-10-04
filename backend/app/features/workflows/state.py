from typing import Any, TypedDict


class BuildState(TypedDict, total=False):
    """Everything a build run knows. Saved in a checkpoint after every node: keep it JSON-like."""

    run_id: str  # the run's id, so nodes can record activity against it
    request: str  # what the founder asked for
    test_command: str  # shell command that decides "done" (detected from the repo if empty)
    repo: dict[str, Any]  # the founder's GitHub repository (RepoSource-shaped), if any
    new_repo: dict[str, Any]  # no repo: create one on release (NewRepo-shaped; absent = don't)
    repo_commit: str  # the commit the team started from
    codebase_map: str  # what the team learned about the project before changing it
    setup_ok: bool  # installing the project's dependencies worked
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
    checks: list[dict[str, Any]]  # QA's last checks, one per tool (CheckRun-shaped)
    checks_baseline: dict[str, bool]  # check name -> passed, before the team changed anything
    qa_rounds: int  # fix rounds QA's checks have asked for
    security: dict[str, Any]  # the security engineer's last report (SecurityReport-shaped)
    security_rounds: int  # fix rounds the security engineer has asked for
    security_passed: bool  # no blocking security findings remain
    browser: dict[str, Any]  # QA's browser test: needed, passed, test files, output, round
    browser_rounds: int  # fix rounds the browser test has asked for
    browser_passed: bool  # the browser test passes (or none was needed)
    preview: dict[str, Any]  # DevOps' preview before the gate (Deployment-shaped)
    deployment: dict[str, Any]  # the production deployment after approval (Deployment-shaped)
    approved: bool  # the founder's decision at the release gate
    feedback: str  # the founder's note at the gate, if any
    approval: dict[str, Any]  # the approval rules' verdict at the gate (Verdict-shaped)
    delivery: dict[str, Any]  # how released work went back to the repo (Delivery-shaped)
    status: str  # "released" | "rejected" | "failed"
