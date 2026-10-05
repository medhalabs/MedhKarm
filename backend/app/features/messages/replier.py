"""An agent answers the founder: in its own role and name, from what it can see of the run or
project, briefly and honestly. Runs in a worker (the reply job); safe to repeat."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from app.features.events.interfaces import EventStore
from app.features.events.schemas import Actor, EventType
from app.features.events.service import RunRecorder
from app.features.messages.interfaces import MessageRepository
from app.features.messages.schemas import Message, ThreadKind
from app.features.messages.service import FOUNDER
from app.features.models.interfaces import LLMProvider

HISTORY = 20  # earlier messages in the thread the agent reads

REPLY_PROMPT = """You are {name}, the {title} on a solo founder's AI software team (MedhKarm).
The founder is writing to you about {what}. Reply in 2-5 short sentences, plainly, as yourself.
Be honest about what the team has done and what it will do, using only the context below.
If they ask for a change: for a run, say it goes into the team's next task; for a project,
say it goes into the next backlog plan. Never claim work that isn't in the context."""


@dataclass(frozen=True)
class Persona:
    role: str  # the role id, also the actor in the activity log
    name: str  # "Mira"
    title: str  # "Product Manager"


class ThreadContext(Protocol):
    """What the agent can see: the run's request and progress, or the project's backlog."""

    async def describe(self, kind: ThreadKind, thread_id: str) -> str: ...


class AgentReplier:
    def __init__(
        self,
        messages: MessageRepository,
        llm_for: Callable[[str], LLMProvider],
        personas: dict[str, Persona],
        context: ThreadContext,
        events: EventStore | None = None,
    ) -> None:
        """`llm_for(role)`: that role's model. `personas`: role id -> who answers."""
        self._messages = messages
        self._llm_for = llm_for
        self._personas = personas
        self._context = context
        self._events = events

    async def reply(self, message_id: int) -> Message | None:
        message = await self._messages.get(message_id)
        if message is None or message.author != FOUNDER:
            return None
        history = await self._messages.thread(message.thread, message.thread_id)
        persona = self._personas.get(message.to) or next(iter(self._personas.values()))
        answered = next(
            (m for m in history if m.id > message.id and m.author == persona.role), None
        )
        if answered:  # a retry after the reply was saved
            return answered
        what = "a build run" if message.thread == ThreadKind.RUN else "a project and its backlog"
        earlier = [m for m in history if m.id <= message.id][-HISTORY:]
        conversation = "\n".join(f"{m.name}: {m.body}" for m in earlier)
        context = await self._context.describe(message.thread, message.thread_id)
        response = await self._llm_for(persona.role).complete(
            [
                {
                    "role": "system",
                    "content": REPLY_PROMPT.format(
                        name=persona.name, title=persona.title, what=what
                    ),
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nConversation so far:\n{conversation}\n\n"
                    f"Reply to the founder's last message as {persona.name}.",
                },
            ]
        )
        body = (response.content or "").strip() or "Noted. I'll take it into account."
        reply = await self._messages.add(
            message.company_id,
            message.thread,
            message.thread_id,
            persona.role,
            persona.name,
            FOUNDER,
            body,
        )
        if message.thread == ThreadKind.RUN:
            actor = Actor(persona.role) if persona.role in Actor._value2member_map_ else Actor.CTO
            await RunRecorder(self._events, message.thread_id).record(
                actor,
                EventType.MESSAGE_POSTED,
                f"{persona.name}: {body[:160]}",
                {"message_id": reply.id, "member": persona.name},
                tokens=response.usage.total_tokens,
            )
        return reply
