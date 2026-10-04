import logging
from functools import cache
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.database import session_factory
from app.features.auth.repository import SqlUserRepository
from app.features.auth.schemas import CurrentUser
from app.features.auth.service import AuthService, who_is
from app.features.auth.tokens import TokenIssuer
from app.features.companies.repository import SqlCompanyRepository

logger = logging.getLogger(__name__)
DEV_SECRET = "medhkarm-development-only-secret-change-me"
bearer = HTTPBearer(auto_error=False)


@cache
def get_token_issuer() -> TokenIssuer:
    settings = get_settings()
    if settings.auth_secret is not None:
        secret = settings.auth_secret.get_secret_value()
    elif settings.environment == "development":
        logger.warning("AUTH_SECRET isn't set: using the development secret")
        secret = DEV_SECRET
    else:
        raise RuntimeError("Set AUTH_SECRET (a long random string) outside development")
    return TokenIssuer(secret, settings.auth_token_days)


def get_auth_service() -> AuthService:
    # Imported here: runs and projects depend on auth for their routes, not the other way round.
    from app.features.projects.dependencies import get_project_service
    from app.features.runs.dependencies import get_run_service

    return AuthService(
        SqlUserRepository(session_factory),
        SqlCompanyRepository(session_factory),
        get_token_issuer(),
        adopters=[get_run_service(), get_project_service()],
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> CurrentUser:
    """Every signed-in route depends on this: who's calling, from their token."""
    return who_is(credentials.credentials if credentials else None, get_token_issuer())


SignedIn = Annotated[CurrentUser, Depends(get_current_user)]
