"""Reading and writing the activity log.

Other features record events through `RunRecorder`, a small helper bound to one run, and read
them through `EventService`. Neither knows how events are stored.
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from app.features.events.interfaces import EventStore
from app.features.events.schemas import FINAL_TYPES, Actor, Event, EventType, NewEvent, RunTotals

logger = logging.getLogger(__name__)


class RunRecorder:
    """Records events for one run. A failure to record is logged, never raised: losing a log
    line must not break the customer's build."""

    def __init__(
        self, store: EventStore | None, run_id: str, context: dict[str, Any] | None = None
    ) -> None:
        self._store = store
        self.run_id = run_id
        self._context = context or {}

    def with_context(self, **context: Any) -> "RunRecorder":
        """A recorder that adds `context` (e.g. which team member, which task) to every event."""
        return RunRecorder(self._store, self.run_id, {**self._context, **context})

    async def record(
        self,
        actor: Actor,
        type: EventType,
        summary: str,
        data: dict[str, Any] | None = None,
        tokens: int = 0,
    ) -> None:
        if self._store is None:
            return
        event = NewEvent(
            run_id=self.run_id,
            actor=actor,
            type=type,
            summary=summary[:500],
            data={**self._context, **(data or {})},
            tokens=tokens,
        )
        try:
            await self._store.append([event])
        except Exception:
            logger.exception("Could not record event %s for run %s", type, self.run_id)


class EventService:
    def __init__(self, store: EventStore, poll_seconds: float = 1.0) -> None:
        self._store = store
        self._poll = poll_seconds

    async def list_for_run(self, run_id: str, after_id: int = 0, limit: int = 500) -> list[Event]:
        return await self._store.list_for_run(run_id, after_id, min(max(limit, 1), 1000))

    async def totals_for_run(self, run_id: str) -> RunTotals:
        return await self._store.totals_for_run(run_id)

    async def stream(
        self, run_id: str, after_id: int = 0, max_idle_seconds: float = 600
    ) -> AsyncIterator[str]:
        """Server-sent events: new events as they happen. Ends after the run finishes, or after
        `max_idle_seconds` without news. Polls the store, so it works with any number of workers."""
        last_id, idle = after_id, 0.0
        while idle < max_idle_seconds:
            events = await self._store.list_for_run(run_id, last_id)
            if events:
                idle = 0.0
                for event in events:
                    last_id = event.id
                    payload = json.dumps(event.model_dump(mode="json"))
                    yield f"id: {event.id}\nevent: {event.type}\ndata: {payload}\n\n"
                if any(event.type in FINAL_TYPES for event in events):
                    return
            else:
                yield ": keep-alive\n\n"
                await asyncio.sleep(self._poll)
                idle += self._poll
