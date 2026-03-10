"""DNS convenience tools."""

from ..models import RouterConnection
from ..server import mcp
from ._helpers import tool_request, tool_request_delete


@mcp.tool(annotations={"title": "Get DNS Configuration", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_dns_get(connection: RouterConnection) -> str:
    """Get the current DNS configuration."""
    return await tool_request(connection, "GET", "ip/dns")


@mcp.tool(annotations={"title": "Set DNS Servers", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_dns_set_servers(
    connection: RouterConnection,
    servers: str,
    allow_remote_requests: bool = False,
) -> str:
    """Set DNS servers. Uses POST to ip/dns/set (singleton config, not a record list).

    Args:
        connection: MikroTik device connection parameters.
        servers: Comma-separated DNS server addresses (e.g. "8.8.8.8,8.8.4.4").
        allow_remote_requests: Allow other devices to use this router as DNS server.
    """
    data: dict = {"servers": servers}
    if allow_remote_requests:
        data["allow-remote-requests"] = "true"
    return await tool_request(connection, "POST", "ip/dns/set", data=data)


@mcp.tool(annotations={"title": "Add Static DNS Entry", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_dns_static_add(
    connection: RouterConnection,
    name: str | None = None,
    address: str | None = None,
    type: str | None = None,
    cname: str | None = None,
    forward_to: str | None = None,
    mx_exchange: str | None = None,
    mx_preference: str | None = None,
    ns: str | None = None,
    srv_target: str | None = None,
    srv_port: str | None = None,
    srv_priority: str | None = None,
    srv_weight: str | None = None,
    text: str | None = None,
    regexp: str | None = None,
    address_list: str | None = None,
    match_subdomain: bool = False,
    ttl: str | None = None,
    disabled: bool = False,
    comment: str | None = None,
) -> str:
    """Add a static DNS entry. Supports all RouterOS record types.

    Args:
        connection: MikroTik device connection parameters.
        name: Domain name (e.g. "example.com"). Either name or regexp is required.
        address: IP address for A/AAAA records (e.g. "192.168.1.1" or "2001:db8::1").
        type: Record type: A, AAAA, CNAME, FWD, MX, NS, NXDOMAIN, SRV, TXT.
            If omitted, RouterOS auto-detects from provided fields.
        cname: Target domain for CNAME records (e.g. "other.example.com").
        forward_to: DNS server(s) for FWD records (e.g. "8.8.8.8" or "8.8.8.8,1.1.1.1").
        mx_exchange: Mail server for MX records (e.g. "mail.example.com").
        mx_preference: MX priority (e.g. "10"). Lower = higher priority.
        ns: Name server for NS records (e.g. "ns1.example.com").
        srv_target: Target host for SRV records.
        srv_port: Port for SRV records.
        srv_priority: Priority for SRV records.
        srv_weight: Weight for SRV records.
        text: Content for TXT records (e.g. "v=spf1 include:example.com ~all").
        regexp: Regex pattern to match domain names (alternative to name).
        address_list: Add matching names to this firewall address list.
        match_subdomain: Also match all subdomains of name.
        ttl: Time to live (e.g. "1d", "01:00:00").
        disabled: Whether the entry starts disabled.
        comment: Optional comment.
    """
    if name is None and regexp is None:
        return "Error: Either 'name' or 'regexp' must be provided."

    data: dict = {}
    if name is not None:
        data["name"] = name
    if address is not None:
        data["address"] = address
    if type is not None:
        data["type"] = type
    if cname is not None:
        data["cname"] = cname
    if forward_to is not None:
        data["forward-to"] = forward_to
    if mx_exchange is not None:
        data["mx-exchange"] = mx_exchange
    if mx_preference is not None:
        data["mx-preference"] = mx_preference
    if ns is not None:
        data["ns"] = ns
    if srv_target is not None:
        data["srv-target"] = srv_target
    if srv_port is not None:
        data["srv-port"] = srv_port
    if srv_priority is not None:
        data["srv-priority"] = srv_priority
    if srv_weight is not None:
        data["srv-weight"] = srv_weight
    if text is not None:
        data["text"] = text
    if regexp is not None:
        data["regexp"] = regexp
    if address_list is not None:
        data["address-list"] = address_list
    if match_subdomain:
        data["match-subdomain"] = "true"
    if ttl is not None:
        data["ttl"] = ttl
    if disabled:
        data["disabled"] = "true"
    if comment is not None:
        data["comment"] = comment
    return await tool_request(connection, "PUT", "ip/dns/static", data=data)


@mcp.tool(annotations={"title": "List Static DNS Entries", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_dns_static_list(connection: RouterConnection) -> str:
    """List all static DNS entries."""
    return await tool_request(connection, "GET", "ip/dns/static")


@mcp.tool(annotations={"title": "Remove Static DNS Entry", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_dns_static_remove(connection: RouterConnection, id: str) -> str:
    """Remove a static DNS entry by its .id."""
    return await tool_request_delete(connection, "ip/dns/static", id)


@mcp.tool(annotations={"title": "Flush DNS Cache", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_dns_cache_flush(connection: RouterConnection) -> str:
    """Flush the DNS cache."""
    return await tool_request(connection, "POST", "ip/dns/cache/flush")
