from typing import Protocol

from app.features.models.schemas import LLMResponse, Message, ToolSpec


class LLMProvider(Protocol):
    """A chat model that can answer and call tools. Agents use this, never a vendor SDK."""

    @property
    def model_name(self) -> str: ...

    async def complete(
        self, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> LLMResponse: ...
