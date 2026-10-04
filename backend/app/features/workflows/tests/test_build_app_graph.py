"""The build graph with fakes: no network, no Docker, in-memory checkpoints."""

from langgraph.checkpoint.memory import InMemorySaver

from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, TokenUsage, ToolCall
from app.features.repos.service import RepoService
from app.features.repos.tests.fakes import FakeHost
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.sandbox.schemas import CommandResult
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.service import WorkflowService


def _call(name: str, **arguments: str) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


def _script(write_app: bool) -> list[LLMResponse]:
    """Plan (numbered text: one task) → developer → CTO review. Without app.py the tests fail,
    so the CTO sends it back once (no model call) and the developer tries again."""
    plan = LLMResponse(content="1. Write app.py", usage=TokenUsage(prompt_tokens=40))
    if not write_app:
        return [plan, _call("finish", summary="Done"), _call("finish", summary="Still done")]
    approve = _call("submit_review", decision="approve", feedback="")
    approve.usage = TokenUsage(prompt_tokens=30)
    return [
        plan,
        _call("write_file", path="app.py", content="x = 1"),
        _call("finish", summary="Done"),
        approve,
    ]


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

    assert seen == [
        "prepare",
        "connect",
        "plan",
        "develop",
        "review",
        "verify",
        "browser_qa",
        "security",
        "preview",
    ]


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
        "model.used",  # CTO plans
        "plan.created",
        "task.assigned",
        "work.started",
        "model.used",
        "tool.used",
        "model.used",
        "work.finished",
        "model.used",  # CTO reviews
        "review.finished",
        "check.finished",
        "approval.requested",
        "approval.decided",
        "run.finished",
    ]
    assert all(e.run_id == "run-9" for e in store.events)
    assert next(e for e in store.events if e.type == "tool.used").summary == "Wrote app.py"
    assert next(e for e in store.events if e.type == "task.assigned").data["member"] == "Developer"
    assert next(e for e in store.events if e.type == "review.finished").summary.startswith(
        "Approved"
    )
    assert sum(e.tokens for e in store.events if e.actor == "cto") == 70
    assert store.events[-1].summary == "Released"


async def test_repo_run_maps_the_project_then_opens_a_pull_request() -> None:
    store = InMemoryEventStore()
    llm = ScriptedLLMProvider(_script(write_app=True))
    host = FakeHost()
    sandboxes = InMemorySandboxProvider(_tests_pass_if_app_exists)
    graph = build_app_graph(
        llm, ToolLoopEngine(llm), sandboxes, InMemorySaver(), events=store, repos=RepoService(host)
    )
    service = WorkflowService(graph, store)
    repo = {"url": "https://github.com/medhalabs/notes", "branch": None}

    paused = await service.start("run-r", "Add search", "", repo=repo)

    assert host.clones == 1
    assert paused.state["test_command"] == "python -m pytest -q"  # detected from the repo
    assert "Existing project" in paused.state["codebase_map"]
    assert "Existing project" in str(llm.calls[0])  # the CTO planned with the map
    assert "About the project" in str(llm.calls[1])  # and the developer worked with it

    done = await service.resume("run-r", approved=True)

    assert done.state["delivery"]["pull_request_url"] == "u"
    assert host.delivered[0][0] == "medhkarm/run-r"
    types = [e.type for e in store.events]
    assert types[1] == "codebase.mapped"
    assert types[-2:] == ["changes.delivered", "run.finished"]


async def test_rejected_repo_run_opens_no_pull_request() -> None:
    llm = ScriptedLLMProvider(_script(write_app=True))
    host = FakeHost()
    sandboxes = InMemorySandboxProvider(_tests_pass_if_app_exists)
    graph = build_app_graph(
        llm, ToolLoopEngine(llm), sandboxes, InMemorySaver(), repos=RepoService(host)
    )
    service = WorkflowService(graph)
    await service.start("run-x", "Add search", "pytest", repo={"url": "https://github.com/a/b"})

    done = await service.resume("run-x", approved=False)

    assert done.state["status"] == "rejected" and host.delivered == []
    assert "delivery" not in done.state


async def test_work_that_changes_nothing_is_sent_back_and_never_reaches_the_gate() -> None:
    """On an existing project the old tests pass untouched: that must not count as done."""
    llm = ScriptedLLMProvider(
        [
            LLMResponse(content="1. Add search"),
            _call("finish", summary="Looked around"),
            _call("finish", summary="Still looking"),
        ]
    )
    sandboxes = InMemorySandboxProvider()  # every test command passes
    graph = build_app_graph(
        llm, ToolLoopEngine(llm), sandboxes, InMemorySaver(), repos=RepoService(FakeHost())
    )

    done = await WorkflowService(graph).start(
        "run-n", "Add search", "", repo={"url": "https://github.com/a/b"}
    )

    [task] = done.state["tasks"]
    assert task["attempts"] == 2  # sent back once without asking the CTO's model
    assert "didn't change any files" in done.state["last_review"]["feedback"]
    assert not done.waiting_for_approval
    assert done.state["status"] == "failed"
    assert done.state["verify_output"].startswith("No files were changed")


async def test_asked_for_tests_but_wrote_none_is_sent_back_and_fails() -> None:
    llm = ScriptedLLMProvider(
        [
            LLMResponse(content="1. Add peek"),
            _call("write_file", path="app.py", content="def peek(): ..."),
            _call("finish", summary="Added peek"),
            _call("finish", summary="Done, really"),
            # QA's fix round: still no test file
            _call("finish", summary="Fixed"),
            _call("finish", summary="Fixed, really"),
        ]
    )
    sandboxes = InMemorySandboxProvider(_tests_pass_if_app_exists)
    graph = build_app_graph(llm, ToolLoopEngine(llm), sandboxes, InMemorySaver())

    done = await WorkflowService(graph).start("run-t", "Add peek() with tests", "pytest")

    assert any("no test file" in str(call) for call in llm.calls)  # sent back, no CTO call
    assert not done.waiting_for_approval and done.state["status"] == "failed"
    assert done.state["verify_output"].startswith("The request asks for tests")
    assert [t["id"] for t in done.state["tasks"]][-1] == "qa1"  # one fix round, then stop


async def test_new_project_gets_a_new_repo_on_release_only() -> None:
    def run_with(approved: bool) -> tuple[WorkflowService, FakeHost]:
        llm = ScriptedLLMProvider(_script(write_app=True))
        host = FakeHost()
        sandboxes = InMemorySandboxProvider(_tests_pass_if_app_exists)
        graph = build_app_graph(
            llm, ToolLoopEngine(llm), sandboxes, InMemorySaver(), repos=RepoService(host)
        )
        return WorkflowService(graph), host

    service, host = run_with(approved=True)
    await service.start("run-new1", "Build app", "pytest", new_repo={"name": None})
    done = await service.resume("run-new1", approved=True)

    assert host.published == [("build-app-run-ne", "Build app")]
    assert done.state["delivery"]["repo_url"] == "https://github.com/me/build-app-run-ne"

    service, host = run_with(approved=False)
    await service.start("run-new2", "Build app", "pytest", new_repo={"name": "mine"})
    await service.resume("run-new2", approved=False)
    assert host.published == []

    service, host = run_with(approved=True)
    await service.start("run-new3", "Build app", "pytest")  # no new_repo: evals, opt-out
    assert "delivery" not in (await service.resume("run-new3", approved=True)).state
    assert host.published == []
