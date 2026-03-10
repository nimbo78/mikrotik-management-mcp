"""DHCP server convenience tools."""

from ..models import RouterConnection
from ..server import mcp
from ._helpers import tool_request, tool_request_delete


@mcp.tool(annotations={"title": "Add DHCP Server", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_dhcp_server_add(
    connection: RouterConnection,
    name: str,
    interface: str,
    address_pool: str,
    disabled: bool = False,
) -> str:
    """Create a DHCP server on an interface."""
    data = {
        "name": name,
        "interface": interface,
        "address-pool": address_pool,
    }
    if disabled:
        data["disabled"] = "true"
    return await tool_request(connection, "PUT", "ip/dhcp-server", data=data)


@mcp.tool(annotations={"title": "List DHCP Servers", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_dhcp_server_list(connection: RouterConnection) -> str:
    """List all DHCP servers."""
    return await tool_request(connection, "GET", "ip/dhcp-server")


@mcp.tool(annotations={"title": "Remove DHCP Server", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_dhcp_server_remove(connection: RouterConnection, id: str) -> str:
    """Remove a DHCP server by its .id."""
    return await tool_request_delete(connection, "ip/dhcp-server", id)


@mcp.tool(annotations={"title": "Add DHCP Network", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_dhcp_network_add(
    connection: RouterConnection,
    address: str,
    gateway: str,
    dns_server: str | None = None,
    domain: str | None = None,
) -> str:
    """Add a DHCP network definition."""
    data = {"address": address, "gateway": gateway}
    if dns_server is not None:
        data["dns-server"] = dns_server
    if domain is not None:
        data["domain"] = domain
    return await tool_request(connection, "PUT", "ip/dhcp-server/network", data=data)


@mcp.tool(annotations={"title": "Add IP Pool", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_pool_add(
    connection: RouterConnection,
    name: str,
    ranges: str,
    comment: str | None = None,
) -> str:
    """Add an IP address pool."""
    data = {"name": name, "ranges": ranges}
    if comment is not None:
        data["comment"] = comment
    return await tool_request(connection, "PUT", "ip/pool", data=data)


@mcp.tool(annotations={"title": "List DHCP Leases", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_dhcp_lease_list(connection: RouterConnection) -> str:
    """List all DHCP leases."""
    return await tool_request(connection, "GET", "ip/dhcp-server/lease")


@mcp.tool(annotations={"title": "Make DHCP Lease Static", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_dhcp_lease_make_static(connection: RouterConnection, id: str) -> str:
    """Convert a dynamic DHCP lease to a static lease by its .id.

    This gives the device a permanent IP address reservation.

    Args:
        connection: MikroTik device connection parameters.
        id: The .id of the DHCP lease to make static.
    """
    return await tool_request(connection, "POST", "ip/dhcp-server/lease/make-static", data={".id": id})


@mcp.tool(annotations={"title": "List DHCP Clients", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_dhcp_client_list(connection: RouterConnection) -> str:
    """List all DHCP clients (interfaces getting IP via DHCP, typically WAN)."""
    return await tool_request(connection, "GET", "ip/dhcp-client")


@mcp.tool(annotations={"title": "Release DHCP Client", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True})
async def ros_dhcp_client_release(connection: RouterConnection, id: str) -> str:
    """Release and renew a DHCP client lease by its .id.

    Common for resetting WAN DHCP to get a new IP from ISP.

    Args:
        connection: MikroTik device connection parameters.
        id: The .id of the DHCP client to release.
    """
    return await tool_request(connection, "POST", "ip/dhcp-client/release", data={".id": id})
