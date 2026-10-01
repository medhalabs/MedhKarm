"""Application settings, read from environment variables (and `.env` in development)."""

from functools import lru_cache
from typing import Literal

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
    # gpt-oss:20b: 0 errors in the eval suite; gpt-oss:120b hit Ollama Cloud 500s on 1 in 4 tasks.
    default_model: str = "ollama_chat/gpt-oss:20b"
    ollama_api_base: str = "https://ollama.com"
    ollama_api_key: SecretStr | None = None

    # Sandbox
    sandbox_image: str = "python:3.13-slim"
    # Python + Node + test tools, built from backend/sandbox-image/ (see features/evals.md)
    eval_sandbox_image: str = "medhkarm-sandbox:dev"

    # Which team template runs builds (app/features/teams/templates/<id>.toml)
    team_template: str = "software"

    # Daily standup: covers 24 hours up to this hour, in this time zone
    standup_timezone: str = "Asia/Kolkata"
    standup_hour: int = 9
    # A run with no activity for this long (and not waiting for approval) is reported as stalled
    standup_stall_minutes: int = 120
    # The worker queues each day's standup once it's past STANDUP_HOUR
    standup_schedule: bool = True

    # Background jobs (Postgres job queue, see docs/technical/features/jobs.md)
    worker_concurrency: int = 2  # jobs one worker process runs at once
    worker_poll_seconds: float = 2.0
    job_lease_seconds: int = 60  # a dead worker's job is picked up again after this
    job_retry_seconds: int = 30  # first retry delay; doubles each attempt
    build_max_attempts: int = 3  # tries per build job (each continues from the last checkpoint)

    # Developer engine: "builtin" (ToolLoopEngine + plain Docker sandbox)
    # or "openhands" (OpenHands agent + OpenHands agent-server sandbox)
    developer_engine: Literal["builtin", "openhands"] = "builtin"
    # Keep the image tag equal to the installed openhands-sdk version.
    openhands_server_image: str = "ghcr.io/openhands/agent-server:1.50.1-python"
    openhands_max_iterations: int = 50
    # Built-in engine: most tasks need 6-10 steps; 15 cut off several (eval run, 2026-10-01).
    builtin_max_steps: int = 25  # used when the team template sets no max_steps
    # Offer the apply_patch tool (OpenAI patch format). Off: doubled tokens on gpt-oss:120b.
    builtin_apply_patch: bool = False

    @property
    def psycopg_database_url(self) -> str:
        """Plain `postgresql://` URL for libraries that use psycopg (e.g. LangGraph checkpoints)."""
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
