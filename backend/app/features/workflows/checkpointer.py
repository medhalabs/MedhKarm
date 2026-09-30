"""Postgres checkpoint storage for LangGraph runs."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.config import Settings


@asynccontextmanager
async def postgres_checkpointer(settings: Settings) -> AsyncIterator[AsyncPostgresSaver]:
    """Open a checkpointer and make sure its tables exist (`setup()` is idempotent)."""
    async with AsyncPostgresSaver.from_conn_string(settings.psycopg_database_url) as saver:
        await saver.setup()
        yield saver
