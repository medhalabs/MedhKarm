"""LLMProvider backed by LiteLLM: one class for Ollama, Claude, OpenAI, Gemini and others."""

import json
from typing import Any

import litellm

from app.features.models.exceptions import ModelCallError
from app.features.models.schemas import LLMResponse, Message, TokenUsage, ToolCall, ToolSpec


class LiteLLMProvider:
    def __init__(
        self,
        model: str,
        api_base: str | None = None,
        api_key: str | None = None,
        num_retries: int = 3,
    ) -> None:
        self._model = model
        self._api_base = api_base
        self._api_key = api_key
        self._num_retries = num_retries  # hosted models return occasional 5xx errors

    @property
    def model_name(self) -> str:
        return self._model

    async def complete(
        self, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> LLMResponse:
        try:
            response = await litellm.acompletion(
                model=self._model,
                messages=messages,
                tools=tools or None,
                api_base=self._api_base,
                api_key=self._api_key,
                num_retries=self._num_retries,
            )
        except Exception as exc:  # LiteLLM raises many provider-specific types
            raise ModelCallError(f"{self._model} call failed: {exc}") from exc

        message = response.choices[0].message
        usage = getattr(response, "usage", None)
        return LLMResponse(
            content=message.content,
            tool_calls=[_to_tool_call(call) for call in (message.tool_calls or [])],
            usage=TokenUsage(
                prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            ),
        )


def _to_tool_call(call: Any) -> ToolCall:
    raw = call.function.arguments
    try:
        arguments = json.loads(raw) if isinstance(raw, str) else dict(raw or {})
    except json.JSONDecodeError:
        arguments = {"_raw": raw}
    return ToolCall(id=call.id, name=call.function.name, arguments=arguments)
