from datetime import datetime

from pydantic import BaseModel


class Artifact(BaseModel):
    """A file a run produced for the founder: today, the demo video of QA's browser test."""

    id: int
    run_id: str
    kind: str  # "demo"
    name: str
    content_type: str
    size: int  # bytes
    created_at: datetime


class Content(BaseModel):
    """An artifact with its bytes, for serving."""

    artifact: Artifact
    data: bytes
