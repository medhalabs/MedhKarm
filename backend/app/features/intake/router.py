"""Starting a run by talking to the CTO. Each call is one turn: send the conversation so far,
get the CTO's reply, and a brief once it's ready (start it with POST /runs)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import company_scope
from app.features.auth.dependencies import SignedIn
from app.features.intake.dependencies import get_intake_service, get_project_intake_service
from app.features.intake.schemas import Conversation, ProjectReply, Reply
from app.features.intake.service import IntakeService

router = APIRouter(prefix="/intake", tags=["intake"])
Service = Annotated[IntakeService, Depends(get_intake_service)]


@router.post("", response_model=Reply)
async def turn(body: Conversation, who: SignedIn, service: Service) -> Reply:
    with company_scope(who.company_id):  # the founder's own model and key
        return await service.turn(body)


ProjectIntake = Annotated[IntakeService, Depends(get_project_intake_service)]


@router.post("/project", response_model=ProjectReply)
async def project_turn(body: Conversation, who: SignedIn, service: ProjectIntake) -> ProjectReply:
    """Talk to the PM about a new project; create it with POST /projects once it's ready."""
    with company_scope(who.company_id):
        return await service.project_turn(body)
