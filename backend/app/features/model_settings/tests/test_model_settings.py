import pytest

from app.core.tenant import company_scope
from app.features.model_settings.exceptions import MissingKeyError, ModelSettingsError
from app.features.model_settings.memory_repository import InMemoryModelSettingsRepository
from app.features.model_settings.routed import CompanyRoutedProvider
from app.features.model_settings.schemas import (
    KeyMode,
    ModelChoices,
    NewKey,
    Provider,
    provider_of,
)
from app.features.model_settings.service import ModelSettingsService
from app.features.models.exceptions import ModelCallError
from app.features.models.interfaces import LLMProvider
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ModelConfig
from app.shared.secret_box import SecretBox

DEFAULT = "ollama_chat/gpt-oss:20b"
A, B = "company-a", "company-b"


def server(model: str | None) -> ModelConfig:
    return ModelConfig(model=model or DEFAULT, api_base="https://ollama.com", api_key="ours")


class Factory:
    """Builds scripted providers and remembers each config, as LiteLLM would get it."""

    def __init__(self, fail: str | None = None) -> None:
        self.configs: list[ModelConfig] = []
        self._fail = fail

    def __call__(self, config: ModelConfig, num_retries: int = 5) -> LLMProvider:
        self.configs.append(config)
        if self._fail:
            return Failing(self._fail)
        return ScriptedLLMProvider([LLMResponse(content="OK")] * 10, config.model)


class Failing(ScriptedLLMProvider):
    def __init__(self, message: str) -> None:
        super().__init__([])
        self._message = message

    async def complete(self, messages, tools=None):  # type: ignore[no-untyped-def]
        raise ModelCallError(self._message)


def make(
    factory: Factory | None = None, servers: set[Provider] | None = None
) -> tuple[ModelSettingsService, InMemoryModelSettingsRepository]:
    repository = InMemoryModelSettingsRepository()
    service = ModelSettingsService(
        repository,
        SecretBox("test-secret"),
        server,
        {Provider.OLLAMA} if servers is None else servers,
        factory or Factory(),
    )
    return service, repository


def test_a_model_name_tells_its_provider() -> None:
    assert provider_of("anthropic/claude-sonnet-5-5") == Provider.ANTHROPIC
    assert provider_of("ollama_chat/gpt-oss:20b") == Provider.OLLAMA
    assert provider_of("local/qwen3-coder:30b") == Provider.LOCAL
    assert provider_of("claude-sonnet-5-5") is None
    assert provider_of("anthropic/") is None


def test_choices_refuse_unknown_models_and_bad_urls() -> None:
    with pytest.raises(ValueError, match="Unknown model"):
        ModelChoices(default_model="gpt-5")
    with pytest.raises(ValueError, match="https://"):
        ModelChoices(local_url="my-laptop:11434")
    assert ModelChoices(role_models={"cto": " ", "qa": "groq/openai/gpt-oss-20b"}).role_models == {
        "qa": "groq/openai/gpt-oss-20b"
    }


async def test_without_settings_every_call_runs_on_our_keys() -> None:
    service, _ = make()
    assert await service.config(None, "cto", None) == server(None)
    assert await service.config(A, "cto", "ollama_chat/gemma4:31b") == server(
        "ollama_chat/gemma4:31b"
    )


async def test_a_key_is_sealed_and_only_its_end_is_shown() -> None:
    service, repository = make()
    view = await service.add_key(A, NewKey(provider=Provider.ANTHROPIC, key=" sk-ant-secret-a1b2 "))
    assert [(k.provider, k.hint) for k in view.keys] == [(Provider.ANTHROPIC, "…a1b2")]
    sealed = repository.rows[A].sealed_keys[Provider.ANTHROPIC]
    assert "sk-ant" not in sealed
    assert "sk-ant" not in view.model_dump_json()


async def test_the_founders_model_and_key_run_their_calls() -> None:
    service, _ = make()
    await service.add_key(A, NewKey(provider=Provider.ANTHROPIC, key="sk-ant-secret-a1b2"))
    await service.save(
        A,
        ModelChoices(
            default_model="anthropic/claude-sonnet-5-5",
            role_models={"qa": "ollama_chat/gpt-oss:120b"},
        ),
    )
    cto = await service.config(A, "cto", None)
    assert (cto.model, cto.api_key) == ("anthropic/claude-sonnet-5-5", "sk-ant-secret-a1b2")
    qa = await service.config(A, "qa", None)
    assert qa == server("ollama_chat/gpt-oss:120b")  # no own Ollama key: managed, ours
    assert await service.config(B, "cto", None) == server(None)  # another company: untouched


