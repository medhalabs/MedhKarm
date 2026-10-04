"""The Daytona provider against a fake Daytona client: commands, files, and waking a sandbox
that stopped while its run waited at the gate."""

from types import SimpleNamespace
from typing import Any

import pytest

from app.features.sandbox.exceptions import SandboxError, SandboxNotFoundError
from app.features.sandbox.providers.daytona_provider import DaytonaSandboxProvider


class FakeRemote:
    def __init__(self, sandbox_id: str) -> None:
        self.id = sandbox_id
        self.state = "started"
        self.files: dict[str, bytes] = {}
        self.commands: list[tuple[str, str | None]] = []
        self.process = SimpleNamespace(exec=self._exec)
        self.fs = SimpleNamespace(upload_file=self._upload, download_file=self._download)

    async def _exec(self, command: str, cwd: str | None = None, timeout: int | None = None) -> Any:  # noqa: ASYNC109 (Daytona's own signature)
        self.commands.append((command, cwd))
        return SimpleNamespace(exit_code=3 if "fail" in command else 0, result="out")

    async def _upload(self, data: bytes, dst: str) -> None:
        self.files[dst] = data

    async def _download(self, path: str) -> bytes:
        if path not in self.files:
            raise RuntimeError("404")
        return self.files[path]

    async def start(self, timeout: float = 60) -> None:  # noqa: ASYNC109 (Daytona's own signature)
        self.state = "started"


class FakeClient:
    def __init__(self) -> None:
        self.sandboxes: dict[str, FakeRemote] = {}
        self.created: list[Any] = []

    async def create(self, params: Any = None, *, timeout: float = 60) -> FakeRemote:  # noqa: ASYNC109 (Daytona's own signature)
        self.created.append(params)
        remote = FakeRemote(f"sb-{len(self.sandboxes) + 1}")
        self.sandboxes[remote.id] = remote
        return remote

    async def get(self, sandbox_id_or_name: str) -> FakeRemote:
        if sandbox_id_or_name not in self.sandboxes:
            raise RuntimeError("not found")
        return self.sandboxes[sandbox_id_or_name]

    async def delete(self, sandbox: Any, timeout: float = 60) -> None:  # noqa: ASYNC109 (Daytona's own signature)
        self.sandboxes.pop(sandbox.id)


async def test_runs_commands_and_files_in_the_workspace() -> None:
    client = FakeClient()
    provider = DaytonaSandboxProvider(client, snapshot="medhkarm-sandbox-4")
    sandbox = await provider.create()

    result = await sandbox.run("npm test", timeout_seconds=60)
    await sandbox.write_file("app/page.tsx", "export default 1")

    assert (result.exit_code, result.output) == (0, "out")
    remote = client.sandboxes[sandbox.id]
    assert remote.commands[1] == ("timeout 60 sh -c 'npm test'", "/workspace")
    assert await sandbox.read_file("app/page.tsx") == "export default 1"
    assert (await sandbox.run("fail")).exit_code == 3
    with pytest.raises(SandboxError):
        await sandbox.read_file("missing.txt")
    assert client.created[0].snapshot == "medhkarm-sandbox-4"


async def test_a_stopped_sandbox_wakes_up_with_its_files() -> None:
    client = FakeClient()
    provider = DaytonaSandboxProvider(client, snapshot="s")
    sandbox = await provider.create()
    await sandbox.write_file("notes.txt", "kept")
    client.sandboxes[sandbox.id].state = "SandboxState.STOPPED"

    again = await provider.attach(sandbox.id)

    assert client.sandboxes[sandbox.id].state == "started"
    assert await again.read_file("notes.txt") == "kept"
    await provider.destroy(sandbox.id)
    await provider.destroy(sandbox.id)  # twice is fine
    with pytest.raises(SandboxNotFoundError):
        await provider.attach(sandbox.id)
