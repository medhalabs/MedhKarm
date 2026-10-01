"""The standups API on a feature-only app, with an in-memory log instead of Postgres."""

from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import register_error_handlers
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.standups.dependencies import get_standup_service
from app.features.standups.router import router
from app.features.standups.service import StandupService

NOW = datetime(2026, 10, 1, 5, 0, tzinfo=UTC)


def client() -> TestClient:
    service = StandupService(InMemoryEventStore(), clock=lambda: NOW)
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router)
    app.dependency_overrides[get_standup_service] = lambda: service
    return TestClient(app)


def test_today_as_json_and_a_day_as_text() -> None:
    api = client()

    today = api.get("/standups/today")
    text = api.get("/standups/2026-10-01/text")
    future = api.get("/standups/2026-10-05")

    assert today.status_code == 200
    assert today.json()["day"] == "2026-10-01"
    assert text.text.startswith("Standup for Thu 01 Oct 2026")
    assert future.status_code == 400
    assert future.json()["error"]["code"] == "standup_day_in_future"
