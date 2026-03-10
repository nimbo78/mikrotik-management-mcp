"""Tests for safe change workflow tools."""

import json

import httpx
import pytest
import respx
from unittest.mock import patch

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.safe_change import (
    ros_safe_change_start,
    ros_safe_change_confirm,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestRosSafeChangeStart:
    @respx.mock
    async def test_success(self, conn):
        respx.post(f"{BASE}/system/backup/save").mock(
            return_value=httpx.Response(200, json={})
        )
        respx.put(f"{BASE}/system/scheduler").mock(
            return_value=httpx.Response(201, json={".id": "*A", "name": "mcp-safe-revert-123"})
        )
        result = await ros_safe_change_start(conn, revert_minutes=5)
        data = json.loads(result)
        assert data["success"] is True
        assert data["scheduler_id"] == "*A"
        assert data["revert_minutes"] == 5
        assert "backup_name" in data

    @respx.mock
    async def test_revert_minutes_too_high(self, conn):
        result = await ros_safe_change_start(conn, revert_minutes=60)
        assert "Error" in result
        assert "30" in result

    @respx.mock
    async def test_revert_minutes_too_low(self, conn):
        result = await ros_safe_change_start(conn, revert_minutes=0)
        assert "Error" in result

    @respx.mock
    async def test_connection_error(self, conn):
        respx.post(f"{BASE}/system/backup/save").mock(
            side_effect=httpx.ConnectError("refused")
        )
        result = await ros_safe_change_start(conn)
        assert "Connection Error" in result

    async def test_target_not_allowed(self):
        blocked = RouterConnection(host="10.99.99.99")
        with patch("mikrotik_management_mcp.tools.safe_change.check_target_allowed", return_value=False):
            result = await ros_safe_change_start(blocked)
        assert "not in the allowed targets list" in result


@pytest.mark.asyncio
class TestRosSafeChangeConfirm:
    @respx.mock
    async def test_success(self, conn):
        respx.delete(f"{BASE}/system/scheduler/*A").mock(
            return_value=httpx.Response(200, content=b"")
        )
        result = await ros_safe_change_confirm(conn, scheduler_id="*A")
        data = json.loads(result)
        assert data["success"] is True
        assert "confirmed" in data["message"].lower() or "permanent" in data["message"].lower()

    @respx.mock
    async def test_not_found(self, conn):
        respx.delete(f"{BASE}/system/scheduler/*Z").mock(
            return_value=httpx.Response(404, json={"message": "no such item"})
        )
        result = await ros_safe_change_confirm(conn, scheduler_id="*Z")
        assert "RouterOS Error (404)" in result

    async def test_target_not_allowed(self):
        blocked = RouterConnection(host="10.99.99.99")
        with patch("mikrotik_management_mcp.tools.safe_change.check_target_allowed", return_value=False):
            result = await ros_safe_change_confirm(blocked, scheduler_id="*1")
        assert "not in the allowed targets list" in result
