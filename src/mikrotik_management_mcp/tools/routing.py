"""Static routing convenience tools."""

from ..models import RouterConnection
from ..server import mcp
from ._helpers import tool_request, tool_request_delete


@mcp.tool(annotations={"title": "Add Static Route", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_route_add(
    connection: RouterConnection,
    dst_address: str,
    gateway: str,
    distance: int | None = None,
    comment: str | None = None,
    disabled: bool = False,
) -> str:
    """Add a static route."""
    data: dict = {"dst-address": dst_address, "gateway": gateway}
    if distance is not None:
        data["distance"] = str(distance)
    if comment is not None:
        data["comment"] = comment
    if disabled:
        data["disabled"] = "true"
    return await tool_request(connection, "PUT", "ip/route", data=data)


@mcp.tool(annotations={"title": "List Static Routes", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_route_list(connection: RouterConnection) -> str:
    """List all routes."""
    return await tool_request(connection, "GET", "ip/route")


@mcp.tool(annotations={"title": "Remove Static Route", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_route_remove(connection: RouterConnection, id: str) -> str:
    """Remove a static route by its .id."""
    return await tool_request_delete(connection, "ip/route", id)
