"""LLMProvider that replays prepared responses. For tests: no network, fully predictable."""

from app.features.models.schemas import LLMResponse, Message, ToolSpec


class ScriptedLLMProvider:
    def __init__(self, responses: list[LLMResponse], model: str = "scripted") -> None:
        self._responses = list(responses)
        self._model = model
        self.calls: list[list[Message]] = []

    @property
    def model_name(self) -> str:
        return self._model

    async def complete(
        self, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> LLMResponse:
        self.calls.append(list(messages))
        if not self._responses:
            raise AssertionError("ScriptedLLMProvider ran out of responses")
        return self._responses.pop(0)
