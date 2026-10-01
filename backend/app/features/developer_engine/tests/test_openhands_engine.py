import pytest

from app.features.developer_engine.engines.openhands_engine import OpenHandsEngine
from app.features.developer_engine.exceptions import IncompatibleSandboxError
from app.features.developer_engine.schemas import DevTask
from app.features.models.schemas import ModelConfig
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider


async def test_refuses_sandboxes_without_an_agent_server() -> None:
    engine = OpenHandsEngine(ModelConfig(model="ollama_chat/test"))
    sandbox = await InMemorySandboxProvider().create()

    with pytest.raises(IncompatibleSandboxError):
        await engine.run_task(DevTask(description="x", test_command="true"), sandbox)
