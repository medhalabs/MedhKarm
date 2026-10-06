"""ShareRepository on Postgres."""

import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.shares.models import ShareRow
from app.features.shares.schemas import Share


class SqlShareRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def create(self, token: str, run_id: str, company_id: str) -> Share:
        row = ShareRow(token=token, run_id=run_id, company_id=uuid.UUID(company_id))
        async with self._sessions() as session, session.begin():
            session.add(row)
        found = await self.by_token(token)
        assert found is not None
        return found

    async def for_run(self, run_id: str) -> Share | None:
        statement = select(ShareRow).where(ShareRow.run_id == run_id)
        async with self._sessions() as session:
            row = (await session.scalars(statement)).first()
            return _to_share(row) if row else None

    async def by_token(self, token: str) -> Share | None:
        async with self._sessions() as session:
            row = await session.get(ShareRow, token)
            return _to_share(row) if row else None

    async def delete_for_run(self, run_id: str) -> None:
        async with self._sessions() as session, session.begin():
            await session.execute(delete(ShareRow).where(ShareRow.run_id == run_id))

    async def count_view(self, token: str) -> None:
        statement = update(ShareRow).where(ShareRow.token == token).values(views=ShareRow.views + 1)
        async with self._sessions() as session, session.begin():
            await session.execute(statement)


def _to_share(row: ShareRow) -> Share:
    return Share(token=row.token, run_id=row.run_id, views=row.views, created_at=row.created_at)
