"""Signing up, logging in and who's signed in."""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.features.companies.schemas import Company

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _email(value: str) -> str:
    cleaned = value.strip().lower()
    if not EMAIL.match(cleaned):
        raise ValueError("Enter a valid email address")
    return cleaned


class SignUp(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=200)
    name: str = Field(default="", max_length=80)
    company_name: str = Field(min_length=2, max_length=120)  # the founder's business

    _check_email = field_validator("email")(_email)


class LogIn(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=200)

    _check_email = field_validator("email")(_email)


class User(BaseModel):
    id: str
    email: str
    name: str
    company_id: str
    created_at: datetime


class StoredUser(User):
    password_hash: str


class Session(BaseModel):
    """What signing up or logging in returns: the token goes in every request's
    `Authorization: Bearer <token>` header."""

    token: str
    user: User
    company: Company


class Me(BaseModel):
    user: User
    company: Company


class CurrentUser(BaseModel):
    """Who's calling, from their token: what every other feature needs."""

    user_id: str
    company_id: str
