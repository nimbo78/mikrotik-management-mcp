"""Tests for IP address convenience tools."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.ip_address import (
    ros_ip_address_add,
    ros_ip_address_list,
    ros_ip_address_remove,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestIpAddressTools:
    @respx.mock
    async def test_add_with_comment_and_disabled(self, conn):
        route = respx.put(f"{BASE}/ip/address").mock(
            return_value=httpx.Response(
                201,
                json={
                    ".id": "*5",
                    "address": "10.0.0.1/24",
                    "interface": "ether1",
                    "comment": "management",
                    "disabled": "true",
                },
            )
        )
        result = await ros_ip_address_add(
            conn, address="10.0.0.1/24", interface="ether1", comment="management", disabled=True
        )
        data = json.loads(result)
        assert data[".id"] == "*5"
        assert data["address"] == "10.0.0.1/24"
        # Verify disabled is sent as string "true"
        body = json.loads(route.calls[0].request.content)
        assert body["address"] == "10.0.0.1/24"
        assert body["interface"] == "ether1"
        assert body["comment"] == "management"
        assert body["disabled"] == "true"

    @respx.mock
    async def test_list(self, conn):
        respx.get(f"{BASE}/ip/address").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {".id": "*1", "address": "10.0.0.1/24", "interface": "ether1"},
                    {".id": "*2", "address": "192.168.1.1/24", "interface": "bridge1"},
                ],
            )
        )
        result = await ros_ip_address_list(conn)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[1]["address"] == "192.168.1.1/24"

    @respx.mock
    async def test_remove(self, conn):
        respx.delete(f"{BASE}/ip/address/*1").mock(
            return_value=httpx.Response(204, content=b"")
        )
        result = await ros_ip_address_remove(conn, id="*1")
        data = json.loads(result)
        assert data["success"] is True
        assert data["removed"] == "*1"
