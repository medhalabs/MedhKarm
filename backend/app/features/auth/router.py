"""Sign up, log in, and who's signed in. Logging out is the frontend forgetting the token."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.features.auth.dependencies import SignedIn, get_auth_service
from app.features.auth.schemas import LogIn, Me, Session, SignUp
from app.features.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
Service = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/signup", response_model=Session, status_code=status.HTTP_201_CREATED)
async def sign_up(body: SignUp, service: Service) -> Session:
    return await service.sign_up(body)


@router.post("/login", response_model=Session)
async def log_in(body: LogIn, service: Service) -> Session:
    return await service.log_in(body)


@router.get("/me", response_model=Me)
async def me(who: SignedIn, service: Service) -> Me:
    return await service.me(who)
