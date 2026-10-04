"""A company: the founder's business. Everything the teams do belongs to one."""

from datetime import datetime

from pydantic import BaseModel


class Company(BaseModel):
    id: str
    name: str
    created_at: datetime
