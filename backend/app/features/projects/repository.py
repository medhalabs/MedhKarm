"""ProjectRepository on Postgres."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.projects.models import BacklogItemRow, ProjectRow
from app.features.projects.schemas import (
    OPEN_ITEMS,
    BacklogItem,
    ItemFields,
    ItemStatus,
    Project,
    ProjectStatus,
    Size,
)
from app.features.repos.schemas import RepoSource
from app.features.starters.schemas import StackChoice


class SqlProjectRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def create_project(self, project_id: str, values: dict[str, Any]) -> Project:
        row = ProjectRow(id=project_id, **_project_values(values))
        async with self._sessions() as session, session.begin():
            session.add(row)
            await session.flush()
            await session.refresh(row)
            return _to_project(row)

    async def get_project(self, project_id: str) -> Project | None:
        async with self._sessions() as session:
            row = await session.get(ProjectRow, project_id)
            return _to_project(row) if row else None

    async def adopt_unowned(self, company_id: str) -> int:
        statement = (
            update(ProjectRow)
            .where(ProjectRow.company_id.is_(None))
            .values(company_id=uuid.UUID(company_id))
            .returning(ProjectRow.id)
        )
        async with self._sessions() as session, session.begin():
            return len((await session.scalars(statement)).all())

    async def list_projects(self, limit: int = 50, company_id: str | None = None) -> list[Project]:
        query = select(ProjectRow).order_by(ProjectRow.created_at.desc()).limit(limit)
        if company_id:
            query = query.where(ProjectRow.company_id == uuid.UUID(company_id))
        async with self._sessions() as session:
            return [_to_project(r) for r in (await session.scalars(query)).all()]

    async def update_project(self, project_id: str, values: dict[str, Any]) -> Project:
        async with self._sessions() as session, session.begin():
            await session.execute(
                update(ProjectRow)
                .where(ProjectRow.id == project_id)
                .values(**_project_values(values), updated_at=func.now())
            )
            row = await session.get(ProjectRow, project_id, populate_existing=True)
            assert row is not None
            return _to_project(row)

    async def autopilot_projects(self) -> list[Project]:
        query = select(ProjectRow).where(
            ProjectRow.autopilot.is_(True), ProjectRow.status == ProjectStatus.ACTIVE
        )
        async with self._sessions() as session:
            return [_to_project(r) for r in (await session.scalars(query)).all()]

    async def list_items(self, project_id: str) -> list[BacklogItem]:
        async with self._sessions() as session:
            return await _items(session, project_id)

    async def get_item(self, item_id: str) -> BacklogItem | None:
        async with self._sessions() as session:
            row = await session.get(BacklogItemRow, item_id)
            return _to_item(row) if row else None

    async def item_for_run(self, run_id: str) -> BacklogItem | None:
        query = select(BacklogItemRow).where(BacklogItemRow.run_id == run_id)
        async with self._sessions() as session:
            row = (await session.scalars(query)).first()
            return _to_item(row) if row else None

    async def replace_open_items(
        self, project_id: str, items: list[ItemFields], status: ItemStatus
    ) -> list[BacklogItem]:
        async with self._sessions() as session, session.begin():
            await session.execute(
                delete(BacklogItemRow).where(
                    BacklogItemRow.project_id == project_id,
                    BacklogItemRow.status.in_(list(OPEN_ITEMS)),
                )
            )
            kept = await _items(session, project_id)
            for i, kept_item in enumerate(kept, 1):
                await session.execute(
                    update(BacklogItemRow)
                    .where(BacklogItemRow.id == kept_item.id)
                    .values(position=i)
                )
            for i, item in enumerate(items, len(kept) + 1):
                session.add(_new_row(project_id, item, status, i))
            await session.flush()
            return await _items(session, project_id)

    async def add_item(self, project_id: str, item: ItemFields, status: ItemStatus) -> BacklogItem:
        async with self._sessions() as session, session.begin():
            last = await session.scalar(
                select(func.coalesce(func.max(BacklogItemRow.position), 0)).where(
                    BacklogItemRow.project_id == project_id
                )
            )
            row = _new_row(project_id, item, status, int(last or 0) + 1)
            session.add(row)
            await session.flush()
            await session.refresh(row)
            return _to_item(row)

    async def update_item(self, item_id: str, values: dict[str, Any]) -> BacklogItem:
        async with self._sessions() as session, session.begin():
            await session.execute(
                update(BacklogItemRow)
                .where(BacklogItemRow.id == item_id)
                .values(**values, updated_at=func.now())
            )
            row = await session.get(BacklogItemRow, item_id, populate_existing=True)
            assert row is not None
            return _to_item(row)

    async def delete_item(self, item_id: str) -> None:
        async with self._sessions() as session, session.begin():
            await session.execute(delete(BacklogItemRow).where(BacklogItemRow.id == item_id))

    async def reorder(self, project_id: str, item_ids: list[str]) -> None:
        async with self._sessions() as session, session.begin():
            for position, item_id in enumerate(item_ids, 1):
                await session.execute(
                    update(BacklogItemRow)
                    .where(BacklogItemRow.id == item_id, BacklogItemRow.project_id == project_id)
                    .values(position=position)
                )

    async def started_since(self, project_id: str, since: datetime) -> int:
        query = select(func.count(BacklogItemRow.id)).where(
            BacklogItemRow.project_id == project_id, BacklogItemRow.started_at >= since
        )
        async with self._sessions() as session:
            return int(await session.scalar(query) or 0)


async def _items(session: AsyncSession, project_id: str) -> list[BacklogItem]:
    query = (
        select(BacklogItemRow)
        .where(BacklogItemRow.project_id == project_id)
        .order_by(BacklogItemRow.position, BacklogItemRow.created_at)
    )
    return [_to_item(r) for r in (await session.scalars(query)).all()]


def _new_row(
    project_id: str, item: ItemFields, status: ItemStatus, position: int
) -> BacklogItemRow:
    return BacklogItemRow(
        id=uuid.uuid4().hex[:12],
        project_id=project_id,
        position=position,
        status=status,
        **item.model_dump(mode="json"),
    )


def _project_values(values: dict[str, Any]) -> dict[str, Any]:
    """Pydantic values as columns (the repository as JSON)."""
    out = dict(values)
    if "repo" in out:
        repo = out["repo"]
        out["repo"] = repo.model_dump() if isinstance(repo, RepoSource) else repo
    if out.get("company_id"):
        out["company_id"] = uuid.UUID(str(out["company_id"]))
    if isinstance(out.get("stack"), StackChoice):
        out["stack"] = out["stack"].model_dump(mode="json")
    return out


def _to_project(row: ProjectRow) -> Project:
    return Project(
        id=row.id,
        company_id=str(row.company_id) if row.company_id else None,
        name=row.name,
        goal=row.goal,
        repo=RepoSource.model_validate(row.repo) if row.repo else None,
        repo_owned=row.repo_owned,
        test_command=row.test_command,
        stack=StackChoice.model_validate(row.stack) if row.stack else None,
        status=ProjectStatus(row.status),
        autopilot=row.autopilot,
        daily_limit=row.daily_limit,
        questions=list(row.questions or []),
        error=row.error,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _to_item(row: BacklogItemRow) -> BacklogItem:
    return BacklogItem(
        id=row.id,
        project_id=row.project_id,
        position=row.position,
        title=row.title,
        description=row.description,
        acceptance=list(row.acceptance or []),
        size=Size(row.size),
        status=ItemStatus(row.status),
        run_id=row.run_id,
        attempts=row.attempts,
        note=row.note,
        pull_request_url=row.pull_request_url,
        started_at=row.started_at,
        done_at=row.done_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
