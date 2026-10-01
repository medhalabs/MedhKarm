"""Work that fakes its tests (a stand-in pytest.py, as seen live) is refused by review and QA."""

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.sandbox.schemas import CommandResult
from app.features.workflows.checkers.test_command import TestCommandChecker
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.guards import shadowed_test_tools
from app.features.workflows.service import WorkflowService


def tool(name: str, **arguments: Any) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


def test_spots_stand_ins_for_test_tools() -> None:
    assert shadowed_test_tools(
        ["pytest.py", "pytest/__init__.py", "tests/unittest.py", "lib/sitecustomize.py"]
    ) == ["pytest.py", "pytest/__init__.py", "tests/unittest.py", "lib/sitecustomize.py"]
    assert shadowed_test_tools(["calc.py", "test_calc.py", "conftest.py", "my_pytest.py"]) == []


async def test_qa_fails_a_workspace_with_a_fake_pytest() -> None:
    sandbox = await InMemorySandboxProvider().create()  # every command "passes"
    await sandbox.write_file("pytest.py", "import sys; sys.exit(0)")

    result = await TestCommandChecker().check({"test_command": "python -m pytest"}, sandbox)

    assert not result.passed
    assert "pytest.py" in result.output


async def test_review_sends_a_fake_pytest_back_without_asking_the_model() -> None:
    llm = ScriptedLLMProvider(
        [
            tool("submit_plan", summary="s", developers=1, tasks=[{"title": "calc"}]),
            tool("write_file", path="calc.py", content="1"),
            tool("write_file", path="pytest.py", content="import sys; sys.exit(0)"),
            tool("finish", summary="tests pass"),
            # no submit_review here: the guard decides
            tool("finish", summary="still the same"),
        ]
    )
    sandboxes = InMemorySandboxProvider(lambda c, f: CommandResult(exit_code=0, output="ok"))
    graph = build_app_graph(llm, ToolLoopEngine(llm), sandboxes, InMemorySaver())

    state = (await WorkflowService(graph).start("r", "Build calc", "python -m pytest")).state

    [task] = state["tasks"]
    assert task["attempts"] == 2
    assert "replaces the real test tool" in state["last_review"]["feedback"]
    assert state["verified"] is False  # QA refuses it too, so the founder is never asked
    assert state["status"] == "failed"
