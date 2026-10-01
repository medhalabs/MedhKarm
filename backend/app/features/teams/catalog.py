"""The words a team template may use. A template naming anything outside these is rejected.

Each name maps to a real implementation chosen in `app/workers/wiring.py`.
"""

# Tools an agent can be given (the built-in developer engine implements all of them).
KNOWN_TOOLS = frozenset(
    {
        "read_file",
        "write_file",
        "edit_file",
        "list_files",
        "search",
        "explain_symbol",
        "run_command",
        "apply_patch",
        "finish",
    }
)

# Workflows (graphs) a team can run, and the roles each one needs to be active.
WORKFLOW_ROLES: dict[str, frozenset[str]] = {
    "build_app": frozenset({"cto", "developer", "qa"}),
}

# How a team's work is checked before the founder sees it.
KNOWN_CHECKERS = frozenset({"test_command"})  # later: "human_review", "approval_rules"

# Facts each workflow gives its approval rules at the release gate (see the workflow's
# `approval_facts()`; a test keeps the two in sync).
WORKFLOW_FACTS: dict[str, frozenset[str]] = {
    "build_app": frozenset(
        {
            "files_changed",  # list of paths
            "files_count",
            "tokens",  # all model tokens in the run so far (CTO and developers)
            "tasks_count",
            "tasks_with_issues",  # tasks accepted with review comments still open
            "tests_passed",
        }
    ),
}
