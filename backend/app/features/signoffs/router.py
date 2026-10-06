"""The release sign-off card for a run."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.features.events.dependencies import get_event_store
from app.features.events.interfaces import EventStore
from app.features.runs.dependencies import owned_run
from app.features.signoffs.schemas import Signoff
from app.features.signoffs.service import build
from app.features.teams.dependencies import get_team_service

router = APIRouter(prefix="/runs/{run_id}", tags=["signoffs"], dependencies=[Depends(owned_run)])
ROLES = ("cto", "qa", "security", "devops", "docs")


@router.get("/signoffs", response_model=list[Signoff])
async def signoffs(
    run_id: str, store: Annotated[EventStore, Depends(get_event_store)]
) -> list[Signoff]:
    """Who signed off the release, and what they say, from the run's activity log."""
    template = get_team_service().get_template("software")
    names = {r.id: r.display_names[0] for r in template.roles if r.id in ROLES}
    return build(await store.list_for_run(run_id, 0, 1000), names)
