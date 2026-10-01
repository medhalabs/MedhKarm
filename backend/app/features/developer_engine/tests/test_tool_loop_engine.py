import json

from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
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
