"""QA's demo video: a passing browser test is run with video on, and its recording is kept for
the founder. A missing, oversized or broken video never fails the run."""

import base64
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from app.features.artifacts.memory_repository import InMemoryArtifactRepository
from app.features.artifacts.service import ArtifactService
from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.events.schemas import EventType
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.sandbox.schemas import CommandResult
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.nodes.browser_qa import E2E_COMMAND, MAX_VIDEO_BYTES
from app.features.workflows.schemas import RunOutcome
from app.features.workflows.service import WorkflowService
from app.features.workflows.tests.test_browser_qa import FakeQA, build

VIDEO = b"\x1aE\xdf\xa3 pretend this is a webm recording"


def shell(
    *, size: int | None = None, encoded: str | None = None, exit_code: int = 0
) -> tuple[Any, list[str]]:
    """Answers the browser test, the search for the video and its base64 text."""
    commands: list[str] = []
    data = size if size is not None else len(VIDEO)
    text = encoded if encoded is not None else base64.b64encode(VIDEO).decode()

    def answer(command: str, files: dict[str, str]) -> CommandResult:
        commands.append(command)
        if command.startswith(E2E_COMMAND):
            return CommandResult(
                exit_code=exit_code, output="1 failed" if exit_code else "1 passed"
            )
        if command.startswith("find "):
            return CommandResult(exit_code=0, output=f"{data} /tmp/medhkarm-demo-0/t/video.webm\n")
        if command.startswith("base64 "):
            return CommandResult(exit_code=0, output=text)
        return CommandResult(exit_code=0, output="ok")

    return answer, commands


def fix_round() -> list[LLMResponse]:
    return [
        step("write_file", path="static/index.html", content="<form>still broken</form>"),
        step("finish", summary="tried"),
        step("submit_review", decision="approve", feedback=""),
    ]


def step(name: str, **arguments: Any) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


async def run(
    handler: Any, repo: InMemoryArtifactRepository | None, *more: LLMResponse
) -> tuple[RunOutcome, InMemoryEventStore]:
    script = build("static/index.html", *more)
    llm, events = ScriptedLLMProvider(script), InMemoryEventStore()
    graph = build_app_graph(
        llm,
        ToolLoopEngine(llm),
        InMemorySandboxProvider(handler),
        InMemorySaver(),
        events=events,
        developer_names=["Isha", "Arjun"],
        max_developers=2,
        specialties={"Isha": "backend", "Arjun": "frontend"},
        browser_tester=FakeQA(),
        qa_name="Tara",
        artifacts=ArtifactService(repo) if repo is not None else None,
    )
    return await WorkflowService(graph, events).start("run-3", "Build a page", "pytest"), events


async def test_a_passing_test_is_recorded_and_the_video_is_kept() -> None:
    handler, commands = shell()
    repo = InMemoryArtifactRepository()

    outcome, events = await run(handler, repo)

    assert outcome.waiting_for_approval
    [saved] = await repo.for_run("run-3", "demo")
    assert (saved.name, saved.content_type, saved.size) == (
        "browser-test.webm",
        "video/webm",
        len(VIDEO),
    )
    assert (await repo.content("run-3", saved.id)).data == VIDEO  # type: ignore[union-attr]
    e2e = next(c for c in commands if c.startswith(E2E_COMMAND))
    assert "--video on --slowmo 300 --output /tmp/medhkarm-demo-0" in e2e
    [event] = [e for e in events.events if e.type == EventType.DEMO_RECORDED]
    assert event.data == {"artifact_id": saved.id, "bytes": len(VIDEO)}
    assert outcome.state["browser"]["demo"]["artifact_id"] == saved.id


async def test_without_a_place_to_keep_it_nothing_is_recorded() -> None:
    handler, commands = shell()

    outcome, events = await run(handler, None)

    assert outcome.waiting_for_approval
    assert all("--video" not in c for c in commands)
    assert not [e for e in events.events if e.type == EventType.DEMO_RECORDED]


async def test_a_failing_test_keeps_no_video() -> None:
    handler, _ = shell(exit_code=1)
    repo = InMemoryArtifactRepository()

    outcome, _ = await run(handler, repo, *fix_round())

    assert outcome.state["status"] == "failed"
    assert repo.items == []


async def test_an_oversized_or_broken_video_never_fails_the_run() -> None:
    for handler in (
        shell(size=MAX_VIDEO_BYTES + 1)[0],
        shell(encoded="not base64 at all!!")[0],
        shell(size=0)[0],
    ):
        repo = InMemoryArtifactRepository()
        outcome, events = await run(handler, repo)
        assert outcome.waiting_for_approval  # the release still goes to the founder
        assert repo.items == []
        assert not [e for e in events.events if e.type == EventType.DEMO_RECORDED]
