"""IPsec VPN convenience tools for troubleshooting and management."""

from ..models import RouterConnection
from ..server import mcp
from ._helpers import tool_request


@mcp.tool(annotations={"title": "List IPsec Peers", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_ipsec_peer_list(connection: RouterConnection) -> str:
    """List all IPsec peers (VPN tunnel endpoints)."""
    return await tool_request(connection, "GET", "ip/ipsec/peer")


@mcp.tool(annotations={"title": "List IPsec Identities", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_ipsec_identity_list(connection: RouterConnection) -> str:
    """List all IPsec identities (authentication configuration)."""
    return await tool_request(connection, "GET", "ip/ipsec/identity")


@mcp.tool(annotations={"title": "List IPsec Policies", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_ipsec_policy_list(connection: RouterConnection) -> str:
    """List all IPsec policies (which traffic goes through the tunnel)."""
    return await tool_request(connection, "GET", "ip/ipsec/policy")


@mcp.tool(annotations={"title": "List IPsec Installed SAs", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_ipsec_installed_sa_list(connection: RouterConnection) -> str:
    """List installed IPsec Security Associations (active tunnel status)."""
    return await tool_request(connection, "GET", "ip/ipsec/installed-sa")


@mcp.tool(annotations={"title": "Add IPsec Peer", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_ipsec_peer_add(
    connection: RouterConnection,
    address: str,
    exchange_mode: str = "main",
    profile: str | None = None,
    comment: str | None = None,
    disabled: bool = False,
) -> str:
    """Add an IPsec peer.

    Args:
        connection: MikroTik device connection parameters.
        address: Remote peer IP address or address/mask.
        exchange_mode: IKE exchange mode: "main", "aggressive", or "ike2". Default: "main".
        profile: IPsec profile to use.
        comment: Optional comment.
        disabled: Whether the peer starts disabled.
    """
    data: dict = {"address": address, "exchange-mode": exchange_mode}
    if profile is not None:
        data["profile"] = profile
    if comment is not None:
        data["comment"] = comment
    if disabled:
        data["disabled"] = "true"
    return await tool_request(connection, "PUT", "ip/ipsec/peer", data=data)
