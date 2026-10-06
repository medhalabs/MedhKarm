"""Builds the founder's inbox from what's already stored: runs at the gate, the PM's open
questions, blocked backlog items, and the team's latest replies. Nothing new is stored here."""

from app.features.blueprints.schemas import BlueprintStatus
from app.features.inbox.interfaces import (
    BlueprintsReader,
    MessagesReader,
    ProjectsReader,
    RunsReader,
)
from app.features.inbox.schemas import Approval, Blocked, Inbox, Plan, Questions
from app.features.messages.service import FOUNDER
from app.features.projects.schemas import ItemStatus, ProjectStatus
from app.features.runs.schemas import RunStatus

RECENT_RUNS = 200
LIVE_PROJECTS = 100
REPLIES = 5


class InboxService:
    def __init__(
        self,
        runs: RunsReader,
        projects: ProjectsReader,
        messages: MessagesReader,
        blueprints: BlueprintsReader | None = None,
    ) -> None:
        self._runs = runs
        self._projects = projects
        self._messages = messages
        self._blueprints = blueprints

    async def for_company(self, company_id: str) -> Inbox:
        runs = await self._runs.list(RECENT_RUNS, company_id)
        approvals = [
            Approval(
                run_id=r.id,
                request=r.request,
                summary=str((r.gate or {}).get("summary", "")),
                reasons=list((r.gate or {}).get("reasons", [])),
                preview_url=str((r.gate or {}).get("preview_url", "")),
                security=list((r.gate or {}).get("security", [])),
                waiting_since=r.updated_at,
            )
            for r in runs
            if r.status == RunStatus.WAITING_FOR_APPROVAL
        ]
        questions: list[Questions] = []
        blocked: list[Blocked] = []
        for project in await self._projects.list(LIVE_PROJECTS, company_id):
            if project.status == ProjectStatus.DONE:
                continue
            if project.questions:
                questions.append(
                    Questions(
                        project_id=project.id,
                        project_name=project.name,
                        questions=project.questions,
                    )
                )
            detail = await self._projects.get(project.id)
            blocked += [
                Blocked(
                    project_id=project.id,
                    project_name=project.name,
                    item_id=item.id,
                    title=item.title,
                    note=item.note,
                )
                for item in detail.items
                if item.status == ItemStatus.BLOCKED
            ]
        replies = [m for m in await self._messages.recent(company_id) if m.author != FOUNDER]
        plans = [
            Plan(blueprint_id=b.id, title=b.title, waiting_since=b.updated_at)
            for b in (await self._blueprints.list(company_id) if self._blueprints else [])
            if b.status == BlueprintStatus.READY
        ]
        return Inbox(
            plans=plans,
            approvals=approvals,
            questions=questions,
            blocked=blocked,
            replies=replies[:REPLIES],
        )
