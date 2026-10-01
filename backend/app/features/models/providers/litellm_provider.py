"""LLMProvider backed by LiteLLM: one class for Ollama, Claude, OpenAI, Gemini and others."""

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import litellm
from litellm.exceptions import (
    APIConnectionError,
    BadGatewayError,
    InternalServerError,
    RateLimitError,
    ServiceUnavailableError,
    Timeout,
)

from app.features.models.exceptions import ModelCallError
from app.features.models.schemas import LLMResponse, Message, TokenUsage, ToolCall, ToolSpec

logger = logging.getLogger(__name__)

# Temporary provider problems worth waiting out. Anything else (bad key, bad request) fails at once.
RETRYABLE: tuple[type[Exception], ...] = (
    InternalServerError,
    ServiceUnavailableError,
    BadGatewayError,
    RateLimitError,
    APIConnectionError,
    Timeout,
)

Sleep = Callable[[float], Awaitable[None]]


class LiteLLMProvider:
    def __init__(
        self,
        model: str,
        api_base: str | None = None,
        api_key: str | None = None,
        num_retries: int = 5,
        backoff_seconds: float = 2.0,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self._model = model
        self._api_base = api_base
        self._api_key = api_key
        # Hosted models (Ollama Cloud free tier especially) return bursts of 5xx errors;
        # waiting 2, 4, 8, 16, 32 s rides out short outages that instant retries don't.
        self._num_retries = num_retries
        self._backoff = backoff_seconds
        self._sleep = sleep

    @property
    def model_name(self) -> str:
        return self._model

    async def complete(
        self, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> LLMResponse:
        for attempt in range(self._num_retries + 1):
            try:
                response = await litellm.acompletion(
                    model=self._model,
                    messages=messages,
                    tools=tools or None,
                    api_base=self._api_base,
                    api_key=self._api_key,
                    num_retries=0,  # we retry ourselves, with backoff
                )
                break
            except RETRYABLE as exc:
                if attempt == self._num_retries:
                    raise ModelCallError(
                        f"{self._model} call failed after {attempt + 1} attempts: {exc}"
                    ) from exc
                delay = self._backoff * 2**attempt
                logger.warning(
                    "%s failed (%s); retrying in %.0fs", self._model, type(exc).__name__, delay
                )
                await self._sleep(delay)
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
