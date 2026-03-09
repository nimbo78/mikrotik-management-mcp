"""Interface, VLAN, and Bridge convenience tools."""

from ..models import RouterConnection
from ..server import mcp
from ._helpers import tool_request, tool_request_delete


@mcp.tool(annotations={"title": "List Interfaces", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_interface_list(connection: RouterConnection) -> str:
    """List all interfaces on the router."""
    return await tool_request(connection, "GET", "interface")


@mcp.tool(annotations={"title": "Get Interface", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_interface_get(connection: RouterConnection, name: str) -> str:
    """Get details of a specific interface by name."""
    return await tool_request(connection, "GET", f"interface/{name}")


@mcp.tool(annotations={"title": "Enable Interface", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_interface_enable(connection: RouterConnection, id: str) -> str:
    """Enable an interface by its .id."""
    return await tool_request(connection, "PATCH", f"interface/{id}", data={"disabled": "false"})


@mcp.tool(annotations={"title": "Disable Interface", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_interface_disable(connection: RouterConnection, id: str) -> str:
    """Disable an interface by its .id."""
    return await tool_request(connection, "PATCH", f"interface/{id}", data={"disabled": "true"})


@mcp.tool(annotations={"title": "Add VLAN Interface", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_vlan_add(
    connection: RouterConnection,
    name: str,
    vlan_id: int,
    interface: str,
    comment: str | None = None,
) -> str:
    """Create a VLAN interface."""
    data = {"name": name, "vlan-id": str(vlan_id), "interface": interface}
    if comment is not None:
        data["comment"] = comment
    return await tool_request(connection, "PUT", "interface/vlan", data=data)


@mcp.tool(annotations={"title": "List VLAN Interfaces", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_vlan_list(connection: RouterConnection) -> str:
    """List all VLAN interfaces."""
    return await tool_request(connection, "GET", "interface/vlan")


@mcp.tool(annotations={"title": "Remove VLAN Interface", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_vlan_remove(connection: RouterConnection, id: str) -> str:
    """Remove a VLAN interface by its .id."""
    return await tool_request_delete(connection, "interface/vlan", id)


@mcp.tool(annotations={"title": "Add Bridge", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_bridge_add(
    connection: RouterConnection,
    name: str,
    comment: str | None = None,
) -> str:
    """Create a bridge interface."""
    data = {"name": name}
    if comment is not None:
        data["comment"] = comment
    return await tool_request(connection, "PUT", "interface/bridge", data=data)


@mcp.tool(annotations={"title": "Add Bridge Port", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_bridge_port_add(
    connection: RouterConnection,
    bridge: str,
    interface: str,
    comment: str | None = None,
) -> str:
    """Add an interface as a port to a bridge."""
    data = {"bridge": bridge, "interface": interface}
    if comment is not None:
        data["comment"] = comment
    return await tool_request(connection, "PUT", "interface/bridge/port", data=data)


@mcp.tool(annotations={"title": "List Bridge Ports", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_bridge_port_list(connection: RouterConnection) -> str:
    """List all bridge ports."""
    return await tool_request(connection, "GET", "interface/bridge/port")


@mcp.tool(annotations={"title": "Remove Bridge Port", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_bridge_port_remove(connection: RouterConnection, id: str) -> str:
    """Remove a bridge port by its .id."""
    return await tool_request_delete(connection, "interface/bridge/port", id)
