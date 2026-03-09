"""Tests for scheduler convenience tools."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.scheduler import (
    ros_scheduler_add,
    ros_scheduler_list,
    ros_scheduler_remove,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestRosSchedulerAdd:
    @respx.mock
    async def test_add_scheduler_with_hyphen_mapping(self, conn):
        """PUT /rest/system/scheduler with on-event, start-time, interval hyphenated keys."""
        route = respx.put(f"{BASE}/system/scheduler").mock(
            return_value=httpx.Response(
                200,
                json={".id": "*1", "name": "daily-backup", "on-event": "/system backup save name=daily"},
            )
        )
        result = await ros_scheduler_add(
            connection=conn,
            name="daily-backup",
            on_event="/system backup save name=daily",
            start_time="00:00:00",
            interval="1d",
            comment="Nightly backup",
        )
        data = json.loads(result)
        assert data["name"] == "daily-backup"
        # Verify hyphenated keys in request body
        sent = json.loads(route.calls[0].request.content)
        assert sent["name"] == "daily-backup"
        assert sent["on-event"] == "/system backup save name=daily"
        assert sent["start-time"] == "00:00:00"
        assert sent["interval"] == "1d"
        assert sent["comment"] == "Nightly backup"
        # disabled not sent when False (default)
        assert "disabled" not in sent


@pytest.mark.asyncio
class TestRosSchedulerList:
    @respx.mock
    async def test_list_scheduler_entries(self, conn):
        """GET /rest/system/scheduler returns list of scheduler entries."""
        respx.get(f"{BASE}/system/scheduler").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {".id": "*1", "name": "daily-backup", "on-event": "/system backup save name=daily", "interval": "1d"},
                    {".id": "*2", "name": "reboot-weekly", "on-event": "/system reboot", "interval": "7d"},
                ],
            )
        )
        result = await ros_scheduler_list(connection=conn)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "daily-backup"
        assert data[1]["interval"] == "7d"


@pytest.mark.asyncio
class TestRosSchedulerRemove:
    @respx.mock
    async def test_remove_scheduler_entry(self, conn):
        """DELETE /rest/system/scheduler/*1 removes entry."""
        respx.delete(f"{BASE}/system/scheduler/*1").mock(
            return_value=httpx.Response(200, content=b"")
        )
        result = await ros_scheduler_remove(connection=conn, id="*1")
        data = json.loads(result)
        assert data["success"] is True
        assert data["removed"] == "*1"
