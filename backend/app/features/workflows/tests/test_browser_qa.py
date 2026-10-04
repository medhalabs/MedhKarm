"""QA's browser test step: only for web changes; a failure goes to the frontend developer once;
what still fails stops the release."""

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.developer_engine.schemas import DevResult, DevTask
from app.features.events.service import RunRecorder
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.sandbox.interfaces import Sandbox
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.sandbox.schemas import CommandResult
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.nodes.browser_qa import E2E_COMMAND, needs_browser_test
from app.features.workflows.schemas import RunOutcome
from app.features.workflows.service import WorkflowService

TEST = "tests/e2e/test_page.py"


def tool(name: str, **arguments: Any) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


def build(path: str, *more: LLMResponse) -> list[LLMResponse]:
    return [
        tool("submit_plan", summary="s", developers=1, tasks=[{"title": "Page"}]),
        tool("write_file", path=path, content="<form><label>x</label></form>"),
        tool("finish", summary="done"),
        tool("submit_review", decision="approve", feedback=""),
        *more,
    ]


class FakeQA:
    """Writes the browser test once, like Tara would; `summary` lets it report an app bug."""

    def __init__(self, summary: str = "Wrote a browser test") -> None:
        self.summary = summary
        self.briefs: list[str] = []

    async def run_task(
        self, task: DevTask, sandbox: Sandbox, recorder: RunRecorder | None = None
    ) -> DevResult:
        self.briefs.append(task.description)
        await sandbox.write_file(TEST, "def test_page(page): ...")
        return DevResult(success=True, summary=self.summary, files_changed=[TEST])


def e2e_results(*codes: int) -> Any:
    """Answers the browser test command with the given exit codes in turn; anything else passes."""
    left = list(codes)

    def shell(command: str, files: dict[str, str]) -> CommandResult:
        if command.startswith(E2E_COMMAND):
            code = left.pop(0) if left else 0
            return CommandResult(exit_code=code, output="1 failed: no result shown")
        return CommandResult(exit_code=0, output="ok")

    return shell


async def run(
    script: list[LLMResponse], qa: FakeQA | None, *codes: int
) -> tuple[RunOutcome, InMemoryEventStore]:
    llm, events = ScriptedLLMProvider(script), InMemoryEventStore()
    graph = build_app_graph(
        llm,
        ToolLoopEngine(llm),
        InMemorySandboxProvider(e2e_results(*codes)),
        InMemorySaver(),
        events=events,
        developer_names=["Isha", "Arjun"],
        max_developers=2,
        specialties={"Isha": "backend", "Arjun": "frontend"},
        browser_tester=qa,
        qa_name="Tara",
    )
    return await WorkflowService(graph, events).start("r", "Build a page", "pytest"), events


def test_only_web_changes_need_a_browser_test() -> None:
    assert needs_browser_test(["static/index.html"])
    assert needs_browser_test(["src/App.tsx"])
    assert needs_browser_test(["app/templates/home.jinja"])
    assert not needs_browser_test(["app.py", "test_app.py", "README.md"])


async def test_backend_only_changes_skip_it() -> None:
    qa = FakeQA()
    outcome, _ = await run(build("app.py"), qa)

    assert outcome.waiting_for_approval and qa.briefs == []
    assert outcome.gate is not None and outcome.gate["browser_test"] == ""


async def test_a_passing_browser_test_reaches_the_gate_and_ships() -> None:
    qa = FakeQA()
    outcome, events = await run(build("static/index.html"), qa, 0)

    assert outcome.waiting_for_approval
    assert outcome.gate is not None and outcome.gate["browser_test"] == f"passed: {TEST}"
    assert "static/index.html" in qa.briefs[0]
    assert f"Browser test passed ({TEST})" in [e.summary for e in events.events]


async def test_a_failing_browser_test_goes_to_the_frontend_developer_once() -> None:
    fix = [
        tool("write_file", path="static/index.html", content="<form>fixed</form>"),
        tool("finish", summary="shows the result now"),
        tool("submit_review", decision="approve", feedback=""),
    ]
    qa = FakeQA()
    outcome, events = await run(build("static/index.html", *fix), qa, 1, 0)

    assert outcome.waiting_for_approval
    fix_task = outcome.state["tasks"][-1]
    assert (fix_task["id"], fix_task["owner"], fix_task["status"]) == ("ui1", "Arjun", "done")
    assert "no result shown" in fix_task["description"]
    assert len(qa.briefs) == 1  # the same test is re-run, not rewritten
    summaries = [e.summary for e in events.events if e.actor == "qa"]
    assert "Browser test failed: sent to Arjun to fix" in summaries
    assert summaries[-1] == f"Browser test passed ({TEST})"


async def test_still_failing_stops_the_release() -> None:
    fix = [
        tool("write_file", path="static/index.html", content="<form>still broken</form>"),
        tool("finish", summary="tried"),
        tool("submit_review", decision="approve", feedback=""),
    ]
    outcome, _ = await run(build("static/index.html", *fix), FakeQA(), 1, 1)

    assert not outcome.waiting_for_approval
    assert outcome.state["status"] == "failed"


async def test_an_app_bug_reported_by_qa_is_sent_back_with_its_words() -> None:
    fix = [
        tool("write_file", path="static/index.html", content="<button>works</button>"),
        tool("finish", summary="fixed"),
        tool("submit_review", decision="approve", feedback=""),
    ]
    qa = FakeQA("APP BUG: the button does nothing")
    outcome, _ = await run(build("static/index.html", *fix), qa, 0, 0)

    first_fix = outcome.state["tasks"][-1]
    assert "APP BUG: the button does nothing" in first_fix["description"]
