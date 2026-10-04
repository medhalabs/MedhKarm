from typing import Any

from app.features.events.schemas import EventType
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, TokenUsage, ToolCall
from app.features.projects.memory_repository import InMemoryProjectRepository
from app.features.projects.planner import BacklogPlanner
from app.features.projects.schemas import ItemFields, ItemStatus, ProjectStatus


def backlog(*titles: str) -> LLMResponse:
    items: list[dict[str, Any]] = [
        {"title": t, "description": "", "acceptance": ["works"], "size": "M"} for t in titles
    ]
    return LLMResponse(
        tool_calls=[
            ToolCall(
                id="b",
                name="submit_backlog",
                arguments={"summary": "s", "questions": ["One user?"], "items": items},
            )
        ],
        usage=TokenUsage(prompt_tokens=300, completion_tokens=200, total_tokens=500),
    )


async def test_planning_proposes_items_and_logs_it_like_a_run() -> None:
    repo, events = InMemoryProjectRepository(), InMemoryEventStore()
    await repo.create_project(
        "p1",
        {
            "name": "Habits",
            "goal": "Track habits",
            "status": ProjectStatus.PLANNING,
            "autopilot": False,
            "daily_limit": 2,
        },
    )
    planner = BacklogPlanner(ScriptedLLMProvider([backlog("Add habit", "Streaks")]), repo, events)

    count = await planner.plan("p1")

    project = await repo.get_project("p1")
    assert count == 2 and project and project.status == ProjectStatus.PLAN_READY
    assert project.questions == ["One user?"]
    assert [i.status for i in await repo.list_items("p1")] == ["proposed", "proposed"]
    assert [e.type for e in events.events] == [
        EventType.RUN_STARTED,
        EventType.MODEL_USED,
        EventType.PLAN_CREATED,
        EventType.RUN_FINISHED,
    ]
    assert sum(e.tokens for e in events.events) == 500
    assert events.events[-1].data["status"] == "planned"


async def test_replanning_keeps_started_work_and_tells_the_pm() -> None:
    repo = InMemoryProjectRepository()
    await repo.create_project(
        "p1",
        {
            "name": "Habits",
            "goal": "Track habits",
            "status": ProjectStatus.PLANNING,
            "autopilot": False,
            "daily_limit": 2,
        },
    )
    done = await repo.add_item("p1", ItemFields(title="Add habit"), ItemStatus.DONE)
    await repo.add_item("p1", ItemFields(title="Old idea"), ItemStatus.TODO)
    llm = ScriptedLLMProvider([backlog("Streaks")])

    await BacklogPlanner(llm, repo).plan("p1")

    items = await repo.list_items("p1")
    assert [(i.title, i.status) for i in items] == [
        ("Add habit", "done"),
        ("Streaks", "proposed"),
    ]
    assert items[0].id == done.id
    brief = llm.calls[0][1]["content"]
    assert "Already built or under way" in brief and "Add habit" in brief
