"""NAT (Network Address Translation) convenience tools."""

from ..models import RouterConnection
from ..server import mcp
from ._helpers import tool_request, tool_request_delete


@mcp.tool(annotations={"title": "Add NAT Rule", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_nat_add(
    connection: RouterConnection,
    chain: str,
    action: str,
    src_address: str | None = None,
    dst_address: str | None = None,
    protocol: str | None = None,
    dst_port: str | None = None,
    to_addresses: str | None = None,
    to_ports: str | None = None,
    in_interface: str | None = None,
    out_interface: str | None = None,
    comment: str | None = None,
    disabled: bool = False,
) -> str:
    """Add a NAT rule."""
    data: dict = {"chain": chain, "action": action}
    if src_address is not None:
        data["src-address"] = src_address
    if dst_address is not None:
        data["dst-address"] = dst_address
    if protocol is not None:
        data["protocol"] = protocol
    if dst_port is not None:
        data["dst-port"] = dst_port
    if to_addresses is not None:
        data["to-addresses"] = to_addresses
    if to_ports is not None:
        data["to-ports"] = to_ports
    if in_interface is not None:
        data["in-interface"] = in_interface
    if out_interface is not None:
        data["out-interface"] = out_interface
    if comment is not None:
        data["comment"] = comment
    if disabled:
        data["disabled"] = "true"
    return await tool_request(connection, "PUT", "ip/firewall/nat", data=data)


@mcp.tool(annotations={"title": "List NAT Rules", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_nat_list(connection: RouterConnection) -> str:
    """List all NAT rules."""
    return await tool_request(connection, "GET", "ip/firewall/nat")


@mcp.tool(annotations={"title": "Get NAT Rule", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_nat_get(connection: RouterConnection, id: str) -> str:
    """Get a specific NAT rule by its .id."""
    return await tool_request(connection, "GET", f"ip/firewall/nat/{id}")


@mcp.tool(annotations={"title": "Update NAT Rule", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_nat_update(
    connection: RouterConnection,
    id: str,
    data: dict,
) -> str:
    """Update a NAT rule by its .id."""
    return await tool_request(connection, "PATCH", f"ip/firewall/nat/{id}", data=data)


@mcp.tool(annotations={"title": "Remove NAT Rule", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_nat_remove(connection: RouterConnection, id: str) -> str:
    """Remove a NAT rule by its .id."""
    return await tool_request_delete(connection, "ip/firewall/nat", id)


@mcp.tool(annotations={"title": "Enable NAT Rule", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_nat_enable(connection: RouterConnection, id: str) -> str:
    """Enable a NAT rule by its .id."""
    return await tool_request(connection, "PATCH", f"ip/firewall/nat/{id}", data={"disabled": "false"})


@mcp.tool(annotations={"title": "Disable NAT Rule", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_nat_disable(connection: RouterConnection, id: str) -> str:
    """Disable a NAT rule by its .id."""
    return await tool_request(connection, "PATCH", f"ip/firewall/nat/{id}", data={"disabled": "true"})
