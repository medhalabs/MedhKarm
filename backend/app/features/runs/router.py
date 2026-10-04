"""HTTP endpoints to start runs, follow them and approve releases. Each call returns at once:
the work happens in workers, and progress arrives through `/runs/{run_id}/events`. Everything
is scoped to the signed-in founder's company."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.features.auth.dependencies import SignedIn
from app.features.runs.dependencies import OwnedRun, get_run_service
from app.features.runs.schemas import ApprovalDecision, Run, StartRun
from app.features.runs.service import RunService

router = APIRouter(prefix="/runs", tags=["runs"])
Service = Annotated[RunService, Depends(get_run_service)]


@router.post("", response_model=Run, status_code=status.HTTP_202_ACCEPTED)
async def start_run(body: StartRun, who: SignedIn, service: Service) -> Run:
    return await service.start(body, who.company_id)


@router.get("", response_model=list[Run])
async def list_runs(
    who: SignedIn, service: Service, limit: Annotated[int, Query(ge=1, le=200)] = 50
) -> list[Run]:
    return await service.list(limit, who.company_id)


@router.get("/{run_id}", response_model=Run)
async def get_run(run: OwnedRun) -> Run:
    return run


@router.post("/{run_id}/cancel", response_model=Run, status_code=status.HTTP_202_ACCEPTED)
async def cancel(run: OwnedRun, service: Service) -> Run:
    """Stop the run, whatever it's doing; its work is thrown away."""
    return await service.cancel(run.id)


@router.post("/{run_id}/approval", response_model=Run, status_code=status.HTTP_202_ACCEPTED)
async def decide(run: OwnedRun, body: ApprovalDecision, service: Service) -> Run:
    """Approve or reject the release the run is waiting on."""
    return await service.decide(run.id, body)
