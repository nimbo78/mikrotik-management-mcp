"""Shared helper functions for convenience tools."""

import json
import logging
import time

import httpx

from ..client import RouterOSClient, RouterOSError
from ..models import RouterConnection
from ..security import check_target_allowed

logger = logging.getLogger(__name__)


async def tool_request(
    connection: RouterConnection,
    method: str,
    path: str,
    data: dict | None = None,
    params: dict | None = None,
    timeout: float = 30.0,
) -> str:
    """Execute a RouterOS REST request with standard security check and error handling.

    Returns JSON-formatted result string on success, or a human-readable error message.
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    start = time.monotonic()
    try:
        result = await RouterOSClient.request(
            conn=connection,
            method=method,
            path=path,
            data=data,
            params=params,
            timeout=timeout,
        )
        logger.info(
            "tool_request",
            extra={
                "host": connection.host,
                "method": method,
                "path": path,
                "status": "success",
                "latency_ms": round((time.monotonic() - start) * 1000),
            },
        )
        return json.dumps(result, indent=2)
    except RouterOSError as e:
        logger.warning(
            "tool_request",
            extra={
                "host": connection.host,
                "method": method,
                "path": path,
                "status": "error",
                "error": str(e),
            },
        )
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError as e:
        logger.warning(
            "tool_request",
            extra={
                "host": connection.host,
                "method": method,
                "path": path,
                "status": "error",
                "error": str(e),
            },
        )
        return (
            f"Connection Error: Cannot reach {connection.host}:{connection.port}. "
            f"Check host, port, and network connectivity."
        )
    except httpx.TimeoutException as e:
        logger.warning(
            "tool_request",
            extra={
                "host": connection.host,
                "method": method,
                "path": path,
                "status": "error",
                "error": str(e),
            },
        )
        return (
            f"Timeout: Router {connection.host} did not respond within the timeout period."
        )
    except Exception as e:
        logger.warning(
            "tool_request",
            extra={
                "host": connection.host,
                "method": method,
                "path": path,
                "status": "error",
                "error": str(e),
            },
        )
        return f"Unexpected Error: {type(e).__name__}: {e}"


async def tool_request_delete(
    connection: RouterConnection,
    path: str,
    id: str,
) -> str:
    """Execute a DELETE request with standard security check and error handling.

    Returns JSON with success status and removed ID, or a human-readable error message.
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    start = time.monotonic()
    try:
        await RouterOSClient.request(
            conn=connection,
            method="DELETE",
            path=f"{path}/{id}",
        )
        logger.info(
            "tool_request_delete",
            extra={
                "host": connection.host,
                "method": "DELETE",
                "path": f"{path}/{id}",
                "status": "success",
                "latency_ms": round((time.monotonic() - start) * 1000),
            },
        )
        return json.dumps({"success": True, "removed": id}, indent=2)
    except RouterOSError as e:
        logger.warning(
            "tool_request_delete",
            extra={
                "host": connection.host,
                "method": "DELETE",
                "path": f"{path}/{id}",
                "status": "error",
                "error": str(e),
            },
        )
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError as e:
        logger.warning(
            "tool_request_delete",
            extra={
                "host": connection.host,
                "method": "DELETE",
                "path": f"{path}/{id}",
                "status": "error",
                "error": str(e),
            },
        )
        return (
            f"Connection Error: Cannot reach {connection.host}:{connection.port}. "
            f"Check host, port, and network connectivity."
        )
    except httpx.TimeoutException as e:
        logger.warning(
            "tool_request_delete",
            extra={
                "host": connection.host,
                "method": "DELETE",
                "path": f"{path}/{id}",
                "status": "error",
                "error": str(e),
            },
        )
        return (
            f"Timeout: Router {connection.host} did not respond within the timeout period."
        )
    except Exception as e:
        logger.warning(
            "tool_request_delete",
            extra={
                "host": connection.host,
                "method": "DELETE",
                "path": f"{path}/{id}",
                "status": "error",
                "error": str(e),
            },
        )
        return f"Unexpected Error: {type(e).__name__}: {e}"
