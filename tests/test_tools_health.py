"""Tests for health check and export tools."""

import json

import httpx
import pytest
import respx
from unittest.mock import patch

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.health import (
    ros_health_check,
    ros_export,
)

BASE = "https://192.168.81.1:443/rest"

MOCK_RESOURCE = {
    "board-name": "hAP ax3",
    "version": "7.16.2 (stable)",
    "uptime": "1d2h",
    "cpu-load": "5",
    "total-memory": "1073741824",
    "free-memory": "536870912",
    "total-hdd-space": "134217728",
    "free-hdd-space": "67108864",
}


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestRosHealthCheck:
    @respx.mock
    async def test_success(self, conn):
        respx.get(f"{BASE}/system/resource").mock(
            return_value=httpx.Response(200, json=MOCK_RESOURCE)
        )
        respx.get(f"{BASE}/system/health").mock(
            return_value=httpx.Response(200, json=[
                {"name": "temperature", "value": "45", "unit": "C"},
            ])
        )
        respx.get(f"{BASE}/ip/firewall/connection/tracking").mock(
            return_value=httpx.Response(200, json=[{
                "total-entries": "500",
                "max-entries": "16384",
            }])
        )
        respx.get(f"{BASE}/interface").mock(
            return_value=httpx.Response(200, json=[
                {"name": "ether1", "tx-error": "0", "rx-error": "0", "tx-drop": "0", "rx-drop": "0"},
            ])
        )

        result = await ros_health_check(conn)
        assert "hAP ax3" in result
        assert "CPU Load" in result
        assert "Memory" in result
        assert "temperature" in result
        assert "500 / 16384" in result
        assert "No interface errors" in result

    @respx.mock
    async def test_with_interface_errors(self, conn):
        respx.get(f"{BASE}/system/resource").mock(
            return_value=httpx.Response(200, json=MOCK_RESOURCE)
        )
        respx.get(f"{BASE}/system/health").mock(
            return_value=httpx.Response(200, json=[])
        )
        respx.get(f"{BASE}/ip/firewall/connection/tracking").mock(
            return_value=httpx.Response(200, json=[{
                "total-entries": "100",
                "max-entries": "16384",
            }])
        )
        respx.get(f"{BASE}/interface").mock(
            return_value=httpx.Response(200, json=[
                {"name": "ether1", "tx-error": "5", "rx-error": "0", "tx-drop": "0", "rx-drop": "0"},
            ])
        )

        result = await ros_health_check(conn)
        assert "ether1" in result
        assert "tx-error=5" in result

    async def test_target_not_allowed(self):
        blocked = RouterConnection(host="10.99.99.99")
        with patch("mikrotik_management_mcp.tools.health.check_target_allowed", return_value=False):
            result = await ros_health_check(blocked)
        assert "not in the allowed targets list" in result

    @respx.mock
    async def test_resource_connection_error(self, conn):
        respx.get(f"{BASE}/system/resource").mock(
            side_effect=httpx.ConnectError("refused")
        )
        result = await ros_health_check(conn)
        # Should still return some output even if resource fails
        assert "ERROR" in result or "Error" in result


@pytest.mark.asyncio
class TestRosExport:
    @respx.mock
    async def test_full_export(self, conn):
        respx.post(f"{BASE}/export").mock(
            return_value=httpx.Response(200, text="# 2024-01-01\n/ip address\nadd address=10.0.0.1/24 interface=ether1\n")
        )
        result = await ros_export(conn)
        assert "/ip address" in result
        assert "10.0.0.1/24" in result

    @respx.mock
    async def test_section_export(self, conn):
        respx.post(f"{BASE}/ip/firewall/export").mock(
            return_value=httpx.Response(200, text="/ip firewall filter\nadd chain=forward action=accept\n")
        )
        result = await ros_export(conn, section="ip/firewall")
        assert "/ip firewall" in result

    @respx.mock
    async def test_connection_error(self, conn):
        respx.post(f"{BASE}/export").mock(side_effect=httpx.ConnectError("refused"))
        result = await ros_export(conn)
        assert "Connection Error" in result

    async def test_target_not_allowed(self):
        blocked = RouterConnection(host="10.99.99.99")
        with patch("mikrotik_management_mcp.tools.health.check_target_allowed", return_value=False):
            result = await ros_export(blocked)
        assert "not in the allowed targets list" in result
