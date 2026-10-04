"""UserRepository on Postgres."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.auth.models import UserRow
from app.features.auth.schemas import StoredUser


class SqlUserRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def create(
        self, email: str, name: str, password_hash: str, company_id: str
    ) -> StoredUser:
        row = UserRow(
            id=uuid.uuid4(),
            company_id=uuid.UUID(company_id),
            email=email,
            name=name,
            password_hash=password_hash,
        )
        async with self._sessions() as session, session.begin():
            session.add(row)
            await session.flush()
            await session.refresh(row)
            return _to_user(row)

    async def by_email(self, email: str) -> StoredUser | None:
        async with self._sessions() as session:
            row = await session.scalar(select(UserRow).where(UserRow.email == email))
            return _to_user(row) if row else None

    async def get(self, user_id: str) -> StoredUser | None:
        try:
            key = uuid.UUID(user_id)
        except ValueError:
            return None
        async with self._sessions() as session:
            row = await session.get(UserRow, key)
            return _to_user(row) if row else None


def _to_user(row: UserRow) -> StoredUser:
    return StoredUser(
        id=str(row.id),
        email=row.email,
        name=row.name,
        company_id=str(row.company_id),
        password_hash=row.password_hash,
        created_at=row.created_at,
    )
