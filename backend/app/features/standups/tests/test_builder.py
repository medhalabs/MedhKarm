"""Edge cases built from hand-written events: work in progress, stalled and failed runs."""

from datetime import UTC, date, datetime, timedelta
from typing import Any

from app.features.events.schemas import Actor, Event, EventType
from app.features.standups.builder import build_standup
from app.features.standups.schemas import ProjectStatus, Standup

SINCE = datetime(2026, 9, 30, 3, 30, tzinfo=UTC)
UNTIL = SINCE + timedelta(days=1)


class Log:
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self.events: list[Event] = []

    def add(self, hours: float, type: EventType, **data: Any) -> "Log":
        self.events.append(
            Event(
                id=len(self.events) + 1,
                occurred_at=SINCE + timedelta(hours=hours),
                run_id=self.run_id,
                actor=Actor.SYSTEM,
                type=type,
                summary="",
                data=data,
                tokens=10,
            )
        )
        return self


def started(run_id: str, hours: float = 1) -> Log:
    return (
        Log(run_id)
        .add(hours, EventType.RUN_STARTED, request=f"Build {run_id}")
        .add(hours, EventType.TASK_ASSIGNED, task_id="t1", member="Isha", title="Form")
        .add(hours, EventType.TASK_ASSIGNED, task_id="t2", member="Arjun", title="List")
    )


def build(*logs: Log) -> Standup:
    histories = {log.run_id: log.events for log in logs}
    return build_standup(
        histories, date(2026, 10, 1), "Asia/Kolkata", SINCE, UNTIL, timedelta(hours=2)
    )


def test_work_in_progress_is_planned_for_today() -> None:
    log = started("app", hours=22).add(23, EventType.WORK_STARTED, task_id="t1", member="Isha")

    standup = build(log)

    assert [i.text for i in standup.planned] == [
        "Isha: “Form” (working)",
        "Arjun: “List” (to do)",
    ]
    assert standup.projects[0].status == ProjectStatus.IN_PROGRESS


def test_silent_run_is_stalled_and_blocked() -> None:
    standup = build(started("app", hours=2))

    assert standup.projects[0].status == ProjectStatus.STALLED
    assert standup.blocked[0].text.startswith("No activity for a while")
    assert len(standup.planned) == 2  # the tasks are still to do


def test_failed_run_and_open_review_comments_are_blocked() -> None:
    log = (
        started("app")
        .add(2, EventType.REVIEW_FINISHED, task_id="t1", decision="revise", feedback="Tests")
        .add(
            3,
            EventType.REVIEW_FINISHED,
            task_id="t1",
            decision="approve",
            accepted_with_issues=True,
            feedback="Still no tests",
        )
        .add(4, EventType.RUN_FINISHED, status="failed")
    )

    standup = build(log)

    assert [i.text for i in standup.blocked] == [
        "“Form” was accepted with review comments still open: Still no tests",
        "Stopped: the final checks did not pass",
    ]
    assert standup.sent_back == 1
    assert standup.planned == []
    assert standup.headline == "0 tasks done, 2 blocked."


def test_projects_get_short_names_and_tokens_count_in_window_only() -> None:
    long = "Build an expense tracker module in Python: (1) expenses.py with an ExpenseBook"
    numbered = "Make a todo app (1) add (2) list"
    rambling = "Create calc.py with add and divide where divide raises ValueError on zero"
    logs = [
        Log(f"r{i}").add(-5, EventType.RUN_STARTED, request=r).add(1, EventType.WORK_STARTED)
        for i, r in enumerate([long, numbered, rambling])
    ]

    standup = build(*logs)

    assert [p.project for p in standup.projects] == [
        "Build an expense tracker module in Python",
        "Make a todo app",
        "Create calc.py with add and divide where divide\u2026",
    ]
    assert standup.tokens == 30  # the events before the window don't count
