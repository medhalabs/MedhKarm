"""Priya's project report."""

from datetime import UTC, datetime, timedelta

from app.features.projects.health import project_health
from app.features.projects.schemas import BacklogItem, ItemStatus, Project, ProjectStatus, Size

NOW = datetime(2026, 10, 7, tzinfo=UTC)


def project(
    status: ProjectStatus = ProjectStatus.ACTIVE, questions: list[str] | None = None
) -> Project:
    return Project(
        id="p1",
        name="Chai stall",
        goal="Orders",
        status=status,
        autopilot=False,
        daily_limit=2,
        questions=questions or [],
        created_at=NOW,
        updated_at=NOW,
    )


def item(n: int, status: ItemStatus, run: str | None = None) -> BacklogItem:
    return BacklogItem(
        id=f"i{n}",
        project_id="p1",
        position=n,
        status=status,
        title=f"Item {n}",
        what="w",
        size=Size.S,
        run_id=run,
        created_at=NOW,
        updated_at=NOW,
    )


def health(items: list[BacklogItem], tokens: dict[str, int] | None = None, **more):  # type: ignore[no-untyped-def]
    return project_health(
        more.pop("project", project()),
        items,
        tokens or {},
        more.pop("last", NOW - timedelta(hours=5)),
        NOW,
    )


def test_a_project_that_is_moving() -> None:
    result = health(
        [
            item(1, ItemStatus.DONE, "r1"),
            item(2, ItemStatus.IN_PROGRESS, "r2"),
            item(3, ItemStatus.TODO),
        ],
        {"r1": 120_000, "r2": 30_000},
    )
    assert (result.items_total, result.done, result.in_progress, result.waiting) == (3, 1, 1, 1)
    assert (result.runs, result.tokens, result.state) == (2, 150_000, "moving")
    assert (
        result.summary
        == "Moving: 1 of 3 items done, 1 in progress; 150,000 model tokens used so far."
    )


def test_skipped_items_dont_count_and_runs_of_other_projects_dont_add_tokens() -> None:
    result = health(
        [item(1, ItemStatus.DONE, "r1"), item(2, ItemStatus.SKIPPED)], {"r1": 10, "other": 999}
    )
    assert (result.items_total, result.tokens, result.state) == (1, 10, "done")


def test_blocked_work_or_open_questions_mean_it_needs_the_founder() -> None:
    blocked = health([item(1, ItemStatus.BLOCKED, "r1"), item(2, ItemStatus.TODO)])
    assert blocked.state == "needs_you" and "1 blocked" in blocked.summary
    asking = health(
        [item(1, ItemStatus.DONE, "r1"), item(2, ItemStatus.TODO)],
        project=project(questions=["Why?"]),
    )
    assert asking.state == "needs_you" and "waiting on you" in asking.summary


def test_quiet_for_days_with_work_waiting_is_stalled() -> None:
    result = health(
        [item(1, ItemStatus.DONE, "r1"), item(2, ItemStatus.TODO)], last=NOW - timedelta(days=5)
    )
    assert result.state == "stalled" and result.days_since_activity == 5
    assert result.summary.startswith("Quiet for 5 days with work waiting")


def test_not_started_and_done() -> None:
    fresh = health([item(1, ItemStatus.TODO)], last=None)
    assert fresh.state == "not_started" and fresh.days_since_activity is None
    assert "nothing spent yet" in fresh.summary
    assert health([], project=project(ProjectStatus.DONE)).state == "done"
