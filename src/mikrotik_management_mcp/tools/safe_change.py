"""Safe change workflow — revert-on-timeout for risky config changes."""

import json
import time

import httpx

from ..client import RouterOSClient, RouterOSError
from ..models import RouterConnection
from ..security import check_target_allowed
from ..server import mcp

_SAFE_CHANGE_PREFIX = "mcp-safe-revert"


@mcp.tool(annotations={"title": "Start Safe Change", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True})
async def ros_safe_change_start(
    connection: RouterConnection,
    revert_minutes: int = 5,
) -> str:
    """Start a safe change session: creates a backup and a scheduler that auto-reverts in N minutes.

    After calling this, apply your config changes using other tools.
    When satisfied the changes work, call ros_safe_change_confirm to cancel the auto-revert.
    If you don't confirm within the timeout, the router restores the backup automatically.

    Args:
        connection: MikroTik device connection parameters.
        revert_minutes: Minutes before auto-revert (1-30, default 5).
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    if revert_minutes < 1 or revert_minutes > 30:
        return f"Error: revert_minutes must be between 1 and 30, got {revert_minutes}."

    backup_name = f"{_SAFE_CHANGE_PREFIX}-{int(time.time())}"
    scheduler_name = f"{_SAFE_CHANGE_PREFIX}-{int(time.time())}"

    try:
        # 1. Create backup
        await RouterOSClient.request(
            connection, "POST", "system/backup/save",
            data={"name": backup_name, "dont-encrypt": "yes"},
            timeout=60.0,
        )

        # 2. Create scheduler entry to auto-restore after N minutes
        interval = f"{revert_minutes:02d}:00:00" if revert_minutes >= 60 else f"00:{revert_minutes:02d}:00"
        scheduler_result = await RouterOSClient.request(
            connection, "PUT", "system/scheduler",
            data={
                "name": scheduler_name,
                "on-event": f"/system/backup/load name={backup_name}.backup",
                "start-time": "startup",
                "interval": interval,
                "comment": "MCP safe change auto-revert — remove with ros_safe_change_confirm",
            },
        )

        scheduler_id = scheduler_result.get(".id", "unknown") if isinstance(scheduler_result, dict) else "unknown"

        return json.dumps({
            "success": True,
            "backup_name": f"{backup_name}.backup",
            "scheduler_name": scheduler_name,
            "scheduler_id": scheduler_id,
            "revert_minutes": revert_minutes,
            "message": f"Safe change started. Auto-revert in {revert_minutes} minutes. "
                       f"Apply your changes now, then call ros_safe_change_confirm with scheduler_id='{scheduler_id}' to keep them.",
        }, indent=2)

    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}. Check host, port, and network connectivity."
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond within the timeout period."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"


@mcp.tool(annotations={"title": "Confirm Safe Change", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_safe_change_confirm(
    connection: RouterConnection,
    scheduler_id: str,
) -> str:
    """Confirm a safe change by removing the auto-revert scheduler.

    Call this after verifying your config changes work correctly.

    Args:
        connection: MikroTik device connection parameters.
        scheduler_id: The scheduler .id returned by ros_safe_change_start.
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    try:
        await RouterOSClient.request(
            connection, "DELETE", f"system/scheduler/{scheduler_id}",
        )
        return json.dumps({
            "success": True,
            "message": "Safe change confirmed. Auto-revert scheduler removed. Your changes are permanent.",
        }, indent=2)

    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}. Check host, port, and network connectivity."
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond within the timeout period."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"
