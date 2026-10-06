"""Runs against the local Postgres. Skipped by default; run with `uv run pytest -m integration`."""

import uuid

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.features.artifacts.models import ArtifactRow
from app.features.artifacts.repository import SqlArtifactRepository

pytestmark = pytest.mark.integration


async def test_a_video_goes_in_and_comes_out_byte_for_byte() -> None:
    sessions = async_sessionmaker(create_async_engine(get_settings().database_url))
    repo = SqlArtifactRepository(sessions)
    run_id = f"test-{uuid.uuid4().hex[:8]}"
    video = bytes(range(256)) * 40
    try:
        saved = await repo.add(run_id, "demo", "browser-test.webm", "video/webm", video)
        await repo.add(run_id, "other", "notes.txt", "text/plain", b"hi")

        assert [a.id for a in await repo.for_run(run_id, "demo")] == [saved.id]
        assert len(await repo.for_run(run_id)) == 2
        found = await repo.content(run_id, saved.id)
        assert found is not None and found.data == video and found.artifact.size == len(video)
        assert await repo.content("another-run", saved.id) is None
    finally:  # never leave test files in the development database
        async with sessions() as session, session.begin():
            await session.execute(delete(ArtifactRow).where(ArtifactRow.run_id == run_id))
