from typing import Protocol

from app.features.events.schemas import Event, NewEvent, RunTotals


class EventStore(Protocol):
    """Where events are kept. Append and read only: events are never changed or removed."""

    async def append(self, events: list[NewEvent]) -> list[Event]: ...

    async def list_for_run(
        self, run_id: str, after_id: int = 0, limit: int = 500
    ) -> list[Event]: ...

    async def totals_for_run(self, run_id: str) -> RunTotals: ...
