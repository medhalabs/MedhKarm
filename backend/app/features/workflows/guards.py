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


# Spotting tests that check nothing: `assert True`, `expect(true).toBe(true)`, or test functions
# with no assertion at all. They make "tests pass" meaningless (live run, 4 Oct 2026: a developer
# added tests/test_dummy.py with `assert True`, and the review let it through).
CODE_SUFFIXES = (".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")
TRIVIAL = re.compile(
    r"\bassert\s+(True|1|not\s+False)\b|expect\(\s*(true|1)\s*\)\s*\.\s*to(Be|Equal)\(\s*(true|1)\s*\)",
    re.I,
)
PY_CHECK = re.compile(r"\bassert\b|pytest\.raises|self\.assert\w+\(|\bexpect\(")
JS_CHECK = re.compile(r"\bexpect\(|\bassert[.(\s]|\.should\b")
PY_TEST = re.compile(r"^\s*(async\s+)?def\s+test", re.M)
JS_TEST = re.compile(r"\b(it|test)\s*\(")
COMMENT = re.compile(r"#.*$|//.*$", re.M)


def hollow_tests(files: dict[str, str]) -> list[str]:
    """Test files (path -> text) that define tests but check nothing real."""
    hollow = []
    for path, text in files.items():
        if not (is_test_file(path) and path.endswith(CODE_SUFFIXES)):
            continue
        python = path.endswith(".py")
        if not (PY_TEST if python else JS_TEST).search(text):
            continue  # helpers, fixtures, conftest: no tests to judge
        code = TRIVIAL.sub("", COMMENT.sub("", text))
        if not (PY_CHECK if python else JS_CHECK).search(code):
            hollow.append(path)
    return hollow


def hollow_feedback(paths: list[str]) -> str:
    return (
        f"These tests check nothing real: {', '.join(paths)}. `assert True` or a test with no "
        "assertion passes whatever the code does. Write tests that call the code and check its "
        "results (e.g. `assert add(2, 3) == 5`), run them, then finish."
    )
