"""The build graph with fakes: no network, no Docker, in-memory checkpoints."""

from langgraph.checkpoint.memory import InMemorySaver

from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.sandbox.schemas import CommandResult
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.service import WorkflowService


def _call(name: str, **arguments: str) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


def _script(write_app: bool) -> list[LLMResponse]:
    plan = LLMResponse(content="1. Write app.py")
    work = [_call("write_file", path="app.py", content="x = 1")] if write_app else []
    return [plan, *work, _call("finish", summary="Done")]


def _tests_pass_if_app_exists(command: str, files: dict[str, str]) -> CommandResult:
    return CommandResult(exit_code=0 if "app.py" in files else 1, output="tests")


def _service(write_app: bool) -> tuple[WorkflowService, InMemorySandboxProvider]:
    llm = ScriptedLLMProvider(_script(write_app))
    sandboxes = InMemorySandboxProvider(_tests_pass_if_app_exists)
    graph = build_app_graph(llm, ToolLoopEngine(llm), sandboxes, InMemorySaver())
    return WorkflowService(graph), sandboxes


async def test_pauses_at_release_gate_then_releases_on_approval() -> None:
    service, sandboxes = _service(write_app=True)

    paused = await service.start("run-1", "Build app", "pytest")

    assert paused.waiting_for_approval
    assert paused.gate is not None and paused.gate["gate"] == "release"
    assert paused.state["verified"] is True
    assert len(sandboxes.sandboxes) == 1  # kept alive while waiting

    done = await service.resume("run-1", approved=True, feedback="ship it")

    assert not done.waiting_for_approval
    assert done.state["status"] == "released"
    assert done.state["feedback"] == "ship it"
    assert sandboxes.sandboxes == {}  # cleaned up


async def test_rejection_ends_as_rejected() -> None:
    service, _ = _service(write_app=True)
    await service.start("run-2", "Build app", "pytest")

    done = await service.resume("run-2", approved=False)

    assert done.state["status"] == "rejected"


async def test_failed_tests_skip_the_gate() -> None:
    service, _ = _service(write_app=False)

    done = await service.start("run-3", "Build app", "pytest")

    assert not done.waiting_for_approval
    assert done.state["status"] == "failed"


async def test_reports_each_step() -> None:
    service, _ = _service(write_app=True)
    seen: list[str] = []

    await service.start("run-4", "Build app", "pytest", on_step=lambda s: seen.append(s.node))

    assert seen == ["plan", "develop", "verify"]


async def test_activity_log_tells_the_story_of_a_run() -> None:
    store = InMemoryEventStore()
    llm = ScriptedLLMProvider(_script(write_app=True))
    sandboxes = InMemorySandboxProvider(_tests_pass_if_app_exists)
    graph = build_app_graph(llm, ToolLoopEngine(llm), sandboxes, InMemorySaver(), events=store)
    service = WorkflowService(graph, store)

    await service.start("run-9", "Build app", "pytest")
    await service.resume("run-9", approved=True)

    types = [e.type for e in store.events]
    assert types == [
        "run.started",
        "plan.created",
        "work.started",
        "model.used",
        "tool.used",
        "model.used",
        "work.finished",
        "check.finished",
        "approval.requested",
        "approval.decided",
        "run.finished",
    ]
    assert all(e.run_id == "run-9" for e in store.events)
    assert next(e for e in store.events if e.type == "tool.used").summary == "Wrote app.py"
    assert store.events[-1].summary == "Released"
