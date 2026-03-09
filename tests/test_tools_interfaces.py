"""Tests for interface, VLAN, and bridge convenience tools."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.interfaces import (
    ros_bridge_port_add,
    ros_interface_enable,
    ros_interface_get,
    ros_interface_list,
    ros_vlan_add,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestInterfaceTools:
    @respx.mock
    async def test_interface_list(self, conn):
        respx.get(f"{BASE}/interface").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {".id": "*1", "name": "ether1", "type": "ether"},
                    {".id": "*2", "name": "ether2", "type": "ether"},
                ],
            )
        )
        result = await ros_interface_list(conn)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "ether1"

    @respx.mock
    async def test_interface_get_by_name(self, conn):
        respx.get(f"{BASE}/interface/ether1").mock(
            return_value=httpx.Response(
                200,
                json={".id": "*1", "name": "ether1", "type": "ether", "mtu": "1500"},
            )
        )
        result = await ros_interface_get(conn, name="ether1")
        data = json.loads(result)
        assert data["name"] == "ether1"
        assert data["type"] == "ether"

    @respx.mock
    async def test_interface_enable(self, conn):
        route = respx.patch(f"{BASE}/interface/*1").mock(
            return_value=httpx.Response(
                200,
                json={".id": "*1", "name": "ether1", "disabled": "false"},
            )
        )
        result = await ros_interface_enable(conn, id="*1")
        data = json.loads(result)
        assert data["disabled"] == "false"
        # Verify correct PATCH body
        body = json.loads(route.calls[0].request.content)
        assert body["disabled"] == "false"

    @respx.mock
    async def test_vlan_add_param_mapping(self, conn):
        route = respx.put(f"{BASE}/interface/vlan").mock(
            return_value=httpx.Response(
                201,
                json={".id": "*A", "name": "vlan100", "vlan-id": "100", "interface": "ether1"},
            )
        )
        result = await ros_vlan_add(conn, name="vlan100", vlan_id=100, interface="ether1")
        data = json.loads(result)
        assert data[".id"] == "*A"
        # Verify vlan-id is sent as string (not int)
        body = json.loads(route.calls[0].request.content)
        assert body["vlan-id"] == "100"
        assert body["name"] == "vlan100"
        assert body["interface"] == "ether1"

    @respx.mock
    async def test_bridge_port_add(self, conn):
        route = respx.put(f"{BASE}/interface/bridge/port").mock(
            return_value=httpx.Response(
                201,
                json={".id": "*3", "bridge": "bridge1", "interface": "ether2"},
            )
        )
        result = await ros_bridge_port_add(conn, bridge="bridge1", interface="ether2", comment="uplink")
        data = json.loads(result)
        assert data["bridge"] == "bridge1"
        # Verify body includes comment
        body = json.loads(route.calls[0].request.content)
        assert body["bridge"] == "bridge1"
        assert body["interface"] == "ether2"
        assert body["comment"] == "uplink"
