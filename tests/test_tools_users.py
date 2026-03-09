"""Tests for user management convenience tools."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.users import (
    ros_user_add,
    ros_user_active_list,
    ros_user_group_list,
    ros_user_list,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestRosUserAdd:
    @respx.mock
    async def test_add_user_with_password(self, conn):
        """PUT /rest/user with name, group, and password."""
        route = respx.put(f"{BASE}/user").mock(
            return_value=httpx.Response(
                200,
                json={".id": "*3", "name": "monitor", "group": "read"},
            )
        )
        result = await ros_user_add(
            connection=conn, name="monitor", group="read", password="secret123"
        )
        data = json.loads(result)
        assert data[".id"] == "*3"
        assert data["name"] == "monitor"
        # Verify the request body contained the password
        sent = json.loads(route.calls[0].request.content)
        assert sent["name"] == "monitor"
        assert sent["group"] == "read"
        assert sent["password"] == "secret123"


@pytest.mark.asyncio
class TestRosUserList:
    @respx.mock
    async def test_list_users(self, conn):
        """GET /rest/user returns list of users."""
        respx.get(f"{BASE}/user").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {".id": "*1", "name": "admin", "group": "full"},
                    {".id": "*2", "name": "api", "group": "api"},
                ],
            )
        )
        result = await ros_user_list(connection=conn)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "admin"


@pytest.mark.asyncio
class TestRosUserActiveList:
    @respx.mock
    async def test_list_active_sessions(self, conn):
        """GET /rest/user/active returns active sessions."""
        respx.get(f"{BASE}/user/active").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {".id": "*1", "name": "admin", "via": "api", "when": "mar/10/2026 10:00:00"},
                ],
            )
        )
        result = await ros_user_active_list(connection=conn)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["via"] == "api"


@pytest.mark.asyncio
class TestRosUserGroupList:
    @respx.mock
    async def test_list_user_groups(self, conn):
        """GET /rest/user/group returns list of groups."""
        respx.get(f"{BASE}/user/group").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {".id": "*1", "name": "full", "policy": "local,telnet,ssh,ftp,reboot,read,write,policy,test,winbox,password,sniff,sensitive,romon,rest-api"},
                    {".id": "*2", "name": "read", "policy": "local,read,rest-api"},
                ],
            )
        )
        result = await ros_user_group_list(connection=conn)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[1]["name"] == "read"
