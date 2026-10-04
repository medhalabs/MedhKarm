"""The scaffold step: new projects start from the starter and modules; repos, seeded
workspaces and runs without a stack are left alone."""

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.events.schemas import EventType
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.repos.service import RepoService
from app.features.repos.tests.fakes import FakeHost, project_shell
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.starters.service import StarterService
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.schemas import RunOutcome
from app.features.workflows.service import WorkflowService


def tool(name: str, **arguments: Any) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


SCRIPT = [
    tool("submit_plan", summary="s", developers=1, tasks=[{"title": "Add the menu page"}]),
    tool("write_file", path="app/menu/page.tsx", content="export default function M() {}"),
    tool("finish", summary="done"),
    tool("submit_review", decision="approve", feedback=""),
]


async def run(
    request: str, stack: dict[str, Any] | None, **start: Any
) -> tuple[RunOutcome, InMemoryEventStore, ScriptedLLMProvider, InMemorySandboxProvider]:
    llm, events = ScriptedLLMProvider(list(SCRIPT)), InMemoryEventStore()
    sandboxes = InMemorySandboxProvider(project_shell)
    graph = build_app_graph(
        llm,
        ToolLoopEngine(llm),
        sandboxes,
        InMemorySaver(),
        events=events,
        repos=RepoService(FakeHost()),
        starters=StarterService(),
    )
    outcome = await WorkflowService(graph, events).start("r", request, "", stack=stack, **start)
    return outcome, events, llm, sandboxes


async def test_a_new_app_starts_from_the_starter_with_its_modules() -> None:
    outcome, events, llm, _ = await run("A bakery website where customers log in", {})

    state = outcome.state
    assert state["scaffold"]["starter"] == "nextjs" and state["scaffold"]["modules"] == ["auth"]
    assert state["test_command"] == "npm test"
    assert "lib/auth/index.ts" in state["codebase_map"]  # mapped like an existing project
    [scaffolded] = [e for e in events.events if e.type == EventType.PROJECT_SCAFFOLDED]
    assert scaffolded.actor == "devops"
    assert scaffolded.summary == (
        "Set up the project from our Next.js starter with sign-in "
        "(nextjs + nextjs, supabase, vercel)"
    )
    plan_prompt = str(llm.calls[0])
    assert "Read AGENTS.md first" in plan_prompt  # the CTO knows the stack


async def test_a_stack_without_a_starter_is_still_told_to_the_team() -> None:
    outcome, events, llm, _ = await run("An inventory web app", {"api": "java"})

    assert "scaffold" not in outcome.state
    assert "No ready-made starter for nextjs + java" in str(llm.calls[0])
    assert [e.summary for e in events.events if e.type == EventType.PROJECT_SCAFFOLDED] == [
        "Chose the stack: nextjs + java, postgres, docker"
    ]


async def test_repos_and_runs_without_a_stack_are_left_alone() -> None:
    on_repo, *_ = await run("A website", {}, repo={"url": "https://github.com/a/b"})
    assert "stack" not in on_repo.state and "scaffold" not in on_repo.state

    no_stack, *_ = await run("A website", None)
    assert "stack" not in no_stack.state
