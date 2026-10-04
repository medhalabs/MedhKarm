"""HTTP endpoints for a run's activity log."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.features.events.dependencies import get_event_service
from app.features.events.schemas import Event, RunTotals
from app.features.events.service import EventService
from app.features.runs.dependencies import owned_run

# Every route here is about one run: the caller must be signed in and own it.
router = APIRouter(prefix="/runs/{run_id}", tags=["events"], dependencies=[Depends(owned_run)])
Service = Annotated[EventService, Depends(get_event_service)]


@router.get("/events", response_model=list[Event])
async def list_events(
    run_id: str,
    service: Service,
    after_id: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 500,
) -> list[Event]:
    return await service.list_for_run(run_id, after_id, limit)


@router.get("/events/totals", response_model=RunTotals)
async def run_totals(run_id: str, service: Service) -> RunTotals:
    return await service.totals_for_run(run_id)


@router.get("/events/stream")
async def stream_events(
    run_id: str, service: Service, after_id: Annotated[int, Query(ge=0)] = 0
) -> StreamingResponse:
    """Live activity as server-sent events (EventSource in the browser)."""
    return StreamingResponse(
        service.stream(run_id, after_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
