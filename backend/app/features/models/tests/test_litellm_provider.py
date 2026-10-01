from types import SimpleNamespace
from typing import Any

import litellm
import pytest

from app.core.config import Settings
from app.features.models.exceptions import ModelCallError
from app.features.models.providers.litellm_provider import LiteLLMProvider
from app.features.models.service import build_provider, resolve_model_config


def _fake_response(content: str | None, tool_calls: list[Any]) -> SimpleNamespace:
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)


def _fake_call(name: str, arguments: str) -> SimpleNamespace:
    return SimpleNamespace(id="call_1", function=SimpleNamespace(name=name, arguments=arguments))


async def test_parses_tool_calls_and_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_acompletion(**kwargs: Any) -> SimpleNamespace:
        return _fake_response(None, [_fake_call("write_file", '{"path": "a.py", "content": "x"}')])

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    result = await LiteLLMProvider("ollama_chat/test").complete([{"role": "user", "content": "hi"}])

    assert result.tool_calls[0].name == "write_file"
    assert result.tool_calls[0].arguments == {"path": "a.py", "content": "x"}
    assert result.usage.total_tokens == 15


async def test_keeps_unparseable_arguments_raw(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_acompletion(**kwargs: Any) -> SimpleNamespace:
        return _fake_response(None, [_fake_call("run_command", "not json")])

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    result = await LiteLLMProvider("ollama_chat/test").complete([])

    assert result.tool_calls[0].arguments == {"_raw": "not json"}


async def test_wraps_provider_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    async def failing_acompletion(**kwargs: Any) -> SimpleNamespace:
        raise RuntimeError("boom")

    monkeypatch.setattr(litellm, "acompletion", failing_acompletion)

    with pytest.raises(ModelCallError):
        await LiteLLMProvider("ollama_chat/test").complete([])


def test_non_ollama_models_use_provider_env_vars() -> None:
    config = resolve_model_config(Settings(ollama_api_key="secret"), "anthropic/claude-x")

    assert config.api_base is None
    assert config.api_key is None


def test_model_config_never_shows_the_key() -> None:
    config = resolve_model_config(Settings(ollama_api_key="secret"), "ollama_chat/gpt-oss:20b")

    assert config.api_key == "secret"
    assert "secret" not in repr(config)


def test_ollama_models_get_ollama_base_and_key() -> None:
    settings = Settings(ollama_api_base="https://ollama.example", ollama_api_key="secret")

    provider = build_provider(settings, "ollama_chat/gpt-oss:20b")

    assert provider.model_name == "ollama_chat/gpt-oss:20b"
    assert isinstance(provider, LiteLLMProvider)
    assert provider._api_base == "https://ollama.example"
    assert provider._api_key == "secret"
