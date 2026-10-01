"""HTTP endpoints for team templates."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.features.teams.dependencies import get_team_service
from app.features.teams.schemas import Team, TeamTemplate, TemplateSummary
from app.features.teams.service import TeamService

router = APIRouter(prefix="/teams", tags=["teams"])
Service = Annotated[TeamService, Depends(get_team_service)]


@router.get("/templates", response_model=list[TemplateSummary])
def list_templates(service: Service) -> list[TemplateSummary]:
    return service.list_templates()


@router.get("/templates/{template_id}", response_model=TeamTemplate)
def get_template(template_id: str, service: Service) -> TeamTemplate:
    return service.get_template(template_id)


@router.get("/templates/{template_id}/team", response_model=Team)
def default_team(template_id: str, service: Service) -> Team:
    """The team this template starts with: who sits in the office."""
    return service.assemble(template_id)
