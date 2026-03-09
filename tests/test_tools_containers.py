"""Tests for container management convenience tools."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.containers import (
    ros_container_add,
    ros_container_list,
    ros_container_mount_add,
    ros_container_start,
    ros_container_stop,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestRosContainerList:
    @respx.mock
    async def test_list_containers(self, conn):
        """GET /rest/container returns list of containers."""
        respx.get(f"{BASE}/container").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {".id": "*1", "tag": "docker.io/library/alpine:latest", "status": "running"},
                    {".id": "*2", "tag": "docker.io/library/nginx:latest", "status": "stopped"},
                ],
            )
        )
        result = await ros_container_list(connection=conn)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["status"] == "running"


@pytest.mark.asyncio
class TestRosContainerAdd:
    @respx.mock
    async def test_add_container_with_hyphen_mapping(self, conn):
        """PUT /rest/container with remote-image and root-dir hyphenated keys."""
        route = respx.put(f"{BASE}/container").mock(
            return_value=httpx.Response(
                200,
                json={".id": "*3", "tag": "docker.io/library/alpine:latest", "status": "stopped"},
            )
        )
        result = await ros_container_add(
            connection=conn,
            remote_image="docker.io/library/alpine:latest",
            interface="veth1",
            root_dir="disk1/alpine",
            hostname="alpine-test",
        )
        data = json.loads(result)
        assert data[".id"] == "*3"
        # Verify hyphenated keys in request body
        sent = json.loads(route.calls[0].request.content)
        assert sent["remote-image"] == "docker.io/library/alpine:latest"
        assert sent["root-dir"] == "disk1/alpine"
        assert sent["interface"] == "veth1"
        assert sent["hostname"] == "alpine-test"


@pytest.mark.asyncio
class TestRosContainerStart:
    @respx.mock
    async def test_start_container_posts_with_id(self, conn):
        """POST /rest/container/start with .id in body."""
        route = respx.post(f"{BASE}/container/start").mock(
            return_value=httpx.Response(200, content=b"")
        )
        result = await ros_container_start(connection=conn, id="*1")
        data = json.loads(result)
        assert data["success"] is True
        # Verify .id was sent in POST body
        sent = json.loads(route.calls[0].request.content)
        assert sent[".id"] == "*1"


@pytest.mark.asyncio
class TestRosContainerStop:
    @respx.mock
    async def test_stop_container_posts_with_id(self, conn):
        """POST /rest/container/stop with .id in body."""
        route = respx.post(f"{BASE}/container/stop").mock(
            return_value=httpx.Response(200, content=b"")
        )
        result = await ros_container_stop(connection=conn, id="*2")
        data = json.loads(result)
        assert data["success"] is True
        # Verify .id was sent in POST body
        sent = json.loads(route.calls[0].request.content)
        assert sent[".id"] == "*2"


@pytest.mark.asyncio
class TestRosContainerMountAdd:
    @respx.mock
    async def test_add_mount_point(self, conn):
        """PUT /rest/container/mounts with name, src, dst."""
        route = respx.put(f"{BASE}/container/mounts").mock(
            return_value=httpx.Response(
                200,
                json={".id": "*1", "name": "data-mount", "src": "/disk1/data", "dst": "/data"},
            )
        )
        result = await ros_container_mount_add(
            connection=conn,
            name="data-mount",
            src="/disk1/data",
            dst="/data",
            comment="Persistent data",
        )
        data = json.loads(result)
        assert data["name"] == "data-mount"
        # Verify request body
        sent = json.loads(route.calls[0].request.content)
        assert sent["name"] == "data-mount"
        assert sent["src"] == "/disk1/data"
        assert sent["dst"] == "/data"
        assert sent["comment"] == "Persistent data"
