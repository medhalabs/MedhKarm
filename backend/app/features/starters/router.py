"""The stack choices the founder can make, and a preview of what the team would pick."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.features.starters.dependencies import get_starter_service
from app.features.starters.schemas import ModuleSpec, Stack, StackChoice
from app.features.starters.service import StarterService
from app.features.starters.stack import APIS, DATABASES, FRONTENDS, HOSTS, PAYMENTS

router = APIRouter(prefix="/starters", tags=["starters"])
Service = Annotated[StarterService, Depends(get_starter_service)]


class StackOptions(BaseModel):
    """Names the form suggests; any other name is accepted too."""

    frontend: list[str]
    api: list[str]
    database: list[str]
    hosting: list[str]
    payments: list[str]
    modules: list[ModuleSpec]


class StackPreview(BaseModel):
    request: str = Field(min_length=3, max_length=50_000)
    stack: StackChoice = Field(default_factory=StackChoice)


@router.get("/options")
async def options(service: Service) -> StackOptions:
    return StackOptions(
        frontend=list(FRONTENDS),
        api=["nextjs", *APIS],
        database=list(DATABASES),
        hosting=list(HOSTS),
        payments=[*PAYMENTS, "none"],
        modules=service.modules(),
    )


@router.post("/preview")
async def preview(body: StackPreview, service: Service) -> Stack:
    return service.resolve(body.request, body.stack)
