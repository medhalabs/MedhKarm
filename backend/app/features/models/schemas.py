from typing import Any

from pydantic import BaseModel, Field

# Messages and tool specs use the OpenAI chat format, which LiteLLM accepts for every provider.
Message = dict[str, Any]
ToolSpec = dict[str, Any]


class ModelConfig(BaseModel):
    """A LiteLLM model name plus the endpoint and key to reach it."""

    model: str
    api_base: str | None = None
    api_key: str | None = Field(default=None, repr=False)  # never printed or logged


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class LLMResponse(BaseModel):
    content: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: TokenUsage = Field(default_factory=TokenUsage)
