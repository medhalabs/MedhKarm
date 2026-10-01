"""Runs against the local Postgres (docker compose up -d, alembic upgrade head).
Skipped by default; run with `uv run pytest -m integration`."""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.features.events.schemas import Actor, EventType, NewEvent
from app.features.events.stores.sql_store import SqlEventStore

pytestmark = pytest.mark.integration


def make_store() -> tuple[SqlEventStore, async_sessionmaker]:  # type: ignore[type-arg]
    engine = create_async_engine(get_settings().database_url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    return SqlEventStore(sessions), sessions


async def test_append_list_and_totals() -> None:
    store, _ = make_store()
    run_id = f"test-{uuid.uuid4().hex[:8]}"

    first, second = await store.append(
        [
            NewEvent(run_id=run_id, actor=Actor.FOUNDER, type=EventType.RUN_STARTED, summary="Go"),
            NewEvent(
                run_id=run_id,
                actor=Actor.DEVELOPER,
                type=EventType.MODEL_USED,
                summary="Thought",
                data={"step": 1},
                tokens=250,
            ),
        ]
    )

    assert second.id > first.id
    assert [e.summary for e in await store.list_for_run(run_id)] == ["Go", "Thought"]
    assert [e.id for e in await store.list_for_run(run_id, after_id=first.id)] == [second.id]
    assert (await store.list_for_run(run_id))[1].data == {"step": 1}
    totals = await store.totals_for_run(run_id)
    assert (totals.events, totals.tokens) == (2, 250)


async def test_database_refuses_updates_and_deletes() -> None:
    store, sessions = make_store()
    run_id = f"test-{uuid.uuid4().hex[:8]}"
    [event] = await store.append(
        [NewEvent(run_id=run_id, actor=Actor.SYSTEM, type=EventType.RUN_STARTED, summary="x")]
    )

    for statement in (
        "UPDATE events SET summary = 'changed' WHERE id = :id",
        "DELETE FROM events WHERE id = :id",
    ):
        async with sessions() as session:
            with pytest.raises(DBAPIError, match="append-only"):
                await session.execute(text(statement), {"id": event.id})
