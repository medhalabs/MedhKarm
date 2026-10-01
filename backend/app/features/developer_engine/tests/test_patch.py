import pytest

from app.features.developer_engine.engines.patch import (
    PatchError,
    apply_hunks,
    extract_patch,
    parse_patch,
)
from app.features.developer_engine.engines.tools import execute_tool, normalize_call
from app.features.models.schemas import ToolCall
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider

ORIGINAL = "def add(a, b):\n    return a - b\n\n\ndef sub(a, b):\n    return a - b\n"


def test_parse_add_update_delete_move() -> None:
    ops = parse_patch(
        "*** Begin Patch\n"
        "*** Add File: new.py\n+x = 1\n+y = 2\n"
        "*** Update File: calc.py\n*** Move to: maths.py\n@@ def add(a, b):\n"
        "-    return a - b\n+    return a + b\n"
        "*** Delete File: old.py\n"
        "*** End Patch"
    )

    assert [(op.kind, op.path) for op in ops] == [
        ("add", "new.py"),
        ("update", "calc.py"),
        ("delete", "old.py"),
    ]
    assert ops[0].content == "x = 1\ny = 2\n"
    assert ops[1].move_to == "maths.py"
    assert ops[1].hunks[0].anchor == "def add(a, b):"


def test_anchor_picks_the_right_occurrence() -> None:
    [op] = parse_patch(
        "*** Begin Patch\n*** Update File: calc.py\n@@ def add(a, b):\n"
        "-    return a - b\n+    return a + b\n*** End Patch"
    )

    result = apply_hunks(ORIGINAL, op.hunks, "calc.py")

    assert result == "def add(a, b):\n    return a + b\n\n\ndef sub(a, b):\n    return a - b\n"


def test_context_lines_must_match() -> None:
    [op] = parse_patch(
        "*** Begin Patch\n*** Update File: calc.py\n def nope():\n-    pass\n*** End Patch"
    )

    with pytest.raises(PatchError, match="doesn't match"):
        apply_hunks(ORIGINAL, op.hunks, "calc.py")


def test_trailing_whitespace_is_tolerated_and_insertion_appends() -> None:
    [op] = parse_patch(
        "*** Begin Patch\n*** Update File: a.py\n-x = 1   \n+x = 2\n@@\n+z = 3\n*** End Patch"
    )

    assert apply_hunks("x = 1\ny = 1\n", op.hunks, "a.py") == "x = 2\ny = 1\nz = 3\n"


def test_extract_strips_shell_wrapper_and_rejects_garbage() -> None:
    text = "apply_patch <<'PATCH'\n*** Begin Patch\n*** Delete File: a.py\n*** End Patch\nPATCH"
    assert extract_patch(text) == "*** Begin Patch\n*** Delete File: a.py\n*** End Patch"
    with pytest.raises(PatchError):
        extract_patch("just some text")


def test_shell_patches_become_apply_patch_calls() -> None:
    call = ToolCall(
        id="c1",
        name="run_command",
        arguments={
            "command": "apply_patch <<'P'\n*** Begin Patch\n*** Delete File: a.py\n*** End Patch\nP"
        },
    )

    fixed = normalize_call(call)

    assert fixed.name == "apply_patch"
    assert fixed.arguments["input"].startswith("*** Begin Patch")
    assert (
        normalize_call(ToolCall(id="c2", name="run_command", arguments={"command": "ls"})).name
        == "run_command"
    )


async def test_apply_patch_tool_end_to_end() -> None:
    sandbox = await InMemorySandboxProvider().create()
    await sandbox.write_file("calc.py", ORIGINAL)
    await sandbox.write_file("old.py", "bye")
    patch = (
        "*** Begin Patch\n"
        "*** Update File: calc.py\n@@ def add(a, b):\n-    return a - b\n+    return a + b\n"
        "*** Add File: test_calc.py\n+from calc import add\n"
        "*** Delete File: old.py\n"
        "*** End Patch"
    )

    message = await execute_tool("apply_patch", {"input": patch}, sandbox)

    assert message.startswith("Patch applied")
    assert "return a + b" in await sandbox.read_file("calc.py")
    assert await sandbox.read_file("test_calc.py") == "from calc import add\n"
    assert any(cmd == "rm -f old.py" for cmd in sandbox.commands)


async def test_bad_patch_returns_message_to_model() -> None:
    sandbox = await InMemorySandboxProvider().create()
    await sandbox.write_file("calc.py", ORIGINAL)

    message = await execute_tool(
        "apply_patch",
        {"input": "*** Begin Patch\n*** Update File: calc.py\n-nothing\n*** End Patch"},
        sandbox,
    )

    assert message.startswith("Patch not applied")


def test_patch_argument_alias_is_normalised() -> None:
    call = ToolCall(
        id="c1", name="apply_patch", arguments={"patch": "*** Begin Patch\n*** End Patch"}
    )

    assert normalize_call(call).arguments == {"input": "*** Begin Patch\n*** End Patch"}


def test_repeated_and_joined_markers_are_tolerated() -> None:
    text = (
        "*** Begin Patch\n*** Update File: a.py\n-x = 1\n+x = 2\n*** End Patch\n*** End Patch\n"
        "*** Begin Patch\n*** Add File: b.py\n+y = 1\n*** End Patch"
    )

    ops = parse_patch(text)

    assert [(op.kind, op.path) for op in ops] == [("update", "a.py"), ("add", "b.py")]
    assert apply_hunks("x = 1\n", ops[0].hunks, "a.py") == "x = 2\n"
