"""EventStore in memory, for tests and for runs that don't need a database (evals)."""

from datetime import UTC, datetime

from app.features.events.schemas import Event, NewEvent, RunTotals


class InMemoryEventStore:
    def __init__(self) -> None:
        self.events: list[Event] = []

    async def append(self, events: list[NewEvent]) -> list[Event]:
        stored = [
            Event(**event.model_dump(), id=len(self.events) + i + 1, occurred_at=datetime.now(UTC))
            for i, event in enumerate(events)
        ]
        self.events.extend(stored)
        return stored

    async def list_for_run(self, run_id: str, after_id: int = 0, limit: int = 500) -> list[Event]:
        found = [e for e in self.events if e.run_id == run_id and e.id > after_id]
        return found[:limit]

    async def totals_for_run(self, run_id: str) -> RunTotals:
        found = [e for e in self.events if e.run_id == run_id]
        return RunTotals(run_id=run_id, events=len(found), tokens=sum(e.tokens for e in found))
