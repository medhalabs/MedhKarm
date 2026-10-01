"""HTTP endpoints to start runs, follow them and approve releases. Each call returns at once:
the work happens in workers, and progress arrives through `/runs/{run_id}/events`."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.features.runs.dependencies import get_run_service
from app.features.runs.schemas import ApprovalDecision, Run, StartRun
from app.features.runs.service import RunService

router = APIRouter(prefix="/runs", tags=["runs"])
Service = Annotated[RunService, Depends(get_run_service)]


@router.post("", response_model=Run, status_code=status.HTTP_202_ACCEPTED)
async def start_run(body: StartRun, service: Service) -> Run:
    return await service.start(body)


@router.get("", response_model=list[Run])
async def list_runs(service: Service, limit: Annotated[int, Query(ge=1, le=200)] = 50) -> list[Run]:
    return await service.list(limit)


@router.get("/{run_id}", response_model=Run)
async def get_run(run_id: str, service: Service) -> Run:
    return await service.get(run_id)


@router.post("/{run_id}/approval", response_model=Run, status_code=status.HTTP_202_ACCEPTED)
async def decide(run_id: str, body: ApprovalDecision, service: Service) -> Run:
    """Approve or reject the release the run is waiting on."""
    return await service.decide(run_id, body)
