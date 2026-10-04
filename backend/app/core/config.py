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

    # Sign-in: signs session tokens. Required outside development (any long random string).
    auth_secret: SecretStr | None = None
    auth_token_days: int = 30

    # Models (LiteLLM model names, e.g. "ollama_chat/gpt-oss:120b")
    # gpt-oss:20b: 0 errors in the eval suite; gpt-oss:120b hit Ollama Cloud 500s on 1 in 4 tasks.
    default_model: str = "ollama_chat/gpt-oss:20b"
    ollama_api_base: str = "https://ollama.com"
    ollama_api_key: SecretStr | None = None

    # Sandbox
    # Python + Node + pytest, built from backend/sandbox-image/ on first use. A bare
    # python:3.13-slim has no pytest, and developers then faked it (see workflows/guards.py).
    sandbox_image: str = "medhkarm-sandbox:4"
    # Python + Node + test tools, built from backend/sandbox-image/ (see features/evals.md)
    eval_sandbox_image: str = "medhkarm-sandbox:4"
    # Where runs' sandboxes live: "docker" (this machine) or "daytona" (hosted, for customers'
    # code from the beta on; docs/11-hosted-sandbox.md). Daytona needs DAYTONA_API_KEY.
    sandbox_provider: Literal["docker", "daytona"] = "docker"
    daytona_api_key: SecretStr | None = None
    daytona_target: str = "us"
    daytona_snapshot: str | None = None  # a prepared snapshot of our image; else built from it

    # GitHub: clone founders' private repositories and open pull requests with released work.
    # A fine-grained token with Contents and Pull requests (read and write) on those repos.
    # Without it, public repositories still clone; released work isn't pushed.
    github_token: SecretStr | None = None

    # Which team template runs builds (app/features/teams/templates/<id>.toml)
    team_template: str = "software"

    # DevOps: previews and production deploys on Vercel (unset: nothing is deployed)
    vercel_token: SecretStr | None = None
    vercel_team: str | None = None  # team slug; default: the token's own scope

    # Nightly eval suite (the worker runs it between EVAL_NIGHTLY_HOUR and 4 hours later, local
    # time in STANDUP_TIMEZONE; once per day and engine). Off by default: it uses model quota.
    eval_nightly: bool = False
    eval_nightly_hour: int = 2
    eval_nightly_engines: list[Literal["builtin", "openhands"]] = ["builtin"]
    eval_nightly_parallel: int = 2

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
    # Code graph (Graphify, in the sandbox image): adds the most connected code to the codebase
    # map and gives developers `explain_symbol`. An experiment: compare evals with and without.
    code_graph: bool = False
    # Offer the apply_patch tool (OpenAI patch format). Off: doubled tokens on gpt-oss:120b.
    builtin_apply_patch: bool = False

    @property
    def psycopg_database_url(self) -> str:
        """Plain `postgresql://` URL for libraries that use psycopg (e.g. LangGraph checkpoints)."""
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
