from datetime import timedelta

from app.core.config import get_settings
from app.features.events.dependencies import get_event_store
from app.features.standups.service import StandupService


def get_standup_service() -> StandupService:
    settings = get_settings()
    return StandupService(
        get_event_store(),
        timezone=settings.standup_timezone,
        hour=settings.standup_hour,
        stall_after=timedelta(minutes=settings.standup_stall_minutes),
    )
