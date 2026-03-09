"""IP address convenience tools."""

from ..models import RouterConnection
from ..server import mcp
from ._helpers import tool_request, tool_request_delete


@mcp.tool(annotations={"title": "Add IP Address", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_ip_address_add(
    connection: RouterConnection,
    address: str,
    interface: str,
    comment: str | None = None,
    disabled: bool = False,
) -> str:
    """Add an IP address to an interface."""
    data = {"address": address, "interface": interface}
    if comment is not None:
        data["comment"] = comment
    if disabled:
        data["disabled"] = "true"
    return await tool_request(connection, "PUT", "ip/address", data=data)


@mcp.tool(annotations={"title": "List IP Addresses", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_ip_address_list(connection: RouterConnection) -> str:
    """List all IP addresses configured on the router."""
    return await tool_request(connection, "GET", "ip/address")


@mcp.tool(annotations={"title": "Remove IP Address", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_ip_address_remove(connection: RouterConnection, id: str) -> str:
    """Remove an IP address by its .id."""
    return await tool_request_delete(connection, "ip/address", id)
