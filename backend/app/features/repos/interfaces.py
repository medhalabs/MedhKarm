"""Where founders' repositories live. GitHub now; GitLab or Bitbucket would be new classes."""

from typing import Protocol

from app.features.repos.schemas import Delivery, RepoSource
from app.features.sandbox.interfaces import Sandbox


class CodeGraph(Protocol):
    async def describe(self, sandbox: Sandbox) -> str:
        """A short text about how the project's code connects, for the map; "" if unknown."""
        ...


class RepoHost(Protocol):
    async def clone(self, source: RepoSource, sandbox: Sandbox) -> str:
        """Clone the repository into the sandbox's (empty) workspace; returns the commit."""
        ...

    async def deliver(
        self, source: RepoSource, sandbox: Sandbox, branch: str, title: str, body: str
    ) -> Delivery:
        """Commit the workspace's changes to `branch`, push it and open a pull request.
        Safe to repeat: an existing branch is overwritten and an open pull request reused."""
        ...
