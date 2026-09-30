from typing import Any, Protocol

from app.features.workflows.state import BuildState


class BuildNode(Protocol):
    """A step in the build graph: reads the state, returns the fields it changes."""

    async def __call__(self, state: BuildState) -> dict[str, Any]: ...
