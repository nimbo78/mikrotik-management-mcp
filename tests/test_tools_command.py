"""Tests for ros_command MCP tool."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.command import ros_command


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestRosCommand:
    @respx.mock
    async def test_post_print_command(self, conn):
        """POST print command returns list of resources."""
        respx.post("https://192.168.81.1:443/rest/ip/address/print").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {".id": "*1", "address": "10.0.0.1/24", "interface": "ether1"},
                    {".id": "*2", "address": "192.168.1.1/24", "interface": "bridge"},
                ],
            )
        )
        result = await ros_command(connection=conn, path="ip/address/print")
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0]["address"] == "10.0.0.1/24"
        assert parsed[1][".id"] == "*2"

    @respx.mock
    async def test_command_with_data(self, conn):
        """Command with data passes parameters in POST body."""
        respx.post("https://192.168.81.1:443/rest/tool/ping").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"host": "8.8.8.8", "time": "10ms", "status": ""},
                    {"host": "8.8.8.8", "time": "12ms", "status": ""},
                ],
            )
        )
        result = await ros_command(
            connection=conn,
            path="tool/ping",
            data={"address": "8.8.8.8", "count": "2"},
        )
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0]["host"] == "8.8.8.8"

    @respx.mock
    async def test_command_with_proplist_and_query(self, conn):
        """Command with .proplist and .query filters results."""
        respx.post("https://192.168.81.1:443/rest/ip/firewall/filter/print").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"chain": "input", "action": "accept"},
                    {"chain": "input", "action": "drop"},
                ],
            )
        )
        result = await ros_command(
            connection=conn,
            path="ip/firewall/filter/print",
            data={
                ".proplist": ["chain", "action"],
                ".query": ["chain=input"],
            },
        )
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0]["chain"] == "input"
        assert parsed[1]["action"] == "drop"

    @respx.mock
    async def test_command_no_data(self, conn):
        """Command without data sends POST with no body."""
        respx.post("https://192.168.81.1:443/rest/system/reboot").mock(
            return_value=httpx.Response(200, content=b"")
        )
        result = await ros_command(connection=conn, path="system/reboot")
        parsed = json.loads(result)
        assert parsed == {"success": True}

    @respx.mock
    async def test_timeout_error(self, conn):
        """Timeout returns message suggesting limiting parameters."""
        respx.post("https://192.168.81.1:443/rest/tool/ping").mock(
            side_effect=httpx.ReadTimeout("read timed out")
        )
        result = await ros_command(
            connection=conn,
            path="tool/ping",
            data={"address": "8.8.8.8"},
        )
        assert "Timeout" in result
        assert "192.168.81.1" in result
        assert "limiting parameters" in result

    @respx.mock
    async def test_connect_error(self, conn):
        """Connection error returns a descriptive message."""
        respx.post("https://192.168.81.1:443/rest/system/resource/print").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        result = await ros_command(connection=conn, path="system/resource/print")
        assert "Connection Error" in result
        assert "192.168.81.1" in result

    @respx.mock
    async def test_routeros_error(self, conn):
        """RouterOS 400 error returns status code and message."""
        respx.post("https://192.168.81.1:443/rest/bad/command").mock(
            return_value=httpx.Response(
                400,
                json={"message": "no such command", "detail": "bad request"},
            )
        )
        result = await ros_command(connection=conn, path="bad/command")
        assert "RouterOS Error" in result
        assert "400" in result
        assert "no such command" in result

    async def test_target_not_allowed(self, monkeypatch):
        """Blocked target returns an error without making a request."""
        import mikrotik_management_mcp.security as security

        monkeypatch.setattr(security, "ALLOWED_TARGETS", [])
        # Load a restricted list
        monkeypatch.setenv("ALLOWED_TARGETS", "10.0.0.0/8")
        security.load_security_config()

        blocked_conn = RouterConnection(host="192.168.81.1")
        result = await ros_command(connection=blocked_conn, path="ip/address/print")
        assert "not in the allowed targets list" in result

        # Cleanup
        monkeypatch.delenv("ALLOWED_TARGETS", raising=False)
        security.load_security_config()

    @respx.mock
    async def test_unexpected_error(self, conn):
        """Unexpected exception is caught and formatted."""
        respx.post("https://192.168.81.1:443/rest/ip/address/print").mock(
            side_effect=RuntimeError("something unexpected")
        )
        result = await ros_command(connection=conn, path="ip/address/print")
        assert "Unexpected Error" in result
        assert "RuntimeError" in result
        assert "something unexpected" in result
