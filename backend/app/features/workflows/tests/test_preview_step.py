"""DevOps in the workflow: a preview before the gate, production only after approval."""

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from app.features.deploys.schemas import DeployFile, Deployment
from app.features.deploys.service import DeployService
from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.sandbox.schemas import CommandResult
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.service import WorkflowService


def tool(name: str, **arguments: Any) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


SCRIPT = [
    tool("submit_plan", summary="s", developers=1, tasks=[{"title": "Page"}]),
    tool("write_file", path="index.html", content="<h1>Tips</h1>"),
    tool("finish", summary="done"),
    tool("submit_review", decision="approve", feedback=""),
]


class FakeVercel:
    def __init__(self, preview_state: str = "READY") -> None:
        self.preview_state = preview_state
        self.calls: list[tuple[str, bool]] = []

    async def deploy(
        self, name: str, files: list[DeployFile], production: bool, framework: str | None
    ) -> Deployment:
        self.calls.append((name, production))
        state = "READY" if production else self.preview_state
        url = "https://tips.vercel.app" if production else "https://tips-abc.vercel.app"
        return Deployment(id="d", url=url, state=state, error="" if state == "READY" else "boom")


async def run(target: FakeVercel) -> tuple[WorkflowService, InMemoryEventStore]:
    llm, events = ScriptedLLMProvider(list(SCRIPT)), InMemoryEventStore()
    sandboxes = InMemorySandboxProvider(lambda c, f: CommandResult(exit_code=0, output="aGk="))
    graph = build_app_graph(
        llm,
        ToolLoopEngine(llm),
        sandboxes,
        InMemorySaver(),
        events=events,
        deploys=DeployService(target),
    )
    return WorkflowService(graph, events), events


async def test_preview_before_the_gate_and_production_after_approval() -> None:
    target = FakeVercel()
    service, events = await run(target)

    outcome = await service.start("r1", "A tip calculator page", "true")
    assert outcome.gate is not None
    assert outcome.gate["preview_url"] == "https://tips-abc.vercel.app"
    assert target.calls == [("medhkarm-r1", False)]

    done = await service.resume("r1", approved=True)

    assert target.calls[-1] == ("medhkarm-r1", True)
    assert done.state["deployment"]["url"] == "https://tips.vercel.app"
    summaries = [e.summary for e in events.events if e.actor == "devops"]
    assert summaries == [
        "Preview ready: https://tips-abc.vercel.app",
        "Live at https://tips.vercel.app",
    ]


async def test_nothing_goes_live_without_approval() -> None:
    target = FakeVercel()
    service, _ = await run(target)
    await service.start("r1", "A tip calculator page", "true")

    await service.resume("r1", approved=False)

    assert target.calls == [("medhkarm-r1", False)]


async def test_a_failed_preview_is_shown_at_the_gate() -> None:
    service, _ = await run(FakeVercel(preview_state="ERROR"))

    outcome = await service.start("r1", "A tip calculator page", "true")

    assert outcome.gate is not None
    assert (outcome.gate["preview_url"], outcome.gate["preview_error"]) == ("", "boom")
