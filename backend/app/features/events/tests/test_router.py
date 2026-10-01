"""The events API on a feature-only app, with an in-memory store instead of Postgres."""

import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.features.events.dependencies import get_event_service
from app.features.events.router import router
from app.features.events.schemas import Actor, EventType
from app.features.events.service import EventService, RunRecorder
from app.features.events.stores.memory_store import InMemoryEventStore


def client_with_events() -> TestClient:
    store = InMemoryEventStore()
    recorder = RunRecorder(store, "run-1")

    async def seed() -> None:
        await recorder.record(Actor.FOUNDER, EventType.RUN_STARTED, "Asked for an app")
        await recorder.record(Actor.DEVELOPER, EventType.MODEL_USED, "Thought", tokens=500)
        await recorder.record(Actor.SYSTEM, EventType.RUN_FINISHED, "Released")

    asyncio.run(seed())
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_event_service] = lambda: EventService(store, poll_seconds=0)
    return TestClient(app)


def test_list_events_in_order() -> None:
    response = client_with_events().get("/runs/run-1/events")

    assert response.status_code == 200
    assert [e["type"] for e in response.json()] == ["run.started", "model.used", "run.finished"]


def test_list_after_id_and_limit() -> None:
    data = client_with_events().get("/runs/run-1/events", params={"after_id": 1, "limit": 1}).json()

    assert [e["id"] for e in data] == [2]


def test_totals() -> None:
    assert client_with_events().get("/runs/run-1/events/totals").json() == {
        "run_id": "run-1",
        "events": 3,
        "tokens": 500,
    }


def test_stream_is_server_sent_events() -> None:
    with client_with_events().stream("GET", "/runs/run-1/events/stream") as response:
        body = "".join(response.iter_text())

    assert response.headers["content-type"].startswith("text/event-stream")
    assert body.count("event: ") == 3


def test_bad_query_is_422() -> None:
    assert client_with_events().get("/runs/run-1/events", params={"limit": 0}).status_code == 422
