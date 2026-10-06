"""Share links. The founder turns one on for a build and gets a link anyone can open, with no
sign-in; turning it off ends the link. What the public sees is built here, from a whitelist:
the title, the team, the steps of the work (as the office replay needs them), the demo video
and a few facts. The request text, the founder's messages, model and tool activity, file
contents, repositories and the founder's feedback never leave."""

import secrets
from collections.abc import Callable
from datetime import datetime

from app.features.artifacts.schemas import Content
from app.features.events.schemas import Event, EventType
from app.features.runs.schemas import Run
from app.features.shares.exceptions import ShareNotFoundError
from app.features.shares.interfaces import (
    DemoReader,
    EventReader,
    Roster,
    RunReader,
    ShareRepository,
)
from app.features.shares.schemas import PublicEvent, PublicShare, PublicStats, Share

TITLE_LENGTH = 120
# Only these steps are shown. Model and tool activity, messages, the codebase map and GitHub
# delivery stay private.
SHOWN = frozenset(
    {
        EventType.RUN_STARTED,
        EventType.PROJECT_SCAFFOLDED,
        EventType.PLAN_CREATED,
        EventType.TASK_ASSIGNED,
        EventType.WORK_STARTED,
        EventType.WORK_FINISHED,
        EventType.REVIEW_FINISHED,
        EventType.CHECK_FINISHED,
        EventType.SECURITY_FINISHED,
        EventType.DEPLOY_FINISHED,
        EventType.DOCS_UPDATED,
        EventType.DEMO_RECORDED,
        EventType.APPROVAL_REQUESTED,
        EventType.APPROVAL_DECIDED,
        EventType.RUN_FINISHED,
    }
)
SAFE_DATA = ("member", "task_id", "approved", "status", "passed", "specialty")


class ShareService:
    def __init__(
        self,
        shares: ShareRepository,
        runs: RunReader,
        events: EventReader,
        demos: DemoReader,
        roster: Roster,
        new_token: Callable[[], str] = lambda: secrets.token_urlsafe(16),
    ) -> None:
        self._shares = shares
        self._runs = runs
        self._events = events
        self._demos = demos
        self._roster = roster
        self._new_token = new_token

    # The founder's side

    async def create(self, company_id: str, run_id: str) -> Share:
        """Turns the link on (the same link if it already is)."""
        await self._runs.owned(run_id, company_id)
        return await self._shares.for_run(run_id) or await self._shares.create(
            self._new_token(), run_id, company_id
        )

    async def get(self, company_id: str, run_id: str) -> Share | None:
        await self._runs.owned(run_id, company_id)
        return await self._shares.for_run(run_id)

    async def revoke(self, company_id: str, run_id: str) -> None:
        await self._runs.owned(run_id, company_id)
        await self._shares.delete_for_run(run_id)

    # The public side

    async def public(self, token: str) -> PublicShare:
        share = await self._share(token)
        run = await self._runs.get(share.run_id)
        events = await self._events.list_for_run(share.run_id, 0, 1000)
        await self._shares.count_view(token)
        title = title_of(run)
        shown = public_events(events, token, title)
        demos = await self._demos.list(share.run_id, "demo")
        return PublicShare(
            title=title,
            status=run.status,
            team=self._roster.members(),
            events=shown,
            stats=stats(events),
            has_demo=bool(demos),
            live_url=live_url(events),
        )

    async def demo(self, token: str) -> Content:
        """The demo video of a shared build."""
        share = await self._share(token)
        demos = await self._demos.list(share.run_id, "demo")
        if not demos:
            raise ShareNotFoundError("This build has no demo video")
        return await self._demos.content(share.run_id, demos[0].id)

    async def _share(self, token: str) -> Share:
        share = await self._shares.by_token(token)
        if share is None:
            raise ShareNotFoundError("This link doesn't exist, or the owner turned it off")
        return share


def title_of(run: Run) -> str:
    """The first line of the request: all the public sees of it."""
    line = next((ln.strip() for ln in run.request.splitlines() if ln.strip()), "A build")
    line = line.lstrip("#> ").replace("**", "").replace("`", "")
    return line if len(line) <= TITLE_LENGTH else line[: TITLE_LENGTH - 1].rstrip() + "…"


def public_events(events: list[Event], token: str, title: str) -> list[PublicEvent]:
    """The whitelisted steps, with text and data that are safe to show anyone."""
    shown: list[PublicEvent] = []
    for event in events:
        if event.type not in SHOWN:
            continue
        data = {k: event.data[k] for k in SAFE_DATA if k in event.data}
        if event.type == EventType.PLAN_CREATED:
            tasks = event.data.get("tasks", [])
            data["tasks"] = [
                {"id": t.get("id"), "title": t.get("title"), "owner": t.get("owner")}
                for t in tasks
                if isinstance(t, dict)
            ]
        if event.type == EventType.TASK_ASSIGNED and "title" in event.data:
            data["title"] = event.data["title"]
        shown.append(
            PublicEvent(
                id=event.id,
                run_id=token,
                actor=event.actor,
                type=event.type,
                summary=_summary(event, title),
                data=data,
                occurred_at=event.occurred_at,
            )
        )
    return shown


def _summary(event: Event, title: str) -> str:
    """The step's sentence, with anything the founder typed taken out."""
    match event.type:
        case EventType.RUN_STARTED:
            return f"Asked for: {title}"
        case EventType.APPROVAL_REQUESTED:
            return "Waiting for the founder's approval to release"
        case EventType.APPROVAL_DECIDED:
            return (
                "The founder approved the release"
                if event.data.get("approved")
                else ("The release was not approved")
            )
        case _:
            return event.summary


def stats(events: list[Event]) -> PublicStats:
    def of(type_: EventType) -> list[Event]:
        return [e for e in events if e.type == type_]

    tasks = {e.data.get("task_id") for e in of(EventType.WORK_FINISHED)}
    checks = [e for e in of(EventType.CHECK_FINISHED) if not e.data.get("browser")]
    security = of(EventType.SECURITY_FINISHED)
    return PublicStats(
        tasks=len(tasks),
        minutes=_minutes(events[0].occurred_at, events[-1].occurred_at) if events else 0,
        checks_passed=bool(checks) and bool(checks[-1].data.get("passed")),
        security_clean=bool(security) and not int(security[-1].data.get("blocking", 0)),
        docs_updated=bool(of(EventType.DOCS_UPDATED)),
    )


def live_url(events: list[Event]) -> str:
    """Where the app is online: the live site, else the preview."""
    for event in reversed(events):
        if event.type == EventType.DEPLOY_FINISHED and event.summary.startswith(
            ("Live at", "Preview ready")
        ):
            url = str(event.data.get("url", ""))
            return url if url.startswith("https://") else ""
    return ""


def _minutes(first: datetime, last: datetime) -> int:
    return max(round((last - first).total_seconds() / 60), 1)
