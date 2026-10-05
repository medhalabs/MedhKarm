"""Posting and reading messages. Posting is quick: the agent's reply is a background job
(REPLY_JOB, workers/handlers/messages.py). The founder's messages also reach the work: the
CTO's plan and developer briefs for a run, the PM's next plan for a project."""

from app.features.events.interfaces import EventStore
from app.features.events.schemas import Actor, EventType
from app.features.events.service import RunRecorder
from app.features.jobs.interfaces import JobQueue
from app.features.messages.exceptions import ThreadNotFoundError
from app.features.messages.interfaces import MessageRepository, ThreadOwner
from app.features.messages.schemas import Message, NewMessage, ThreadKind

REPLY_JOB = "message.reply"
FOUNDER = "founder"


class MessageService:
    def __init__(
        self,
        messages: MessageRepository,
        owner: ThreadOwner | None = None,
        jobs: JobQueue | None = None,
        events: EventStore | None = None,
    ) -> None:
        self._messages = messages
        self._owner = owner
        self._jobs = jobs
        self._events = events

    async def post(self, company_id: str, body: NewMessage) -> Message:
        kind, thread_id = body.thread
        await self._check(company_id, kind, thread_id)
        message = await self._messages.add(
            company_id, kind, thread_id, FOUNDER, "You", body.to, body.body.strip()
        )
        if kind == ThreadKind.RUN:
            await RunRecorder(self._events, thread_id).record(
                Actor.FOUNDER,
                EventType.MESSAGE_POSTED,
                f"You wrote: {message.body[:160]}",
                {"message_id": message.id, "to": body.to},
            )
        if self._jobs:
            await self._jobs.enqueue(
                REPLY_JOB, {"message_id": message.id}, unique_key=f"{REPLY_JOB}:{message.id}"
            )
        return message

    async def thread(self, company_id: str, kind: ThreadKind, thread_id: str) -> list[Message]:
        await self._check(company_id, kind, thread_id)
        return await self._messages.thread(kind, thread_id)

    async def recent(self, company_id: str, limit: int = 20) -> list[Message]:
        return await self._messages.recent(company_id, limit)

    async def for_run(self, run_id: str) -> list[str]:
        """The founder's messages about a run (FounderNotes, for the team's briefs)."""
        return await self._founders(ThreadKind.RUN, run_id)

    async def for_project(self, project_id: str) -> list[str]:
        """The founder's messages about a project (ProjectNotes, for the PM's plan)."""
        return await self._founders(ThreadKind.PROJECT, project_id)

    async def _founders(self, kind: ThreadKind, thread_id: str) -> list[str]:
        return [m.body for m in await self._messages.thread(kind, thread_id) if m.author == FOUNDER]

    async def _check(self, company_id: str, kind: ThreadKind, thread_id: str) -> None:
        if self._owner and not await self._owner.owns(company_id, kind, thread_id):
            raise ThreadNotFoundError(f"No {kind} {thread_id}")
