"""Tests for DHCP server convenience tools."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.dhcp import (
    ros_dhcp_lease_list,
    ros_dhcp_network_add,
    ros_dhcp_server_add,
    ros_pool_add,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestDhcpTools:
    @respx.mock
    async def test_server_add_param_mapping(self, conn):
        route = respx.put(f"{BASE}/ip/dhcp-server").mock(
            return_value=httpx.Response(
                201,
                json={
                    ".id": "*1",
                    "name": "dhcp1",
                    "interface": "bridge1",
                    "address-pool": "pool1",
                    "disabled": "false",
                },
            )
        )
        result = await ros_dhcp_server_add(
            conn, name="dhcp1", interface="bridge1", address_pool="pool1"
        )
        data = json.loads(result)
        assert data[".id"] == "*1"
        # Verify address_pool -> address-pool mapping
        body = json.loads(route.calls[0].request.content)
        assert body["address-pool"] == "pool1"
        assert body["name"] == "dhcp1"
        assert body["interface"] == "bridge1"
        # disabled should NOT be present when False (default)
        assert "disabled" not in body

    @respx.mock
    async def test_network_add_dns_server_mapping(self, conn):
        route = respx.put(f"{BASE}/ip/dhcp-server/network").mock(
            return_value=httpx.Response(
                201,
                json={
                    ".id": "*2",
                    "address": "10.0.0.0/24",
                    "gateway": "10.0.0.1",
                    "dns-server": "8.8.8.8",
                },
            )
        )
        result = await ros_dhcp_network_add(
            conn, address="10.0.0.0/24", gateway="10.0.0.1", dns_server="8.8.8.8"
        )
        data = json.loads(result)
        assert data["gateway"] == "10.0.0.1"
        # Verify dns_server -> dns-server mapping
        body = json.loads(route.calls[0].request.content)
        assert body["dns-server"] == "8.8.8.8"
        assert body["address"] == "10.0.0.0/24"
        assert body["gateway"] == "10.0.0.1"

    @respx.mock
    async def test_pool_add(self, conn):
        route = respx.put(f"{BASE}/ip/pool").mock(
            return_value=httpx.Response(
                201,
                json={".id": "*3", "name": "pool1", "ranges": "10.0.0.10-10.0.0.100"},
            )
        )
        result = await ros_pool_add(conn, name="pool1", ranges="10.0.0.10-10.0.0.100")
        data = json.loads(result)
        assert data["name"] == "pool1"
        body = json.loads(route.calls[0].request.content)
        assert body["name"] == "pool1"
        assert body["ranges"] == "10.0.0.10-10.0.0.100"

    @respx.mock
    async def test_lease_list(self, conn):
        respx.get(f"{BASE}/ip/dhcp-server/lease").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        ".id": "*1",
                        "address": "10.0.0.50",
                        "mac-address": "AA:BB:CC:DD:EE:FF",
                        "host-name": "laptop",
                        "status": "bound",
                    },
                ],
            )
        )
        result = await ros_dhcp_lease_list(conn)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["address"] == "10.0.0.50"
        assert data[0]["status"] == "bound"
