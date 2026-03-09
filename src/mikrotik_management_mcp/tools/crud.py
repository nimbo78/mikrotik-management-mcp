"""CRUD tools for MikroTik RouterOS resources."""

import json

import httpx

from ..client import RouterOSClient, RouterOSError
from ..models import RouterConnection
from ..security import check_target_allowed
from ..server import mcp


@mcp.tool(
    name="ros_get",
    annotations={
        "title": "Get RouterOS Resources",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def ros_get(
    connection: RouterConnection,
    path: str,
    id: str | None = None,
    proplist: str | None = None,
    query: dict | None = None,
) -> str:
    """Read/list resources from any RouterOS menu path.

    Args:
        connection: MikroTik device connection parameters.
        path: RouterOS menu path (e.g. 'ip/address', 'interface').
        id: Specific record ID (e.g. '*1') or name (e.g. 'ether1').
        proplist: Comma-separated properties to return (e.g. 'address,interface').
        query: Key-value filter pairs (e.g. {"network": "10.0.0.0"}).
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    try:
        request_path = path
        if id is not None:
            request_path = f"{path}/{id}"

        params: dict[str, str] | None = None
        if proplist is not None or query is not None:
            params = {}
            if proplist is not None:
                params[".proplist"] = proplist
            if query is not None:
                params.update(query)

        result = await RouterOSClient.request(connection, "GET", request_path, params=params)
        return json.dumps(result, indent=2)
    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}. Check host, port, and network connectivity."
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond within the timeout period."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"


@mcp.tool(
    name="ros_add",
    annotations={
        "title": "Add RouterOS Record",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def ros_add(
    connection: RouterConnection,
    path: str,
    data: dict,
) -> str:
    """Create a new record in any RouterOS menu.

    Args:
        connection: MikroTik device connection parameters.
        path: RouterOS menu path (e.g. 'ip/address', 'ip/firewall/filter').
        data: Fields for the new record (e.g. {"address": "10.0.0.1/24", "interface": "ether1"}).
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    try:
        result = await RouterOSClient.request(connection, "PUT", path, data=data)
        return json.dumps(result, indent=2)
    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}. Check host, port, and network connectivity."
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond within the timeout period."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"


@mcp.tool(
    name="ros_update",
    annotations={
        "title": "Update RouterOS Record",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def ros_update(
    connection: RouterConnection,
    path: str,
    id: str,
    data: dict,
) -> str:
    """Update an existing RouterOS record by its .id.

    Args:
        connection: MikroTik device connection parameters.
        path: RouterOS menu path (e.g. 'ip/address').
        id: Record ID to update (e.g. '*1').
        data: Fields to update (e.g. {"comment": "updated", "disabled": "true"}).
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    try:
        result = await RouterOSClient.request(
            connection, "PATCH", f"{path}/{id}", data=data
        )
        return json.dumps(result, indent=2)
    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}. Check host, port, and network connectivity."
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond within the timeout period."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"


@mcp.tool(
    name="ros_remove",
    annotations={
        "title": "Remove RouterOS Record",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def ros_remove(
    connection: RouterConnection,
    path: str,
    id: str,
) -> str:
    """Delete a RouterOS record by its .id.

    Args:
        connection: MikroTik device connection parameters.
        path: RouterOS menu path (e.g. 'ip/address').
        id: Record ID to delete (e.g. '*1').
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    try:
        await RouterOSClient.request(connection, "DELETE", f"{path}/{id}")
        return json.dumps({"success": True, "removed": id}, indent=2)
    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}. Check host, port, and network connectivity."
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond within the timeout period."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"
