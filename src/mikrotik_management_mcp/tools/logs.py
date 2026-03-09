"""Log viewing convenience tools."""

from ..models import RouterConnection
from ..server import mcp
from ._helpers import tool_request


@mcp.tool(annotations={"title": "Get System Logs", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_log_get(connection: RouterConnection) -> str:
    """Get system log entries."""
    return await tool_request(connection, "GET", "log")


@mcp.tool(annotations={"title": "Search Logs by Topic", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_log_search_topic(connection: RouterConnection, topic: str) -> str:
    """Search log entries by topic using POST with .query syntax.

    Args:
        connection: MikroTik device connection parameters.
        topic: Topic to filter by (e.g. "system", "firewall", "dhcp").
    """
    return await tool_request(
        connection, "POST", "log/print",
        data={".query": [f"topics~{topic}"]},
    )


@mcp.tool(annotations={"title": "Filter Logs by Severity", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_log_filter_severity(connection: RouterConnection, severity: str) -> str:
    """Filter log entries by severity level using POST with .query syntax.

    Args:
        connection: MikroTik device connection parameters.
        severity: Severity to filter by (e.g. "error", "warning", "info").
    """
    return await tool_request(
        connection, "POST", "log/print",
        data={".query": [f"topics~{severity}"]},
    )
