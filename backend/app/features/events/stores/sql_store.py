"""EventStore on Postgres. One short transaction per call: safe from the API and workers alike."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.events.models import EventRow
from app.features.events.schemas import Actor, Event, EventType, NewEvent, RunTotals


class SqlEventStore:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def append(self, events: list[NewEvent]) -> list[Event]:
        rows = [EventRow(**event.model_dump(mode="json")) for event in events]
        async with self._sessions() as session, session.begin():
            session.add_all(rows)
            await session.flush()
            for row in rows:
                await session.refresh(row)
        return [_to_event(row) for row in rows]

    async def list_for_run(self, run_id: str, after_id: int = 0, limit: int = 500) -> list[Event]:
        query = (
            select(EventRow)
            .where(EventRow.run_id == run_id, EventRow.id > after_id)
            .order_by(EventRow.id)
            .limit(limit)
        )
        async with self._sessions() as session:
            rows = (await session.scalars(query)).all()
        return [_to_event(row) for row in rows]

    async def totals_for_run(self, run_id: str) -> RunTotals:
        query = select(func.count(EventRow.id), func.coalesce(func.sum(EventRow.tokens), 0)).where(
            EventRow.run_id == run_id
        )
        async with self._sessions() as session:
            count, tokens = (await session.execute(query)).one()
        return RunTotals(run_id=run_id, events=int(count), tokens=int(tokens))


def _to_event(row: EventRow) -> Event:
    return Event(
        id=row.id,
        occurred_at=row.occurred_at,
        run_id=row.run_id,
        actor=Actor(row.actor),
        type=EventType(row.type),
        summary=row.summary,
        data=row.data,
        tokens=row.tokens,
    )
