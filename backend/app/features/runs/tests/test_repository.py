"""Runs against the local Postgres. Skipped by default; run with `uv run pytest -m integration`."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.features.runs.repository import SqlRunRepository
from app.features.runs.schemas import RunStatus

pytestmark = pytest.mark.integration


async def test_create_update_and_transition() -> None:
    repo = SqlRunRepository(async_sessionmaker(create_async_engine(get_settings().database_url)))
    run_id = f"test-{uuid.uuid4().hex[:8]}"

    run = await repo.create(run_id, "Build it", "pytest")
    await repo.set_status(run_id, RunStatus.WAITING_FOR_APPROVAL, gate={"question": "Ship?"})

    assert run.status == RunStatus.QUEUED
    assert (await repo.get(run_id)).gate == {"question": "Ship?"}  # type: ignore[union-attr]
    assert await repo.transition(run_id, RunStatus.WAITING_FOR_APPROVAL, RunStatus.QUEUED)
    assert not await repo.transition(run_id, RunStatus.WAITING_FOR_APPROVAL, RunStatus.QUEUED)
    assert run_id in [r.id for r in await repo.list()]
