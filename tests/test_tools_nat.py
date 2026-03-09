"""Tests for NAT convenience tools."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.nat import (
    ros_nat_add,
    ros_nat_enable,
    ros_nat_list,
    ros_nat_remove,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestRosNatAdd:
    @respx.mock
    async def test_add_with_params(self, conn):
        route = respx.put(f"{BASE}/ip/firewall/nat").mock(
            return_value=httpx.Response(
                201,
                json={
                    ".id": "*1",
                    "chain": "dstnat",
                    "action": "dst-nat",
                    "src-address": "10.0.0.0/24",
                    "dst-port": "8080",
                    "to-addresses": "192.168.1.100",
                    "to-ports": "80",
                    "protocol": "tcp",
                },
            )
        )
        result = await ros_nat_add(
            conn,
            chain="dstnat",
            action="dst-nat",
            src_address="10.0.0.0/24",
            protocol="tcp",
            dst_port="8080",
            to_addresses="192.168.1.100",
            to_ports="80",
        )
        data = json.loads(result)
        assert data[".id"] == "*1"
        # Verify hyphen-mapped keys in request body
        body = json.loads(route.calls[0].request.content)
        assert body["chain"] == "dstnat"
        assert body["action"] == "dst-nat"
        assert body["src-address"] == "10.0.0.0/24"
        assert body["dst-port"] == "8080"
        assert body["to-addresses"] == "192.168.1.100"
        assert body["to-ports"] == "80"
        assert body["protocol"] == "tcp"


@pytest.mark.asyncio
class TestRosNatList:
    @respx.mock
    async def test_list(self, conn):
        respx.get(f"{BASE}/ip/firewall/nat").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {".id": "*1", "chain": "srcnat", "action": "masquerade"},
                    {".id": "*2", "chain": "dstnat", "action": "dst-nat"},
                ],
            )
        )
        result = await ros_nat_list(conn)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["chain"] == "srcnat"


@pytest.mark.asyncio
class TestRosNatEnable:
    @respx.mock
    async def test_enable(self, conn):
        route = respx.patch(f"{BASE}/ip/firewall/nat/*3").mock(
            return_value=httpx.Response(
                200,
                json={".id": "*3", "disabled": "false"},
            )
        )
        result = await ros_nat_enable(conn, id="*3")
        data = json.loads(result)
        assert data["disabled"] == "false"
        # Verify PATCH body sets disabled to false
        body = json.loads(route.calls[0].request.content)
        assert body["disabled"] == "false"


@pytest.mark.asyncio
class TestRosNatRemove:
    @respx.mock
    async def test_remove(self, conn):
        respx.delete(f"{BASE}/ip/firewall/nat/*2").mock(
            return_value=httpx.Response(204, content=b"")
        )
        result = await ros_nat_remove(conn, id="*2")
        data = json.loads(result)
        assert data["success"] is True
        assert data["removed"] == "*2"
