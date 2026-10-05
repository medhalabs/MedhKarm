"""The founder's messages to the team, in a thread on a run or a project. Replies arrive a
little later (a worker writes them): read the thread again, or watch the run's activity."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.features.auth.dependencies import SignedIn
from app.features.messages.dependencies import get_message_service
from app.features.messages.schemas import Message, NewMessage, ThreadKind
from app.features.messages.service import MessageService

router = APIRouter(prefix="/messages", tags=["messages"])
Service = Annotated[MessageService, Depends(get_message_service)]


@router.post("", response_model=Message, status_code=status.HTTP_201_CREATED)
async def post_message(body: NewMessage, who: SignedIn, service: Service) -> Message:
    return await service.post(who.company_id, body)


@router.get("", response_model=list[Message])
async def thread(
    who: SignedIn,
    service: Service,
    run_id: str | None = None,
    project_id: str | None = None,
) -> list[Message]:
    """One thread, oldest first: pass `run_id` or `project_id`."""
    if bool(run_id) == bool(project_id):
        raise HTTPException(status_code=422, detail="Pass run_id or project_id")
    kind = ThreadKind.RUN if run_id else ThreadKind.PROJECT
    return await service.thread(who.company_id, kind, str(run_id or project_id))


@router.get("/recent", response_model=list[Message])
async def recent(
    who: SignedIn, service: Service, limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> list[Message]:
    return await service.recent(who.company_id, limit)
