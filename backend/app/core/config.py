"""Application settings, read from environment variables (and `.env` in development)."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "MedhKarm API"
    app_version: str = "0.1.0"
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://medhkarm:medhkarm@localhost:5442/medhkarm"
    redis_url: str = "redis://localhost:6379/0"

    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Models (LiteLLM model names, e.g. "ollama_chat/gpt-oss:120b")
    default_model: str = "ollama_chat/gpt-oss:120b"
    ollama_api_base: str = "https://ollama.com"
    ollama_api_key: SecretStr | None = None

    # Sandbox
    sandbox_image: str = "python:3.13-slim"

    @property
    def psycopg_database_url(self) -> str:
        """Plain `postgresql://` URL for libraries that use psycopg (e.g. LangGraph checkpoints)."""
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
