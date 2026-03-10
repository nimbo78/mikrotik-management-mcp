"""Tests for PPPoE/PPP convenience tools."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.pppoe import (
    ros_ppp_secret_add,
    ros_ppp_secret_list,
    ros_ppp_secret_remove,
    ros_ppp_active_list,
    ros_ppp_active_disconnect,
    ros_ppp_profile_list,
    ros_ppp_profile_add,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestPppSecretTools:
    @respx.mock
    async def test_secret_add_full_params(self, conn):
        route = respx.put(f"{BASE}/ppp/secret").mock(
            return_value=httpx.Response(201, json={".id": "*1", "name": "user1", "service": "pppoe"})
        )
        result = await ros_ppp_secret_add(
            conn, name="user1", password="pass123", service="pppoe",
            profile="default", local_address="10.0.0.1",
            remote_address="10.0.0.100", rate_limit="10M/5M", comment="test"
        )
        data = json.loads(result)
        assert data[".id"] == "*1"
        body = json.loads(route.calls[0].request.content)
        assert body["name"] == "user1"
        assert body["password"] == "pass123"
        assert body["service"] == "pppoe"
        assert body["profile"] == "default"
        assert body["local-address"] == "10.0.0.1"
        assert body["remote-address"] == "10.0.0.100"
        assert body["rate-limit"] == "10M/5M"
        assert body["comment"] == "test"

    @respx.mock
    async def test_secret_add_minimal(self, conn):
        route = respx.put(f"{BASE}/ppp/secret").mock(
            return_value=httpx.Response(201, json={".id": "*2", "name": "user2"})
        )
        result = await ros_ppp_secret_add(conn, name="user2", password="pw")
        data = json.loads(result)
        assert data[".id"] == "*2"
        body = json.loads(route.calls[0].request.content)
        assert body["name"] == "user2"
        assert body["password"] == "pw"
        assert body["service"] == "pppoe"
        assert "profile" not in body
        assert "local-address" not in body

    @respx.mock
    async def test_secret_add_disabled(self, conn):
        route = respx.put(f"{BASE}/ppp/secret").mock(
            return_value=httpx.Response(201, json={".id": "*3"})
        )
        await ros_ppp_secret_add(conn, name="user3", password="pw", disabled=True)
        body = json.loads(route.calls[0].request.content)
        assert body["disabled"] == "true"

    @respx.mock
    async def test_secret_list(self, conn):
        respx.get(f"{BASE}/ppp/secret").mock(
            return_value=httpx.Response(200, json=[
                {".id": "*1", "name": "user1", "service": "pppoe"},
                {".id": "*2", "name": "user2", "service": "pppoe"},
            ])
        )
        result = await ros_ppp_secret_list(conn)
        data = json.loads(result)
        assert len(data) == 2

    @respx.mock
    async def test_secret_remove(self, conn):
        respx.delete(f"{BASE}/ppp/secret/*1").mock(
            return_value=httpx.Response(200, content=b"")
        )
        result = await ros_ppp_secret_remove(conn, id="*1")
        data = json.loads(result)
        assert data["success"] is True
        assert data["removed"] == "*1"


@pytest.mark.asyncio
class TestPppActiveTools:
    @respx.mock
    async def test_active_list(self, conn):
        respx.get(f"{BASE}/ppp/active").mock(
            return_value=httpx.Response(200, json=[
                {".id": "*A", "name": "user1", "address": "10.0.0.100", "uptime": "1h30m"},
            ])
        )
        result = await ros_ppp_active_list(conn)
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["name"] == "user1"

    @respx.mock
    async def test_active_disconnect(self, conn):
        route = respx.post(f"{BASE}/ppp/active/remove").mock(
            return_value=httpx.Response(200, json={})
        )
        result = await ros_ppp_active_disconnect(conn, id="*A")
        body = json.loads(route.calls[0].request.content)
        assert body[".id"] == "*A"


@pytest.mark.asyncio
class TestPppProfileTools:
    @respx.mock
    async def test_profile_list(self, conn):
        respx.get(f"{BASE}/ppp/profile").mock(
            return_value=httpx.Response(200, json=[
                {".id": "*1", "name": "default"},
                {".id": "*2", "name": "premium", "rate-limit": "50M/50M"},
            ])
        )
        result = await ros_ppp_profile_list(conn)
        data = json.loads(result)
        assert len(data) == 2

    @respx.mock
    async def test_profile_add(self, conn):
        route = respx.put(f"{BASE}/ppp/profile").mock(
            return_value=httpx.Response(201, json={".id": "*3", "name": "gold"})
        )
        result = await ros_ppp_profile_add(
            conn, name="gold", local_address="10.0.0.1",
            remote_address="pool-gold", rate_limit="100M/100M", dns_server="8.8.8.8"
        )
        data = json.loads(result)
        assert data["name"] == "gold"
        body = json.loads(route.calls[0].request.content)
        assert body["local-address"] == "10.0.0.1"
        assert body["remote-address"] == "pool-gold"
        assert body["rate-limit"] == "100M/100M"
        assert body["dns-server"] == "8.8.8.8"
