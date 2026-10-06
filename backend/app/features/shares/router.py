"""Share links. The founder's routes need sign-in and their own run; the public ones need
nothing (that is the point), so they are rate limited and show only the whitelisted view."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response

from app.features.artifacts.service import byte_range
from app.features.auth.dependencies import SignedIn
from app.features.runs.dependencies import owned_run
from app.features.shares.dependencies import get_share_service, public_views
from app.features.shares.schemas import PublicShare, Share
from app.features.shares.service import ShareService

owner = APIRouter(prefix="/runs/{run_id}/share", tags=["shares"], dependencies=[Depends(owned_run)])
public = APIRouter(prefix="/public/shares", tags=["shares"])
Service = Annotated[ShareService, Depends(get_share_service)]


@owner.post("", response_model=Share)
async def share(run_id: str, who: SignedIn, service: Service) -> Share:
    """Turns on the public link for this build (the same link if it's already on)."""
    return await service.create(who.company_id, run_id)


@owner.get("", response_model=Share | None)
async def current(run_id: str, who: SignedIn, service: Service) -> Share | None:
    return await service.get(who.company_id, run_id)


@owner.delete("", status_code=204)
async def stop(run_id: str, who: SignedIn, service: Service) -> None:
    """Turns the link off: it stops working at once."""
    await service.revoke(who.company_id, run_id)


def _limit(request: Request) -> None:
    host = request.client.host if request.client else "unknown"
    if not public_views.allow(host):
        raise HTTPException(status_code=429, detail="Too many requests: try again in a minute")


@public.get("/{token}", response_model=PublicShare, dependencies=[Depends(_limit)])
async def view(token: str, service: Service) -> PublicShare:
    return await service.public(token)


@public.get("/{token}/demo", dependencies=[Depends(_limit)])
async def demo(
    token: str, service: Service, range: Annotated[str | None, Header()] = None
) -> Response:
    """The demo video, with byte ranges so a browser can play and skip through it."""
    found = await service.demo(token)
    size = len(found.data)
    headers = {"Accept-Ranges": "bytes", "Cache-Control": "public, max-age=300"}
    wanted = byte_range(range, size)
    if wanted is not None:
        start, end = wanted
        return Response(
            found.data[start : end + 1],
            status_code=206,
            media_type=found.artifact.content_type,
            headers={**headers, "Content-Range": f"bytes {start}-{end}/{size}"},
        )
    return Response(found.data, media_type=found.artifact.content_type, headers=headers)
