from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.features.health.service import HealthService


def get_health_service(settings: Annotated[Settings, Depends(get_settings)]) -> HealthService:
    return HealthService(settings)
