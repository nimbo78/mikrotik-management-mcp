"""Tests for ARP and neighbor discovery tools."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.neighbors import (
    ros_arp_list,
    ros_neighbor_list,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestNeighborTools:
    @respx.mock
    async def test_arp_list(self, conn):
        respx.get(f"{BASE}/ip/arp").mock(
            return_value=httpx.Response(200, json=[
                {".id": "*1", "address": "10.0.0.1", "mac-address": "AA:BB:CC:DD:EE:FF", "interface": "bridge1"},
            ])
        )
        result = await ros_arp_list(conn)
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["address"] == "10.0.0.1"
        assert data[0]["mac-address"] == "AA:BB:CC:DD:EE:FF"

    @respx.mock
    async def test_neighbor_list(self, conn):
        respx.get(f"{BASE}/ip/neighbor").mock(
            return_value=httpx.Response(200, json=[
                {".id": "*1", "identity": "MikroTik-2", "address": "10.0.0.2", "interface": "ether1", "platform": "MikroTik"},
            ])
        )
        result = await ros_neighbor_list(conn)
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["identity"] == "MikroTik-2"
