"""MessageRepository on Postgres."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.messages.models import MessageRow
from app.features.messages.schemas import Message, ThreadKind


class SqlMessageRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def add(
        self,
        company_id: str,
        thread: ThreadKind,
        thread_id: str,
        author: str,
        name: str,
        to: str,
        body: str,
    ) -> Message:
        row = MessageRow(
            company_id=uuid.UUID(company_id),
            thread=thread,
            thread_id=thread_id,
            author=author,
            name=name,
            to=to,
            body=body,
        )
        async with self._sessions() as session, session.begin():
            session.add(row)
            await session.flush()
            await session.refresh(row)
            return _to_message(row)

    async def get(self, message_id: int) -> Message | None:
        async with self._sessions() as session:
            row = await session.get(MessageRow, message_id)
            return _to_message(row) if row else None

    async def thread(self, thread: ThreadKind, thread_id: str, limit: int = 200) -> list[Message]:
        query = (
            select(MessageRow)
            .where(MessageRow.thread == thread, MessageRow.thread_id == thread_id)
            .order_by(MessageRow.id)
            .limit(limit)
        )
        async with self._sessions() as session:
            return [_to_message(r) for r in (await session.scalars(query)).all()]

    async def recent(self, company_id: str, limit: int = 20) -> list[Message]:
        query = (
            select(MessageRow)
            .where(MessageRow.company_id == uuid.UUID(company_id))
            .order_by(MessageRow.id.desc())
            .limit(limit)
        )
        async with self._sessions() as session:
            return [_to_message(r) for r in (await session.scalars(query)).all()]


def _to_message(row: MessageRow) -> Message:
    return Message(
        id=row.id,
        company_id=str(row.company_id),
        thread=ThreadKind(row.thread),
        thread_id=row.thread_id,
        author=row.author,
        name=row.name,
        to=row.to,
        body=row.body,
        created_at=row.created_at,
    )
