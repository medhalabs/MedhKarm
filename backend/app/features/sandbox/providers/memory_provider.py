"""In-memory sandbox for tests: files live in a dict, commands return prepared results."""

import uuid
from collections.abc import Callable

from app.features.sandbox.exceptions import SandboxError, SandboxNotFoundError
from app.features.sandbox.paths import safe_relative_path
from app.features.sandbox.schemas import CommandResult

CommandHandler = Callable[[str, dict[str, str]], CommandResult]


def _always_ok(command: str, files: dict[str, str]) -> CommandResult:
    return CommandResult(exit_code=0, output="")


class InMemorySandbox:
    def __init__(self, sandbox_id: str, on_command: CommandHandler) -> None:
        self._id = sandbox_id
        self._on_command = on_command
        self.files: dict[str, str] = {}
        self.commands: list[str] = []

    @property
    def id(self) -> str:
        return self._id

    async def run(self, command: str, timeout_seconds: int = 120) -> CommandResult:
        self.commands.append(command)
        return self._on_command(command, self.files)

    async def write_file(self, path: str, content: str) -> None:
        self.files[safe_relative_path(path)] = content

    async def read_file(self, path: str) -> str:
        relative = safe_relative_path(path)
        if relative not in self.files:
            raise SandboxError(f"Could not read {relative}")
        return self.files[relative]

    async def list_files(self) -> list[str]:
        return sorted(self.files)


class InMemorySandboxProvider:
    def __init__(self, on_command: CommandHandler = _always_ok) -> None:
        self._on_command = on_command
        self.sandboxes: dict[str, InMemorySandbox] = {}

    async def create(self) -> InMemorySandbox:
        sandbox = InMemorySandbox(uuid.uuid4().hex, self._on_command)
        self.sandboxes[sandbox.id] = sandbox
        return sandbox

    async def attach(self, sandbox_id: str) -> InMemorySandbox:
        if sandbox_id not in self.sandboxes:
            raise SandboxNotFoundError(f"No sandbox {sandbox_id}")
        return self.sandboxes[sandbox_id]

    async def destroy(self, sandbox_id: str) -> None:
        self.sandboxes.pop(sandbox_id, None)
