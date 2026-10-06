"""The autonomy dial: how much the team does on its own, for everything or for one project."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.features.auth.dependencies import SignedIn
from app.features.autonomy.dependencies import get_autonomy_service
from app.features.autonomy.schemas import AutonomySettings, AutonomyView
from app.features.autonomy.service import AutonomyService

router = APIRouter(prefix="/settings/autonomy", tags=["autonomy"])
Service = Annotated[AutonomyService, Depends(get_autonomy_service)]


@router.get("", response_model=AutonomyView)
async def get_autonomy(
    who: SignedIn, service: Service, project_id: str | None = None
) -> AutonomyView:
    """The settings for the company, or for a project (the company's when it has none)."""
    return await service.view(who.company_id, project_id)


@router.put("", response_model=AutonomyView)
async def save_autonomy(
    body: AutonomySettings, who: SignedIn, service: Service, project_id: str | None = None
) -> AutonomyView:
    return await service.save(who.company_id, project_id, body)


@router.delete("", response_model=AutonomyView)
async def reset_autonomy(who: SignedIn, service: Service, project_id: str) -> AutonomyView:
    """A project goes back to the company's settings."""
    return await service.reset(who.company_id, project_id)
