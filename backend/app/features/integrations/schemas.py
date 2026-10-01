"""MCP servers the platform can run, and what each agent may do with them."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class McpServer(BaseModel):
    """One entry in the catalog (mcp_servers.toml). Secrets are never written here: `env`
    lists the names of environment variables passed through to the server."""

    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")  # also the prefix of its tool names
    title: str
    description: str
    transport: Literal["stdio", "http"]
    command: str = ""  # stdio: the program; "{python}" means this backend's Python
    args: list[str] = Field(default_factory=list)
    url: str = ""  # http: the server's streamable-HTTP endpoint
    env: list[str] = Field(default_factory=list)  # environment variable names to pass on
    enabled: bool = True  # False = listed, but not started (needs a token, a download, ...)
    timeout_seconds: int = Field(default=30, ge=1, le=300)

    @model_validator(mode="after")
    def _transport_settings(self) -> "McpServer":
        if self.transport == "stdio" and not self.command:
            raise ValueError(f"server {self.id}: stdio needs a command")
        if self.transport == "http" and not self.url:
            raise ValueError(f"server {self.id}: http needs a url")
        return self


class McpAccess(BaseModel):
    """What one role may use on one server (in the team template)."""

    server: str
    tools: list[str] = Field(default_factory=lambda: ["*"])  # names or patterns, e.g. "get_*"
    read_only: bool = True  # only tools the server marks read-only
    max_calls: int = Field(default=20, ge=1, le=500)  # per task


class McpServerSummary(BaseModel):
    id: str
    title: str
    description: str
    transport: str
    enabled: bool
