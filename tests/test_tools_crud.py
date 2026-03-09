"""Tests for CRUD tools (ros_get, ros_add, ros_update, ros_remove)."""

import json
import os

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.security import load_security_config
from mikrotik_management_mcp.tools.crud import ros_add, ros_get, ros_remove, ros_update

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


# ---------------------------------------------------------------------------
# ros_get
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestRosGet:
    @respx.mock
    async def test_list_all(self, conn):
        respx.get(f"{BASE}/ip/address").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {".id": "*1", "address": "10.0.0.1/24", "interface": "ether1"},
                    {".id": "*2", "address": "10.0.0.2/24", "interface": "ether2"},
                ],
            )
        )
        result = await ros_get(conn, path="ip/address")
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0][".id"] == "*1"

    @respx.mock
    async def test_get_by_id(self, conn):
        respx.get(f"{BASE}/ip/address/*1").mock(
            return_value=httpx.Response(
                200,
                json={".id": "*1", "address": "10.0.0.1/24", "interface": "ether1"},
            )
        )
        result = await ros_get(conn, path="ip/address", id="*1")
        data = json.loads(result)
        assert data[".id"] == "*1"
        assert data["address"] == "10.0.0.1/24"

    @respx.mock
    async def test_get_by_name(self, conn):
        respx.get(f"{BASE}/interface/ether1").mock(
            return_value=httpx.Response(
                200,
                json={".id": "*1", "name": "ether1", "type": "ether"},
            )
        )
        result = await ros_get(conn, path="interface", id="ether1")
        data = json.loads(result)
        assert data["name"] == "ether1"

    @respx.mock
    async def test_get_with_proplist(self, conn):
        route = respx.get(f"{BASE}/ip/address").mock(
            return_value=httpx.Response(
                200,
                json=[{"address": "10.0.0.1/24", "interface": "ether1"}],
            )
        )
        result = await ros_get(conn, path="ip/address", proplist="address,interface")
        data = json.loads(result)
        assert len(data) == 1
        # Verify proplist was sent as query parameter
        assert route.calls[0].request.url.params[".proplist"] == "address,interface"

    @respx.mock
    async def test_get_with_query(self, conn):
        route = respx.get(f"{BASE}/ip/address").mock(
            return_value=httpx.Response(
                200,
                json=[{".id": "*3", "address": "10.0.0.0/24", "dynamic": "true"}],
            )
        )
        result = await ros_get(
            conn, path="ip/address", query={"network": "10.0.0.0", "dynamic": "true"}
        )
        data = json.loads(result)
        assert len(data) == 1
        assert route.calls[0].request.url.params["network"] == "10.0.0.0"
        assert route.calls[0].request.url.params["dynamic"] == "true"

    @respx.mock
    async def test_get_with_proplist_and_query(self, conn):
        route = respx.get(f"{BASE}/ip/address").mock(
            return_value=httpx.Response(200, json=[{"address": "10.0.0.1/24"}])
        )
        result = await ros_get(
            conn,
            path="ip/address",
            proplist="address",
            query={"dynamic": "true"},
        )
        data = json.loads(result)
        assert len(data) == 1
        params = route.calls[0].request.url.params
        assert params[".proplist"] == "address"
        assert params["dynamic"] == "true"

    @respx.mock
    async def test_get_empty_list(self, conn):
        respx.get(f"{BASE}/ip/address").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await ros_get(conn, path="ip/address")
        assert json.loads(result) == []

    @respx.mock
    async def test_get_routeros_error(self, conn):
        respx.get(f"{BASE}/bad/path").mock(
            return_value=httpx.Response(
                400, json={"message": "no such command", "detail": "bad path"}
            )
        )
        result = await ros_get(conn, path="bad/path")
        assert "RouterOS Error (400)" in result
        assert "no such command" in result

    @respx.mock
    async def test_get_connection_error(self, conn):
        respx.get(f"{BASE}/ip/address").mock(side_effect=httpx.ConnectError("refused"))
        result = await ros_get(conn, path="ip/address")
        assert "Connection Error" in result
        assert "192.168.81.1" in result

    @respx.mock
    async def test_get_timeout_error(self, conn):
        respx.get(f"{BASE}/ip/address").mock(
            side_effect=httpx.ReadTimeout("timed out")
        )
        result = await ros_get(conn, path="ip/address")
        assert "Timeout" in result
        assert "192.168.81.1" in result

    @respx.mock
    async def test_get_unexpected_error(self, conn):
        respx.get(f"{BASE}/ip/address").mock(side_effect=RuntimeError("boom"))
        result = await ros_get(conn, path="ip/address")
        assert "Unexpected Error" in result
        assert "RuntimeError" in result
        assert "boom" in result

    async def test_get_target_not_allowed(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_TARGETS", "10.0.0.0/8")
        load_security_config()
        conn = RouterConnection(host="192.168.81.1")
        result = await ros_get(conn, path="ip/address")
        assert "not in the allowed targets list" in result

    def teardown_method(self):
        os.environ.pop("ALLOWED_TARGETS", None)
        load_security_config()


# ---------------------------------------------------------------------------
# ros_add
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestRosAdd:
    @respx.mock
    async def test_add_success(self, conn):
        respx.put(f"{BASE}/ip/address").mock(
            return_value=httpx.Response(
                201,
                json={
                    ".id": "*5",
                    "address": "10.0.0.5/24",
                    "interface": "ether1",
                    "disabled": "false",
                },
            )
        )
        result = await ros_add(
            conn,
            path="ip/address",
            data={"address": "10.0.0.5/24", "interface": "ether1"},
        )
        data = json.loads(result)
        assert data[".id"] == "*5"
        assert data["address"] == "10.0.0.5/24"

    @respx.mock
    async def test_add_sends_json_body(self, conn):
        route = respx.put(f"{BASE}/ip/firewall/filter").mock(
            return_value=httpx.Response(201, json={".id": "*A"})
        )
        await ros_add(
            conn,
            path="ip/firewall/filter",
            data={"chain": "forward", "action": "accept"},
        )
        request = route.calls[0].request
        body = json.loads(request.content)
        assert body["chain"] == "forward"
        assert body["action"] == "accept"

    @respx.mock
    async def test_add_routeros_error(self, conn):
        respx.put(f"{BASE}/ip/address").mock(
            return_value=httpx.Response(
                400,
                json={"message": "failure: already have such address"},
            )
        )
        result = await ros_add(
            conn, path="ip/address", data={"address": "10.0.0.1/24", "interface": "ether1"}
        )
        assert "RouterOS Error (400)" in result
        assert "already have such address" in result

    @respx.mock
    async def test_add_connection_error(self, conn):
        respx.put(f"{BASE}/ip/address").mock(side_effect=httpx.ConnectError("refused"))
        result = await ros_add(conn, path="ip/address", data={"address": "10.0.0.1/24"})
        assert "Connection Error" in result

    @respx.mock
    async def test_add_timeout(self, conn):
        respx.put(f"{BASE}/ip/address").mock(
            side_effect=httpx.ReadTimeout("timed out")
        )
        result = await ros_add(conn, path="ip/address", data={"address": "10.0.0.1/24"})
        assert "Timeout" in result

    async def test_add_target_not_allowed(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_TARGETS", "10.0.0.0/8")
        load_security_config()
        conn = RouterConnection(host="192.168.81.1")
        result = await ros_add(conn, path="ip/address", data={"address": "10.0.0.1/24"})
        assert "not in the allowed targets list" in result

    def teardown_method(self):
        os.environ.pop("ALLOWED_TARGETS", None)
        load_security_config()


# ---------------------------------------------------------------------------
# ros_update
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestRosUpdate:
    @respx.mock
    async def test_update_success(self, conn):
        respx.patch(f"{BASE}/ip/address/*1").mock(
            return_value=httpx.Response(
                200,
                json={
                    ".id": "*1",
                    "address": "10.0.0.1/24",
                    "comment": "updated",
                    "disabled": "false",
                },
            )
        )
        result = await ros_update(
            conn, path="ip/address", id="*1", data={"comment": "updated"}
        )
        data = json.loads(result)
        assert data[".id"] == "*1"
        assert data["comment"] == "updated"

    @respx.mock
    async def test_update_sends_patch(self, conn):
        route = respx.patch(f"{BASE}/ip/address/*2").mock(
            return_value=httpx.Response(
                200, json={".id": "*2", "disabled": "true"}
            )
        )
        await ros_update(
            conn, path="ip/address", id="*2", data={"disabled": "true"}
        )
        request = route.calls[0].request
        assert request.method == "PATCH"
        body = json.loads(request.content)
        assert body["disabled"] == "true"

    @respx.mock
    async def test_update_not_found(self, conn):
        respx.patch(f"{BASE}/ip/address/*FF").mock(
            return_value=httpx.Response(
                404, json={"message": "no such item"}
            )
        )
        result = await ros_update(
            conn, path="ip/address", id="*FF", data={"comment": "test"}
        )
        assert "RouterOS Error (404)" in result
        assert "no such item" in result

    @respx.mock
    async def test_update_connection_error(self, conn):
        respx.patch(f"{BASE}/ip/address/*1").mock(
            side_effect=httpx.ConnectError("refused")
        )
        result = await ros_update(
            conn, path="ip/address", id="*1", data={"comment": "test"}
        )
        assert "Connection Error" in result

    @respx.mock
    async def test_update_timeout(self, conn):
        respx.patch(f"{BASE}/ip/address/*1").mock(
            side_effect=httpx.ReadTimeout("timed out")
        )
        result = await ros_update(
            conn, path="ip/address", id="*1", data={"comment": "test"}
        )
        assert "Timeout" in result

    async def test_update_target_not_allowed(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_TARGETS", "10.0.0.0/8")
        load_security_config()
        conn = RouterConnection(host="192.168.81.1")
        result = await ros_update(conn, path="ip/address", id="*1", data={"comment": "test"})
        assert "not in the allowed targets list" in result

    def teardown_method(self):
        os.environ.pop("ALLOWED_TARGETS", None)
        load_security_config()


# ---------------------------------------------------------------------------
# ros_remove
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestRosRemove:
    @respx.mock
    async def test_remove_success(self, conn):
        respx.delete(f"{BASE}/ip/address/*1").mock(
            return_value=httpx.Response(204, content=b"")
        )
        result = await ros_remove(conn, path="ip/address", id="*1")
        data = json.loads(result)
        assert data["success"] is True
        assert data["removed"] == "*1"

    @respx.mock
    async def test_remove_hex_id(self, conn):
        respx.delete(f"{BASE}/ip/firewall/filter/*A").mock(
            return_value=httpx.Response(204, content=b"")
        )
        result = await ros_remove(conn, path="ip/firewall/filter", id="*A")
        data = json.loads(result)
        assert data["success"] is True
        assert data["removed"] == "*A"

    @respx.mock
    async def test_remove_not_found(self, conn):
        respx.delete(f"{BASE}/ip/address/*FF").mock(
            return_value=httpx.Response(404, json={"message": "no such item"})
        )
        result = await ros_remove(conn, path="ip/address", id="*FF")
        assert "RouterOS Error (404)" in result
        assert "no such item" in result

    @respx.mock
    async def test_remove_connection_error(self, conn):
        respx.delete(f"{BASE}/ip/address/*1").mock(
            side_effect=httpx.ConnectError("refused")
        )
        result = await ros_remove(conn, path="ip/address", id="*1")
        assert "Connection Error" in result

    @respx.mock
    async def test_remove_timeout(self, conn):
        respx.delete(f"{BASE}/ip/address/*1").mock(
            side_effect=httpx.ReadTimeout("timed out")
        )
        result = await ros_remove(conn, path="ip/address", id="*1")
        assert "Timeout" in result

    async def test_remove_target_not_allowed(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_TARGETS", "10.0.0.0/8")
        load_security_config()
        conn = RouterConnection(host="192.168.81.1")
        result = await ros_remove(conn, path="ip/address", id="*1")
        assert "not in the allowed targets list" in result

    def teardown_method(self):
        os.environ.pop("ALLOWED_TARGETS", None)
        load_security_config()
