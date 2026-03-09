"""Wireless (legacy interface/wireless) convenience tools."""

from ..models import RouterConnection
from ..server import mcp
from ._helpers import tool_request, tool_request_delete


@mcp.tool(annotations={"title": "List Wireless Interfaces", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_wireless_list(connection: RouterConnection) -> str:
    """List all wireless interfaces."""
    return await tool_request(connection, "GET", "interface/wireless")


@mcp.tool(annotations={"title": "Scan Wireless Networks", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True})
async def ros_wireless_scan(
    connection: RouterConnection,
    interface: str,
    duration: int = 5,
) -> str:
    """Scan for wireless networks on an interface.

    Args:
        connection: MikroTik device connection parameters.
        interface: Wireless interface name to scan on (e.g. "wlan1").
        duration: Scan duration in seconds (default 5).
    """
    return await tool_request(
        connection, "POST", "interface/wireless/scan",
        data={".id": interface, "duration": str(duration)},
        timeout=60.0,
    )


@mcp.tool(annotations={"title": "List Wireless Registration Table", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_wireless_registration_list(connection: RouterConnection) -> str:
    """List the wireless registration table (connected clients)."""
    return await tool_request(connection, "GET", "interface/wireless/registration-table")


@mcp.tool(annotations={"title": "Add Wireless Security Profile", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_wireless_security_profile_add(
    connection: RouterConnection,
    name: str,
    mode: str = "dynamic-keys",
    authentication_types: str = "wpa2-psk",
    wpa2_pre_shared_key: str | None = None,
    comment: str | None = None,
) -> str:
    """Add a wireless security profile.

    Args:
        connection: MikroTik device connection parameters.
        name: Profile name.
        mode: Security mode (default "dynamic-keys").
        authentication_types: Auth types (default "wpa2-psk").
        wpa2_pre_shared_key: WPA2 pre-shared key.
        comment: Optional comment.
    """
    data: dict = {
        "name": name,
        "mode": mode,
        "authentication-types": authentication_types,
    }
    if wpa2_pre_shared_key is not None:
        data["wpa2-pre-shared-key"] = wpa2_pre_shared_key
    if comment is not None:
        data["comment"] = comment
    return await tool_request(connection, "PUT", "interface/wireless/security-profiles", data=data)


@mcp.tool(annotations={"title": "Remove Wireless Security Profile", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_wireless_security_profile_remove(connection: RouterConnection, id: str) -> str:
    """Remove a wireless security profile by its .id."""
    return await tool_request_delete(connection, "interface/wireless/security-profiles", id)
