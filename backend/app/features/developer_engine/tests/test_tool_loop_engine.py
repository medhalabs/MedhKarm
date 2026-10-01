import json

from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.developer_engine.engines.tools import execute_tool, normalize_call
from app.features.developer_engine.schemas import DevTask
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.sandbox.schemas import CommandResult

TASK = DevTask(description="Create app.py", test_command="pytest -q")


def _call(name: str, **arguments: str) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


def _tests_pass_if_app_exists(command: str, files: dict[str, str]) -> CommandResult:
    return CommandResult(exit_code=0 if "app.py" in files else 1, output="ran tests")


async def test_writes_files_and_succeeds_when_our_test_run_passes() -> None:
    llm = ScriptedLLMProvider(
        [_call("write_file", path="app.py", content="x = 1"), _call("finish", summary="Done")]
    )
    sandbox = await InMemorySandboxProvider(_tests_pass_if_app_exists).create()

    result = await ToolLoopEngine(llm).run_task(TASK, sandbox)

    assert result.success
    assert result.summary == "Done"
    assert result.files_changed == ["app.py"]
    assert result.steps == 2
    assert "pytest -q" in sandbox.commands


async def test_fails_when_tests_fail_even_if_model_claims_success() -> None:
    llm = ScriptedLLMProvider([_call("finish", summary="All good, trust me")])
    sandbox = await InMemorySandboxProvider(_tests_pass_if_app_exists).create()

    result = await ToolLoopEngine(llm).run_task(TASK, sandbox)

    assert not result.success


async def test_stops_at_step_limit() -> None:
    llm = ScriptedLLMProvider([_call("list_files") for _ in range(3)])
    sandbox = await InMemorySandboxProvider().create()

    result = await ToolLoopEngine(llm, max_steps=3).run_task(TASK, sandbox)

    assert result.steps == 3
    assert "step limit" in result.summary


async def test_tool_errors_go_back_to_the_model_instead_of_crashing() -> None:
    llm = ScriptedLLMProvider(
        [_call("read_file", path="missing.py"), _call("finish", summary="Gave up")]
    )
    sandbox = await InMemorySandboxProvider().create()

    await ToolLoopEngine(llm).run_task(TASK, sandbox)

    tool_reply = llm.calls[1][-1]
    assert tool_reply["role"] == "tool"
    assert "Could not read missing.py" in tool_reply["content"]


async def test_applied_patches_are_compacted_in_the_conversation() -> None:
    patch = "*** Begin Patch\n*** Add File: app.py\n+x = 1\n*** End Patch"
    llm = ScriptedLLMProvider(
        [
            LLMResponse(
                tool_calls=[ToolCall(id="p1", name="apply_patch", arguments={"input": patch})]
            ),
            _call("finish", summary="Done"),
        ]
    )
    sandbox = await InMemorySandboxProvider(_tests_pass_if_app_exists).create()

    result = await ToolLoopEngine(llm).run_task(TASK, sandbox)

    assert result.success
    sent_back = json.dumps(llm.calls[1])
    assert "*** Begin Patch" not in sent_back
    assert "patch already handled" in sent_back


async def test_apply_patch_is_offered_only_when_enabled() -> None:
    seen: list[list[str]] = []

    class Spy(ScriptedLLMProvider):
        async def complete(self, messages, tools=None):  # type: ignore[no-untyped-def]
            seen.append([t["function"]["name"] for t in tools or []])
            return await super().complete(messages, tools)

    sandbox = await InMemorySandboxProvider().create()
    await ToolLoopEngine(Spy([_call("finish", summary="x")])).run_task(TASK, sandbox)
    await ToolLoopEngine(
        Spy([_call("finish", summary="x")]), tools=["write_file", "apply_patch"]
    ).run_task(TASK, sandbox)

    assert "apply_patch" not in seen[0]
    assert "apply_patch" in seen[1]


async def test_long_files_are_read_in_numbered_parts() -> None:
    sandbox = await InMemorySandboxProvider().create()
    sandbox.files["big.py"] = "\n".join(f"line {n}" for n in range(1, 401))

    first = await execute_tool("read_file", {"path": "big.py"}, sandbox)
    part = await execute_tool(
        "read_file", {"path": "big.py", "start_line": 390, "end_line": 999}, sandbox
    )

    assert first.startswith("  1| line 1") and "150| line 150" in first
    assert first.endswith("(lines 1-150 of 400. Next: read_file with start_line=151.)")
    assert part.startswith("390| line 390") and part.endswith("(lines 390-400 of 400.)")
    assert await execute_tool("read_file", {"path": "big.py", "start_line": 500}, sandbox) == (
        "big.py has only 400 lines."
    )


