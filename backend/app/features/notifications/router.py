"""The founder's update settings: where the daily standup and weekly report go."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.features.auth.dependencies import SignedIn
from app.features.notifications.dependencies import get_notification_service
from app.features.notifications.schemas import (
    Channel,
    CompanySettings,
    Delivery,
    NotificationSettings,
)
from app.features.notifications.service import NotificationService

router = APIRouter(prefix="/settings/notifications", tags=["notifications"])
Service = Annotated[NotificationService, Depends(get_notification_service)]


class SettingsView(BaseModel):
    settings: CompanySettings
    available: list[Channel]  # channels the server can send on (keys set)


@router.get("", response_model=SettingsView)
async def get_settings(who: SignedIn, service: Service) -> SettingsView:
    return SettingsView(settings=await service.get(who.company_id), available=service.channels())


@router.put("", response_model=SettingsView)
async def save_settings(
    body: NotificationSettings, who: SignedIn, service: Service
) -> SettingsView:
    saved = await service.save(who.company_id, body)
    return SettingsView(settings=saved, available=service.channels())


@router.post("/test", response_model=list[Delivery])
async def send_test(who: SignedIn, service: Service) -> list[Delivery]:
    """Sends a short test to every channel set up, and says what happened on each."""
    return await service.send_test(who.company_id)
