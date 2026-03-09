"""User management convenience tools."""

from ..models import RouterConnection
from ..server import mcp
from ._helpers import tool_request, tool_request_delete


@mcp.tool(annotations={"title": "Add User", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_user_add(
    connection: RouterConnection,
    name: str,
    group: str,
    password: str | None = None,
    comment: str | None = None,
) -> str:
    """Add a new user."""
    data: dict = {"name": name, "group": group}
    if password is not None:
        data["password"] = password
    if comment is not None:
        data["comment"] = comment
    return await tool_request(connection, "PUT", "user", data=data)


@mcp.tool(annotations={"title": "List Users", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_user_list(connection: RouterConnection) -> str:
    """List all users."""
    return await tool_request(connection, "GET", "user")


@mcp.tool(annotations={"title": "Remove User", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_user_remove(connection: RouterConnection, id: str) -> str:
    """Remove a user by their .id."""
    return await tool_request_delete(connection, "user", id)


@mcp.tool(annotations={"title": "List Active User Sessions", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_user_active_list(connection: RouterConnection) -> str:
    """List active user sessions."""
    return await tool_request(connection, "GET", "user/active")


@mcp.tool(annotations={"title": "List User Groups", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_user_group_list(connection: RouterConnection) -> str:
    """List all user groups."""
    return await tool_request(connection, "GET", "user/group")
