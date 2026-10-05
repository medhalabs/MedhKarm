from datetime import datetime
from typing import Any, Protocol

from app.features.projects.schemas import BacklogItem, ItemFields, ItemStatus, Project
from app.features.runs.schemas import Run, StartRun


class ProjectRepository(Protocol):
    async def create_project(self, project_id: str, values: dict[str, Any]) -> Project: ...

    async def get_project(self, project_id: str) -> Project | None: ...

    async def adopt_unowned(self, company_id: str) -> int:
        """Gives projects without a company to this one; how many."""
        ...

    async def list_projects(self, limit: int = 50, company_id: str | None = None) -> list[Project]:
        """Newest first."""
        ...

    async def update_project(self, project_id: str, values: dict[str, Any]) -> Project: ...

    async def autopilot_projects(self) -> list[Project]:
        """Active projects on autopilot: the ones the scheduler looks at."""
        ...

    async def list_items(self, project_id: str) -> list[BacklogItem]:
        """In backlog order."""
        ...

    async def get_item(self, item_id: str) -> BacklogItem | None: ...

    async def item_for_run(self, run_id: str) -> BacklogItem | None: ...

    async def replace_open_items(
        self, project_id: str, items: list[ItemFields], status: ItemStatus
    ) -> list[BacklogItem]:
        """Drop the not-yet-started items (proposed and to-do) and add `items` after the
        others, in order. Returns the whole backlog."""
        ...

    async def add_item(self, project_id: str, item: ItemFields, status: ItemStatus) -> BacklogItem:
        """At the end of the backlog."""
        ...

    async def update_item(self, item_id: str, values: dict[str, Any]) -> BacklogItem: ...

    async def delete_item(self, item_id: str) -> None: ...

    async def reorder(self, project_id: str, item_ids: list[str]) -> None:
        """Positions 1..n in this order."""
        ...

    async def started_since(self, project_id: str, since: datetime) -> int:
        """Items whose work started at or after `since` (for the daily limit)."""
        ...


class RunStarter(Protocol):
    """What the backlog needs from runs (RunService satisfies it)."""

    async def start(self, body: StartRun, company_id: str | None = None) -> Run: ...

    async def get(self, run_id: str) -> Run: ...


class PullRequests(Protocol):
    """Following a pull request after its release (GitHubRepoHost satisfies it)."""

    async def pull_request_state(self, url: str) -> str:
        """ "open", "merged" or "closed"."""
        ...

    async def merge_pull_request(self, url: str, title: str) -> bool:
        """Merge it; False if GitHub refused (conflicts, checks, permissions)."""
        ...


class ProjectNotes(Protocol):
    """The founder's messages to the PM about a project, oldest first (messages feature)."""

    async def for_project(self, project_id: str) -> list[str]: ...
