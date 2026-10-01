"""Runs against real Docker with the OpenHands agent-server image (~1.2 GB).
Skipped by default; run with `uv run pytest -m integration`."""

import pytest

from app.core.config import get_settings
from app.features.sandbox.exceptions import SandboxNotFoundError
from app.features.sandbox.interfaces import AgentServerSandbox
from app.features.sandbox.providers.openhands_provider import OpenHandsSandboxProvider

pytestmark = pytest.mark.integration


async def test_agent_server_sandbox_lifecycle() -> None:
    provider = OpenHandsSandboxProvider(get_settings().openhands_server_image)
    sandbox = await provider.create()
    try:
        await sandbox.write_file("pkg/hello.py", "print('hi')\n")
        result = await sandbox.run("python3 pkg/hello.py")
        again = await provider.attach(sandbox.id)

        assert isinstance(sandbox, AgentServerSandbox)
        assert result.ok and result.output.strip() == "hi"
        assert await again.list_files() == ["pkg/hello.py"]  # agent-server logs stay outside
        assert (await sandbox.run("sleep 5", timeout_seconds=1)).exit_code == 124
    finally:
        await provider.destroy(sandbox.id)

    with pytest.raises(SandboxNotFoundError):
        await provider.attach(sandbox.id)
