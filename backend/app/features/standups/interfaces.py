from datetime import datetime
from typing import Protocol

from app.features.events.schemas import Event
from app.features.standups.schemas import Standup


class ActivityLog(Protocol):
    """The parts of the event log a standup reads. `EventStore` implementations satisfy it."""

    async def run_ids_between(self, since: datetime, until: datetime) -> list[str]: ...

    async def latest_per_run(self, until: datetime) -> list[Event]: ...

    async def list_for_run(
        self, run_id: str, after_id: int = 0, limit: int = 500
    ) -> list[Event]: ...


class StandupDelivery(Protocol):
    """Where a finished standup goes: the log today; email and WhatsApp in Phase 2."""

    async def send(self, standup: Standup, text: str) -> str:
        """Returns where it was sent, e.g. "log" or an email address."""
        ...