async def test_search_runs_grep_and_caps_matches() -> None:
    hits = "\n".join(f"./src/a.py:{n}:def f{n}():" for n in range(100))
    sandbox = await InMemorySandboxProvider(
        lambda command, files: CommandResult(exit_code=0, output=hits)
    ).create()

    result = await execute_tool("search", {"pattern": "def f"}, sandbox)

    assert "grep -rnIE" in sandbox.commands[0] and "'def f'" in sandbox.commands[0]
    assert result.startswith("src/a.py:0:def f0():")
    assert result.endswith("(more matches: narrow the pattern or path)")


async def test_existing_projects_get_more_steps_and_a_nudge_to_write() -> None:
    reads = [_call("list_files") for _ in range(12)]
    llm = ScriptedLLMProvider(reads)
    sandbox = await InMemorySandboxProvider().create()
    engine = ToolLoopEngine(llm, max_steps=5, existing_project_max_steps=12)

    result = await engine.run_task(
        DevTask(description="Add search", test_command="pytest", existing_project=True), sandbox
    )

    assert result.steps == 12
    nudges = [m for m in llm.calls[-1] if "steps left and no file is changed" in str(m)]
    assert len(nudges) == 1


async def test_new_projects_keep_the_normal_step_limit() -> None:
    llm = ScriptedLLMProvider([_call("list_files") for _ in range(5)])
    sandbox = await InMemorySandboxProvider().create()

    result = await ToolLoopEngine(llm, max_steps=5, existing_project_max_steps=12).run_task(
        TASK, sandbox
    )

    assert result.steps == 5


async def test_edit_file_replaces_one_exact_match() -> None:
    sandbox = await InMemorySandboxProvider().create()
    sandbox.files["app.py"] = "def a():\n    return 1\n\ndef b():\n    return 1\n"

    missing = await execute_tool(
        "edit_file", {"path": "app.py", "old_text": "return 2", "new_text": "x"}, sandbox
    )
    twice = await execute_tool(
        "edit_file", {"path": "app.py", "old_text": "return 1", "new_text": "x"}, sandbox
    )
    done = await execute_tool(
        "edit_file",
        {
            "path": "app.py",
            "old_text": "def b():\n    return 1",
            "new_text": "def b():\n    return 2",
        },
        sandbox,
    )

    assert missing.startswith("old_text not found") and twice.startswith("old_text appears 2")
    assert done == "Edited app.py"
    assert sandbox.files["app.py"] == "def a():\n    return 1\n\ndef b():\n    return 2\n"


async def test_write_file_refuses_to_replace_a_module_with_a_fragment() -> None:
    sandbox = await InMemorySandboxProvider().create()
    module = "\n".join(f"x{n} = {n}" for n in range(100))
    sandbox.files["serializer.py"] = module

    refused = await execute_tool(
        "write_file", {"path": "serializer.py", "content": "    def loads(self): ..."}, sandbox
    )
    replaced = await execute_tool(
        "write_file", {"path": "serializer.py", "content": module + "\ny = 1"}, sandbox
    )

    assert refused.startswith("Not written: serializer.py has 100 lines") and "edit_file" in refused
    assert replaced == "Wrote serializer.py" and sandbox.files["serializer.py"].endswith("y = 1")


def test_other_argument_names_are_understood() -> None:
    call = ToolCall(id="1", name="write_file", arguments={"file_path": "a.py", "contents": "x"})
    assert normalize_call(call).arguments == {"path": "a.py", "content": "x"}


async def test_explain_symbol_without_graphify_points_to_search() -> None:
    sandbox = await InMemorySandboxProvider(
        lambda command, files: CommandResult(exit_code=3, output="")
    ).create()
    result = await execute_tool("explain_symbol", {"name": "Serializer"}, sandbox)
    assert result.startswith("explain_symbol isn't available")


async def test_explain_symbol_explains_each_match_of_an_ambiguous_name() -> None:
    def graphify(command: str, files: dict[str, str]) -> CommandResult:
        if "graphify explain loads " in command:
            return CommandResult(
                exit_code=0,
                output="Ambiguous: 'loads' matches 2 nodes\n  a.py\n    id: a_loads\n"
                "  b.py\n    id: b_loads\n",
            )
        if "graphify explain a_loads" in command:
            return CommandResult(exit_code=0, output="Node: loads (a.py L3)")
        if "graphify explain b_loads" in command:
            return CommandResult(exit_code=0, output="Node: loads (b.py L9)")
        return CommandResult(exit_code=0, output="")

    sandbox = await InMemorySandboxProvider(graphify).create()

    result = await execute_tool("explain_symbol", {"name": "loads"}, sandbox)

    assert result == "Node: loads (a.py L3)\n\nNode: loads (b.py L9)"
    assert "graphify extract . --code-only" in sandbox.commands[0]  # rebuilt with the changes
