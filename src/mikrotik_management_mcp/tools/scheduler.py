"""Scheduler convenience tools."""

from ..models import RouterConnection
from ..server import mcp
from ._helpers import tool_request, tool_request_delete


@mcp.tool(annotations={"title": "Add Scheduler Entry", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_scheduler_add(
    connection: RouterConnection,
    name: str,
    on_event: str,
    start_time: str | None = None,
    interval: str | None = None,
    comment: str | None = None,
    disabled: bool = False,
) -> str:
    """Add a scheduler entry.

    Args:
        connection: MikroTik device connection parameters.
        name: Scheduler entry name.
        on_event: Script to execute (RouterOS commands).
        start_time: When to start (e.g. "startup", "00:00:00").
        interval: Repeat interval (e.g. "1d", "01:00:00").
        comment: Optional comment.
        disabled: Whether the entry starts disabled.
    """
    data: dict = {"name": name, "on-event": on_event}
    if start_time is not None:
        data["start-time"] = start_time
    if interval is not None:
        data["interval"] = interval
    if comment is not None:
        data["comment"] = comment
    if disabled:
        data["disabled"] = "true"
    return await tool_request(connection, "PUT", "system/scheduler", data=data)


@mcp.tool(annotations={"title": "List Scheduler Entries", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_scheduler_list(connection: RouterConnection) -> str:
    """List all scheduler entries."""
    return await tool_request(connection, "GET", "system/scheduler")


@mcp.tool(annotations={"title": "Remove Scheduler Entry", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_scheduler_remove(connection: RouterConnection, id: str) -> str:
    """Remove a scheduler entry by its .id."""
    return await tool_request_delete(connection, "system/scheduler", id)
