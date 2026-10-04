"""Moving through the backlog: each item becomes a build run, one at a time, so every item
builds on the last.

- `start_next` turns the next to-do item into a run (manually, or from `tick`).
- `on_run_finished` (called by the worker when a run ends) marks the item done, blocked, or
  waiting for the founder to merge its pull request.
- `tick` (the worker, once a minute) moves autopilot projects on: it follows pull requests
  and starts the next item, up to the project's daily limit.

Work carries over between items through the project's repository: the first item of a new
project creates a private one; later items work in it, and their pull requests are merged on
approval because MedhKarm owns that repository. On the founder's own repository, the backlog
waits until the founder merges each pull request.
"""

import logging
from collections.abc import Callable
from datetime import UTC, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

from app.features.projects.exceptions import BacklogConflictError, ProjectNotFoundError
from app.features.projects.interfaces import ProjectRepository, PullRequests, RunStarter
from app.features.projects.schemas import (
    BUSY_ITEMS,
    BacklogItem,
    ItemStatus,
    Project,
    ProjectStatus,
)
from app.features.repos.schemas import RepoSource, repo_name_for
from app.features.runs.schemas import RunStatus, StartRun

logger = logging.getLogger(__name__)

MAX_REQUEST = 5000
FINAL = (RunStatus.RELEASED, RunStatus.REJECTED, RunStatus.FAILED, RunStatus.ERROR)
NO_REPO = (
    "The released work wasn't saved to a repository (is GITHUB_TOKEN set?), so the next "
    "item couldn't build on it. Fix that, then retry the item."
)


