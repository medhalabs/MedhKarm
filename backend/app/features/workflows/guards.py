"""Spotting work that fakes its tests instead of passing them.

A small model whose test tool is missing (or whose tests fail) may write its own `pytest.py`:
the test command then "passes" without running a single test. Seen live on 1 Oct 2026 with
gpt-oss:20b in a sandbox without pytest. The review and QA both refuse such work.
"""

from pathlib import PurePosixPath

# Module names that, as a file or folder in the workspace, replace the real tool on import.
SHADOWED_MODULES = frozenset(
    {"pytest", "_pytest", "py", "unittest", "doctest", "sitecustomize", "usercustomize"}
)


def shadowed_test_tools(paths: list[str]) -> list[str]:
    """The paths that would replace a real test tool, e.g. `pytest.py` or `pytest/__init__.py`."""
    found = []
    for path in paths:
        parts = PurePosixPath(path).parts
        names = [PurePosixPath(p).stem if p.endswith(".py") else p for p in parts]
        if any(name in SHADOWED_MODULES for name in names):
            found.append(path)
    return found


def shadow_feedback(paths: list[str]) -> str:
    return (
        f"You created {', '.join(paths)}, which replaces the real test tool, so the test "
        "command passes without running your tests. Delete it and make the real tests pass. "
        "If a tool is missing from the workspace, say so in your summary instead."
    )
