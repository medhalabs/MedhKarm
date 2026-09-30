"""Runs against real Docker. Skipped by default; run with `uv run pytest -m integration`."""

import pytest

from app.features.sandbox.exceptions import SandboxNotFoundError, UnsafePathError
from app.features.sandbox.providers.docker_provider import DockerSandboxProvider

pytestmark = pytest.mark.integration


async def test_write_run_attach_and_destroy() -> None:
    provider = DockerSandboxProvider("python:3.13-slim")
    sandbox = await provider.create()
    try:
        await sandbox.write_file("pkg/hello.py", "print('hi')\n")
        result = await sandbox.run("python pkg/hello.py")
        again = await provider.attach(sandbox.id)

        assert result.ok and result.output.strip() == "hi"
        assert await again.list_files() == ["pkg/hello.py"]
        assert (await again.read_file("pkg/hello.py")).strip() == "print('hi')"
        assert (await sandbox.run("sleep 5", timeout_seconds=1)).exit_code == 124
        with pytest.raises(UnsafePathError):
            await sandbox.write_file("../escape.txt", "no")
    finally:
        await provider.destroy(sandbox.id)

    with pytest.raises(SandboxNotFoundError):
        await provider.attach(sandbox.id)
