"""Spotting work that fakes its tests instead of passing them.

A small model whose test tool is missing (or whose tests fail) may write its own `pytest.py`:
the test command then "passes" without running a single test. Seen live on 1 Oct 2026 with
gpt-oss:20b in a sandbox without pytest. The review and QA both refuse such work.
"""

import re
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


# Spotting requests for tests that got none. On an existing project the old tests still pass,
# so "tests pass" doesn't prove the new tests exist (live run on itsdangerous, 1 Oct 2026).
# Asking for new tests ("add tests", "with pytest tests"), not "the existing tests must pass".
ASKS_FOR_TESTS = re.compile(
    r"\b(add|adds|adding|write|writes|writing|with|include|includes|create|plus)\b"
    r"[^.!?\n]{0,40}?\b(tests?|test cases?|unit[- ]tests?)\b",
    re.I,
)


def asks_for_tests(request: str) -> bool:
    return bool(ASKS_FOR_TESTS.search(request))


def is_test_file(path: str) -> bool:
    """tests/…, test_x.py, x_test.py, x.test.ts, x.spec.js, __tests__/…"""
    parts = PurePosixPath(path).parts
    name = parts[-1].lower() if parts else ""
    folders = {p.lower() for p in parts[:-1]}
    return (
        bool(folders & {"test", "tests", "__tests__", "spec"})
        or name.startswith("test_")
        or PurePosixPath(name).stem.endswith(("_test", ".test", ".spec"))
    )


def missing_tests_feedback() -> str:
    return (
        "The request asks for tests, but no test file was added or changed. The existing "
        "tests passing doesn't cover the new work: write tests for it, run them, then finish."
    )
