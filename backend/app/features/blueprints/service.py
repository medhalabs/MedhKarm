"""Blueprints: the founder's plan, written by Lekha, read and approved before any code.

The founder agrees a brief with the CTO. Asking for the plan saves it and queues Lekha's
writing job; comments queue a rewrite; approving starts the build run with the same brief.
The API only records and queues, the worker writes (see author.py).
"""

import uuid
from datetime import UTC, datetime

from app.features.blueprints.exceptions import BlueprintNotFoundError, BlueprintNotReadyError
from app.features.blueprints.interfaces import BlueprintRepository, RunStarter
from app.features.blueprints.schemas import (
    ApprovedPlan,
    Blueprint,
    BlueprintStatus,
    BlueprintSummary,
    Comment,
    NewBlueprint,
)
from app.features.jobs.interfaces import JobQueue

WRITE_JOB = "blueprint.write"
REVISE_JOB = "blueprint.revise"
TITLE_LENGTH = 70


class BlueprintService:
    def __init__(
        self,
        blueprints: BlueprintRepository,
        jobs: JobQueue,
        runs: RunStarter,
        max_attempts: int = 3,
    ) -> None:
        self._blueprints = blueprints
        self._jobs = jobs
        self._runs = runs
        self._max_attempts = max_attempts

    async def create(self, company_id: str, body: NewBlueprint) -> Blueprint:
        blueprint = await self._blueprints.create(
            uuid.uuid4().hex[:12], company_id, title_of(body.brief.request), body.brief
        )
        await self._queue_write(blueprint.id, f"{WRITE_JOB}:{blueprint.id}")
        return blueprint

    async def get(self, blueprint_id: str) -> Blueprint:
        found = await self._blueprints.get(blueprint_id)
        if found is None:
            raise BlueprintNotFoundError(f"No blueprint {blueprint_id}")
        return found

    async def owned(self, blueprint_id: str, company_id: str) -> Blueprint:
        """The blueprint, if it's this company's; otherwise "not found"."""
        found = await self.get(blueprint_id)
        if found.company_id != company_id:
            raise BlueprintNotFoundError(f"No blueprint {blueprint_id}")
        return found

    async def list(self, company_id: str) -> list[BlueprintSummary]:
        return [
            BlueprintSummary.model_validate(b.model_dump())
            for b in await self._blueprints.for_company(company_id)
        ]

    async def comment(self, blueprint_id: str, company_id: str, text: str) -> Blueprint:
        """The founder's change request: Lekha rewrites what it touches."""
        blueprint = await self.owned(blueprint_id, company_id)
        if not await self._blueprints.transition(
            blueprint_id, BlueprintStatus.READY, BlueprintStatus.REVISING
        ):
            raise BlueprintNotReadyError(f"The plan is {blueprint.status}, not ready for changes")
        comments = [*blueprint.comments, Comment(author="founder", text=text, at=_now())]
        await self._blueprints.update(
            blueprint_id, comments=comments, progress="Lekha is reading your comment"
        )
        await self._jobs.enqueue(
            REVISE_JOB,
            {"blueprint_id": blueprint_id},
            unique_key=f"{REVISE_JOB}:{blueprint_id}:{len(comments)}",
            max_attempts=self._max_attempts,
        )
        return await self.get(blueprint_id)

    async def approve(self, blueprint_id: str, company_id: str) -> Blueprint:
        """Approves the plan and starts the build run. The run's team gets the documents."""
        blueprint = await self.owned(blueprint_id, company_id)
        if not await self._blueprints.transition(
            blueprint_id, BlueprintStatus.READY, BlueprintStatus.APPROVED
        ):
            raise BlueprintNotReadyError(f"The plan is {blueprint.status}, not ready to approve")
        try:
            run = await self._runs.start(blueprint.brief, company_id)
        except Exception:
            await self._blueprints.transition(
                blueprint_id, BlueprintStatus.APPROVED, BlueprintStatus.READY
            )
            raise
        return await self._blueprints.update(blueprint_id, run_id=run.id, progress="")

    async def retry(self, blueprint_id: str, company_id: str) -> Blueprint:
        """Asks Lekha again after a failure; the documents she already wrote are kept."""
        blueprint = await self.owned(blueprint_id, company_id)
        if not await self._blueprints.transition(
            blueprint_id, BlueprintStatus.FAILED, BlueprintStatus.WRITING
        ):
            raise BlueprintNotReadyError(f"The plan is {blueprint.status}, not failed")
        await self._blueprints.update(blueprint_id, error="", progress="Lekha is starting again")
        await self._queue_write(blueprint_id, f"{WRITE_JOB}:{blueprint_id}:{uuid.uuid4().hex[:6]}")
        return await self.get(blueprint_id)

    async def for_run(self, run_id: str) -> ApprovedPlan | None:
        """The approved plan a run builds from (None: the run didn't start from a blueprint)."""
        blueprint = await self._blueprints.for_run(run_id)
        if blueprint is None or blueprint.status != BlueprintStatus.APPROVED:
            return None
        return ApprovedPlan(docs=blueprint.docs)

    async def _queue_write(self, blueprint_id: str, key: str) -> None:
        await self._jobs.enqueue(
            WRITE_JOB,
            {"blueprint_id": blueprint_id},
            unique_key=key,
            max_attempts=self._max_attempts,
        )


def title_of(request: str) -> str:
    """The first line of the request, as a title."""
    first = next((line.strip() for line in request.splitlines() if line.strip()), "Plan")
    return first if len(first) <= TITLE_LENGTH else first[: TITLE_LENGTH - 1].rstrip() + "…"


def _now() -> datetime:
    return datetime.now(UTC)
