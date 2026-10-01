"""The words a team template may use. A template naming anything outside these is rejected.

Each name maps to a real implementation chosen in `app/workers/wiring.py`.
"""

# Tools an agent can be given (the built-in developer engine implements all of them).
KNOWN_TOOLS = frozenset(
    {"read_file", "write_file", "list_files", "run_command", "apply_patch", "finish"}
)

# Workflows (graphs) a team can run, and the roles each one needs to be active.
WORKFLOW_ROLES: dict[str, frozenset[str]] = {
    "build_app": frozenset({"cto", "developer", "qa"}),
}

# How a team's work is checked before the founder sees it.
KNOWN_CHECKERS = frozenset({"test_command"})  # later: "human_review", "approval_rules"
