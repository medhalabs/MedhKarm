"""Runs against the local Postgres (docker compose up -d, alembic upgrade head).
Skipped by default; run with `uv run pytest -m integration`.

Each test uses its own job kind and claims only that kind, so it never touches real jobs in
the development database, and deletes its jobs afterwards."""

import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import timedelta

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.features.jobs.models import JobRow
from app.features.jobs.schemas import JobStatus
from app.features.jobs.stores.sql_queue import SqlJobQueue

pytestmark = pytest.mark.integration
LEASE = timedelta(seconds=60)


@pytest.fixture
async def queue_and_kind() -> AsyncIterator[tuple[SqlJobQueue, str]]:
    sessions = async_sessionmaker(create_async_engine(get_settings().database_url))
    kind = f"test.{uuid.uuid4().hex[:12]}"
    yield SqlJobQueue(sessions), kind
    async with sessions() as session, session.begin():
        await session.execute(delete(JobRow).where(JobRow.kind == kind))


async def test_enqueue_claim_complete_and_unique_keys(
    queue_and_kind: tuple[SqlJobQueue, str],
) -> None:
    queue, kind = queue_and_kind
    key = f"{kind}:once"

    job = await queue.enqueue(kind, {"n": 1}, unique_key=key)
    assert job is not None
    assert await queue.enqueue(kind, {"n": 2}, unique_key=key) is None

    claimed = await queue.claim("w1", LEASE, [kind])
    assert claimed is not None
    assert (claimed.id, claimed.status, claimed.attempts) == (job.id, JobStatus.RUNNING, 1)
    assert await queue.extend(job.id, "w1", LEASE)
    assert not await queue.extend(job.id, "someone-else", LEASE)

    await queue.complete(job.id, {"ok": True})
    done = await queue.get(job.id)
    assert done is not None
    assert (done.status, done.result, done.locked_by) == (JobStatus.DONE, {"ok": True}, None)


async def test_workers_never_claim_the_same_job(queue_and_kind: tuple[SqlJobQueue, str]) -> None:
    queue, kind = queue_and_kind
    ids = set()
    for i in range(5):
        job = await queue.enqueue(kind, {"n": i})
        assert job is not None
        ids.add(job.id)

    claimed = await asyncio.gather(*(queue.claim(f"w{i}", LEASE, [kind]) for i in range(8)))

    got = [j.id for j in claimed if j]
    assert sorted(got) == sorted(ids)  # each job once; the extra workers got nothing


async def test_expired_leases_retry_and_release(queue_and_kind: tuple[SqlJobQueue, str]) -> None:
    queue, kind = queue_and_kind
    job = await queue.enqueue(kind, {})
    assert job is not None

    await queue.claim("w1", timedelta(seconds=-1), [kind])  # a lease that has already run out
    taken = await queue.claim("w2", LEASE, [kind])
    assert taken is not None and (taken.id, taken.attempts) == (job.id, 2)

    await queue.release(job.id)
    released = await queue.get(job.id)
    assert released is not None
    assert (released.status, released.attempts) == (JobStatus.QUEUED, 1)

    await queue.claim("w3", LEASE, [kind])
    await queue.fail(job.id, "boom", None)
    failed = await queue.get(job.id)
    assert failed is not None and (failed.status, failed.last_error) == (JobStatus.FAILED, "boom")
