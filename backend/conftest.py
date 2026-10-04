"""Integration tests get their own database, never the development one.

Tests marked `integration` run against `<your database>_test` (e.g. `medhkarm_test`): created
on first use on the same Postgres server and migrated to the latest version, then pointed to by
DATABASE_URL for the whole test session. Runs, jobs and events they write never show up on the
admin page or in standups. Set TEST_DATABASE_URL to use another database."""

import os
import subprocess
from pathlib import Path

import psycopg
import pytest
from psycopg import sql
from sqlalchemy.engine import make_url

from app.core.config import get_settings

BACKEND = Path(__file__).parent
_ready: dict[str, str] = {}


def test_database_url() -> str:
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        return explicit
    url = make_url(get_settings().database_url)
    return url.set(database=f"{url.database}_test").render_as_string(hide_password=False)


def _prepare(url: str) -> None:
    """Create the test database if it's missing, then migrate it."""
    target = make_url(url)
    admin = target.set(drivername="postgresql", database="postgres")
    with psycopg.connect(admin.render_as_string(hide_password=False), autocommit=True) as conn:
        exists = conn.execute(
            "select 1 from pg_database where datname = %s", (target.database,)
        ).fetchone()
        if not exists:
            conn.execute(sql.SQL("create database {}").format(sql.Identifier(target.database)))
    subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=BACKEND,
        env={**os.environ, "DATABASE_URL": url},
        check=True,
        capture_output=True,
    )


@pytest.fixture(autouse=True)
def _integration_database(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    if request.node.get_closest_marker("integration") is None:
        return
    if "url" not in _ready:
        _ready["url"] = test_database_url()
        _prepare(_ready["url"])
    monkeypatch.setenv("DATABASE_URL", _ready["url"])
    get_settings.cache_clear()
    request.addfinalizer(get_settings.cache_clear)
