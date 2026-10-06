"""The founder's models: whose keys run the team, which models, and their own keys."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.features.auth.dependencies import SignedIn
from app.features.model_settings.dependencies import get_model_settings_service
from app.features.model_settings.schemas import (
    CompanyModels,
    KeyCheck,
    ModelChoices,
    ModelsView,
    NewKey,
    Provider,
)
from app.features.model_settings.service import ModelSettingsService
from app.features.teams.dependencies import get_team_service

router = APIRouter(prefix="/settings/models", tags=["model_settings"])
Service = Annotated[ModelSettingsService, Depends(get_model_settings_service)]
MODEL_ROLES = ("pm", "cto", "docs", "design", "developer", "qa")  # the roles that call a model


def _view(service: ModelSettingsService, settings: CompanyModels) -> ModelsView:
    template = get_team_service().get_template("software")
    roles = {
        r.id: f"{r.display_names[0]} ({r.title})" for r in template.roles if r.id in MODEL_ROLES
    }
    return ModelsView(settings=settings, options=service.options(), roles=roles)


@router.get("", response_model=ModelsView)
async def get_models(who: SignedIn, service: Service) -> ModelsView:
    return _view(service, await service.get(who.company_id))


@router.put("", response_model=ModelsView)
async def save_models(body: ModelChoices, who: SignedIn, service: Service) -> ModelsView:
    return _view(service, await service.save(who.company_id, body))


@router.post("/keys", response_model=ModelsView)
async def add_key(body: NewKey, who: SignedIn, service: Service) -> ModelsView:
    """Saves the key sealed; only its last four characters are ever shown again."""
    return _view(service, await service.add_key(who.company_id, body))


@router.delete("/keys/{provider}", response_model=ModelsView)
async def remove_key(provider: Provider, who: SignedIn, service: Service) -> ModelsView:
    return _view(service, await service.remove_key(who.company_id, provider))


@router.post("/keys/{provider}/check", response_model=KeyCheck)
async def check_key(provider: Provider, who: SignedIn, service: Service) -> KeyCheck:
    """One tiny call with the key, to show whether it works."""
    return await service.check(who.company_id, provider)
