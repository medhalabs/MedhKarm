import pytest

from app.features.integrations.loader import load_servers
from app.features.integrations.schemas import McpAccess
from app.features.integrations.service import access_problems, list_servers, tool_sources
from app.features.teams.exceptions import InvalidTemplateError
from app.features.teams.loader import TEMPLATES_DIR, parse_template


def test_catalog_loads_with_disabled_servers_listed() -> None:
    servers = load_servers()

    assert servers["python_docs"].enabled
    assert not servers["github"].enabled
    assert {s.id for s in list_servers()} >= {"python_docs", "fetch", "github"}


def test_disabled_servers_offer_no_tools() -> None:
    sources = tool_sources([McpAccess(server="python_docs"), McpAccess(server="github")])

    assert [s.name for s in sources] == ["python_docs"]


def test_templates_can_only_name_catalog_servers() -> None:
    assert access_problems("developer", [McpAccess(server="jira")]) == [
        "role developer: unknown MCP server 'jira'"
    ]
    text = (
        (TEMPLATES_DIR / "software.toml")
        .read_text()
        .replace('server = "python_docs"', 'server = "jira"')
    )
    with pytest.raises(InvalidTemplateError, match="unknown MCP server 'jira'"):
        parse_template(text)
