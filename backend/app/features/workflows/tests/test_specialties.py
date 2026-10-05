"""Developer specialties: the CTO tags tasks, specialists get them, and their instructions."""

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.sandbox.schemas import CommandResult
from app.features.teams.loader import load_templates
from app.features.workflows.cto import CtoPlan, PlannedTask, assign, parse_plan
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.service import WorkflowService

NAMES = ["Isha", "Arjun", "Ravi"]
SPECIALTIES = {"Isha": "backend", "Arjun": "frontend", "Ravi": "backend"}


def tool(name: str, **arguments: Any) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


def test_tasks_go_to_matching_specialists_within_the_limit() -> None:
    plan = CtoPlan(
        developers=1,
        tasks=[
            PlannedTask(title="API for bookings", specialty="backend"),
            PlannedTask(title="Booking form", specialty="frontend"),
            PlannedTask(title="Reminders job", specialty="backend"),
            PlannedTask(title="Readme", specialty="any"),
        ],
    )

    tasks = assign(plan, NAMES, max_developers=3, specialties=SPECIALTIES)

    assert [(t["owner"], t["specialty"]) for t in tasks] == [
        ("Isha", "backend"),
        ("Arjun", "frontend"),
        ("Ravi", "backend"),
        ("Isha", "backend"),  # "any": the team the CTO chose (one developer)
    ]


def test_specialists_beyond_the_limit_are_not_used() -> None:
    plan = CtoPlan(developers=1, tasks=[PlannedTask(title="Form", specialty="frontend")])

    [task] = assign(plan, NAMES, max_developers=1, specialties=SPECIALTIES)

    assert task["owner"] == "Isha"  # the only developer allowed


def test_the_plan_reads_specialties_leniently() -> None:
    response = tool(
        "submit_plan",
        summary="s",
        developers=2,
        tasks=[{"title": "Form", "area": "Frontend"}, {"title": "API"}],
    )

    assert [t.specialty for t in parse_plan(response, "r").tasks] == ["frontend", "any"]


async def test_the_cto_sees_specialties_and_the_developer_gets_their_instructions() -> None:
    seen: list[list[dict[str, Any]]] = []

    class Spy(ScriptedLLMProvider):
        async def complete(self, messages, tools=None):  # type: ignore[no-untyped-def]
            seen.append(list(messages))
            return await super().complete(messages, tools)

    llm = Spy(
        [
            tool(
                "submit_plan",
                summary="s",
                developers=2,
                tasks=[{"title": "Booking form", "description": "", "specialty": "frontend"}],
            ),
            tool("write_file", path="form.js", content="x"),
            tool("finish", summary="done"),
            tool("submit_review", decision="approve", feedback=""),
        ]
    )
    sandboxes = InMemorySandboxProvider(lambda c, f: CommandResult(exit_code=0, output="ok"))
    graph = build_app_graph(
        llm,
        ToolLoopEngine(llm),
        sandboxes,
        InMemorySaver(),
        developer_names=NAMES,
        max_developers=3,
        specialties=SPECIALTIES,
        specialty_instructions={"frontend": "Label every form field."},
    )

    state = (await WorkflowService(graph).start("r", "Booking page", "true")).state

    assert "Arjun (frontend)" in seen[0][1]["content"]
    assert state["tasks"][0]["owner"] == "Arjun"
    developer_system = seen[1][0]["content"]
    assert developer_system.endswith("Label every form field.")


def test_the_software_team_has_backend_and_frontend_developers() -> None:
    developer = load_templates()["software"].role("developer")

    assert developer.specialty_of() == SPECIALTIES
    assert all(s.instructions for s in developer.specialties)


def test_page_work_goes_to_frontend_whatever_the_plan_says() -> None:
    from app.features.workflows.cto import _normalise_task

    ui = _normalise_task(
        {"title": "Add UI for submitting feedback on home page", "specialty": "backend"}
    )
    api = _normalise_task({"title": "Add API route for posting messages", "specialty": "backend"})
    assert ui is not None and ui.specialty == "frontend"
    assert api is not None and api.specialty == "backend"


def test_landing_page_sections_are_frontend_work() -> None:
    from app.features.workflows.cto import _normalise_task

    for title in (
        "Create Hero Section",
        "Add Services Cards and Process Steps",
        "Update Global Styles and Metadata",
        "Add Final CTA Section",
    ):
        task = _normalise_task({"title": title, "specialty": "backend"})
        assert task is not None and task.specialty == "frontend", title
