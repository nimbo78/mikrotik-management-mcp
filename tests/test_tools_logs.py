"""Tests for log viewing convenience tools."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.logs import (
    ros_log_filter_severity,
    ros_log_get,
    ros_log_search_topic,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestRosLogGet:
    @respx.mock
    async def test_get(self, conn):
        respx.get(f"{BASE}/log").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {".id": "*1", "time": "12:00:00", "topics": "system,info", "message": "router rebooted"},
                    {".id": "*2", "time": "12:01:00", "topics": "dhcp,info", "message": "lease assigned"},
                ],
            )
        )
        result = await ros_log_get(conn)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["topics"] == "system,info"


@pytest.mark.asyncio
class TestRosLogSearchTopic:
    @respx.mock
    async def test_search_topic(self, conn):
        route = respx.post(f"{BASE}/log/print").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {".id": "*3", "time": "12:05:00", "topics": "firewall,info", "message": "packet dropped"},
                ],
            )
        )
        result = await ros_log_search_topic(conn, topic="firewall")
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["topics"] == "firewall,info"
        # Verify POST body with .query
        body = json.loads(route.calls[0].request.content)
        assert body[".query"] == ["topics~firewall"]


@pytest.mark.asyncio
class TestRosLogFilterSeverity:
    @respx.mock
    async def test_filter_severity(self, conn):
        route = respx.post(f"{BASE}/log/print").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {".id": "*5", "time": "13:00:00", "topics": "system,error", "message": "disk full"},
                ],
            )
        )
        result = await ros_log_filter_severity(conn, severity="error")
        data = json.loads(result)
        assert len(data) == 1
        assert "error" in data[0]["topics"]
        # Verify POST body with .query
        body = json.loads(route.calls[0].request.content)
        assert body[".query"] == ["topics~error"]
