"""MCP tool for executing arbitrary RouterOS commands via POST."""

import json

import httpx

from ..client import RouterOSClient, RouterOSError
from ..models import RouterConnection
from ..security import check_target_allowed
from ..server import mcp


@mcp.tool(
    name="ros_command",
    annotations={
        "title": "Execute RouterOS Command",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def ros_command(
    connection: RouterConnection,
    path: str,
    data: dict | None = None,
) -> str:
    """Execute any RouterOS command via POST.

    This is the most flexible tool -- it can do anything the RouterOS
    console can, including print with queries, ping, torch, export, etc.

    Examples:
        - path="ip/address/print" to list addresses via POST
        - path="tool/ping", data={"address": "8.8.8.8", "count": "4"}
        - path="system/reboot" to reboot the router
        - path="ip/firewall/filter/print",
          data={".proplist": ["chain","action"], ".query": ["chain=input"]}

    Args:
        connection: RouterOS device connection parameters.
        path: Full command path (e.g. "ip/address/print", "tool/ping").
        data: Optional command parameters as a JSON-compatible dict.

    Returns:
        JSON-formatted result string on success, or an error message.
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    try:
        result = await RouterOSClient.request(
            conn=connection,
            method="POST",
            path=path,
            data=data,
            timeout=60.0,
        )
        return json.dumps(result, indent=2)
    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return (
            f"Connection Error: Cannot reach {connection.host}:{connection.port}. "
            f"Check host, port, and network connectivity."
        )
    except httpx.TimeoutException:
        return (
            f"Timeout: Router {connection.host} did not respond within the timeout period. "
            f"Consider adding limiting parameters (e.g. count for ping) to prevent long-running commands."
        )
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"
