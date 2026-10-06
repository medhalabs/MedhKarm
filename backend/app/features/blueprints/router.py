"""The plan before the build: ask Lekha for it, read it, comment, approve."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.features.auth.dependencies import SignedIn
from app.features.blueprints.dependencies import get_blueprint_service
from app.features.blueprints.schemas import (
    Blueprint,
    BlueprintSummary,
    NewBlueprint,
    NewComment,
)
from app.features.blueprints.service import BlueprintService

router = APIRouter(prefix="/blueprints", tags=["blueprints"])
Service = Annotated[BlueprintService, Depends(get_blueprint_service)]


@router.post("", response_model=Blueprint, status_code=201)
async def ask_for_plan(body: NewBlueprint, who: SignedIn, service: Service) -> Blueprint:
    """Saves the agreed brief and queues Lekha's writing job."""
    return await service.create(who.company_id, body)


@router.get("", response_model=list[BlueprintSummary])
async def list_plans(who: SignedIn, service: Service) -> list[BlueprintSummary]:
    return await service.list(who.company_id)


@router.get("/{blueprint_id}", response_model=Blueprint)
async def get_plan(blueprint_id: str, who: SignedIn, service: Service) -> Blueprint:
    return await service.owned(blueprint_id, who.company_id)


@router.post("/{blueprint_id}/comments", response_model=Blueprint)
async def comment(
    blueprint_id: str, body: NewComment, who: SignedIn, service: Service
) -> Blueprint:
    """A change request: Lekha rewrites the documents it touches."""
    return await service.comment(blueprint_id, who.company_id, body.text)


@router.post("/{blueprint_id}/approve", response_model=Blueprint)
async def approve(blueprint_id: str, who: SignedIn, service: Service) -> Blueprint:
    """Approves the plan and starts the build (`run_id` in the answer)."""
    return await service.approve(blueprint_id, who.company_id)


@router.post("/{blueprint_id}/retry", response_model=Blueprint)
async def retry(blueprint_id: str, who: SignedIn, service: Service) -> Blueprint:
    """Asks Lekha again after a failure."""
    return await service.retry(blueprint_id, who.company_id)
