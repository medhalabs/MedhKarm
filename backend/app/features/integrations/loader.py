"""Reads the MCP server catalog (mcp_servers.toml) and checks role access against it."""

import tomllib
from functools import lru_cache
from pathlib import Path

from pydantic import ValidationError

from app.features.integrations.exceptions import InvalidServerCatalogError
from app.features.integrations.schemas import McpAccess, McpServer

CATALOG = Path(__file__).parent / "mcp_servers.toml"


@lru_cache
def load_servers(path: Path = CATALOG) -> dict[str, McpServer]:
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        servers = [McpServer.model_validate(entry) for entry in raw.get("servers", [])]
    except (tomllib.TOMLDecodeError, ValidationError) as exc:
        raise InvalidServerCatalogError(f"{path.name}: {exc}") from exc
    ids = [server.id for server in servers]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise InvalidServerCatalogError(f"{path.name}: duplicate servers {', '.join(duplicates)}")
    return {server.id: server for server in servers}


def access_problems(role_id: str, grants: list[McpAccess]) -> list[str]:
    """Grants naming servers that aren't in the catalog (checked when a template loads)."""
    known = load_servers()
    problems = [
        f"role {role_id}: unknown MCP server {grant.server!r}"
        for grant in grants
        if grant.server not in known
    ]
    servers = [grant.server for grant in grants]
    problems += [
        f"role {role_id}: MCP server {s!r} listed twice"
        for s in sorted({s for s in servers if servers.count(s) > 1})
    ]
    return problems
