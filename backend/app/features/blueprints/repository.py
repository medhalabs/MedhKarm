"""BlueprintRepository on Postgres."""

import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.blueprints.models import BlueprintRow
from app.features.blueprints.schemas import Blueprint, BlueprintStatus, Comment, Doc
from app.features.runs.schemas import StartRun


class SqlBlueprintRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def create(
        self, blueprint_id: str, company_id: str, title: str, brief: StartRun
    ) -> Blueprint:
        row = BlueprintRow(
            id=blueprint_id,
            company_id=uuid.UUID(company_id),
            title=title,
            brief=brief.model_dump(mode="json"),
            status=BlueprintStatus.WRITING,
        )
        async with self._sessions() as session, session.begin():
            session.add(row)
        return await self._get(blueprint_id)

    async def get(self, blueprint_id: str) -> Blueprint | None:
        async with self._sessions() as session:
            row = await session.get(BlueprintRow, blueprint_id)
            return _to_blueprint(row) if row else None

    async def for_company(self, company_id: str, limit: int = 50) -> list[Blueprint]:
        statement = (
            select(BlueprintRow)
            .where(BlueprintRow.company_id == uuid.UUID(company_id))
            .order_by(BlueprintRow.created_at.desc())
            .limit(limit)
        )
        async with self._sessions() as session:
            return [_to_blueprint(r) for r in (await session.scalars(statement)).all()]

    async def for_run(self, run_id: str) -> Blueprint | None:
        statement = select(BlueprintRow).where(BlueprintRow.run_id == run_id)
        async with self._sessions() as session:
            row = (await session.scalars(statement)).first()
            return _to_blueprint(row) if row else None

    async def update(
        self,
        blueprint_id: str,
        *,
        status: BlueprintStatus | None = None,
        docs: list[Doc] | None = None,
        comments: list[Comment] | None = None,
        progress: str | None = None,
        error: str | None = None,
        run_id: str | None = None,
        revision: int | None = None,
    ) -> Blueprint:
        values: dict[str, Any] = {}
        if status is not None:
            values["status"] = status
        if docs is not None:
            values["docs"] = [d.model_dump(mode="json") for d in docs]
        if comments is not None:
            values["comments"] = [c.model_dump(mode="json") for c in comments]
        if progress is not None:
            values["progress"] = progress
        if error is not None:
            values["error"] = error
        if run_id is not None:
            values["run_id"] = run_id
        if revision is not None:
            values["revision"] = revision
        async with self._sessions() as session, session.begin():
            if values:
                await session.execute(
                    update(BlueprintRow).where(BlueprintRow.id == blueprint_id).values(**values)
                )
        return await self._get(blueprint_id)

    async def transition(
        self, blueprint_id: str, expected: BlueprintStatus, new: BlueprintStatus
    ) -> bool:
        statement = (
            update(BlueprintRow)
            .where(BlueprintRow.id == blueprint_id, BlueprintRow.status == expected)
            .values(status=new)
        )
        async with self._sessions() as session, session.begin():
            return (await session.execute(statement)).rowcount == 1  # type: ignore[attr-defined,no-any-return]

    async def _get(self, blueprint_id: str) -> Blueprint:
        found = await self.get(blueprint_id)
        assert found is not None
        return found


def _to_blueprint(row: BlueprintRow) -> Blueprint:
    return Blueprint(
        id=row.id,
        company_id=str(row.company_id),
        title=row.title,
        brief=StartRun.model_validate(row.brief),
        status=BlueprintStatus(row.status),
        docs=[Doc.model_validate(d) for d in row.docs],
        comments=[Comment.model_validate(c) for c in row.comments],
        progress=row.progress,
        error=row.error,
        run_id=row.run_id,
        revision=row.revision,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
