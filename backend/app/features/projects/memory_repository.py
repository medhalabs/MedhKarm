"""ProjectRepository in memory, for tests."""

import uuid
from datetime import UTC, datetime
from typing import Any

from app.features.projects.schemas import (
    OPEN_ITEMS,
    BacklogItem,
    ItemFields,
    ItemStatus,
    Project,
    ProjectStatus,
)


class InMemoryProjectRepository:
    def __init__(self) -> None:
        self.projects: dict[str, Project] = {}
        self.items: dict[str, BacklogItem] = {}

    async def create_project(self, project_id: str, values: dict[str, Any]) -> Project:
        now = datetime.now(UTC)
        project = Project(id=project_id, created_at=now, updated_at=now, **values)
        self.projects[project_id] = project
        return project.model_copy()

    async def get_project(self, project_id: str) -> Project | None:
        project = self.projects.get(project_id)
        return project.model_copy() if project else None

    async def adopt_unowned(self, company_id: str) -> int:
        unowned = [p for p in self.projects.values() if p.company_id is None]
        for project in unowned:
            project.company_id = company_id
        return len(unowned)

    async def list_projects(self, limit: int = 50, company_id: str | None = None) -> list[Project]:
        mine = [p for p in self.projects.values() if not company_id or p.company_id == company_id]
        newest = sorted(mine, key=lambda p: p.created_at, reverse=True)
        return [p.model_copy() for p in newest[:limit]]

    async def update_project(self, project_id: str, values: dict[str, Any]) -> Project:
        project = self.projects[project_id].model_copy(
            update={**values, "updated_at": datetime.now(UTC)}
        )
        self.projects[project_id] = Project.model_validate(project.model_dump())
        return self.projects[project_id].model_copy()

    async def autopilot_projects(self) -> list[Project]:
        return [
            p.model_copy()
            for p in self.projects.values()
            if p.autopilot and p.status == ProjectStatus.ACTIVE
        ]

    async def list_items(self, project_id: str) -> list[BacklogItem]:
        found = [i for i in self.items.values() if i.project_id == project_id]
        return [i.model_copy() for i in sorted(found, key=lambda i: (i.position, i.created_at))]

    async def get_item(self, item_id: str) -> BacklogItem | None:
        item = self.items.get(item_id)
        return item.model_copy() if item else None

    async def item_for_run(self, run_id: str) -> BacklogItem | None:
        item = next((i for i in self.items.values() if i.run_id == run_id), None)
        return item.model_copy() if item else None

    async def replace_open_items(
        self, project_id: str, items: list[ItemFields], status: ItemStatus
    ) -> list[BacklogItem]:
        for existing in await self.list_items(project_id):
            if existing.status in OPEN_ITEMS:
                del self.items[existing.id]
        kept = await self.list_items(project_id)
        for i, kept_item in enumerate(kept, 1):
            self.items[kept_item.id].position = i
        for fields in items:
            await self.add_item(project_id, fields, status)
        return await self.list_items(project_id)

    async def add_item(self, project_id: str, item: ItemFields, status: ItemStatus) -> BacklogItem:
        now = datetime.now(UTC)
        position = len([i for i in self.items.values() if i.project_id == project_id]) + 1
        new = BacklogItem(
            id=uuid.uuid4().hex[:12],
            project_id=project_id,
            position=position,
            status=status,
            created_at=now,
            updated_at=now,
            **item.model_dump(),
        )
        self.items[new.id] = new
        return new.model_copy()

    async def update_item(self, item_id: str, values: dict[str, Any]) -> BacklogItem:
        updated = self.items[item_id].model_copy(update={**values, "updated_at": datetime.now(UTC)})
        self.items[item_id] = BacklogItem.model_validate(updated.model_dump())
        return self.items[item_id].model_copy()

    async def delete_item(self, item_id: str) -> None:
        self.items.pop(item_id, None)

    async def reorder(self, project_id: str, item_ids: list[str]) -> None:
        for position, item_id in enumerate(item_ids, 1):
            if item_id in self.items and self.items[item_id].project_id == project_id:
                self.items[item_id].position = position

    async def started_since(self, project_id: str, since: datetime) -> int:
        return sum(
            1
            for i in self.items.values()
            if i.project_id == project_id and i.started_at is not None and i.started_at >= since
        )
