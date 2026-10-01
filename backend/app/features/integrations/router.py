"""HTTP endpoints for integrations."""

from fastapi import APIRouter

from app.features.integrations.schemas import McpServerSummary
from app.features.integrations.service import list_servers

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/mcp-servers", response_model=list[McpServerSummary])
def mcp_servers() -> list[McpServerSummary]:
    """The MCP servers the platform knows, and whether each is switched on."""
    return list_servers()
