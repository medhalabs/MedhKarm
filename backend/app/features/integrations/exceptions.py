class InvalidServerCatalogError(Exception):
    """mcp_servers.toml can't be used (bad TOML, missing settings, duplicate ids)."""
