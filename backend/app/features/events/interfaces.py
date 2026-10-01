from datetime import datetime
from typing import Protocol

from app.features.events.schemas import Event, NewEvent, RunTotals


class EventStore(Protocol):
    """Where events are kept. Append and read only: events are never changed or removed."""

    async def append(self, events: list[NewEvent]) -> list[Event]: ...

    async def list_for_run(
        self, run_id: str, after_id: int = 0, limit: int = 500
    ) -> list[Event]: ...

    async def totals_for_run(self, run_id: str) -> RunTotals: ...

    async def run_ids_between(self, since: datetime, until: datetime) -> list[str]:
        """Runs with at least one event in [since, until)."""
        ...

    async def latest_per_run(self, until: datetime) -> list[Event]:
        """The last event of every run, counting only events before `until`."""
        ...
