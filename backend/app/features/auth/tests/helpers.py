"""For other features' API tests: act as a signed-in founder without a real token."""

from fastapi import FastAPI

from app.features.auth.dependencies import get_current_user
from app.features.auth.schemas import CurrentUser

SIGNED_IN = CurrentUser(user_id="u1", company_id="c1")
OTHER_COMPANY = CurrentUser(user_id="u2", company_id="c2")


def sign_in(app: FastAPI, who: CurrentUser = SIGNED_IN) -> None:
    app.dependency_overrides[get_current_user] = lambda: who
