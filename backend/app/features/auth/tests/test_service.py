"""Sign-up, log-in, tokens, and the first account adopting earlier records."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.features.auth.exceptions import EmailTakenError, InvalidCredentialsError, NotSignedInError
from app.features.auth.memory_repository import InMemoryUserRepository
from app.features.auth.passwords import check_password, hash_password
from app.features.auth.schemas import LogIn, SignUp
from app.features.auth.service import AuthService
from app.features.auth.tokens import TokenIssuer
from app.features.companies.memory_repository import InMemoryCompanyRepository


class Adopter:
    def __init__(self) -> None:
        self.adopted_by: list[str] = []

    async def adopt_unowned(self, company_id: str) -> int:
        self.adopted_by.append(company_id)
        return 3


def service(adopter: Adopter | None = None) -> AuthService:
    return AuthService(
        InMemoryUserRepository(),
        InMemoryCompanyRepository(),
        TokenIssuer("test-secret"),
        [adopter] if adopter else [],
    )


SIGN_UP = SignUp(email=" Pavan@Example.com ", password="long enough", company_name="Pavan Labs")


async def test_sign_up_creates_a_company_and_a_working_session() -> None:
    adopter = Adopter()
    auth = service(adopter)

    session = await auth.sign_up(SIGN_UP)

    assert (session.user.email, session.company.name) == ("pavan@example.com", "Pavan Labs")
    who = auth.current(session.token)
    assert (who.user_id, who.company_id) == (session.user.id, session.company.id)
    assert adopter.adopted_by == [session.company.id]  # the first account adopts earlier work
    me = await auth.me(who)
    assert me.company.id == session.company.id


async def test_only_the_first_account_adopts_and_emails_are_unique() -> None:
    adopter = Adopter()
    auth = service(adopter)
    await auth.sign_up(SIGN_UP)

    await auth.sign_up(
        SignUp(email="ravi@example.com", password="12345678", company_name="Ravi Co")
    )

    assert len(adopter.adopted_by) == 1
    with pytest.raises(EmailTakenError):
        await auth.sign_up(SIGN_UP)


async def test_log_in_needs_the_right_password() -> None:
    auth = service()
    await auth.sign_up(SIGN_UP)

    session = await auth.log_in(LogIn(email="pavan@example.com", password="long enough"))

    assert session.company.name == "Pavan Labs"
    with pytest.raises(InvalidCredentialsError):
        await auth.log_in(LogIn(email="pavan@example.com", password="wrong password"))
    with pytest.raises(InvalidCredentialsError):
        await auth.log_in(LogIn(email="nobody@example.com", password="long enough"))


def test_tokens_must_be_genuine_and_unexpired() -> None:
    tokens = TokenIssuer("secret", days=30)
    token = tokens.issue("u1", "c1")
    old = tokens.issue("u1", "c1", now=datetime.now(UTC) - timedelta(days=31))

    assert tokens.read(token) is not None
    assert tokens.read(old) is None
    assert TokenIssuer("another secret").read(token) is None
    assert tokens.read(token + "x") is None
    with pytest.raises(NotSignedInError):
        service().current(None)


def test_passwords_are_hashed_and_checked() -> None:
    stored = hash_password("correct horse")

    assert "correct horse" not in stored
    assert check_password("correct horse", stored)
    assert not check_password("wrong horse", stored)
    assert not check_password("x", "garbage")


def test_sign_up_checks_its_fields() -> None:
    with pytest.raises(ValidationError):
        SignUp(email="not-an-email", password="long enough", company_name="X Co")
    with pytest.raises(ValidationError):
        SignUp(email="a@b.co", password="short", company_name="X Co")
