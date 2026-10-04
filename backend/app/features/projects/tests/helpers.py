"""Fakes for backlog tests: runs that start on request, and pull requests to follow."""

from datetime import UTC, datetime

from app.features.projects.memory_repository import InMemoryProjectRepository
from app.features.projects.schemas import ItemFields, ItemStatus, ProjectStatus
from app.features.repos.schemas import RepoSource
from app.features.runs.schemas import Run, RunStatus, StartRun


class FakeRuns:
    def __init__(self) -> None:
        self.started: list[StartRun] = []
        self.runs: dict[str, Run] = {}

    async def start(self, body: StartRun) -> Run:
        self.started.append(body)
        now = datetime.now(UTC)
        run = Run(
            id=f"run{len(self.started)}",
            request=body.request,
            test_command=body.test_command or "",
            repo=body.repo,
            status=RunStatus.QUEUED,
            created_at=now,
            updated_at=now,
        )
        self.runs[run.id] = run
        return run

    async def get(self, run_id: str) -> Run:
        return self.runs[run_id]

    def finish(
        self, run_id: str, status: RunStatus, delivery: dict[str, str] | None = None
    ) -> None:
        self.runs[run_id] = self.runs[run_id].model_copy(
            update={"status": status, "delivery": delivery}
        )


class FakePullRequests:
    def __init__(self, merge_ok: bool = True) -> None:
        self.states: dict[str, str] = {}
        self.merged: list[str] = []
        self.merge_ok = merge_ok

    async def pull_request_state(self, url: str) -> str:
        return self.states.get(url, "open")

    async def merge_pull_request(self, url: str, title: str) -> bool:
        if self.merge_ok:
            self.merged.append(url)
        return self.merge_ok


async def active_project(
    repo: InMemoryProjectRepository,
    titles: list[str],
    *,
    source: RepoSource | None = None,
    autopilot: bool = True,
    daily_limit: int = 2,
) -> str:
    project = await repo.create_project(
        "p1",
        {
            "name": "Habit tracker",
            "goal": "Track daily habits with streaks",
            "repo": source,
            "status": ProjectStatus.ACTIVE,
            "autopilot": autopilot,
            "daily_limit": daily_limit,
        },
    )
    for title in titles:
        await repo.add_item(
            project.id, ItemFields(title=title, acceptance=["works"]), ItemStatus.TODO
        )
    return project.id
