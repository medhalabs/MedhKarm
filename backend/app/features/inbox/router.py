"""The signed-in founder's inbox. Acting on an item uses the usual endpoints: approve at
`/runs/{id}/approval`, answer at `/projects/{id}/answers`, retry or skip backlog items."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.features.auth.dependencies import SignedIn
from app.features.inbox.dependencies import get_inbox_service
from app.features.inbox.schemas import Inbox, InboxCount
from app.features.inbox.service import InboxService

router = APIRouter(prefix="/inbox", tags=["inbox"])
Service = Annotated[InboxService, Depends(get_inbox_service)]


@router.get("", response_model=Inbox)
async def inbox(who: SignedIn, service: Service) -> Inbox:
    return await service.for_company(who.company_id)


@router.get("/count", response_model=InboxCount)
async def count(who: SignedIn, service: Service) -> InboxCount:
    """How many things need the founder (for the nav's badge)."""
    return InboxCount(count=(await service.for_company(who.company_id)).count)
