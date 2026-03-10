"""Tests for diagnostic tools."""

import json

import httpx
import pytest
import respx
from unittest.mock import patch

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.diagnostics import (
    ros_ping,
    ros_traceroute,
    ros_torch,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestRosPing:
    @respx.mock
    async def test_success(self, conn):
        respx.post(f"{BASE}/ping").mock(
            return_value=httpx.Response(200, json=[
                {"host": "8.8.8.8", "time": "10", "status": ""},
                {"host": "8.8.8.8", "time": "12", "status": ""},
                {"host": "8.8.8.8", "time": "11", "status": ""},
                {"host": "8.8.8.8", "time": "9", "status": ""},
            ])
        )
        result = await ros_ping(conn, address="8.8.8.8", count=4)
        assert "4 packets sent" in result
        assert "4 received" in result
        assert "0.0% loss" in result
        assert "RTT min/avg/max" in result

    @respx.mock
    async def test_count_cap(self, conn):
        result = await ros_ping(conn, address="8.8.8.8", count=200)
        assert "Error" in result
        assert "100" in result

    @respx.mock
    async def test_count_zero(self, conn):
        result = await ros_ping(conn, address="8.8.8.8", count=0)
        assert "Error" in result

    @respx.mock
    async def test_connection_error(self, conn):
        respx.post(f"{BASE}/ping").mock(side_effect=httpx.ConnectError("refused"))
        result = await ros_ping(conn, address="8.8.8.8")
        assert "Connection Error" in result

    async def test_target_not_allowed(self):
        blocked = RouterConnection(host="10.99.99.99")
        with patch("mikrotik_management_mcp.tools.diagnostics.check_target_allowed", return_value=False):
            result = await ros_ping(blocked, address="8.8.8.8")
        assert "not in the allowed targets list" in result

    @respx.mock
    async def test_with_optional_params(self, conn):
        route = respx.post(f"{BASE}/ping").mock(
            return_value=httpx.Response(200, json=[])
        )
        await ros_ping(conn, address="8.8.8.8", count=2, size=1500, src_address="10.0.0.1")
        body = json.loads(route.calls[0].request.content)
        assert body["size"] == "1500"
        assert body["src-address"] == "10.0.0.1"
        assert body["count"] == "2"


@pytest.mark.asyncio
class TestRosTraceroute:
    @respx.mock
    async def test_success(self, conn):
        respx.post(f"{BASE}/tool/traceroute").mock(
            return_value=httpx.Response(200, json=[
                {"hop": "1", "address": "192.168.1.1", "loss": "0", "sent": "1", "last": "1"},
                {"hop": "2", "address": "10.0.0.1", "loss": "0", "sent": "1", "last": "5"},
            ])
        )
        result = await ros_traceroute(conn, address="8.8.8.8")
        data = json.loads(result)
        assert len(data) == 2

    @respx.mock
    async def test_count_cap(self, conn):
        result = await ros_traceroute(conn, address="8.8.8.8", count=50)
        assert "Error" in result
        assert "30" in result


@pytest.mark.asyncio
class TestRosTorch:
    @respx.mock
    async def test_success(self, conn):
        respx.post(f"{BASE}/tool/torch").mock(
            return_value=httpx.Response(200, json=[
                {"src-address": "10.0.0.1", "dst-address": "8.8.8.8", "tx": "1000", "rx": "2000"},
            ])
        )
        result = await ros_torch(conn, interface="ether1", duration=5)
        data = json.loads(result)
        assert len(data) == 1

    @respx.mock
    async def test_duration_cap(self, conn):
        result = await ros_torch(conn, interface="ether1", duration=60)
        assert "Error" in result
        assert "30" in result

    @respx.mock
    async def test_with_filters(self, conn):
        route = respx.post(f"{BASE}/tool/torch").mock(
            return_value=httpx.Response(200, json=[])
        )
        await ros_torch(conn, interface="ether1", src_address="10.0.0.1", dst_address="8.8.8.8", port="80")
        body = json.loads(route.calls[0].request.content)
        assert body["src-address"] == "10.0.0.1"
        assert body["dst-address"] == "8.8.8.8"
        assert body["port"] == "80"

    async def test_target_not_allowed(self):
        blocked = RouterConnection(host="10.99.99.99")
        with patch("mikrotik_management_mcp.tools.diagnostics.check_target_allowed", return_value=False):
            result = await ros_torch(blocked, interface="ether1")
        assert "not in the allowed targets list" in result
