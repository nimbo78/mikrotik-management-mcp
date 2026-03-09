"""DNS convenience tools."""

from ..models import RouterConnection
from ..server import mcp
from ._helpers import tool_request, tool_request_delete


@mcp.tool(annotations={"title": "Get DNS Configuration", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_dns_get(connection: RouterConnection) -> str:
    """Get the current DNS configuration."""
    return await tool_request(connection, "GET", "ip/dns")


@mcp.tool(annotations={"title": "Set DNS Servers", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_dns_set_servers(
    connection: RouterConnection,
    servers: str,
    allow_remote_requests: bool = False,
) -> str:
    """Set DNS servers. Uses POST to ip/dns/set (singleton config, not a record list).

    Args:
        connection: MikroTik device connection parameters.
        servers: Comma-separated DNS server addresses (e.g. "8.8.8.8,8.8.4.4").
        allow_remote_requests: Allow other devices to use this router as DNS server.
    """
    data: dict = {"servers": servers}
    if allow_remote_requests:
        data["allow-remote-requests"] = "true"
    return await tool_request(connection, "POST", "ip/dns/set", data=data)


@mcp.tool(annotations={"title": "Add Static DNS Entry", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_dns_static_add(
    connection: RouterConnection,
    name: str,
    address: str,
    ttl: str | None = None,
    comment: str | None = None,
) -> str:
    """Add a static DNS entry."""
    data: dict = {"name": name, "address": address}
    if ttl is not None:
        data["ttl"] = ttl
    if comment is not None:
        data["comment"] = comment
    return await tool_request(connection, "PUT", "ip/dns/static", data=data)


@mcp.tool(annotations={"title": "List Static DNS Entries", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_dns_static_list(connection: RouterConnection) -> str:
    """List all static DNS entries."""
    return await tool_request(connection, "GET", "ip/dns/static")


@mcp.tool(annotations={"title": "Remove Static DNS Entry", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_dns_static_remove(connection: RouterConnection, id: str) -> str:
    """Remove a static DNS entry by its .id."""
    return await tool_request_delete(connection, "ip/dns/static", id)


@mcp.tool(annotations={"title": "Flush DNS Cache", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_dns_cache_flush(connection: RouterConnection) -> str:
    """Flush the DNS cache."""
    return await tool_request(connection, "POST", "ip/dns/cache/flush")
