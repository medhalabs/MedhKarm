from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class Provider(StrEnum):
    """Where a model runs. A model name starts with its provider's prefix (`PREFIX`)."""

    OLLAMA = "ollama"  # Ollama Cloud
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    GROQ = "groq"
    LOCAL = "local"  # the founder's own Ollama, reached through a connector (a tunnel URL)


PREFIX: dict[Provider, str] = {
    Provider.OLLAMA: "ollama_chat/",
    Provider.ANTHROPIC: "anthropic/",
    Provider.OPENAI: "openai/",
    Provider.GEMINI: "gemini/",
    Provider.OPENROUTER: "openrouter/",
    Provider.GROQ: "groq/",
    Provider.LOCAL: "local/",
}


def provider_of(model: str) -> Provider | None:
    for provider, prefix in PREFIX.items():
        if model.startswith(prefix) and len(model) > len(prefix):
            return provider
    return None


class KeyMode(StrEnum):
    MANAGED = "managed"  # our keys for anything the founder hasn't added a key for
    OWN = "own"  # only the founder's keys: a model without one of theirs doesn't run


class ModelChoices(BaseModel):
    """What the founder chose: whose keys, the team's model, and models for single roles."""

    mode: KeyMode = KeyMode.MANAGED
    default_model: str = Field(default="", max_length=200)  # "" = the team template's models
    role_models: dict[str, str] = Field(default_factory=dict)  # role id -> model
    local_url: str = Field(default="", max_length=500)  # the connector's URL for local models

    @field_validator("default_model")
    @classmethod
    def _known_model(cls, value: str) -> str:
        value = value.strip()
        if value and provider_of(value) is None:
            raise ValueError(f"Unknown model {value!r}: start it with a provider, e.g. {_EXAMPLE}")
        return value

    @field_validator("role_models")
    @classmethod
    def _known_models(cls, value: dict[str, str]) -> dict[str, str]:
        cleaned = {role: model.strip() for role, model in value.items() if model.strip()}
        for model in cleaned.values():
            if provider_of(model) is None:
                raise ValueError(
                    f"Unknown model {model!r}: start it with a provider, e.g. {_EXAMPLE}"
                )
        return cleaned

    @field_validator("local_url")
    @classmethod
    def _url(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        if value and not value.startswith(("http://", "https://")):
            raise ValueError("The connector URL starts with https://")
        return value

    def models(self) -> set[str]:
        return {m for m in [self.default_model, *self.role_models.values()] if m}


_EXAMPLE = "anthropic/claude-sonnet-5-5"


class SavedKey(BaseModel):
    """A key the founder added: only its last characters are ever shown."""

    provider: Provider
    hint: str  # "…a1b2"


class CompanyModels(ModelChoices):
    company_id: str
    keys: list[SavedKey] = Field(default_factory=list)
    updated_at: datetime | None = None


class StoredModels(ModelChoices):
    """A company's row as stored: choices plus the sealed (encrypted) keys."""

    company_id: str
    sealed_keys: dict[Provider, str] = Field(default_factory=dict, repr=False)
    hints: dict[Provider, str] = Field(default_factory=dict)
    updated_at: datetime | None = None


class NewKey(BaseModel):
    provider: Provider
    key: str = Field(min_length=8, max_length=500, repr=False)


class KeyCheck(BaseModel):
    provider: Provider
    model: str
    ok: bool
    error: str = ""


class ModelOption(BaseModel):
    provider: Provider
    models: list[str]  # suggestions; any model the provider has can be typed in
    server_key: bool  # we can run it on our keys (managed)


class ModelsView(BaseModel):
    settings: CompanyModels
    options: list[ModelOption]
    roles: dict[str, str]  # role id -> "Kabir (CTO)", the roles that use a model
