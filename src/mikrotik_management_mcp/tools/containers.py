"""Container management convenience tools."""

from ..models import RouterConnection
from ..server import mcp
from ._helpers import tool_request, tool_request_delete


@mcp.tool(annotations={"title": "List Containers", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_container_list(connection: RouterConnection) -> str:
    """List all containers."""
    return await tool_request(connection, "GET", "container")


@mcp.tool(annotations={"title": "Add Container", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_container_add(
    connection: RouterConnection,
    remote_image: str,
    interface: str,
    root_dir: str,
    envlist: str | None = None,
    mounts: str | None = None,
    hostname: str | None = None,
    comment: str | None = None,
) -> str:
    """Add a container from a remote image.

    Args:
        connection: MikroTik device connection parameters.
        remote_image: Container image (e.g. "docker.io/library/alpine:latest").
        interface: VETH interface to attach to.
        root_dir: Root directory for the container filesystem.
        envlist: Environment variable list name.
        mounts: Mount point name.
        hostname: Container hostname.
        comment: Optional comment.
    """
    data: dict = {
        "remote-image": remote_image,
        "interface": interface,
        "root-dir": root_dir,
    }
    if envlist is not None:
        data["envlist"] = envlist
    if mounts is not None:
        data["mounts"] = mounts
    if hostname is not None:
        data["hostname"] = hostname
    if comment is not None:
        data["comment"] = comment
    return await tool_request(connection, "PUT", "container", data=data)


@mcp.tool(annotations={"title": "Start Container", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_container_start(connection: RouterConnection, id: str) -> str:
    """Start a container by its .id."""
    return await tool_request(
        connection, "POST", "container/start",
        data={".id": id},
        timeout=60.0,
    )


@mcp.tool(annotations={"title": "Stop Container", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_container_stop(connection: RouterConnection, id: str) -> str:
    """Stop a container by its .id."""
    return await tool_request(
        connection, "POST", "container/stop",
        data={".id": id},
        timeout=60.0,
    )


@mcp.tool(annotations={"title": "Remove Container", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})
async def ros_container_remove(connection: RouterConnection, id: str) -> str:
    """Remove a container by its .id."""
    return await tool_request_delete(connection, "container", id)


@mcp.tool(annotations={"title": "Add Container Mount", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})
async def ros_container_mount_add(
    connection: RouterConnection,
    name: str,
    src: str,
    dst: str,
    comment: str | None = None,
) -> str:
    """Add a container mount point.

    Args:
        connection: MikroTik device connection parameters.
        name: Mount name.
        src: Source path on the router.
        dst: Destination path inside the container.
        comment: Optional comment.
    """
    data: dict = {"name": name, "src": src, "dst": dst}
    if comment is not None:
        data["comment"] = comment
    return await tool_request(connection, "PUT", "container/mounts", data=data)


@mcp.tool(annotations={"title": "List Container Mounts", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})
async def ros_container_mount_list(connection: RouterConnection) -> str:
    """List all container mount points."""
    return await tool_request(connection, "GET", "container/mounts")