class BacklogProgress:
    def __init__(
        self,
        projects: ProjectRepository,
        runs: RunStarter,
        pull_requests: PullRequests | None = None,
        timezone: str = "Asia/Kolkata",
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._projects = projects
        self._runs = runs
        self._prs = pull_requests
        self._zone = ZoneInfo(timezone)
        self._clock = clock

    async def start_next(self, project_id: str) -> BacklogItem:
        """Start the next to-do item now (the founder's "start next" button, or the tick)."""
        project = await self._projects.get_project(project_id)
        if project is None:
            raise ProjectNotFoundError(f"No project {project_id}")
        if project.status not in (ProjectStatus.ACTIVE, ProjectStatus.PAUSED):
            raise BacklogConflictError(f"The backlog isn't approved yet ({project.status})")
        items = await self._projects.list_items(project_id)
        busy = next((i for i in items if i.status in BUSY_ITEMS), None)
        if busy:
            raise BacklogConflictError(f"“{busy.title}” is {busy.status}: one item at a time")
        item = next((i for i in items if i.status == ItemStatus.TODO), None)
        if item is None:
            raise BacklogConflictError("Nothing left to do in the backlog")
        run = await self._runs.start(
            StartRun(
                request=item_request(project, item, items),
                test_command=project.test_command or None,
                repo=project.repo,
                create_repo=project.repo is None,
                new_repo_name=None if project.repo else repo_name_for(project.name, project.id),
            )
        )
        if project.status == ProjectStatus.PAUSED:
            await self._projects.update_project(
                project_id, {"status": ProjectStatus.ACTIVE, "error": ""}
            )
        return await self._projects.update_item(
            item.id,
            {
                "status": ItemStatus.IN_PROGRESS,
                "run_id": run.id,
                "attempts": item.attempts + 1,
                "started_at": self._clock(),
                "note": "",
            },
        )

    async def on_run_finished(
        self, run_id: str, status: RunStatus, delivery: dict[str, Any] | None = None
    ) -> None:
        """The worker reports a run's outcome; runs that aren't backlog items are ignored."""
        item = await self._projects.item_for_run(run_id)
        if item is None or item.status != ItemStatus.IN_PROGRESS:
            return
        project = await self._projects.get_project(item.project_id)
        if project is None:
            return
        if status == RunStatus.RELEASED:
            await self._released(project, item, delivery or {})
        elif status == RunStatus.REJECTED:
            await self._block(item, "You didn't approve the release. Edit and retry, or skip it.")
        elif status == RunStatus.FAILED:
            await self._block(item, "The team couldn't make the checks pass. Retry or skip it.")
        elif status == RunStatus.ERROR:
            await self._block(item, "Something broke while building it. Retry or skip it.")
        await self._finish_if_done(project.id)

    async def tick(self) -> None:
        """Move every autopilot project on by at most one step. Errors stay per project."""
        for project in await self._projects.autopilot_projects():
            try:
                await self._advance(project)
            except Exception:
                logger.exception("Backlog step failed for project %s", project.id)

    async def _advance(self, project: Project) -> None:
        items = await self._projects.list_items(project.id)
        for item in items:
            if item.status == ItemStatus.WAITING_FOR_MERGE:
                await self._follow_pull_request(item)
            elif item.status == ItemStatus.IN_PROGRESS and item.run_id:
                await self._catch_up(item.run_id)
        items = await self._projects.list_items(project.id)
        if any(i.status in BUSY_ITEMS for i in items):
            return
        if not any(i.status == ItemStatus.TODO for i in items):
            await self._finish_if_done(project.id)
            return
        started = await self._projects.started_since(project.id, self._start_of_today())
        if started >= project.daily_limit:
            return
        await self.start_next(project.id)

    async def _released(
        self, project: Project, item: BacklogItem, delivery: dict[str, Any]
    ) -> None:
        kind = str(delivery.get("status", ""))
        if kind == "created" and delivery.get("repo_url"):
            await self._projects.update_project(
                project.id,
                {"repo": RepoSource(url=str(delivery["repo_url"])), "repo_owned": True},
            )
            await self._done(item, "")
        elif kind == "opened" and delivery.get("pull_request_url"):
            url = str(delivery["pull_request_url"])
            await self._projects.update_item(item.id, {"pull_request_url": url})
            if (
                project.repo_owned
                and self._prs
                and await self._prs.merge_pull_request(url, item.title)
            ):
                await self._done(item, "")
            else:
                note = (
                    "Couldn't merge the pull request; merge it on GitHub to continue."
                    if project.repo_owned
                    else "Merge the pull request on GitHub to continue."
                )
                await self._projects.update_item(
                    item.id, {"status": ItemStatus.WAITING_FOR_MERGE, "note": note}
                )
        elif kind == "no_changes":
            await self._done(item, "No changes were needed.")
        else:  # skipped (no GitHub token) or nothing recorded: the work isn't saved anywhere
            await self._block(item, str(delivery.get("reason") or "") + " " + NO_REPO)
            await self._projects.update_project(
                project.id, {"status": ProjectStatus.PAUSED, "error": NO_REPO}
            )

    async def _catch_up(self, run_id: str) -> None:
        """If the worker's report was missed, the run's own status still moves the item on."""
        run = await self._runs.get(run_id)
        if run.status in FINAL:
            await self.on_run_finished(run_id, run.status, run.delivery)

    async def _follow_pull_request(self, item: BacklogItem) -> None:
        if not (self._prs and item.pull_request_url):
            return
        state = await self._prs.pull_request_state(item.pull_request_url)
        if state == "merged":
            await self._done(item, "")
        elif state == "closed":
            await self._block(item, "The pull request was closed without merging.")

    async def _done(self, item: BacklogItem, note: str) -> None:
        await self._projects.update_item(
            item.id, {"status": ItemStatus.DONE, "note": note, "done_at": self._clock()}
        )

    async def _block(self, item: BacklogItem, note: str) -> None:
        await self._projects.update_item(
            item.id, {"status": ItemStatus.BLOCKED, "note": note.strip()}
        )

    async def _finish_if_done(self, project_id: str) -> None:
        items = await self._projects.list_items(project_id)
        finished = (ItemStatus.DONE, ItemStatus.SKIPPED)
        if items and all(i.status in finished for i in items):
            await self._projects.update_project(project_id, {"status": ProjectStatus.DONE})

    def _start_of_today(self) -> datetime:
        today = self._clock().astimezone(self._zone).date()
        return datetime.combine(today, time(0), self._zone)


def item_request(project: Project, item: BacklogItem, items: list[BacklogItem]) -> str:
    """What the team is asked for one backlog item: the item, in the context of the project."""
    position = [i.id for i in items].index(item.id) + 1
    done = [i.title for i in items if i.status == ItemStatus.DONE]
    parts = [
        f"{item.title}",
        item.description,
        "Done when:\n" + "\n".join(f"- {c}" for c in item.acceptance) if item.acceptance else "",
        f"This is item {position} of {len(items)} in the backlog of the project "
        f"“{project.name}”. The project's goal: {project.goal}",
        "Already built in this project (keep it working, and its tests passing): " + "; ".join(done)
        if done
        else "",
    ]
    text = "\n\n".join(p for p in parts if p.strip())
    return text if len(text) <= MAX_REQUEST else text[: MAX_REQUEST - 3] + "..."
