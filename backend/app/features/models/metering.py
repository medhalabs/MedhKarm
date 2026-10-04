"""Counting model use per piece of work (e.g. one eval task), across every agent in it.

`metering()` opens a meter for the current asyncio context; every `MeteredLLMProvider` call
inside it (including in tasks it starts) adds its tokens. Outside a meter, the wrapper only
passes calls through, so it is always safe to wrap providers.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from pydantic import BaseModel, Field

from app.features.models.interfaces import LLMProvider
from app.features.models.schemas import LLMResponse, Message, ToolSpec


class ModelUse(BaseModel):
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class Meter(BaseModel):
    by_model: dict[str, ModelUse] = Field(default_factory=dict)

    def add(self, model: str, prompt_tokens: int, completion_tokens: int) -> None:
        use = self.by_model.setdefault(model, ModelUse())
        use.calls += 1
        use.prompt_tokens += prompt_tokens
        use.completion_tokens += completion_tokens

    @property
    def total(self) -> ModelUse:
        return ModelUse(
            calls=sum(u.calls for u in self.by_model.values()),
            prompt_tokens=sum(u.prompt_tokens for u in self.by_model.values()),
            completion_tokens=sum(u.completion_tokens for u in self.by_model.values()),
        )


_current: ContextVar[Meter | None] = ContextVar("model_meter", default=None)


@contextmanager
def metering() -> Iterator[Meter]:
    meter = Meter()
    token = _current.set(meter)
    try:
        yield meter
    finally:
        _current.reset(token)


class MeteredLLMProvider:
    """Wraps any provider; adds each call's usage to the meter that's open, if any."""

    def __init__(self, inner: LLMProvider) -> None:
        self._inner = inner

    @property
    def model_name(self) -> str:
        return self._inner.model_name

    async def complete(
        self, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> LLMResponse:
        response = await self._inner.complete(messages, tools)
        meter = _current.get()
        if meter is not None:
            meter.add(
                self._inner.model_name,
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
            )
        return response
