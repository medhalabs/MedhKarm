from typing import Protocol

from app.features.deploys.schemas import DeployFile, Deployment


class DeployTarget(Protocol):
    """Where apps go online. Vercel now; Netlify, Render or Fly would be new classes."""

    async def deploy(
        self, name: str, files: list[DeployFile], production: bool, framework: str | None
    ) -> Deployment:
        """Upload the files as project `name`, build, and wait until it's ready or failed."""
        ...
