"""Working through a backlog across items and days, with fake runs and pull requests."""

from datetime import UTC, datetime, timedelta

import pytest

from app.features.projects.exceptions import BacklogConflictError
from app.features.projects.memory_repository import InMemoryProjectRepository
from app.features.projects.progress import BacklogProgress
from app.features.projects.schemas import ItemStatus, ProjectStatus
from app.features.projects.tests.helpers import FakePullRequests, FakeRuns, active_project
from app.features.repos.schemas import RepoSource
from app.features.runs.schemas import RunStatus

NOW = datetime(2026, 10, 3, 6, 0, tzinfo=UTC)  # 11:30 in India
CREATED = {"status": "created", "repo_url": "https://github.com/me/habit-tracker-p1"}


def opened(n: int, repo: str = "me/habit-tracker-p1") -> dict[str, str]:
    return {"status": "opened", "pull_request_url": f"https://github.com/{repo}/pull/{n}"}


def setup(
    prs: FakePullRequests | None = None, now: list[datetime] | None = None
) -> tuple[InMemoryProjectRepository, FakeRuns, BacklogProgress, FakePullRequests]:
    repo, runs, prs = InMemoryProjectRepository(), FakeRuns(), prs or FakePullRequests()
    clock = now or [NOW]
    progress = BacklogProgress(repo, runs, prs, clock=lambda: clock[0])
    return repo, runs, progress, prs


async def statuses(repo: InMemoryProjectRepository) -> list[str]:
    return [i.status for i in await repo.list_items("p1")]


async def test_new_project_creates_its_repo_then_later_items_merge_into_it() -> None:
    repo, runs, progress, prs = setup()
    await active_project(repo, ["Add a habit", "Streaks", "Weekly view"])

    await progress.tick()  # item 1 starts
    first = runs.started[0]
    assert first.repo is None and first.create_repo
    assert first.new_repo_name == "habit-tracker-p1"
    assert first.request.startswith("Add a habit") and "item 1 of 3" in first.request

    await progress.on_run_finished("run1", RunStatus.RELEASED, CREATED)
    project = await repo.get_project("p1")
    assert project and project.repo and project.repo_owned
    assert project.repo.url == "https://github.com/me/habit-tracker-p1"

    await progress.tick()  # item 2 starts in the new repository
    assert runs.started[1].repo == project.repo
    assert "Already built in this project" in runs.started[1].request
    await progress.on_run_finished("run2", RunStatus.RELEASED, opened(2))

    assert prs.merged == ["https://github.com/me/habit-tracker-p1/pull/2"]
    assert await statuses(repo) == ["done", "done", "todo"]


async def test_daily_limit_then_next_day() -> None:
    now = [NOW]
    repo, runs, progress, _ = setup(now=now)
    await active_project(repo, ["A item", "B item", "C item"], daily_limit=1)

    await progress.tick()
    await progress.on_run_finished("run1", RunStatus.RELEASED, CREATED)
    await progress.tick()  # today's one item is used up
    assert len(runs.started) == 1

    now[0] = NOW + timedelta(days=1)
    await progress.tick()
    assert len(runs.started) == 2


async def test_founders_own_repo_waits_for_their_merge() -> None:
    repo, runs, progress, prs = setup()
    source = RepoSource(url="https://github.com/founder/shop")
    await active_project(repo, ["Coupons", "Wishlist"], source=source)

    await progress.tick()
    assert runs.started[0].repo == source and not runs.started[0].create_repo
    await progress.on_run_finished("run1", RunStatus.RELEASED, opened(5, "founder/shop"))
    await progress.tick()

    [first, second] = await repo.list_items("p1")
    assert first.status == ItemStatus.WAITING_FOR_MERGE
    assert "Merge the pull request" in first.note
    assert second.status == ItemStatus.TODO and prs.merged == []

    prs.states[first.pull_request_url] = "merged"
    await progress.tick()
    assert await statuses(repo) == ["done", "in_progress"]


async def test_rejected_or_failed_items_block_the_backlog() -> None:
    repo, runs, progress, _ = setup()
    await active_project(repo, ["A item", "B item"])

    await progress.tick()
    await progress.on_run_finished("run1", RunStatus.REJECTED)
    await progress.tick()

    assert await statuses(repo) == ["blocked", "todo"]
    assert len(runs.started) == 1
    with pytest.raises(BacklogConflictError):
        await progress.start_next("p1")


async def test_missed_reports_are_caught_up_from_the_run() -> None:
    repo, runs, progress, _ = setup()
    await active_project(repo, ["A item", "B item"])
    await progress.tick()

    runs.finish("run1", RunStatus.RELEASED, CREATED)  # the worker's report never arrived
    await progress.tick()

    assert await statuses(repo) == ["done", "in_progress"]  # caught up, then moved on


async def test_work_that_isnt_saved_pauses_the_project() -> None:
    repo, _, progress, _ = setup()
    await active_project(repo, ["A item", "B item"])
    await progress.tick()

    await progress.on_run_finished(
        "run1", RunStatus.RELEASED, {"status": "skipped", "reason": "No GITHUB_TOKEN set."}
    )

    project = await repo.get_project("p1")
    assert project and project.status == ProjectStatus.PAUSED
    assert "GITHUB_TOKEN" in project.error
    assert await statuses(repo) == ["blocked", "todo"]


async def test_finishing_the_last_item_finishes_the_project() -> None:
    repo, _, progress, _ = setup()
    await active_project(repo, ["Only item"])

    await progress.tick()
    await progress.on_run_finished("run1", RunStatus.RELEASED, CREATED)

    project = await repo.get_project("p1")
    assert project and project.status == ProjectStatus.DONE


async def test_manual_start_works_without_autopilot_and_resumes_a_pause() -> None:
    repo, runs, progress, _ = setup()
    await active_project(repo, ["A item"], autopilot=False)
    await repo.update_project("p1", {"status": ProjectStatus.PAUSED})

    await progress.tick()  # not on autopilot: nothing happens
    assert runs.started == []
    item = await progress.start_next("p1")

    assert item.status == ItemStatus.IN_PROGRESS and item.attempts == 1
    project = await repo.get_project("p1")
    assert project and project.status == ProjectStatus.ACTIVE
