"""The blueprint step: an approved plan's documents go into the project, and the CTO and the
developers are told to follow it. Runs without a plan are untouched."""

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.repos.service import RepoService
from app.features.repos.tests.fakes import FakeHost, project_shell
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.nodes.blueprint import BRIEF_LIMIT, plan_brief
from app.features.workflows.schemas import PlanDocs
from app.features.workflows.service import WorkflowService

PLAN = PlanDocs(
    files={
        "docs/README.md": "# Project plan",
        "docs/01-product-brief.md": "# Product brief\nCoffee orders.",
        "docs/03-architecture.md": "# Architecture\nNext.js with Supabase.",
    },
    titles={"docs/01-product-brief.md": "Product brief", "docs/03-architecture.md": "Architecture"},
)


class Plans:
    def __init__(self, plan: PlanDocs | None) -> None:
        self._plan = plan
        self.asked: list[str] = []

    async def for_run(self, run_id: str) -> PlanDocs | None:
        self.asked.append(run_id)
        return self._plan


def tool(name: str, **arguments: Any) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


async def run(plans: Plans) -> tuple[ScriptedLLMProvider, InMemorySandboxProvider, dict[str, Any]]:
    llm = ScriptedLLMProvider(
        [
            tool("submit_plan", summary="s", developers=1, tasks=[{"title": "Menu page"}]),
            tool("write_file", path="menu.py", content="x = 1"),
            tool("finish", summary="done"),
            tool("submit_review", decision="approve", feedback=""),
        ]
    )
    sandboxes, events = InMemorySandboxProvider(project_shell), InMemoryEventStore()
    graph = build_app_graph(
        llm,
        ToolLoopEngine(llm),
        sandboxes,
        InMemorySaver(),
        events=events,
        repos=RepoService(FakeHost()),
        plans=plans,
    )
    outcome = await WorkflowService(graph, events).start("run-9", "Coffee shop orders", "pytest")
    return llm, sandboxes, outcome.state


async def test_the_plan_is_written_into_the_project_and_given_to_the_team() -> None:
    plans = Plans(PLAN)
    llm, sandboxes, state = await run(plans)

    sandbox = await sandboxes.attach(state["sandbox_id"])
    assert (
        await sandbox.read_file("docs/03-architecture.md")
        == "# Architecture\nNext.js with Supabase."
    )
    assert "docs/README.md" in state["blueprint_files"]
    assert plans.asked == ["run-9"]
    plan_prompt, developer_prompt = str(llm.calls[0]), str(llm.calls[1])
    assert "Build only milestone 1" in plan_prompt and "Next.js with Supabase" in plan_prompt
    assert "Next.js with Supabase" in developer_prompt  # developers follow it too


async def test_a_run_without_a_plan_is_left_alone() -> None:
    llm, sandboxes, state = await run(Plans(None))

    assert "blueprint_brief" not in state
    assert (
        "docs/03-architecture.md"
        not in await (await sandboxes.attach(state["sandbox_id"])).list_files()
    )
    assert "Build only milestone 1" not in str(llm.calls[0])


def test_the_most_useful_documents_come_first_and_the_brief_is_cut_to_a_limit() -> None:
    text = plan_brief(PLAN)
    assert text.index("Architecture") < text.index("Product brief")

    long = PlanDocs(
        files={"docs/03-architecture.md": "a" * 9000, "docs/02-roadmap.md": "r" * 9000},
        titles={"docs/03-architecture.md": "Architecture", "docs/02-roadmap.md": "Roadmap"},
    )
    cut = plan_brief(long)
    assert len(cut) <= BRIEF_LIMIT and "Architecture" in cut and "Roadmap" not in cut
