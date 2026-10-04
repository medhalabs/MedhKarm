"""Sign-up, log-in and who's signed in. Each founder gets their own company; the very first
account also adopts what was made before sign-in existed (the founder's own early runs)."""

import logging

from app.features.auth.exceptions import (
    EmailTakenError,
    InvalidCredentialsError,
    NotSignedInError,
)
from app.features.auth.interfaces import DataAdopter, UserRepository
from app.features.auth.passwords import check_password, hash_password
from app.features.auth.schemas import CurrentUser, LogIn, Me, Session, SignUp, User
from app.features.auth.tokens import TokenIssuer
from app.features.companies.interfaces import CompanyRepository

logger = logging.getLogger(__name__)
# A real hash to check against when the email is unknown, so both cases take as long
_DUMMY_HASH = hash_password("not-a-real-password")


def who_is(token: str | None, tokens: TokenIssuer) -> CurrentUser:
    """The caller behind a session token; NotSignedInError when there's no valid one."""
    who = tokens.read(token) if token else None
    if who is None:
        raise NotSignedInError("Sign in to continue")
    return who


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        companies: CompanyRepository,
        tokens: TokenIssuer,
        adopters: list[DataAdopter] | None = None,
    ) -> None:
        self._users = users
        self._companies = companies
        self._tokens = tokens
        self._adopters = adopters or []

    async def sign_up(self, body: SignUp) -> Session:
        if await self._users.by_email(body.email):
            raise EmailTakenError("An account with this email already exists")
        first = await self._companies.count() == 0
        company = await self._companies.create(body.company_name.strip())
        stored = await self._users.create(
            body.email, body.name.strip(), hash_password(body.password), company.id
        )
        if first:
            for adopter in self._adopters:
                adopted = await adopter.adopt_unowned(company.id)
                logger.info("First account adopted %d earlier records", adopted)
        user = User.model_validate(stored.model_dump())
        return Session(token=self._tokens.issue(user.id, company.id), user=user, company=company)

    async def log_in(self, body: LogIn) -> Session:
        stored = await self._users.by_email(body.email)
        if not check_password(body.password, stored.password_hash if stored else _DUMMY_HASH):
            raise InvalidCredentialsError("Wrong email or password")
        assert stored is not None
        company = await self._companies.get(stored.company_id)
        if company is None:
            raise InvalidCredentialsError("Wrong email or password")
        user = User.model_validate(stored.model_dump())
        return Session(token=self._tokens.issue(user.id, company.id), user=user, company=company)

    def current(self, token: str | None) -> CurrentUser:
        return who_is(token, self._tokens)

    async def me(self, who: CurrentUser) -> Me:
        stored = await self._users.get(who.user_id)
        company = await self._companies.get(who.company_id)
        if stored is None or company is None:
            raise NotSignedInError("Sign in to continue")
        return Me(user=User.model_validate(stored.model_dump()), company=company)
