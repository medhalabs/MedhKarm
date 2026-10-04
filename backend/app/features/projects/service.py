"""Projects and their backlog, as the founder edits them. Planning and the work itself happen in
workers: `planner.py` (the PM) and `progress.py` (items becoming runs)."""

import uuid

from app.features.jobs.interfaces import JobQueue
from app.features.projects.exceptions import (
    BacklogConflictError,
    ItemNotFoundError,
    ProjectNotFoundError,
)
from app.features.projects.interfaces import ProjectRepository
from app.features.projects.schemas import (
    OPEN_ITEMS,
    BacklogItem,
    ItemFields,
    ItemStatus,
    ItemUpdate,
    NewProject,
    Project,
    ProjectDetail,
    ProjectStatus,
    ProjectUpdate,
)

PLAN_JOB = "backlog.plan"
EDITABLE = (*OPEN_ITEMS, ItemStatus.BLOCKED)


class ProjectService:
    def __init__(self, projects: ProjectRepository, jobs: JobQueue) -> None:
        self._projects = projects
        self._jobs = jobs

    async def create(self, body: NewProject) -> ProjectDetail:
        project = await self._projects.create_project(
            uuid.uuid4().hex[:12],
            {
                "name": body.name,
                "goal": body.goal,
                "repo": body.repo,
                "test_command": body.test_command or "",
                "status": ProjectStatus.PLANNING,
                "autopilot": body.autopilot,
                "daily_limit": body.daily_limit,
            },
        )
        await self._queue_plan(project.id)
        return await self.get(project.id)

    async def get(self, project_id: str) -> ProjectDetail:
        project = await self._project(project_id)
        items = await self._projects.list_items(project_id)
        return ProjectDetail(**project.model_dump(), items=items)

    async def list(self, limit: int = 50) -> list[Project]:
        return await self._projects.list_projects(min(max(limit, 1), 200))

    async def update(self, project_id: str, body: ProjectUpdate) -> ProjectDetail:
        await self._project(project_id)
        values = body.model_dump(exclude_unset=True)
        if values:
            await self._projects.update_project(project_id, values)
        return await self.get(project_id)

    async def replan(self, project_id: str) -> ProjectDetail:
        """Ask the PM again: the items not started yet are replaced by a new proposal."""
        project = await self._project(project_id)
        if project.status == ProjectStatus.PLANNING:
            raise BacklogConflictError("The PM is already planning this project")
        await self._projects.update_project(project_id, {"status": ProjectStatus.PLANNING})
        await self._queue_plan(project_id)
        return await self.get(project_id)

    async def approve_plan(self, project_id: str) -> ProjectDetail:
        project = await self._project(project_id)
        if project.status != ProjectStatus.PLAN_READY:
            raise BacklogConflictError(f"There's no plan waiting for approval ({project.status})")
        items = await self._projects.list_items(project_id)
        for item in items:
            if item.status == ItemStatus.PROPOSED:
                await self._projects.update_item(item.id, {"status": ItemStatus.TODO})
        await self._projects.update_project(
            project_id, {"status": ProjectStatus.ACTIVE, "error": ""}
        )
        return await self.get(project_id)

    async def pause(self, project_id: str) -> ProjectDetail:
        await self._project(project_id)
        await self._projects.update_project(project_id, {"status": ProjectStatus.PAUSED})
        return await self.get(project_id)

    async def resume(self, project_id: str) -> ProjectDetail:
        project = await self._project(project_id)
        if project.status != ProjectStatus.PAUSED:
            raise BacklogConflictError(f"The project isn't paused ({project.status})")
        await self._projects.update_project(
            project_id, {"status": ProjectStatus.ACTIVE, "error": ""}
        )
        return await self.get(project_id)

    async def add_item(self, project_id: str, fields: ItemFields) -> BacklogItem:
        project = await self._project(project_id)
        status = (
            ItemStatus.PROPOSED
            if project.status in (ProjectStatus.PLANNING, ProjectStatus.PLAN_READY)
            else ItemStatus.TODO
        )
        item = await self._projects.add_item(project_id, fields, status)
        if project.status == ProjectStatus.DONE:  # new work for a finished project
            await self._projects.update_project(project_id, {"status": ProjectStatus.ACTIVE})
        return item

    async def update_item(self, project_id: str, item_id: str, body: ItemUpdate) -> BacklogItem:
        item = await self._item(project_id, item_id)
        values = body.model_dump(exclude_unset=True, exclude={"position"}, mode="json")
        if values and item.status not in EDITABLE:
            raise BacklogConflictError(f"Items that are {item.status} can't be edited")
        if values:
            item = await self._projects.update_item(item_id, values)
        if body.position is not None:
            order = [i.id for i in await self._projects.list_items(project_id) if i.id != item_id]
            order.insert(min(body.position, len(order) + 1) - 1, item_id)
            await self._projects.reorder(project_id, order)
            item = await self._item(project_id, item_id)
        return item

    async def delete_item(self, project_id: str, item_id: str) -> None:
        item = await self._item(project_id, item_id)
        if item.status not in OPEN_ITEMS:
            raise BacklogConflictError("Only items that haven't started can be deleted; skip it")
        await self._projects.delete_item(item_id)
        await self._projects.reorder(
            project_id, [i.id for i in await self._projects.list_items(project_id)]
        )

    async def skip_item(self, project_id: str, item_id: str) -> BacklogItem:
        item = await self._item(project_id, item_id)
        if item.status not in EDITABLE:
            raise BacklogConflictError(f"Items that are {item.status} can't be skipped")
        return await self._projects.update_item(item_id, {"status": ItemStatus.SKIPPED})

    async def retry_item(self, project_id: str, item_id: str) -> BacklogItem:
        item = await self._item(project_id, item_id)
        if item.status != ItemStatus.BLOCKED:
            raise BacklogConflictError("Only blocked items can be retried")
        return await self._projects.update_item(item_id, {"status": ItemStatus.TODO, "note": ""})

    async def _queue_plan(self, project_id: str) -> None:
        await self._jobs.enqueue(PLAN_JOB, {"project_id": project_id}, max_attempts=3)

    async def _project(self, project_id: str) -> Project:
        project = await self._projects.get_project(project_id)
        if project is None:
            raise ProjectNotFoundError(f"No project {project_id}")
        return project

    async def _item(self, project_id: str, item_id: str) -> BacklogItem:
        item = await self._projects.get_item(item_id)
        if item is None or item.project_id != project_id:
            raise ItemNotFoundError(f"No backlog item {item_id} in project {project_id}")
        return item
