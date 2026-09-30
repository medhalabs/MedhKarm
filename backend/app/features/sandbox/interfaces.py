"""Sandbox contracts. Code that runs agent-written code depends only on these.

Implementations: Docker (local development) now; a hosted VM sandbox from Phase 2.
Paths are always relative to the sandbox's workspace directory.
"""

from typing import Protocol

from app.features.sandbox.schemas import CommandResult


class SandboxCommands(Protocol):
    async def run(self, command: str, timeout_seconds: int = 120) -> CommandResult: ...


class SandboxFiles(Protocol):
    async def write_file(self, path: str, content: str) -> None: ...

    async def read_file(self, path: str) -> str: ...

    async def list_files(self) -> list[str]: ...


class Sandbox(SandboxCommands, SandboxFiles, Protocol):
    @property
    def id(self) -> str: ...


class SandboxProvider(Protocol):
    """Creates sandboxes, and re-attaches to one by id (e.g. after a worker restart)."""

    async def create(self) -> Sandbox: ...

    async def attach(self, sandbox_id: str) -> Sandbox: ...

    async def destroy(self, sandbox_id: str) -> None: ...
