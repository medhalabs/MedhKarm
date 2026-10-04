from typing import Any

from app.features.models.schemas import LLMResponse, ToolCall
from app.features.projects.pm import parse_backlog
from app.features.projects.schemas import Size


def tool(**arguments: Any) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id="b", name="submit_backlog", arguments=arguments)])


def test_reads_the_tool_call() -> None:
    backlog = parse_backlog(
        tool(
            summary="Habit tracker",
            questions=["Daily habits only?"],
            items=[
                {
                    "title": "Add a habit",
                    "description": "Name it",
                    "acceptance": ["saved", "listed"],
                    "size": "S",
                },
                {"title": "Mark done today", "description": "", "acceptance": [], "size": "M"},
            ],
        ),
        "goal",
    )

    assert [i.title for i in backlog.items] == ["Add a habit", "Mark done today"]
    assert backlog.items[0].acceptance == ["saved", "listed"]
    assert backlog.items[0].size == Size.S
    assert backlog.questions == ["Daily habits only?"]


def test_small_model_shapes_are_tolerated() -> None:
    backlog = parse_backlog(
        tool(
            backlog=[
                {"name": "Item 1: Streak counter", "acceptance_criteria": "shows days; resets"},
                {"description": "Weekly report\nemails nothing", "size": "large"},
                "3. Export to CSV",
                {"title": "x"},  # too short: dropped
            ],
            assumptions="Single user",
        ),
        "goal",
    )

    assert [i.title for i in backlog.items] == ["Streak counter", "Weekly report", "Export to CSV"]
    assert backlog.items[0].acceptance == ["shows days", "resets"]
    assert backlog.items[1].size == Size.L
    assert backlog.questions == ["Single user"]


def test_falls_back_to_numbered_lines_then_the_goal() -> None:
    lines = parse_backlog(LLMResponse(content="Plan:\n1. Login page\n2) Dashboard"), "g")
    nothing = parse_backlog(
        LLMResponse(content="Sounds good!"), "Build a habit tracker\nwith streaks"
    )

    assert [i.title for i in lines.items] == ["Login page", "Dashboard"]
    assert [i.title for i in nothing.items] == ["Build a habit tracker"]
    assert "streaks" in nothing.items[0].description
