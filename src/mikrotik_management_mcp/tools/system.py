"""System tools: ros_system_info, ros_backup, ros_backup_download."""

import asyncio
import base64
import json

import httpx

from ..client import RouterOSClient, RouterOSError
from ..models import RouterConnection
from ..security import check_target_allowed
from ..server import mcp


def _format_bytes(value: str) -> str:
    """Convert a byte-count string to a human-readable size (KB/MB/GB)."""
    try:
        num = int(value)
    except (ValueError, TypeError):
        return value
    if num >= 1_073_741_824:  # >= 1 GiB
        return f"{num / 1_073_741_824:.2f} GB"
    if num >= 1_048_576:  # >= 1 MiB
        return f"{num / 1_048_576:.2f} MB"
    if num >= 1024:
        return f"{num / 1024:.2f} KB"
    return f"{num} B"


# ---------- ros_system_info ----------


@mcp.tool(
    name="ros_system_info",
    annotations={
        "title": "Get RouterOS System Info",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def ros_system_info(connection: RouterConnection) -> str:
    """Get system overview: version, CPU, RAM, uptime, board name, architecture."""
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    try:
        result = await RouterOSClient.request(connection, "GET", "system/resource")

        if isinstance(result, list):
            result = result[0] if result else {}

        lines = [
            f"Board:        {result.get('board-name', 'N/A')}",
            f"Version:      {result.get('version', 'N/A')}",
            f"Architecture: {result.get('architecture-name', 'N/A')}",
            f"CPU:          {result.get('cpu', 'N/A')}",
            f"CPU Count:    {result.get('cpu-count', 'N/A')}",
            f"CPU Load:     {result.get('cpu-load', 'N/A')}%",
            f"Total Memory: {_format_bytes(result.get('total-memory', '0'))}",
            f"Free Memory:  {_format_bytes(result.get('free-memory', '0'))}",
            f"Total HDD:    {_format_bytes(result.get('total-hdd-space', '0'))}",
            f"Free HDD:     {_format_bytes(result.get('free-hdd-space', '0'))}",
            f"Uptime:       {result.get('uptime', 'N/A')}",
        ]
        return "\n".join(lines)

    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return (
            f"Connection Error: Cannot reach {connection.host}:{connection.port}. "
            "Check host, port, and network connectivity."
        )
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond within the timeout period."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"


# ---------- ros_backup ----------


@mcp.tool(
    name="ros_backup",
    annotations={
        "title": "Create RouterOS Backup",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def ros_backup(
    connection: RouterConnection,
    name: str,
    backup_password: str,
) -> str:
    """Create an encrypted .backup file on the router."""
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    try:
        await RouterOSClient.request(
            connection,
            "POST",
            "system/backup/save",
            data={
                "name": name,
                "password": backup_password,
                "encryption": "aes-sha256",
            },
            timeout=60.0,
        )

        # Wait for the backup file to be created
        await asyncio.sleep(2)

        # Verify file exists
        files = await RouterOSClient.request(
            connection,
            "GET",
            "file",
            params={"name": f"{name}.backup"},
        )

        if isinstance(files, list) and files:
            file_info = files[0]
            return json.dumps(
                {
                    "success": True,
                    "filename": f"{name}.backup",
                    "size": file_info.get("size", "unknown"),
                },
                indent=2,
            )

        return json.dumps(
            {
                "success": True,
                "filename": f"{name}.backup",
                "size": "unknown",
                "note": "Backup command completed but file verification returned no results.",
            },
            indent=2,
        )

    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return (
            f"Connection Error: Cannot reach {connection.host}:{connection.port}. "
            "Check host, port, and network connectivity."
        )
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond within the timeout period."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"


# ---------- ros_backup_download ----------


@mcp.tool(
    name="ros_backup_download",
    annotations={
        "title": "Download RouterOS Backup File",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def ros_backup_download(
    connection: RouterConnection,
    filename: str,
) -> str:
    """Download a previously created .backup file from the router as base64."""
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    try:
        content = await RouterOSClient.download_file(connection, filename)
        encoded = base64.b64encode(content).decode("ascii")
        return json.dumps(
            {
                "filename": filename,
                "size_bytes": len(content),
                "content_base64": encoded,
            },
            indent=2,
        )

    except httpx.HTTPStatusError as e:
        return f"HTTP Error ({e.response.status_code}): Could not download '{filename}'. File may not exist."
    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return (
            f"Connection Error: Cannot reach {connection.host}:{connection.port}. "
            "Check host, port, and network connectivity."
        )
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond within the timeout period."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"
