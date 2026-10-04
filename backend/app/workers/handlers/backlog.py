"""The backlog in the worker: the PM's planning job, and the once-a-minute step that moves
autopilot projects on (see app/features/projects/progress.py)."""

from collections.abc import Awaitable, Callable
from typing import Any

from app.features.jobs.exceptions import PermanentJobError
from app.features.projects.interfaces import ProjectRepository
from app.features.projects.planner import BacklogPlanner
from app.features.projects.progress import BacklogProgress
from app.features.projects.schemas import ProjectStatus


class PlanBacklog:
    def __init__(self, planner: BacklogPlanner, projects: ProjectRepository) -> None:
        self._planner = planner
        self._projects = projects

    async def run(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        project_id = str(payload.get("project_id", ""))
        if not await self._projects.get_project(project_id):
            raise PermanentJobError(f"Unknown project in job payload: {payload}")
        return {"project_id": project_id, "items": await self._planner.plan(project_id)}

    async def give_up(self, payload: dict[str, Any], error: str) -> None:
        project_id = str(payload.get("project_id", ""))
        if await self._projects.get_project(project_id):
            await self._projects.update_project(
                project_id,
                {
                    "status": ProjectStatus.PAUSED,
                    "error": f"Mira couldn't plan the backlog: {error[:300]}. Ask her again.",
                },
            )


def backlog_schedule(progress: BacklogProgress) -> Callable[[], Awaitable[None]]:
    async def move_backlogs_on() -> None:
        await progress.tick()

    return move_backlogs_on