async def test_an_own_ollama_key_goes_to_ollama_cloud() -> None:
    service, _ = make()
    await service.add_key(A, NewKey(provider=Provider.OLLAMA, key="ollama-key-9999"))
    config = await service.config(A, "developer", None)
    assert (config.model, config.api_base, config.api_key) == (
        DEFAULT,
        "https://ollama.com",
        "ollama-key-9999",
    )


async def test_on_own_keys_a_model_without_a_key_does_not_run_on_ours() -> None:
    service, _ = make()
    await service.save(A, ModelChoices(mode=KeyMode.OWN))
    with pytest.raises(MissingKeyError, match="no ollama key"):
        await service.config(A, "cto", None)


async def test_choices_that_cannot_run_are_refused() -> None:
    service, _ = make()
    with pytest.raises(ModelSettingsError, match="add your anthropic key"):
        await service.save(A, ModelChoices(default_model="anthropic/claude-sonnet-5-5"))
    with pytest.raises(ModelSettingsError, match="Add your ollama key"):
        await service.save(A, ModelChoices(mode=KeyMode.OWN, default_model=DEFAULT))
    with pytest.raises(ModelSettingsError, match="connector"):
        await service.save(A, ModelChoices(default_model="local/gpt-oss:20b"))
    await service.save(A, ModelChoices(default_model=DEFAULT))  # ours: fine


async def test_local_models_go_through_the_founders_connector() -> None:
    service, _ = make()
    await service.save(
        A,
        ModelChoices(
            mode=KeyMode.OWN,
            default_model="local/qwen3-coder:30b",
            local_url="https://my-ollama.trycloudflare.com/",
        ),
    )
    config = await service.config(A, "developer", None)
    assert config == ModelConfig(
        model="ollama_chat/qwen3-coder:30b", api_base="https://my-ollama.trycloudflare.com"
    )


async def test_a_key_sealed_with_another_secret_asks_to_be_added_again() -> None:
    service, repository = make()
    await service.add_key(A, NewKey(provider=Provider.OLLAMA, key="ollama-key-9999"))
    other = ModelSettingsService(
        repository, SecretBox("another-secret"), server, {Provider.OLLAMA}, Factory()
    )
    with pytest.raises(MissingKeyError, match="add it again"):
        await other.config(A, "cto", None)


async def test_removing_a_key_falls_back_to_ours() -> None:
    service, _ = make()
    await service.add_key(A, NewKey(provider=Provider.OLLAMA, key="ollama-key-9999"))
    view = await service.remove_key(A, Provider.OLLAMA)
    assert view.keys == []
    assert await service.config(A, "cto", None) == server(None)


async def test_checking_a_key_makes_one_call_with_it() -> None:
    factory = Factory()
    service, _ = make(factory)
    missing = await service.check(A, Provider.GROQ)
    assert (missing.ok, missing.error) == (False, "Add your groq key first")
    await service.add_key(A, NewKey(provider=Provider.GROQ, key="gsk-secret-7777"))
    check = await service.check(A, Provider.GROQ)
    assert (check.ok, check.model) == (True, "groq/openai/gpt-oss-20b")
    assert factory.configs[-1].api_key == "gsk-secret-7777"


async def test_a_refused_key_says_why() -> None:
    raw = 'call failed: GroqException - {"error":{"message":"Invalid API Key","type":"x"}}'
    service, _ = make(Factory(fail=raw))
    await service.add_key(A, NewKey(provider=Provider.GROQ, key="gsk-wrong-0000"))
    check = await service.check(A, Provider.GROQ)
    assert (check.ok, check.error) == (False, "Invalid API Key")


async def test_routed_provider_uses_the_running_companys_choice() -> None:
    factory = Factory()
    service, _ = make(factory)
    await service.add_key(A, NewKey(provider=Provider.ANTHROPIC, key="sk-ant-secret-a1b2"))
    await service.save(A, ModelChoices(role_models={"cto": "anthropic/claude-haiku-4-5-20251001"}))
    llm = CompanyRoutedProvider(service, "cto", None, factory)

    with company_scope(A):
        await llm.complete([{"role": "user", "content": "plan"}])
        assert llm.model_name == "anthropic/claude-haiku-4-5-20251001"
        assert llm.own_key is True
    with company_scope(B):
        await llm.complete([{"role": "user", "content": "plan"}])
        assert llm.model_name == DEFAULT
        assert llm.own_key is False
    assert [c.api_key for c in factory.configs] == ["sk-ant-secret-a1b2", "ours"]

    with company_scope(A):  # the same model and key reuse the built provider
        await llm.complete([{"role": "user", "content": "again"}])
    assert len(factory.configs) == 2
