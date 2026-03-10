"""Health check and export tools."""

import json

import httpx

from ..client import RouterOSClient, RouterOSError
from ..models import RouterConnection
from ..security import check_target_allowed
from ..server import mcp


def _format_bytes(value: str) -> str:
    """Convert a byte-count string to human-readable size."""
    try:
        num = int(value)
    except (ValueError, TypeError):
        return value
    if num >= 1_073_741_824:
        return f"{num / 1_073_741_824:.2f} GB"
    if num >= 1_048_576:
        return f"{num / 1_048_576:.2f} MB"
    if num >= 1024:
        return f"{num / 1024:.2f} KB"
    return f"{num} B"


@mcp.tool(annotations={"title": "Router Health Check", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_health_check(connection: RouterConnection) -> str:
    """Comprehensive health dashboard: CPU, RAM, disk, temperature, conntrack, interface errors.

    Calls multiple endpoints and returns a formatted summary.
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    sections = []

    try:
        # 1. System resource
        resource = await RouterOSClient.request(connection, "GET", "system/resource")
        if isinstance(resource, list):
            resource = resource[0] if resource else {}

        total_mem = int(resource.get("total-memory", "0") or "0")
        free_mem = int(resource.get("free-memory", "0") or "0")
        mem_pct = round((1 - free_mem / total_mem) * 100, 1) if total_mem > 0 else 0

        total_hdd = int(resource.get("total-hdd-space", "0") or "0")
        free_hdd = int(resource.get("free-hdd-space", "0") or "0")
        hdd_pct = round((1 - free_hdd / total_hdd) * 100, 1) if total_hdd > 0 else 0

        sections.append("=== System Resource ===")
        sections.append(f"Board:        {resource.get('board-name', 'N/A')}")
        sections.append(f"Version:      {resource.get('version', 'N/A')}")
        sections.append(f"Uptime:       {resource.get('uptime', 'N/A')}")
        sections.append(f"CPU Load:     {resource.get('cpu-load', 'N/A')}%")
        sections.append(f"Memory:       {_format_bytes(resource.get('total-memory', '0'))} total, "
                        f"{_format_bytes(resource.get('free-memory', '0'))} free ({mem_pct}% used)")
        sections.append(f"Disk:         {_format_bytes(resource.get('total-hdd-space', '0'))} total, "
                        f"{_format_bytes(resource.get('free-hdd-space', '0'))} free ({hdd_pct}% used)")

    except Exception as e:
        sections.append(f"=== System Resource === ERROR: {e}")

    try:
        # 2. System health (temperature, voltage, etc.)
        health = await RouterOSClient.request(connection, "GET", "system/health")
        if isinstance(health, list) and health:
            sections.append("")
            sections.append("=== System Health ===")
            for item in health:
                name = item.get("name", item.get("type", "unknown"))
                value = item.get("value", "N/A")
                unit = item.get("unit", "")
                sections.append(f"{name}: {value} {unit}".strip())
        elif isinstance(health, dict) and health:
            sections.append("")
            sections.append("=== System Health ===")
            for key, val in health.items():
                if not key.startswith("."):
                    sections.append(f"{key}: {val}")
    except Exception:
        pass  # Some routers don't have health sensors

    try:
        # 3. Connection tracking
        conntrack = await RouterOSClient.request(connection, "GET", "ip/firewall/connection/tracking")
        if isinstance(conntrack, list):
            conntrack = conntrack[0] if conntrack else {}
        if isinstance(conntrack, dict):
            total_entries = conntrack.get("total-entries", "N/A")
            max_entries = conntrack.get("max-entries", "N/A")
            sections.append("")
            sections.append("=== Connection Tracking ===")
            sections.append(f"Active: {total_entries} / {max_entries}")
            try:
                pct = round(int(total_entries) / int(max_entries) * 100, 1)
                sections.append(f"Usage: {pct}%")
            except (ValueError, TypeError, ZeroDivisionError):
                pass
    except Exception:
        pass

    try:
        # 4. Interface error counts
        interfaces = await RouterOSClient.request(connection, "GET", "interface")
        if isinstance(interfaces, list):
            error_ifaces = []
            for iface in interfaces:
                errors = {}
                for key in ("tx-error", "rx-error", "tx-drop", "rx-drop", "fp-tx-error", "fp-rx-error"):
                    val = iface.get(key, "0")
                    try:
                        if int(val) > 0:
                            errors[key] = val
                    except (ValueError, TypeError):
                        pass
                if errors:
                    error_ifaces.append((iface.get("name", "?"), errors))

            if error_ifaces:
                sections.append("")
                sections.append("=== Interface Errors ===")
                for name, errs in error_ifaces:
                    err_str = ", ".join(f"{k}={v}" for k, v in errs.items())
                    sections.append(f"{name}: {err_str}")
            else:
                sections.append("")
                sections.append("=== Interface Errors ===")
                sections.append("No interface errors detected.")
    except Exception:
        pass

    return "\n".join(sections) if sections else "Error: Could not retrieve health data."


@mcp.tool(annotations={"title": "Export RouterOS Config", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_export(
    connection: RouterConnection,
    section: str | None = None,
) -> str:
    """Export RouterOS configuration in RSC (script) format.

    Args:
        connection: MikroTik device connection parameters.
        section: Optional section to export (e.g. "ip/firewall", "ip/address"). If omitted, exports full config.
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    path = f"{section}/export" if section else "export"

    try:
        result = await RouterOSClient.request_text(
            connection, "POST", path, timeout=60.0
        )
        return result

    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}. Check host, port, and network connectivity."
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond within the timeout period."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"
