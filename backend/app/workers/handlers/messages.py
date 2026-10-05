"""The reply job: an agent answers the founder's message (messages/replier.py)."""

from typing import Any

from app.features.events.interfaces import EventStore
from app.features.events.schemas import EventType
from app.features.jobs.exceptions import PermanentJobError
from app.features.messages.replier import AgentReplier
from app.features.messages.schemas import ThreadKind
from app.features.projects.interfaces import ProjectRepository
from app.features.runs.service import RunService

QUIET = {EventType.TOOL_USED, EventType.MODEL_USED}  # too detailed for an agent's context
RECENT_EVENTS = 40


class MessageReply:
    def __init__(self, replier: AgentReplier) -> None:
        self._replier = replier

    async def run(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        try:
            message_id = int(payload["message_id"])
        except (KeyError, TypeError, ValueError) as error:
            raise PermanentJobError(f"No message in reply job: {payload}") from error
        reply = await self._replier.reply(message_id)
        return {"reply_id": reply.id if reply else None}

    async def give_up(self, payload: dict[str, Any], error: str) -> None:
        return None  # the founder's message stays; they can write again


class TeamContext:
    """What an agent sees when it answers: the run's request and latest activity, or the
    project's goal, backlog and the founder's earlier answers."""

    def __init__(self, runs: RunService, projects: ProjectRepository, events: EventStore) -> None:
        self._runs = runs
        self._projects = projects
        self._events = events

    async def describe(self, kind: ThreadKind, thread_id: str) -> str:
        if kind == ThreadKind.RUN:
            run = await self._runs.get(thread_id)
            events = [
                e
                for e in await self._events.list_for_run(thread_id, 0, 1000)
                if e.type not in QUIET
            ][-RECENT_EVENTS:]
            activity = "\n".join(f"- {e.actor}: {e.summary}" for e in events)
            return (
                f"The run's request:\n{run.request}\n\nStatus: {run.status}\n\n"
                f"Latest activity:\n{activity or '(nothing yet)'}"
            )
        project = await self._projects.get_project(thread_id)
        if project is None:
            return "(the project no longer exists)"
        items = await self._projects.list_items(thread_id)
        backlog = "\n".join(f"{i.position}. [{i.status}] {i.title}" for i in items)
        answers = "\n".join(f"- {a.question} → {a.answer}" for a in project.answers)
        return (
            f"Project: {project.name} ({project.status})\nGoal:\n{project.goal}\n\n"
            f"Backlog:\n{backlog or '(empty)'}\n\n"
            f"Open questions: {'; '.join(project.questions) or 'none'}\n"
            f"The founder's answers:\n{answers or '(none yet)'}"
        )
