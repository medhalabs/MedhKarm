"""Where a founder's updates go (email, WhatsApp) and when, and what happened when we sent."""

import re
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE = re.compile(r"^\+[1-9]\d{7,14}$")  # E.164: +91 98765 43210 → +919876543210


class Channel(StrEnum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class Update(BaseModel):
    """One message to the founder, in the shapes the channels need."""

    subject: str  # email subject
    text: str  # full plain text (email)
    short: str  # one line, at most ~900 characters (WhatsApp templates allow no line breaks)


class NotificationSettings(BaseModel):
    email: str = Field(default="", max_length=254)  # empty: no email
    whatsapp: str = Field(default="", max_length=20)  # E.164; empty: no WhatsApp
    standup_on: bool = True  # the daily standup
    standup_hour: int = Field(default=9, ge=0, le=23)  # local hour (STANDUP_TIMEZONE)
    weekly_on: bool = True  # the Monday report
    nudge_on: bool = True  # Priya's reminder when something has waited a day for you

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned and not EMAIL.match(cleaned):
            raise ValueError("Enter a valid email address")
        return cleaned

    @field_validator("whatsapp")
    @classmethod
    def _phone(cls, value: str) -> str:
        cleaned = re.sub(r"[\s()-]", "", value)
        if cleaned and not PHONE.match(cleaned):
            raise ValueError("Use the full number with country code, e.g. +919876543210")
        return cleaned


class CompanySettings(NotificationSettings):
    company_id: str
    updated_at: datetime | None = None


class Delivery(BaseModel):
    channel: Channel
    to: str
    ok: bool
    error: str = ""
