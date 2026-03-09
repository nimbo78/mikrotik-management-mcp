"""Security configuration for MikroTik MCP server."""

import ipaddress
import os
from typing import Optional

ALLOWED_TARGETS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
ALLOWED_CLIENTS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
MCP_AUTH_TOKEN: Optional[str] = None


def load_security_config() -> None:
    """Load security settings from environment variables."""
    global ALLOWED_TARGETS, ALLOWED_CLIENTS, MCP_AUTH_TOKEN

    targets = os.environ.get("ALLOWED_TARGETS", "")
    ALLOWED_TARGETS = (
        [ipaddress.ip_network(t.strip(), strict=False) for t in targets.split(",") if t.strip()]
        if targets
        else []
    )

    clients = os.environ.get("ALLOWED_CLIENTS", "")
    ALLOWED_CLIENTS = (
        [ipaddress.ip_network(c.strip(), strict=False) for c in clients.split(",") if c.strip()]
        if clients
        else []
    )

    MCP_AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN") or None


def check_target_allowed(host: str) -> bool:
    """Check if the target MikroTik host is in the allowed list."""
    if not ALLOWED_TARGETS:
        return True
    try:
        addr = ipaddress.ip_address(host)
        return any(addr in network for network in ALLOWED_TARGETS)
    except ValueError:
        return True  # hostname — allow by default


def check_client_allowed(client_ip: str) -> bool:
    """Check if the connecting client IP is allowed."""
    if not ALLOWED_CLIENTS:
        return True
    try:
        addr = ipaddress.ip_address(client_ip)
        return any(addr in network for network in ALLOWED_CLIENTS)
    except ValueError:
        return False
