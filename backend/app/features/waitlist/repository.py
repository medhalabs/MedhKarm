"""WaitlistRepository on Postgres."""

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.waitlist.models import WaitlistRow
from app.features.waitlist.schemas import JoinWaitlist, WaitlistEntry


class SqlWaitlistRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def add(self, entry: JoinWaitlist) -> bool:
        statement = (
            insert(WaitlistRow)
            .values(
                email=entry.email, name=entry.name, building=entry.building, source=entry.source
            )
            .on_conflict_do_nothing(index_elements=["email"])
            .returning(WaitlistRow.id)
        )
        async with self._sessions() as session, session.begin():
            return (await session.execute(statement)).first() is not None

    async def count(self) -> int:
        async with self._sessions() as session:
            return int((await session.scalar(select(func.count()).select_from(WaitlistRow))) or 0)

    async def all(self) -> list[WaitlistEntry]:
        async with self._sessions() as session:
            rows = (await session.scalars(select(WaitlistRow).order_by(WaitlistRow.id))).all()
            return [
                WaitlistEntry(
                    id=r.id,
                    email=r.email,
                    name=r.name,
                    building=r.building,
                    source=r.source,
                    created_at=r.created_at,
                    invited_at=r.invited_at,
                )
                for r in rows
            ]

    async def invite(self, email: str) -> bool:
        statement = (
            update(WaitlistRow)
            .where(WaitlistRow.email == email.strip().lower())
            .values(invited_at=func.now())
        )
        async with self._sessions() as session, session.begin():
            return (await session.execute(statement)).rowcount > 0  # type: ignore[attr-defined,no-any-return]
