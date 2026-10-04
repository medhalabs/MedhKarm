"""Deploying a project's work: what kind of app it is, and where it went."""

from enum import StrEnum

from pydantic import BaseModel


class AppKind(StrEnum):
    STATIC = "static"  # plain pages (index.html)
    NEXTJS = "nextjs"
    FASTAPI = "fastapi"
    NONE = "none"  # a library or scripts: nothing to put online


class DeployFile(BaseModel):
    path: str
    data: str  # base64


class Deployment(BaseModel):
    id: str = ""
    url: str = ""  # https://…
    target: str = "preview"  # "preview" | "production"
    state: str = ""  # READY, ERROR, CANCELED, or a timeout
    kind: AppKind = AppKind.NONE
    inspector_url: str = ""  # the host's page with build logs
    error: str = ""

    @property
    def ready(self) -> bool:
        return self.state == "READY" and bool(self.url)
