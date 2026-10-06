"""The waitlist: people who want to build with MedhKarm, collected from the public page."""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class JoinWaitlist(BaseModel):
    email: str = Field(max_length=254)
    name: str = Field(default="", max_length=100)
    building: str = Field(default="", max_length=600)  # what they want to build
    source: str = Field(default="", max_length=60)  # where they came from (a share link, a post)
    website: str = Field(default="", max_length=200)  # hidden field: only bots fill it in

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        value = value.strip().lower()
        if not EMAIL.match(value):
            raise ValueError("That doesn't look like an email address")
        return value

    @field_validator("name", "building", "source")
    @classmethod
    def _tidy(cls, value: str) -> str:
        return value.strip()


class Joined(BaseModel):
    ok: bool = True
    count: int  # how many are on the list, for "join N builders"


class WaitlistEntry(BaseModel):
    id: int
    email: str
    name: str
    building: str
    source: str
    created_at: datetime
    invited_at: datetime | None = None
