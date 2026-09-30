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
    assert sandbox.commands[-1] == "pytest -q"


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
