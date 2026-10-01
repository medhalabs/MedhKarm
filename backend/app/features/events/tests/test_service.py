import json
from datetime import UTC, datetime, timedelta

from app.features.events.schemas import Actor, EventType, NewEvent
from app.features.events.service import EventService, RunRecorder
from app.features.events.stores.memory_store import InMemoryEventStore


async def test_recorder_records_against_its_run() -> None:
    store = InMemoryEventStore()

    await RunRecorder(store, "run-1").record(
        Actor.DEVELOPER, EventType.MODEL_USED, "Thought", {"step": 1}, tokens=120
    )

    [event] = store.events
    assert (event.run_id, event.actor, event.type, event.tokens) == (
        "run-1",
        Actor.DEVELOPER,
        EventType.MODEL_USED,
        120,
    )


async def test_recorder_without_store_does_nothing() -> None:
    await RunRecorder(None, "run-1").record(Actor.SYSTEM, EventType.RUN_FINISHED, "Done")


async def test_recording_failures_never_break_the_run() -> None:
    class BrokenStore(InMemoryEventStore):
        async def append(self, events: list[NewEvent]):  # type: ignore[no-untyped-def]
            raise RuntimeError("database down")

    await RunRecorder(BrokenStore(), "run-1").record(Actor.SYSTEM, EventType.RUN_STARTED, "Hi")


async def test_list_after_id_and_totals() -> None:
    store = InMemoryEventStore()
    recorder = RunRecorder(store, "run-1")
    for i in range(3):
        await recorder.record(Actor.DEVELOPER, EventType.MODEL_USED, f"Step {i}", tokens=10)
    await RunRecorder(store, "other").record(Actor.SYSTEM, EventType.RUN_STARTED, "Other run")
    service = EventService(store)

    assert [e.summary for e in await service.list_for_run("run-1", after_id=1)] == [
        "Step 1",
        "Step 2",
    ]
    totals = await service.totals_for_run("run-1")
    assert (totals.events, totals.tokens) == (3, 30)


async def test_stream_sends_events_and_stops_after_run_finished() -> None:
    store = InMemoryEventStore()
    recorder = RunRecorder(store, "run-1")
    await recorder.record(Actor.FOUNDER, EventType.RUN_STARTED, "Asked for an app")
    await recorder.record(Actor.SYSTEM, EventType.RUN_FINISHED, "Released")

    chunks = [chunk async for chunk in EventService(store, poll_seconds=0).stream("run-1")]

    assert len(chunks) == 2
    assert chunks[0].startswith("id: 1\nevent: run.started\n")
    assert json.loads(chunks[1].split("data: ", 1)[1])["summary"] == "Released"


async def test_stream_gives_up_when_idle() -> None:
    service = EventService(InMemoryEventStore(), poll_seconds=0.01)

    chunks = [c async for c in service.stream("quiet-run", max_idle_seconds=0.03)]

    assert chunks and all(c == ": keep-alive\n\n" for c in chunks)


async def test_memory_store_window_queries() -> None:
    store = InMemoryEventStore()
    store.now = datetime(2026, 10, 1, tzinfo=UTC)
    await RunRecorder(store, "old").record(Actor.SYSTEM, EventType.RUN_STARTED, "a")
    store.now += timedelta(days=1)
    await RunRecorder(store, "new").record(Actor.SYSTEM, EventType.RUN_STARTED, "b")
    await RunRecorder(store, "old").record(Actor.SYSTEM, EventType.RUN_FINISHED, "c")

    assert await store.run_ids_between(store.now, store.now + timedelta(hours=1)) == ["new", "old"]
    latest = await store.latest_per_run(store.now)  # before the second day's events
    assert [(e.run_id, e.summary) for e in latest] == [("old", "a")]
