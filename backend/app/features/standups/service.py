"""Works out the standup window for a day, gathers the runs it covers and builds the standup."""

from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.features.events.schemas import Event, EventType
from app.features.standups.builder import build_standup
from app.features.standups.exceptions import StandupDayInFutureError
from app.features.standups.interfaces import ActivityLog
from app.features.standups.schemas import Standup

PAGE = 1000


class StandupService:
    def __init__(
        self,
        log: ActivityLog,
        timezone: str = "Asia/Kolkata",
        hour: int = 9,
        stall_after: timedelta = timedelta(hours=2),
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._log = log
        self._timezone = timezone
        self._zone = ZoneInfo(timezone)
        self._hour = hour
        self._stall_after = stall_after
        self._clock = clock

    def today(self) -> date:
        return self._clock().astimezone(self._zone).date()

    def due_day(self) -> date | None:
        """Today, once it's past the standup hour (when today's standup should go out)."""
        now = self._clock().astimezone(self._zone)
        return now.date() if now.hour >= self._hour else None

    def window(self, day: date) -> tuple[datetime, datetime]:
        """The 24 hours up to `hour` on `day`, local time; cut off at now for today."""
        end = datetime.combine(day, time(self._hour), self._zone)
        since = end - timedelta(days=1)
        now = self._clock()
        if since >= now:
            raise StandupDayInFutureError(f"No standup for {day} yet")
        return since, min(end, now)

    async def for_day(self, day: date | None = None) -> Standup:
        day = day or self.today()
        since, until = self.window(day)
        histories = {
            run_id: await self._history(run_id, until) for run_id in await self._runs(since, until)
        }
        return build_standup(histories, day, self._timezone, since, until, self._stall_after)

    async def _runs(self, since: datetime, until: datetime) -> list[str]:
        """Runs with activity in the window, plus runs still open at its end (waiting for
        approval, or stuck), however long ago they last moved."""
        active = await self._log.run_ids_between(since, until)
        still_open = [
            e.run_id
            for e in await self._log.latest_per_run(until)
            if e.type != EventType.RUN_FINISHED
        ]
        return list(dict.fromkeys([*active, *still_open]))

    async def _history(self, run_id: str, until: datetime) -> list[Event]:
        events: list[Event] = []
        while True:
            page = await self._log.list_for_run(run_id, events[-1].id if events else 0, PAGE)
            events += page
            if len(page) < PAGE:
                break
        return [e for e in events if e.occurred_at < until]
