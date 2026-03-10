"""Simple queue convenience tools for bandwidth management."""

from ..models import RouterConnection
from ..server import mcp
from ._helpers import tool_request, tool_request_delete


@mcp.tool(annotations={"title": "Add Simple Queue", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_queue_simple_add(
    connection: RouterConnection,
    name: str,
    target: str,
    max_limit: str | None = None,
    burst_limit: str | None = None,
    burst_threshold: str | None = None,
    burst_time: str | None = None,
    comment: str | None = None,
    disabled: bool = False,
) -> str:
    """Add a simple queue for bandwidth control.

    Args:
        connection: MikroTik device connection parameters.
        name: Queue name.
        target: Target address or subnet (e.g. "10.0.0.100/32", "10.0.0.0/24").
        max_limit: Max bandwidth in "upload/download" format (e.g. "10M/10M", "5M/1M").
        burst_limit: Burst bandwidth in "upload/download" format (e.g. "20M/20M").
        burst_threshold: Burst threshold in "upload/download" format (e.g. "8M/8M").
        burst_time: Burst time in "upload/download" format (e.g. "10/10").
        comment: Optional comment.
        disabled: Whether the queue starts disabled.
    """
    data: dict = {"name": name, "target": target}
    if max_limit is not None:
        data["max-limit"] = max_limit
    if burst_limit is not None:
        data["burst-limit"] = burst_limit
    if burst_threshold is not None:
        data["burst-threshold"] = burst_threshold
    if burst_time is not None:
        data["burst-time"] = burst_time
    if comment is not None:
        data["comment"] = comment
    if disabled:
        data["disabled"] = "true"
    return await tool_request(connection, "PUT", "queue/simple", data=data)


@mcp.tool(annotations={"title": "List Simple Queues", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_queue_simple_list(connection: RouterConnection) -> str:
    """List all simple queues."""
    return await tool_request(connection, "GET", "queue/simple")


@mcp.tool(annotations={"title": "Update Simple Queue", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_queue_simple_update(
    connection: RouterConnection,
    id: str,
    max_limit: str | None = None,
    burst_limit: str | None = None,
    burst_threshold: str | None = None,
    burst_time: str | None = None,
    target: str | None = None,
    comment: str | None = None,
) -> str:
    """Update a simple queue by its .id.

    Args:
        connection: MikroTik device connection parameters.
        id: Queue .id (e.g. "*1").
        max_limit: New max bandwidth in "upload/download" format.
        burst_limit: New burst bandwidth.
        burst_threshold: New burst threshold.
        burst_time: New burst time.
        target: New target address.
        comment: New comment.
    """
    data: dict = {}
    if max_limit is not None:
        data["max-limit"] = max_limit
    if burst_limit is not None:
        data["burst-limit"] = burst_limit
    if burst_threshold is not None:
        data["burst-threshold"] = burst_threshold
    if burst_time is not None:
        data["burst-time"] = burst_time
    if target is not None:
        data["target"] = target
    if comment is not None:
        data["comment"] = comment
    return await tool_request(connection, "PATCH", f"queue/simple/{id}", data=data)


@mcp.tool(annotations={"title": "Remove Simple Queue", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_queue_simple_remove(connection: RouterConnection, id: str) -> str:
    """Remove a simple queue by its .id."""
    return await tool_request_delete(connection, "queue/simple", id)


@mcp.tool(annotations={"title": "Enable Simple Queue", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_queue_simple_enable(connection: RouterConnection, id: str) -> str:
    """Enable a simple queue by its .id (e.g. re-enable a suspended customer)."""
    return await tool_request(connection, "PATCH", f"queue/simple/{id}", data={"disabled": "false"})


@mcp.tool(annotations={"title": "Disable Simple Queue", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_queue_simple_disable(connection: RouterConnection, id: str) -> str:
    """Disable a simple queue by its .id (e.g. suspend customer for non-payment)."""
    return await tool_request(connection, "PATCH", f"queue/simple/{id}", data={"disabled": "true"})
