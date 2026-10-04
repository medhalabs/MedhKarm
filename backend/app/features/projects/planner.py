"""The PM (Mira) writes the backlog: one model call, recorded in the activity log like a run.

Runs in a worker job (`backlog.plan`). The proposed items wait for the founder's approval.
"""

import uuid

from app.features.events.interfaces import EventStore
from app.features.events.schemas import Actor, EventType
from app.features.events.service import RunRecorder
from app.features.models.interfaces import LLMProvider
from app.features.projects.interfaces import ProjectRepository
from app.features.projects.pm import BACKLOG_TOOL, PM_PROMPT, parse_backlog
from app.features.projects.schemas import ItemStatus, Project, ProjectStatus


class BacklogPlanner:
    def __init__(
        self,
        llm: LLMProvider,
        projects: ProjectRepository,
        events: EventStore | None = None,
        instructions: str = PM_PROMPT,
    ) -> None:
        self._llm = llm
        self._projects = projects
        self._events = events
        self._instructions = instructions

    async def plan(self, project_id: str) -> int:
        """Plan (or re-plan) the project's backlog; returns how many items were proposed."""
        project = await self._projects.get_project(project_id)
        if project is None:
            raise LookupError(f"No project {project_id}")
        recorder = RunRecorder(self._events, f"plan-{project.id}-{uuid.uuid4().hex[:4]}")
        await recorder.record(
            Actor.FOUNDER,
            EventType.RUN_STARTED,
            f"Asked Mira to plan {project.name}",
            {"request": f"Plan {project.name}", "project_id": project.id},
        )
        response = await self._llm.complete(
            [
                {"role": "system", "content": self._instructions.strip()},
                {"role": "user", "content": await self._brief(project)},
            ],
            [BACKLOG_TOOL],
        )
        await recorder.record(
            Actor.PM,
            EventType.MODEL_USED,
            "Thought about the backlog",
            {"model": self._llm.model_name},
            tokens=response.usage.total_tokens,
        )
        backlog = parse_backlog(response, project.goal)
        items = await self._projects.replace_open_items(
            project.id, backlog.items, ItemStatus.PROPOSED
        )
        await self._projects.update_project(
            project.id,
            {"status": ProjectStatus.PLAN_READY, "questions": backlog.questions, "error": ""},
        )
        proposed = [i for i in items if i.status == ItemStatus.PROPOSED]
        await recorder.record(
            Actor.PM,
            EventType.PLAN_CREATED,
            f"Planned {len(proposed)} backlog item{'s' if len(proposed) != 1 else ''} "
            f"for {project.name}",
            {
                "project_id": project.id,
                "summary": backlog.summary,
                "items": [i.title for i in proposed],
                "questions": backlog.questions,
            },
        )
        await recorder.record(
            Actor.SYSTEM,
            EventType.RUN_FINISHED,
            "Backlog ready for your review",
            {"status": "planned", "project_id": project.id, "items": len(proposed)},
        )
        return len(proposed)

    async def _brief(self, project: Project) -> str:
        parts = [f"Project: {project.name}", f"Goal:\n{project.goal}"]
        if project.repo:
            parts.append(
                f"It's an existing codebase ({project.repo.url}); the team reads the code "
                "before building each item, so plan changes to that project."
            )
        built = [
            i.title
            for i in await self._projects.list_items(project.id)
            if i.status not in (ItemStatus.PROPOSED, ItemStatus.TODO)
        ]
        if built:
            parts.append(
                "Already built or under way (don't plan these again):\n"
                + "\n".join(f"- {t}" for t in built)
            )
        return "\n\n".join(parts)
