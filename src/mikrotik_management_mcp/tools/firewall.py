"""Firewall filter and address-list convenience tools."""

from ..models import RouterConnection
from ..server import mcp
from ._helpers import tool_request, tool_request_delete


@mcp.tool(annotations={"title": "Add Firewall Filter Rule", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_firewall_filter_add(
    connection: RouterConnection,
    chain: str,
    action: str,
    src_address: str | None = None,
    dst_address: str | None = None,
    protocol: str | None = None,
    dst_port: str | None = None,
    src_port: str | None = None,
    in_interface: str | None = None,
    out_interface: str | None = None,
    comment: str | None = None,
    disabled: bool = False,
) -> str:
    """Add a firewall filter rule."""
    data: dict = {"chain": chain, "action": action}
    if src_address is not None:
        data["src-address"] = src_address
    if dst_address is not None:
        data["dst-address"] = dst_address
    if protocol is not None:
        data["protocol"] = protocol
    if dst_port is not None:
        data["dst-port"] = dst_port
    if src_port is not None:
        data["src-port"] = src_port
    if in_interface is not None:
        data["in-interface"] = in_interface
    if out_interface is not None:
        data["out-interface"] = out_interface
    if comment is not None:
        data["comment"] = comment
    if disabled:
        data["disabled"] = "true"
    return await tool_request(connection, "PUT", "ip/firewall/filter", data=data)


@mcp.tool(annotations={"title": "List Firewall Filter Rules", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_firewall_filter_list(connection: RouterConnection) -> str:
    """List all firewall filter rules."""
    return await tool_request(connection, "GET", "ip/firewall/filter")


@mcp.tool(annotations={"title": "Get Firewall Filter Rule", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_firewall_filter_get(connection: RouterConnection, id: str) -> str:
    """Get a specific firewall filter rule by its .id."""
    return await tool_request(connection, "GET", f"ip/firewall/filter/{id}")


@mcp.tool(annotations={"title": "Update Firewall Filter Rule", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_firewall_filter_update(
    connection: RouterConnection,
    id: str,
    data: dict,
) -> str:
    """Update a firewall filter rule by its .id."""
    return await tool_request(connection, "PATCH", f"ip/firewall/filter/{id}", data=data)


@mcp.tool(annotations={"title": "Remove Firewall Filter Rule", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_firewall_filter_remove(connection: RouterConnection, id: str) -> str:
    """Remove a firewall filter rule by its .id."""
    return await tool_request_delete(connection, "ip/firewall/filter", id)


@mcp.tool(annotations={"title": "Enable Firewall Filter Rule", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_firewall_filter_enable(connection: RouterConnection, id: str) -> str:
    """Enable a firewall filter rule by its .id."""
    return await tool_request(connection, "PATCH", f"ip/firewall/filter/{id}", data={"disabled": "false"})


@mcp.tool(annotations={"title": "Disable Firewall Filter Rule", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_firewall_filter_disable(connection: RouterConnection, id: str) -> str:
    """Disable a firewall filter rule by its .id."""
    return await tool_request(connection, "PATCH", f"ip/firewall/filter/{id}", data={"disabled": "true"})


@mcp.tool(annotations={"title": "Add Firewall Address List Entry", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_firewall_address_list_add(
    connection: RouterConnection,
    list: str,
    address: str,
    comment: str | None = None,
    timeout: str | None = None,
) -> str:
    """Add an entry to a firewall address list."""
    data: dict = {"list": list, "address": address}
    if comment is not None:
        data["comment"] = comment
    if timeout is not None:
        data["timeout"] = timeout
    return await tool_request(connection, "PUT", "ip/firewall/address-list", data=data)


@mcp.tool(annotations={"title": "List Firewall Address Lists", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_firewall_address_list_list(connection: RouterConnection) -> str:
    """List all firewall address list entries."""
    return await tool_request(connection, "GET", "ip/firewall/address-list")


@mcp.tool(annotations={"title": "Remove Firewall Address List Entry", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_firewall_address_list_remove(connection: RouterConnection, id: str) -> str:
    """Remove a firewall address list entry by its .id."""
    return await tool_request_delete(connection, "ip/firewall/address-list", id)
