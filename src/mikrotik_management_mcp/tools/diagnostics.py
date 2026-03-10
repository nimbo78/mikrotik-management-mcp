"""Network diagnostic tools with safety guardrails."""

import json

import httpx

from ..client import RouterOSClient, RouterOSError
from ..models import RouterConnection
from ..security import check_target_allowed
from ..server import mcp

MAX_PING_COUNT = 100
MAX_TRACEROUTE_COUNT = 30
MAX_TORCH_DURATION = 30


@mcp.tool(annotations={"title": "Ping from Router", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_ping(
    connection: RouterConnection,
    address: str,
    count: int = 4,
    size: int | None = None,
    src_address: str | None = None,
) -> str:
    """Ping a host from the router. Returns min/avg/max/loss summary.

    Args:
        connection: MikroTik device connection parameters.
        address: Target IP address or hostname to ping.
        count: Number of ping packets (1-100, default 4).
        size: Packet size in bytes.
        src_address: Source address for the ping.
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    if count < 1 or count > MAX_PING_COUNT:
        return f"Error: count must be between 1 and {MAX_PING_COUNT}, got {count}."

    data: dict = {"address": address, "count": str(count)}
    if size is not None:
        data["size"] = str(size)
    if src_address is not None:
        data["src-address"] = src_address

    try:
        result = await RouterOSClient.request(
            connection, "POST", "ping", data=data, timeout=60.0
        )

        if isinstance(result, list) and result:
            # RouterOS returns a list of per-packet results; last entry often has summary
            # Extract summary stats
            sent = count
            received = sum(1 for r in result if r.get("status") == "" or "time" in r or r.get("received", "") != "")
            loss_pct = round((1 - received / sent) * 100, 1) if sent > 0 else 0

            times = []
            for r in result:
                t = r.get("time")
                if t is not None:
                    try:
                        # time might be "1ms" or just a number
                        t_str = str(t).replace("ms", "").replace("us", "").strip()
                        times.append(float(t_str))
                    except (ValueError, TypeError):
                        pass

            summary_lines = [
                f"Ping {address}: {sent} packets sent, {received} received, {loss_pct}% loss",
            ]
            if times:
                summary_lines.append(
                    f"RTT min/avg/max: {min(times):.1f}/{sum(times)/len(times):.1f}/{max(times):.1f} ms"
                )

            summary_lines.append("")
            summary_lines.append("Raw results:")
            summary_lines.append(json.dumps(result, indent=2))
            return "\n".join(summary_lines)

        return json.dumps(result, indent=2)

    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}. Check host, port, and network connectivity."
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond within the timeout period."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"


@mcp.tool(annotations={"title": "Traceroute from Router", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_traceroute(
    connection: RouterConnection,
    address: str,
    count: int = 1,
    size: int | None = None,
    src_address: str | None = None,
) -> str:
    """Run traceroute from the router to a target address.

    Args:
        connection: MikroTik device connection parameters.
        address: Target IP address or hostname.
        count: Probes per hop (1-30, default 1).
        size: Packet size in bytes.
        src_address: Source address for traceroute.
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    if count < 1 or count > MAX_TRACEROUTE_COUNT:
        return f"Error: count must be between 1 and {MAX_TRACEROUTE_COUNT}, got {count}."

    data: dict = {"address": address, "count": str(count)}
    if size is not None:
        data["size"] = str(size)
    if src_address is not None:
        data["src-address"] = src_address

    try:
        result = await RouterOSClient.request(
            connection, "POST", "tool/traceroute", data=data, timeout=60.0
        )
        return json.dumps(result, indent=2)

    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}. Check host, port, and network connectivity."
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond within the timeout period."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"


@mcp.tool(annotations={"title": "Torch (Traffic Monitor)", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_torch(
    connection: RouterConnection,
    interface: str,
    duration: int = 5,
    src_address: str | None = None,
    dst_address: str | None = None,
    port: str | None = None,
) -> str:
    """Run torch (real-time traffic monitor) on an interface.

    Args:
        connection: MikroTik device connection parameters.
        interface: Interface to monitor (e.g. "ether1").
        duration: Monitor duration in seconds (1-30, default 5).
        src_address: Filter by source address.
        dst_address: Filter by destination address.
        port: Filter by port (e.g. "80" or "80,443").
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    if duration < 1 or duration > MAX_TORCH_DURATION:
        return f"Error: duration must be between 1 and {MAX_TORCH_DURATION}, got {duration}."

    data: dict = {"interface": interface, "duration": str(duration)}
    if src_address is not None:
        data["src-address"] = src_address
    if dst_address is not None:
        data["dst-address"] = dst_address
    if port is not None:
        data["port"] = port

    try:
        result = await RouterOSClient.request(
            connection, "POST", "tool/torch", data=data, timeout=60.0
        )
        return json.dumps(result, indent=2)

    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}. Check host, port, and network connectivity."
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond within the timeout period."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"
