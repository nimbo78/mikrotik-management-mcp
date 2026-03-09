"""Tests for DNS convenience tools."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.dns import (
    ros_dns_cache_flush,
    ros_dns_get,
    ros_dns_set_servers,
    ros_dns_static_add,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestRosDnsGet:
    @respx.mock
    async def test_get_config(self, conn):
        respx.get(f"{BASE}/ip/dns").mock(
            return_value=httpx.Response(
                200,
                json={
                    "servers": "8.8.8.8,8.8.4.4",
                    "allow-remote-requests": "false",
                    "cache-size": "2048",
                },
            )
        )
        result = await ros_dns_get(conn)
        data = json.loads(result)
        assert data["servers"] == "8.8.8.8,8.8.4.4"
        assert data["allow-remote-requests"] == "false"


@pytest.mark.asyncio
class TestRosDnsSetServers:
    @respx.mock
    async def test_set_servers_with_allow_remote(self, conn):
        route = respx.post(f"{BASE}/ip/dns/set").mock(
            return_value=httpx.Response(200, json={})
        )
        result = await ros_dns_set_servers(
            conn, servers="1.1.1.1,8.8.8.8", allow_remote_requests=True
        )
        # Verify POST method and body content
        request = route.calls[0].request
        assert request.method == "POST"
        body = json.loads(request.content)
        assert body["servers"] == "1.1.1.1,8.8.8.8"
        assert body["allow-remote-requests"] == "true"


@pytest.mark.asyncio
class TestRosDnsStaticAdd:
    @respx.mock
    async def test_static_add(self, conn):
        route = respx.put(f"{BASE}/ip/dns/static").mock(
            return_value=httpx.Response(
                201,
                json={
                    ".id": "*1",
                    "name": "myhost.local",
                    "address": "192.168.1.50",
                },
            )
        )
        result = await ros_dns_static_add(
            conn, name="myhost.local", address="192.168.1.50"
        )
        data = json.loads(result)
        assert data[".id"] == "*1"
        assert data["name"] == "myhost.local"
        body = json.loads(route.calls[0].request.content)
        assert body["name"] == "myhost.local"
        assert body["address"] == "192.168.1.50"


@pytest.mark.asyncio
class TestRosDnsCacheFlush:
    @respx.mock
    async def test_cache_flush(self, conn):
        route = respx.post(f"{BASE}/ip/dns/cache/flush").mock(
            return_value=httpx.Response(200, json={})
        )
        result = await ros_dns_cache_flush(conn)
        # Verify POST to correct path
        assert route.calls[0].request.method == "POST"
        assert route.calls[0].request.url.path == "/rest/ip/dns/cache/flush"
