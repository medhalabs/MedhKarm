"""Runs against the local Postgres. Skipped by default; run with `uv run pytest -m integration`."""

import uuid

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.features.companies.models import CompanyRow
from app.features.model_settings.repository import SqlModelSettingsRepository
from app.features.model_settings.schemas import KeyMode, ModelChoices, Provider

pytestmark = pytest.mark.integration


async def test_choices_and_keys_round_trip() -> None:
    sessions = async_sessionmaker(create_async_engine(get_settings().database_url))
    company = uuid.uuid4()
    async with sessions() as session, session.begin():
        session.add(CompanyRow(id=company, name="Model settings test"))
    repo = SqlModelSettingsRepository(sessions)
    try:
        assert await repo.get(str(company)) is None
        await repo.set_key(str(company), Provider.GROQ, "sealed-1", "…1111")
        await repo.save_choices(
            str(company),
            ModelChoices(mode=KeyMode.OWN, role_models={"qa": "groq/openai/gpt-oss-20b"}),
        )
        await repo.set_key(str(company), Provider.ANTHROPIC, "sealed-2", "…2222")
        stored = await repo.set_key(str(company), Provider.GROQ, None, "")

        assert stored.mode == KeyMode.OWN
        assert stored.role_models == {"qa": "groq/openai/gpt-oss-20b"}
        assert stored.sealed_keys == {Provider.ANTHROPIC: "sealed-2"}
        assert stored.hints == {Provider.ANTHROPIC: "…2222"}
    finally:  # the company's settings go with it (ON DELETE CASCADE)
        async with sessions() as session, session.begin():
            await session.execute(delete(CompanyRow).where(CompanyRow.id == company))
