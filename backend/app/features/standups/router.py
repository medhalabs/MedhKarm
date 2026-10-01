"""HTTP endpoints for the daily standup."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from app.features.standups.dependencies import get_standup_service
from app.features.standups.render import to_text
from app.features.standups.schemas import Standup
from app.features.standups.service import StandupService

router = APIRouter(prefix="/standups", tags=["standups"])
Service = Annotated[StandupService, Depends(get_standup_service)]


@router.get("/today", response_model=Standup)
async def today(service: Service) -> Standup:
    return await service.for_day()


@router.get("/{day}", response_model=Standup)
async def for_day(day: date, service: Service) -> Standup:
    return await service.for_day(day)


@router.get("/{day}/text", response_class=PlainTextResponse)
async def for_day_as_text(day: date, service: Service) -> str:
    """The same standup as plain text, as it will be sent by email or WhatsApp."""
    return to_text(await service.for_day(day))
