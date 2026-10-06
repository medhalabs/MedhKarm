"""The public waitlist: join, and how many have. Open to everyone, so it is rate limited."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.features.waitlist.dependencies import get_waitlist_service, joins
from app.features.waitlist.schemas import Joined, JoinWaitlist
from app.features.waitlist.service import WaitlistService

router = APIRouter(prefix="/public/waitlist", tags=["waitlist"])
Service = Annotated[WaitlistService, Depends(get_waitlist_service)]


class Count(BaseModel):
    count: int


@router.post("", response_model=Joined)
async def join(body: JoinWaitlist, request: Request, service: Service) -> Joined:
    host = request.client.host if request.client else "unknown"
    if not joins.allow(host):
        raise HTTPException(status_code=429, detail="Too many sign-ups from here: try later")
    return await service.join(body)


@router.get("/count", response_model=Count)
async def count(service: Service) -> Count:
    return Count(count=await service.count())
