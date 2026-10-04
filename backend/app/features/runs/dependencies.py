from typing import Annotated

from fastapi import Depends

from app.core.config import get_settings
from app.core.database import session_factory
from app.features.auth.dependencies import SignedIn
from app.features.jobs.dependencies import get_job_queue
from app.features.runs.repository import SqlRunRepository
from app.features.runs.schemas import Run
from app.features.runs.service import RunService


def get_run_service() -> RunService:
    return RunService(
        SqlRunRepository(session_factory),
        get_job_queue(),
        max_attempts=get_settings().build_max_attempts,
    )


async def owned_run(
    run_id: str, who: SignedIn, service: Annotated[RunService, Depends(get_run_service)]
) -> Run:
    """The run in the path, if it belongs to the caller's company (404 otherwise)."""
    return await service.owned(run_id, who.company_id)


OwnedRun = Annotated[Run, Depends(owned_run)]
