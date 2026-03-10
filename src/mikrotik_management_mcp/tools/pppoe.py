"""PPPoE/PPP convenience tools for ISP subscriber management."""

from ..models import RouterConnection
from ..server import mcp
from ._helpers import tool_request, tool_request_delete


@mcp.tool(annotations={"title": "Add PPP Secret", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_ppp_secret_add(
    connection: RouterConnection,
    name: str,
    password: str,
    service: str = "pppoe",
    profile: str | None = None,
    local_address: str | None = None,
    remote_address: str | None = None,
    rate_limit: str | None = None,
    comment: str | None = None,
    disabled: bool = False,
) -> str:
    """Add a PPP secret (subscriber account).

    Args:
        connection: MikroTik device connection parameters.
        name: Username for the PPP connection.
        password: Password for the PPP connection.
        service: Service type (pppoe, pptp, l2tp, etc.). Default: pppoe.
        profile: PPP profile to use.
        local_address: Server-side IP address (or pool name).
        remote_address: Client-side IP address (or pool name).
        rate_limit: Speed limit in format "rx/tx" (e.g. "10M/10M", "5M/1M").
        comment: Optional comment.
        disabled: Whether the secret starts disabled.
    """
    data: dict = {"name": name, "password": password, "service": service}
    if profile is not None:
        data["profile"] = profile
    if local_address is not None:
        data["local-address"] = local_address
    if remote_address is not None:
        data["remote-address"] = remote_address
    if rate_limit is not None:
        data["rate-limit"] = rate_limit
    if comment is not None:
        data["comment"] = comment
    if disabled:
        data["disabled"] = "true"
    return await tool_request(connection, "PUT", "ppp/secret", data=data)


@mcp.tool(annotations={"title": "List PPP Secrets", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_ppp_secret_list(connection: RouterConnection) -> str:
    """List all PPP secrets (subscriber accounts)."""
    return await tool_request(connection, "GET", "ppp/secret")


@mcp.tool(annotations={"title": "Remove PPP Secret", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_ppp_secret_remove(connection: RouterConnection, id: str) -> str:
    """Remove a PPP secret by its .id."""
    return await tool_request_delete(connection, "ppp/secret", id)


@mcp.tool(annotations={"title": "List PPP Active Connections", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_ppp_active_list(connection: RouterConnection) -> str:
    """List all active PPP connections (currently connected subscribers)."""
    return await tool_request(connection, "GET", "ppp/active")


@mcp.tool(annotations={"title": "Disconnect PPP Session", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_ppp_active_disconnect(connection: RouterConnection, id: str) -> str:
    """Disconnect an active PPP session by its .id.

    Args:
        connection: MikroTik device connection parameters.
        id: The .id of the active PPP session to disconnect.
    """
    return await tool_request(connection, "POST", "ppp/active/remove", data={".id": id})


@mcp.tool(annotations={"title": "List PPP Profiles", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_ppp_profile_list(connection: RouterConnection) -> str:
    """List all PPP profiles (bandwidth/settings templates)."""
    return await tool_request(connection, "GET", "ppp/profile")


@mcp.tool(annotations={"title": "Add PPP Profile", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_ppp_profile_add(
    connection: RouterConnection,
    name: str,
    local_address: str | None = None,
    remote_address: str | None = None,
    rate_limit: str | None = None,
    dns_server: str | None = None,
    comment: str | None = None,
) -> str:
    """Add a PPP profile (bandwidth/settings template).

    Args:
        connection: MikroTik device connection parameters.
        name: Profile name.
        local_address: Default server-side IP or pool.
        remote_address: Default client-side IP or pool.
        rate_limit: Speed limit in "rx/tx" format (e.g. "10M/5M").
        dns_server: DNS server to assign to clients.
        comment: Optional comment.
    """
    data: dict = {"name": name}
    if local_address is not None:
        data["local-address"] = local_address
    if remote_address is not None:
        data["remote-address"] = remote_address
    if rate_limit is not None:
        data["rate-limit"] = rate_limit
    if dns_server is not None:
        data["dns-server"] = dns_server
    if comment is not None:
        data["comment"] = comment
    return await tool_request(connection, "PUT", "ppp/profile", data=data)
