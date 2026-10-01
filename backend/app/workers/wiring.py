"""Chooses concrete implementations from settings. Entry points (CLI, API, workers) call
this; features only ever see interfaces (dependency inversion)."""

import os

from app.core.config import Settings
from app.features.developer_engine.interfaces import DeveloperEngine
from app.features.models.interfaces import LLMProvider
from app.features.models.service import resolve_model_config
from app.features.sandbox.interfaces import SandboxProvider


def build_engine(settings: Settings, llm: LLMProvider) -> tuple[DeveloperEngine, SandboxProvider]:
    """Pick the developer engine and the sandbox it needs. Imports are local so the
    heavy OpenHands packages load only when that engine is chosen."""
    if settings.developer_engine == "openhands":
        os.environ.setdefault("OPENHANDS_SUPPRESS_BANNER", "1")
        from app.features.developer_engine.engines.openhands_engine import OpenHandsEngine
        from app.features.sandbox.providers.openhands_provider import OpenHandsSandboxProvider

        engine = OpenHandsEngine(
            resolve_model_config(settings), max_iterations=settings.openhands_max_iterations
        )
        return engine, OpenHandsSandboxProvider(settings.openhands_server_image)

    from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
    from app.features.sandbox.providers.docker_provider import DockerSandboxProvider

    return ToolLoopEngine(llm), DockerSandboxProvider(settings.sandbox_image)
