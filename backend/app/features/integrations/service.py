"""What the rest of the platform asks of integrations: the catalog, and tool sources for a role."""

import logging

from app.features.developer_engine.interfaces import ToolSource
from app.features.integrations.loader import access_problems, load_servers
from app.features.integrations.mcp_source import McpToolSource
from app.features.integrations.schemas import McpAccess, McpServerSummary

logger = logging.getLogger(__name__)

__all__ = ["access_problems", "list_servers", "tool_sources"]


def list_servers() -> list[McpServerSummary]:
    return [
        McpServerSummary(
            id=s.id,
            title=s.title,
            description=s.description,
            transport=s.transport,
            enabled=s.enabled,
        )
        for s in load_servers().values()
    ]


def tool_sources(grants: list[McpAccess]) -> list[ToolSource]:
    """One tool source per granted server. Disabled servers are skipped (and logged), so a
    template can name a server before it's switched on."""
    servers = load_servers()
    sources: list[ToolSource] = []
    for grant in grants:
        server = servers[grant.server]
        if not server.enabled:
            logger.warning("MCP server %s is disabled; its tools are not offered", server.id)
            continue
        sources.append(McpToolSource(server, grant))
    return sources
