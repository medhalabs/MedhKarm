"""Sandbox on Daytona: hosted, isolated machines for customers' code (decided Oct 5, 2026;
see docs/11-hosted-sandbox.md). Same image as the local Docker sandbox, built from
backend/sandbox-image/ (or a prepared Daytona snapshot), with the workspace at /workspace.

A sandbox stops after `auto_stop_minutes` without activity and keeps its files, so a run
waiting days at the founder's gate costs storage only; `attach` starts it again."""

import shlex
from pathlib import Path, PurePosixPath
from typing import Any, Protocol

from app.features.sandbox.exceptions import SandboxError, SandboxNotFoundError
from app.features.sandbox.paths import safe_relative_path
from app.features.sandbox.schemas import CommandResult

WORKSPACE = "/workspace"
LABELS = {"medhkarm": "sandbox"}
STOPPED = {"stopped", "archived"}
LIST_COMMAND = (
    "find . \\( -name node_modules -o -name __pycache__ -o -name venv -o -name '.?*' \\)"
    " -prune -o -type f -print | sed 's|^./||' | sort"
)


class DaytonaClient(Protocol):
    """The parts of daytona.AsyncDaytona we use (a fake stands in for it in tests)."""

    async def create(self, params: Any = None, *, timeout: float = 60) -> Any: ...  # noqa: ASYNC109 (Daytona's own signature)

    async def get(self, sandbox_id_or_name: str) -> Any: ...

    async def delete(self, sandbox: Any, timeout: float = 60) -> None: ...  # noqa: ASYNC109 (Daytona's own signature)


class DaytonaSandbox:
    def __init__(self, remote: Any) -> None:
        self._remote = remote

    @property
    def id(self) -> str:
        return str(self._remote.id)

    async def run(self, command: str, timeout_seconds: int = 120) -> CommandResult:
        wrapped = f"timeout {timeout_seconds} sh -c {shlex.quote(command)}"
        try:
            response = await self._remote.process.exec(
                wrapped, cwd=WORKSPACE, timeout=timeout_seconds + 30
            )
        except Exception as exc:  # the SDK raises its own errors for network or API trouble
            raise SandboxError(f"Daytona couldn't run the command: {exc}") from exc
        code = response.exit_code
        return CommandResult(
            exit_code=code if code is not None else -1, output=response.result or ""
        )

    async def write_file(self, path: str, content: str) -> None:
        relative = safe_relative_path(path)
        parent = str(PurePosixPath(WORKSPACE, relative).parent)
        await self.run(f"mkdir -p {shlex.quote(parent)}")
        try:
            await self._remote.fs.upload_file(content.encode("utf-8"), f"{WORKSPACE}/{relative}")
        except Exception as exc:
            raise SandboxError(f"Could not write {relative}: {exc}") from exc

    async def read_file(self, path: str) -> str:
        relative = safe_relative_path(path)
        try:
            data = await self._remote.fs.download_file(f"{WORKSPACE}/{relative}")
        except Exception as exc:
            raise SandboxError(f"Could not read {relative}: {exc}") from exc
        if data is None:
            raise SandboxError(f"Could not read {relative}")
        return bytes(data).decode("utf-8", errors="replace")

    async def list_files(self) -> list[str]:
        result = await self.run(LIST_COMMAND)
        return [line for line in result.output.splitlines() if line]


class DaytonaSandboxProvider:
    def __init__(
        self,
        client: DaytonaClient,
        image_dir: Path | None = None,
        snapshot: str | None = None,
        cpu: int = 2,
        memory_gb: int = 2,
        disk_gb: int = 10,
        auto_stop_minutes: int = 30,
    ) -> None:
        """`snapshot`: a prepared Daytona snapshot of our image (fastest); otherwise the image
        is built from `image_dir`'s Dockerfile (Daytona caches the build)."""
        self._client = client
        self._image_dir = image_dir
        self._snapshot = snapshot
        self._resources = (cpu, memory_gb, disk_gb)
        self._auto_stop = auto_stop_minutes

    async def create(self) -> DaytonaSandbox:
        from daytona import (
            CreateSandboxFromImageParams,
            CreateSandboxFromSnapshotParams,
            Image,
            Resources,
        )

        common: dict[str, Any] = {"labels": LABELS, "auto_stop_interval": self._auto_stop}
        params: Any
        if self._snapshot:
            params = CreateSandboxFromSnapshotParams(snapshot=self._snapshot, **common)
        elif self._image_dir:
            cpu, memory, disk = self._resources
            params = CreateSandboxFromImageParams(
                image=Image.from_dockerfile(self._image_dir / "Dockerfile"),
                resources=Resources(cpu=cpu, memory=memory, disk=disk),
                **common,
            )
        else:
            raise SandboxError("Daytona needs DAYTONA_SNAPSHOT or the sandbox image folder")
        try:
            remote = await self._client.create(params, timeout=900)
        except Exception as exc:
            raise SandboxError(f"Daytona couldn't create a sandbox: {exc}") from exc
        sandbox = DaytonaSandbox(remote)
        await sandbox.run(f"mkdir -p {WORKSPACE}")
        return sandbox

    async def attach(self, sandbox_id: str) -> DaytonaSandbox:
        try:
            remote = await self._client.get(sandbox_id)
        except Exception as exc:
            raise SandboxNotFoundError(f"No sandbox {sandbox_id}: {exc}") from exc
        if str(getattr(remote, "state", "")).lower().rsplit(".", 1)[-1] in STOPPED:
            await remote.start(timeout=300)  # stopped while waiting: files are still there
        return DaytonaSandbox(remote)

    async def destroy(self, sandbox_id: str) -> None:
        try:
            remote = await self._client.get(sandbox_id)
        except Exception:
            return  # already gone
        await self._client.delete(remote)
