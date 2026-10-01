"""Standups built from the events a real (scripted) build run records."""

from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.sandbox.schemas import CommandResult
from app.features.standups.exceptions import StandupDayInFutureError
from app.features.standups.render import to_text
from app.features.standups.schemas import ProjectStatus
from app.features.standups.service import StandupService
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.service import WorkflowService

# 08:30 and 10:30 in India on Oct 1; the Oct 1 standup covers Sep 30 09:00 to Oct 1 09:00.
BEFORE_STANDUP = datetime(2026, 10, 1, 3, 0, tzinfo=UTC)
AFTER_STANDUP = datetime(2026, 10, 1, 5, 0, tzinfo=UTC)
OCT_1 = date(2026, 10, 1)


def tool(name: str, **arguments: Any) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


def two_task_script() -> list[LLMResponse]:
    tasks = [
        {"title": "Write a.py", "description": ""},
        {"title": "Write b.py", "description": ""},
    ]
    return [
        tool("submit_plan", summary="Plan", developers=2, tasks=tasks),
        tool("write_file", path="a.py", content="1"),
        tool("finish", summary="a done"),
        tool("submit_review", decision="revise", feedback="Add a docstring"),
        tool("write_file", path="a.py", content='"""Doc."""'),
        tool("finish", summary="a fixed"),
        tool("submit_review", decision="approve", feedback=""),
        tool("write_file", path="b.py", content="2"),
        tool("finish", summary="b done"),
        tool("submit_review", decision="approve", feedback=""),
    ]


def workflow(store: InMemoryEventStore) -> WorkflowService:
    llm = ScriptedLLMProvider(two_task_script())
    sandboxes = InMemorySandboxProvider(
        lambda command, files: CommandResult(exit_code=0, output="ok")
    )
    graph = build_app_graph(
        llm,
        ToolLoopEngine(llm),
        sandboxes,
        InMemorySaver(),
        events=store,
        developer_names=["Isha", "Arjun"],
        max_developers=2,
    )
    return WorkflowService(graph, store)


def standups(store: InMemoryEventStore, now: datetime) -> StandupService:
    return StandupService(store, "Asia/Kolkata", 9, timedelta(hours=2), clock=lambda: now)


async def test_overnight_run_waiting_for_approval() -> None:
    store = InMemoryEventStore()
    store.now = BEFORE_STANDUP
    await workflow(store).start("run-1", "Build an expense tracker\nwith totals", "pytest")

    standup = await standups(store, AFTER_STANDUP).for_day(OCT_1)

    assert [i.text for i in standup.done] == [
        "Isha finished “Write a.py”",
        "Arjun finished “Write b.py”",
    ]
    assert [(i.project, i.text) for i in standup.needs_you] == [
        ("Build an expense tracker with totals", "Approve the release")
    ]
    assert standup.planned == [] and standup.blocked == []
    assert standup.sent_back == 1
    assert standup.headline == "2 tasks done, 1 waiting for your approval, nothing blocked."
    [project] = standup.projects
    assert (project.status, project.tasks_done, project.tasks_total) == (
        ProjectStatus.WAITING_FOR_APPROVAL,
        2,
        2,
    )
    assert standup.tokens == sum(e.tokens for e in store.events)


async def test_next_day_shows_the_release_and_not_old_work() -> None:
    store = InMemoryEventStore()
    service = workflow(store)
    store.now = BEFORE_STANDUP
    await service.start("run-1", "Build an expense tracker", "pytest")
    store.now = AFTER_STANDUP
    await service.resume("run-1", approved=True)

    standup = await standups(store, AFTER_STANDUP + timedelta(days=1)).for_day(date(2026, 10, 2))

    assert [i.text for i in standup.done] == ["Released"]
    assert standup.needs_you == []
    assert standup.projects[0].status == ProjectStatus.RELEASED


async def test_waiting_runs_keep_showing_until_decided() -> None:
    store = InMemoryEventStore()
    store.now = BEFORE_STANDUP
    await workflow(store).start("run-1", "Build it", "pytest")

    later = AFTER_STANDUP + timedelta(days=3)
    standup = await standups(store, later).for_day()

    assert standup.day == date(2026, 10, 4)
    assert len(standup.needs_you) == 1
    assert standup.done == []  # the work itself happened days ago


async def test_quiet_day() -> None:
    standup = await standups(InMemoryEventStore(), AFTER_STANDUP).for_day(OCT_1)

    assert standup.headline == "A quiet day: no work in progress."
    assert "Nothing" in to_text(standup)


def test_window_is_local_and_cut_off_at_now() -> None:
    service = standups(InMemoryEventStore(), BEFORE_STANDUP)  # 08:30 in India

    since, until = service.window(OCT_1)

    assert since == datetime(2026, 9, 30, 3, 30, tzinfo=UTC)  # Sep 30 09:00 IST
    assert until == BEFORE_STANDUP
    with pytest.raises(StandupDayInFutureError):
        service.window(date(2026, 10, 2))


async def test_text_lists_every_section() -> None:
    store = InMemoryEventStore()
    store.now = BEFORE_STANDUP
    await workflow(store).start("run-1", "Build it", "pytest")

    text = to_text(await standups(store, AFTER_STANDUP).for_day(OCT_1))

    for heading in ("Needs you:", "Done:", "Planned today:", "Blocked:"):
        assert heading in text
    assert "30 Sep 09:00 to 01 Oct 09:00 (Asia/Kolkata)" in text
    assert "The CTO sent 1 task back for changes." in text
