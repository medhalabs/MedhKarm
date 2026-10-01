"""Sandbox on an OpenHands agent-server container (local Docker).

The OpenHands agent runs inside this container, and our own steps (QA re-running tests)
use the same container through the agent server's HTTP API, so both see one workspace.

We start the container with the Docker SDK instead of OpenHands' `DockerWorkspace`, because
`DockerWorkspace` stops its container when the Python object is garbage-collected, which
would break a run that pauses for approval and resumes in another process.
"""

import asyncio
import platform
import shlex
import time
import urllib.request
from pathlib import PurePosixPath

import docker
from docker.errors import NotFound
from docker.models.containers import Container
from openhands.sdk.workspace import RemoteWorkspace

from app.features.sandbox.exceptions import SandboxError, SandboxNotFoundError
from app.features.sandbox.paths import safe_relative_path
from app.features.sandbox.schemas import CommandResult

WORKSPACE = "/workspace/project"  # the agent server keeps its own logs in /workspace
SERVER_PORT = "8000/tcp"
LABEL = "medhkarm.sandbox"
HEALTH_TIMEOUT_SECONDS = 120


def _docker_platform() -> str:
    return "linux/arm64" if platform.machine() in ("arm64", "aarch64") else "linux/amd64"


class OpenHandsSandbox:
    def __init__(self, container_id: str, server_url: str) -> None:
        self._container_id = container_id
        self._server_url = server_url
        self._workspace = RemoteWorkspace(host=server_url, working_dir=WORKSPACE)

    @property
    def id(self) -> str:
        return self._container_id

    @property
    def agent_server_url(self) -> str:
        return self._server_url

    @property
    def workspace_dir(self) -> str:
        return WORKSPACE

    async def run(self, command: str, timeout_seconds: int = 120) -> CommandResult:
        wrapped = f"timeout {timeout_seconds} sh -c {shlex.quote(command)}"
        result = await asyncio.to_thread(
            self._workspace.execute_command, wrapped, WORKSPACE, float(timeout_seconds + 10)
        )
        exit_code = 124 if result.timeout_occurred else result.exit_code
        return CommandResult(exit_code=exit_code, output=result.stdout + result.stderr)

    async def write_file(self, path: str, content: str) -> None:
        relative = safe_relative_path(path)
        target = PurePosixPath(WORKSPACE, relative)
        await self.run(f"mkdir -p {shlex.quote(str(target.parent))}")
        result = await asyncio.to_thread(
            self._workspace.file_upload, content.encode("utf-8"), str(target)
        )
        if not result.success:
            raise SandboxError(f"Could not write {relative}: {result.error}")

    async def read_file(self, path: str) -> str:
        relative = safe_relative_path(path)
        result = await self.run(f"cat {shlex.quote(relative)}")
        if not result.ok:
            raise SandboxError(f"Could not read {relative}: {result.output.strip()}")
        return result.output

    async def list_files(self) -> list[str]:
        result = await self.run(
            "find . -type f -not -path '*/.*' -not -path '*/__pycache__/*' | sed 's|^./||' | sort"
        )
        return [line for line in result.output.splitlines() if line]


class OpenHandsSandboxProvider:
    def __init__(self, image: str, mem_limit: str = "4g") -> None:
        self._image = image
        self._mem_limit = mem_limit
        self._client = docker.from_env()

    async def create(self) -> OpenHandsSandbox:
        container = await asyncio.to_thread(self._start_container)
        url = await asyncio.to_thread(self._server_url, container)
        await asyncio.to_thread(_wait_for_health, url, container)
        sandbox = OpenHandsSandbox(str(container.id), url)
        await sandbox.run(f"mkdir -p {WORKSPACE}")
        return sandbox

    async def attach(self, sandbox_id: str) -> OpenHandsSandbox:
        try:
            container = await asyncio.to_thread(self._client.containers.get, sandbox_id)
        except NotFound as exc:
            raise SandboxNotFoundError(f"No sandbox {sandbox_id}") from exc
        url = await asyncio.to_thread(self._server_url, container)
        await asyncio.to_thread(_wait_for_health, url, container)
        return OpenHandsSandbox(str(container.id), url)

    async def destroy(self, sandbox_id: str) -> None:
        try:
            container = await asyncio.to_thread(self._client.containers.get, sandbox_id)
        except NotFound:
            return
        await asyncio.to_thread(container.remove, force=True)

    def _start_container(self) -> Container:
        try:
            self._client.images.get(self._image)
        except docker.errors.ImageNotFound:
            self._client.images.pull(self._image, platform=_docker_platform())
        return self._client.containers.run(
            self._image,
            command=["--host", "0.0.0.0", "--port", "8000"],
            detach=True,
            platform=_docker_platform(),
            ports={SERVER_PORT: ("127.0.0.1", None)},  # random free port, localhost only
            labels={LABEL: "true", "medhkarm.sandbox.kind": "openhands"},
            mem_limit=self._mem_limit,
            nano_cpus=2_000_000_000,  # 2 CPUs
            ulimits=[docker.types.Ulimit(name="nofile", soft=65536, hard=65536)],
        )

    def _server_url(self, container: Container) -> str:
        container.reload()
        bindings = container.attrs["NetworkSettings"]["Ports"].get(SERVER_PORT) or []
        if not bindings:
            raise SandboxError(f"Agent server port not published for {container.id}")
        return f"http://127.0.0.1:{bindings[0]['HostPort']}"


def _wait_for_health(url: str, container: Container) -> None:
    deadline = time.monotonic() + HEALTH_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=2) as response:
                if 200 <= response.status < 300:
                    return
        except OSError:
            pass
        container.reload()
        if container.status not in ("created", "running"):
            logs = container.logs(tail=20).decode("utf-8", errors="replace")
            raise SandboxError(f"Agent server exited ({container.status}):\n{logs}")
        time.sleep(1)
    raise SandboxError(f"Agent server at {url} not healthy after {HEALTH_TIMEOUT_SECONDS}s")
