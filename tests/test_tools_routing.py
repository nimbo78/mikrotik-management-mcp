"""Tests for static routing convenience tools."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.routing import (
    ros_route_add,
    ros_route_list,
    ros_route_remove,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestRosRouteAdd:
    @respx.mock
    async def test_add_with_distance(self, conn):
        route = respx.put(f"{BASE}/ip/route").mock(
            return_value=httpx.Response(
                201,
                json={
                    ".id": "*1",
                    "dst-address": "10.10.0.0/16",
                    "gateway": "192.168.1.1",
                    "distance": "5",
                },
            )
        )
        result = await ros_route_add(
            conn, dst_address="10.10.0.0/16", gateway="192.168.1.1", distance=5
        )
        data = json.loads(result)
        assert data[".id"] == "*1"
        # Verify hyphen-mapped keys and distance as string
        body = json.loads(route.calls[0].request.content)
        assert body["dst-address"] == "10.10.0.0/16"
        assert body["gateway"] == "192.168.1.1"
        assert body["distance"] == "5"


@pytest.mark.asyncio
class TestRosRouteList:
    @respx.mock
    async def test_list(self, conn):
        respx.get(f"{BASE}/ip/route").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {".id": "*1", "dst-address": "0.0.0.0/0", "gateway": "192.168.1.1"},
                    {".id": "*2", "dst-address": "10.0.0.0/8", "gateway": "172.16.0.1"},
                ],
            )
        )
        result = await ros_route_list(conn)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["dst-address"] == "0.0.0.0/0"


@pytest.mark.asyncio
class TestRosRouteRemove:
    @respx.mock
    async def test_remove(self, conn):
        respx.delete(f"{BASE}/ip/route/*1").mock(
            return_value=httpx.Response(204, content=b"")
        )
        result = await ros_route_remove(conn, id="*1")
        data = json.loads(result)
        assert data["success"] is True
        assert data["removed"] == "*1"
