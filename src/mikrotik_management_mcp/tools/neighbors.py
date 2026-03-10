"""ARP and neighbor discovery tools."""

from ..models import RouterConnection
from ..server import mcp
from ._helpers import tool_request


@mcp.tool(annotations={"title": "List ARP Entries", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_arp_list(connection: RouterConnection) -> str:
    """List all ARP entries (IP-to-MAC address mappings)."""
    return await tool_request(connection, "GET", "ip/arp")


@mcp.tool(annotations={"title": "List Neighbors", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_neighbor_list(connection: RouterConnection) -> str:
    """List discovered network neighbors (via CDP/LLDP/MNDP protocols)."""
    return await tool_request(connection, "GET", "ip/neighbor")
