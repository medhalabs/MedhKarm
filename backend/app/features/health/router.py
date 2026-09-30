"""HTTP endpoints for health checks. Parse input, call the service, return output."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.features.health.dependencies import get_health_service
from app.features.health.schemas import HealthResponse
from app.features.health.service import HealthService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def get_health(service: Annotated[HealthService, Depends(get_health_service)]) -> HealthResponse:
    return service.get_status()
