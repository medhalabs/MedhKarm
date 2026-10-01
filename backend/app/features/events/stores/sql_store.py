"""EventStore on Postgres. One short transaction per call: safe from the API and workers alike."""

from datetime import datetime

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

    async def run_ids_between(self, since: datetime, until: datetime) -> list[str]:
        query = (
            select(EventRow.run_id)
            .where(EventRow.occurred_at >= since, EventRow.occurred_at < until)
            .group_by(EventRow.run_id)
            .order_by(func.min(EventRow.id))
        )
        async with self._sessions() as session:
            return list((await session.scalars(query)).all())

    async def latest_per_run(self, until: datetime) -> list[Event]:
        last_ids = (
            select(func.max(EventRow.id))
            .where(EventRow.occurred_at < until)
            .group_by(EventRow.run_id)
            .scalar_subquery()
        )
        query = select(EventRow).where(EventRow.id.in_(last_ids)).order_by(EventRow.id)
        async with self._sessions() as session:
            rows = (await session.scalars(query)).all()
        return [_to_event(row) for row in rows]


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
