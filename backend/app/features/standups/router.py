"""HTTP endpoints for the daily standup: the signed-in founder's company only."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from app.features.auth.dependencies import SignedIn
from app.features.runs.dependencies import get_run_service
from app.features.runs.service import RunService
from app.features.standups.dependencies import get_standup_service
from app.features.standups.render import to_text
from app.features.standups.schemas import Standup
from app.features.standups.service import StandupService

router = APIRouter(prefix="/standups", tags=["standups"])
Service = Annotated[StandupService, Depends(get_standup_service)]
Runs = Annotated[RunService, Depends(get_run_service)]


@router.get("/today", response_model=Standup)
async def today(who: SignedIn, service: Service, runs: Runs) -> Standup:
    return await service.for_day(only=await runs.run_ids(who.company_id))


@router.get("/{day}", response_model=Standup)
async def for_day(day: date, who: SignedIn, service: Service, runs: Runs) -> Standup:
    return await service.for_day(day, await runs.run_ids(who.company_id))


@router.get("/{day}/text", response_class=PlainTextResponse)
async def for_day_as_text(day: date, who: SignedIn, service: Service, runs: Runs) -> str:
    """The same standup as plain text, as it will be sent by email or WhatsApp."""
    return to_text(await service.for_day(day, await runs.run_ids(who.company_id)))
