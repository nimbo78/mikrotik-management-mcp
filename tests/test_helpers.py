"""Tests for the _helpers module (tool_request and tool_request_delete)."""

import json
import os

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.security import load_security_config
from mikrotik_management_mcp.tools._helpers import tool_request, tool_request_delete

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


# ---------------------------------------------------------------------------
# tool_request
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestToolRequest:
    @respx.mock
    async def test_get_success(self, conn):
        respx.get(f"{BASE}/ip/address").mock(
            return_value=httpx.Response(
                200,
                json=[{".id": "*1", "address": "10.0.0.1/24"}],
            )
        )
        result = await tool_request(conn, "GET", "ip/address")
        data = json.loads(result)
        assert isinstance(data, list)
        assert data[0][".id"] == "*1"

    @respx.mock
    async def test_put_success(self, conn):
        respx.put(f"{BASE}/ip/address").mock(
            return_value=httpx.Response(
                201,
                json={".id": "*5", "address": "10.0.0.5/24"},
            )
        )
        result = await tool_request(
            conn, "PUT", "ip/address", data={"address": "10.0.0.5/24"}
        )
        data = json.loads(result)
        assert data[".id"] == "*5"

    @respx.mock
    async def test_patch_success(self, conn):
        respx.patch(f"{BASE}/ip/address/*1").mock(
            return_value=httpx.Response(
                200,
                json={".id": "*1", "comment": "updated"},
            )
        )
        result = await tool_request(
            conn, "PATCH", "ip/address/*1", data={"comment": "updated"}
        )
        data = json.loads(result)
        assert data["comment"] == "updated"

    @respx.mock
    async def test_post_success(self, conn):
        respx.post(f"{BASE}/ip/dns/set").mock(
            return_value=httpx.Response(200, json={})
        )
        result = await tool_request(
            conn, "POST", "ip/dns/set", data={"servers": "8.8.8.8"}
        )
        data = json.loads(result)
        assert isinstance(data, dict)

    @respx.mock
    async def test_with_params(self, conn):
        route = respx.get(f"{BASE}/ip/address").mock(
            return_value=httpx.Response(200, json=[])
        )
        await tool_request(conn, "GET", "ip/address", params={".proplist": "address"})
        assert route.calls[0].request.url.params[".proplist"] == "address"

    @respx.mock
    async def test_custom_timeout(self, conn):
        respx.post(f"{BASE}/tool/ping").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await tool_request(
            conn, "POST", "tool/ping", data={"address": "8.8.8.8"}, timeout=60.0
        )
        assert json.loads(result) == []

    @respx.mock
    async def test_routeros_error(self, conn):
        respx.get(f"{BASE}/bad/path").mock(
            return_value=httpx.Response(
                400, json={"message": "no such command"}
            )
        )
        result = await tool_request(conn, "GET", "bad/path")
        assert "RouterOS Error (400)" in result
        assert "no such command" in result

    @respx.mock
    async def test_connection_error(self, conn):
        respx.get(f"{BASE}/ip/address").mock(
            side_effect=httpx.ConnectError("refused")
        )
        result = await tool_request(conn, "GET", "ip/address")
        assert "Connection Error" in result
        assert "192.168.81.1" in result

    @respx.mock
    async def test_timeout_error(self, conn):
        respx.get(f"{BASE}/ip/address").mock(
            side_effect=httpx.ReadTimeout("timed out")
        )
        result = await tool_request(conn, "GET", "ip/address")
        assert "Timeout" in result
        assert "192.168.81.1" in result

    @respx.mock
    async def test_unexpected_error(self, conn):
        respx.get(f"{BASE}/ip/address").mock(
            side_effect=RuntimeError("boom")
        )
        result = await tool_request(conn, "GET", "ip/address")
        assert "Unexpected Error" in result
        assert "RuntimeError" in result
        assert "boom" in result

    async def test_target_not_allowed(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_TARGETS", "10.0.0.0/8")
        load_security_config()
        conn = RouterConnection(host="192.168.81.1")
        result = await tool_request(conn, "GET", "ip/address")
        assert "not in the allowed targets list" in result

    def teardown_method(self):
        os.environ.pop("ALLOWED_TARGETS", None)
        load_security_config()


# ---------------------------------------------------------------------------
# tool_request_delete
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestToolRequestDelete:
    @respx.mock
    async def test_delete_success(self, conn):
        respx.delete(f"{BASE}/ip/address/*1").mock(
            return_value=httpx.Response(204, content=b"")
        )
        result = await tool_request_delete(conn, "ip/address", "*1")
        data = json.loads(result)
        assert data["success"] is True
        assert data["removed"] == "*1"

    @respx.mock
    async def test_delete_not_found(self, conn):
        respx.delete(f"{BASE}/ip/address/*FF").mock(
            return_value=httpx.Response(404, json={"message": "no such item"})
        )
        result = await tool_request_delete(conn, "ip/address", "*FF")
        assert "RouterOS Error (404)" in result
        assert "no such item" in result

    @respx.mock
    async def test_delete_connection_error(self, conn):
        respx.delete(f"{BASE}/ip/address/*1").mock(
            side_effect=httpx.ConnectError("refused")
        )
        result = await tool_request_delete(conn, "ip/address", "*1")
        assert "Connection Error" in result

    @respx.mock
    async def test_delete_timeout_error(self, conn):
        respx.delete(f"{BASE}/ip/address/*1").mock(
            side_effect=httpx.ReadTimeout("timed out")
        )
        result = await tool_request_delete(conn, "ip/address", "*1")
        assert "Timeout" in result

    async def test_delete_target_not_allowed(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_TARGETS", "10.0.0.0/8")
        load_security_config()
        conn = RouterConnection(host="192.168.81.1")
        result = await tool_request_delete(conn, "ip/address", "*1")
        assert "not in the allowed targets list" in result

    def teardown_method(self):
        os.environ.pop("ALLOWED_TARGETS", None)
        load_security_config()
