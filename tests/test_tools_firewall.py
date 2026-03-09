"""Tests for firewall filter and address-list convenience tools."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.firewall import (
    ros_firewall_address_list_add,
    ros_firewall_filter_add,
    ros_firewall_filter_enable,
    ros_firewall_filter_get,
    ros_firewall_filter_list,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestFirewallTools:
    @respx.mock
    async def test_filter_add_param_mapping(self, conn):
        route = respx.put(f"{BASE}/ip/firewall/filter").mock(
            return_value=httpx.Response(
                201,
                json={
                    ".id": "*1",
                    "chain": "forward",
                    "action": "drop",
                    "src-address": "10.0.0.0/8",
                    "protocol": "tcp",
                    "dst-port": "443",
                },
            )
        )
        result = await ros_firewall_filter_add(
            conn,
            chain="forward",
            action="drop",
            src_address="10.0.0.0/8",
            protocol="tcp",
            dst_port="443",
            in_interface="ether1",
            comment="block outbound https",
        )
        data = json.loads(result)
        assert data[".id"] == "*1"
        # Verify underscore -> hyphen mapping in request body
        body = json.loads(route.calls[0].request.content)
        assert body["chain"] == "forward"
        assert body["action"] == "drop"
        assert body["src-address"] == "10.0.0.0/8"
        assert body["protocol"] == "tcp"
        assert body["dst-port"] == "443"
        assert body["in-interface"] == "ether1"
        assert body["comment"] == "block outbound https"

    @respx.mock
    async def test_filter_list(self, conn):
        respx.get(f"{BASE}/ip/firewall/filter").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {".id": "*1", "chain": "input", "action": "accept"},
                    {".id": "*2", "chain": "forward", "action": "drop"},
                ],
            )
        )
        result = await ros_firewall_filter_list(conn)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["chain"] == "input"

    @respx.mock
    async def test_filter_enable(self, conn):
        route = respx.patch(f"{BASE}/ip/firewall/filter/*2").mock(
            return_value=httpx.Response(
                200,
                json={".id": "*2", "chain": "forward", "action": "drop", "disabled": "false"},
            )
        )
        result = await ros_firewall_filter_enable(conn, id="*2")
        data = json.loads(result)
        assert data["disabled"] == "false"
        # Verify PATCH body
        body = json.loads(route.calls[0].request.content)
        assert body["disabled"] == "false"

    @respx.mock
    async def test_address_list_add(self, conn):
        route = respx.put(f"{BASE}/ip/firewall/address-list").mock(
            return_value=httpx.Response(
                201,
                json={
                    ".id": "*5",
                    "list": "blocklist",
                    "address": "1.2.3.4",
                    "comment": "bad actor",
                    "timeout": "1d",
                },
            )
        )
        result = await ros_firewall_address_list_add(
            conn, list="blocklist", address="1.2.3.4", comment="bad actor", timeout="1d"
        )
        data = json.loads(result)
        assert data["list"] == "blocklist"
        assert data["address"] == "1.2.3.4"
        body = json.loads(route.calls[0].request.content)
        assert body["list"] == "blocklist"
        assert body["address"] == "1.2.3.4"
        assert body["comment"] == "bad actor"
        assert body["timeout"] == "1d"

    @respx.mock
    async def test_filter_get_by_id(self, conn):
        respx.get(f"{BASE}/ip/firewall/filter/*A").mock(
            return_value=httpx.Response(
                200,
                json={
                    ".id": "*A",
                    "chain": "input",
                    "action": "accept",
                    "protocol": "icmp",
                },
            )
        )
        result = await ros_firewall_filter_get(conn, id="*A")
        data = json.loads(result)
        assert data[".id"] == "*A"
        assert data["chain"] == "input"
        assert data["protocol"] == "icmp"
