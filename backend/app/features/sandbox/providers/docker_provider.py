"""Sandbox on local Docker. For development only: containers share the host kernel.

Each sandbox is one long-lived container (`sleep infinity`) with the workspace at /workspace.
The Docker SDK is synchronous, so every call runs in a thread.
"""

import asyncio
import io
import shlex
import tarfile
import time
from pathlib import PurePosixPath

import docker
from docker.errors import NotFound
from docker.models.containers import Container

from app.features.sandbox.exceptions import SandboxError, SandboxNotFoundError
from app.features.sandbox.paths import safe_relative_path
from app.features.sandbox.schemas import CommandResult

WORKSPACE = "/workspace"
LABEL = "medhkarm.sandbox"


class DockerSandbox:
    def __init__(self, container: Container) -> None:
        self._container = container

    @property
    def id(self) -> str:
        return str(self._container.id)

    async def run(self, command: str, timeout_seconds: int = 120) -> CommandResult:
        wrapped = f"timeout {timeout_seconds} sh -c {shlex.quote(command)}"
        exit_code, output = await asyncio.to_thread(
            self._container.exec_run, ["sh", "-c", wrapped], workdir=WORKSPACE, demux=False
        )
        text = (output or b"").decode("utf-8", errors="replace")
        return CommandResult(exit_code=exit_code if exit_code is not None else -1, output=text)

    async def write_file(self, path: str, content: str) -> None:
        relative = safe_relative_path(path)
        data = content.encode("utf-8")
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w") as archive:
            info = tarfile.TarInfo(name=relative)
            info.size = len(data)
            info.mtime = int(time.time())
            archive.addfile(info, io.BytesIO(data))
        parent = str(PurePosixPath(WORKSPACE, relative).parent)
        await self.run(f"mkdir -p {shlex.quote(parent)}")
        ok = await asyncio.to_thread(self._container.put_archive, WORKSPACE, buffer.getvalue())
        if not ok:
            raise SandboxError(f"Could not write {relative}")

    async def read_file(self, path: str) -> str:
        relative = safe_relative_path(path)
        result = await self.run(f"cat {shlex.quote(relative)}")
        if not result.ok:
            raise SandboxError(f"Could not read {relative}: {result.output.strip()}")
        return result.output

    async def list_files(self) -> list[str]:
        # Dependencies and caches (node_modules, venv, __pycache__, hidden folders) aren't the
        # project's own files: tens of thousands of them would swamp any listing.
        result = await self.run(
            "find . \\( -name node_modules -o -name __pycache__ -o -name venv -o -name '.?*' \\)"
            " -prune -o -type f -print | sed 's|^./||' | sort"
        )
        return [line for line in result.output.splitlines() if line]


class DockerSandboxProvider:
    def __init__(self, image: str, network_enabled: bool = True) -> None:
        self._image = image
        self._network_enabled = network_enabled
        self._client = docker.from_env()

    async def create(self) -> DockerSandbox:
        def _create() -> Container:
            try:
                self._client.images.get(self._image)
            except docker.errors.ImageNotFound:
                self._client.images.pull(self._image)
            return self._client.containers.run(
                self._image,
                command=["sleep", "infinity"],
                detach=True,
                working_dir=WORKSPACE,
                labels={LABEL: "true"},
                network_disabled=not self._network_enabled,
                mem_limit="1g",
                nano_cpus=1_000_000_000,  # 1 CPU
            )

        return DockerSandbox(await asyncio.to_thread(_create))

    async def attach(self, sandbox_id: str) -> DockerSandbox:
        try:
            container = await asyncio.to_thread(self._client.containers.get, sandbox_id)
        except NotFound as exc:
            raise SandboxNotFoundError(f"No sandbox {sandbox_id}") from exc
        return DockerSandbox(container)

    async def destroy(self, sandbox_id: str) -> None:
        try:
            container = await asyncio.to_thread(self._client.containers.get, sandbox_id)
        except NotFound:
            return
        await asyncio.to_thread(container.remove, force=True)
